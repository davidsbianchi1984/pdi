"""At-rest encryption for the private vault — production-grade key management.

Envelope encryption, the pattern a real KMS/HSM uses:

- A **key-encryption key (KEK)** never touches record data. In production it
  lives in the corporation's KMS/HSM and is reached through a *key provider*
  (``PDI_KEY_PROVIDER``); in dev it comes from ``PDI_MASTER_KEY`` (base64, 32
  bytes), or an ephemeral key if unset.
- Each **key version** owns a random **data-encryption key (DEK)**. The DEK is
  what actually seals records (AES-256-GCM). The DEK is stored only *wrapped*
  (encrypted) by the KEK, so the database on disk never holds usable key
  material — the same guarantee the vault gives the data it holds.
- **Rotation** mints a new version + DEK and makes it active. Old versions are
  kept so existing ciphertext still decrypts; ``reseal`` re-encrypts records
  under the active version and old versions can then be retired.

Sealed format: ``"<version>:" + base64(nonce || ciphertext)``. Blobs written by
earlier releases (no version prefix) are still read, using the KEK directly, and
are upgraded to a version on the next write or ``reseal``.

**BYOK.** A tenant can bring its own KEK, which is what makes outsourced
hosting a different proposition from trusting the operator. Such a tenant gets
its own keyring (``tenant_key_versions``), wrapped by a key the operator does
not hold:

- ``held`` — the customer presents the key on every request. Nothing derived
  from it is written to disk, so the operator's database, backups, and disk
  images are unreadable without the customer's participation. Read
  :func:`custody` for what this does and does not promise.
- ``kms`` — the KEK lives in the customer's own KMS and PDI calls out to
  unwrap. The operator can decrypt while the customer's grant is live and
  cannot after the customer revokes it. An integration seam, not finished.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from . import db

_EPHEMERAL: bytes | None = None


class CustomerKeyRequired(Exception):
    """This tenant's records are sealed under a key the deployment does not
    have. The caller must present it (``x-tenant-key``)."""


class CustomerKeyMismatch(Exception):
    """A key was presented, but it is not the one this tenant's records were
    sealed under. Refused before use so a wrong key cannot quietly write
    records nothing can later open."""


# --------------------------------------------------------------------------- #
# key provider — where the KEK lives (env in dev, KMS/HSM in production)
# --------------------------------------------------------------------------- #
def _kek() -> bytes:
    """The key-encryption key. ``PDI_KEY_PROVIDER=kms`` routes to a hosted HSM
    (see ``KmsKeyProvider``); the default ``env`` provider reads
    ``PDI_MASTER_KEY``."""
    provider = os.environ.get("PDI_KEY_PROVIDER", "env")
    if provider == "kms":
        return KmsKeyProvider().kek()
    raw = os.environ.get("PDI_MASTER_KEY")
    if raw:
        key = base64.b64decode(raw)
        if len(key) != 32:
            raise ValueError("PDI_MASTER_KEY must be base64 of 32 bytes")
        return key
    # No configured key. An ephemeral one is fine for a laptop — but it lives
    # only in this process, so anything sealed under it is unreadable after a
    # restart. On a published deployment that is silent, unrecoverable data
    # loss, which is worse than refusing to start: fail closed instead.
    from . import mobile
    if mobile.public_base():
        raise RuntimeError(
            "PDI_PUBLIC_URL is set (this deployment is published) but no key "
            "is configured. Set PDI_MASTER_KEY (base64 of 32 bytes) or "
            "PDI_KEY_PROVIDER=kms — an ephemeral key would make every sealed "
            "record unreadable after the next restart.")
    global _EPHEMERAL
    if _EPHEMERAL is None:
        _EPHEMERAL = AESGCM.generate_key(bit_length=256)
    return _EPHEMERAL


class KmsUnavailable(Exception):
    """The KMS could not be reached, or is not configured to be reachable.

    Its own class rather than a bare ``RuntimeError`` because a caller must be
    able to tell *the key store is down* from *the key is wrong*: the first is
    an outage to retry and page about, the second is a refusal that retrying
    will never fix.
    """


#: How long an unwrapped KEK may be held in memory before the KMS is asked
#: again. Not zero: an unwrap per record would make the vault's throughput a
#: function of somebody's KMS quota, and the API call is also billed. Not
#: unbounded: a revoked key must stop working within a bounded time, and
#: "until the next deploy" is not bounded.
KEK_CACHE_SECONDS = 300

_KEK_CACHE: dict[str, tuple[bytes, float]] = {}


def clear_kek_cache() -> None:
    """Drop every cached KEK. Called after a key is retired or rotated, and by
    tests that would otherwise inherit a previous case's key."""
    _KEK_CACHE.clear()


class KmsKeyProvider:
    """Production key provider — the KEK lives in a cloud KMS or an HSM and is
    unwrapped on demand, never stored on the app host.

    ## The shape, and why it is unwrap rather than fetch

    PDI does not ask the KMS *for* a key. It stores a **wrapped** KEK
    (``PDI_KMS_WRAPPED_KEK``, base64 of the ciphertext blob the KMS returned
    when the KEK was created) and asks the KMS to **decrypt** it. That is the
    difference between a deployment whose database leak costs you the data and
    one where it costs you nothing: the blob is useless without the KMS, the
    KMS enforces its own policy on every call, and every unwrap is a line in
    the customer's CloudTrail rather than a thing that silently happened here.

    ## Backends

    * ``aws`` — ``kms:Decrypt`` through boto3, with an encryption context
      binding the blob to this deployment so a blob lifted from one tenant
      cannot be replayed against another.
    * ``pkcs11`` — a ``C_UnwrapKey`` against a hardware token through
      ``python-pkcs11``.

    Both raise :class:`KmsUnavailable` when their library, configuration or
    service is missing. **Nothing falls back to a local key.** A vault that
    quietly seals under a laptop key when the HSM is unreachable has converted
    an outage into a silent, permanent downgrade of its central claim.

    ## What has and has not been exercised

    The wrap/unwrap contract, the encryption context, the cache and every
    refusal path are driven by the tests next door against an injected client.
    **No live AWS or HSM call has been made from this repository** — that needs
    credentials and hardware this project does not have — so the boto3 and
    pkcs11 call sites are written from their documented signatures and are
    marked ``pragma: no cover``. Read them before pointing this at production.
    """

    def __init__(self, key_id: str | None = None, client=None) -> None:
        # A per-tenant key id (BYOK) takes precedence over the deployment's.
        self.key_id = key_id
        # Injectable so the contract can be driven without an AWS account.
        # It is a constructor argument rather than a module global because a
        # global would let one tenant's test double answer another's unwrap.
        self.client = client

    # -- configuration ------------------------------------------------------

    def resolved_key_id(self) -> str:
        key_id = self.key_id or os.environ.get("PDI_KMS_KEY_ID")
        if not key_id:
            raise KmsUnavailable(
                "PDI_KEY_PROVIDER=kms but no key id: set PDI_KMS_KEY_ID, or "
                "give the tenant its own under BYOK. Refusing rather than "
                "reaching for a local key.")
        return key_id

    def wrapped(self) -> bytes:
        raw = os.environ.get("PDI_KMS_WRAPPED_KEK")
        if not raw:
            raise KmsUnavailable(
                "PDI_KMS_WRAPPED_KEK is unset. This deployment stores the KEK "
                "wrapped and asks the KMS to unwrap it — without the blob "
                "there is nothing to unwrap, and inventing a key here would "
                "make every existing record unreadable.")
        try:
            return base64.b64decode(raw, validate=True)
        except Exception as exc:
            raise KmsUnavailable(
                f"PDI_KMS_WRAPPED_KEK is not valid base64: {exc}") from exc

    def encryption_context(self) -> dict[str, str]:
        """Binds the blob to this deployment and this key.

        Without it, a wrapped KEK copied out of one deployment's environment
        decrypts in any other deployment the same KMS key allows — the blob
        stops being a secret about *this* vault and becomes a bearer token for
        the key.
        """
        return {"pdi:key_id": self.resolved_key_id(),
                "pdi:purpose": "record-kek"}

    # -- the backends -------------------------------------------------------

    def _aws(self) -> bytes:  # pragma: no cover - needs an AWS account
        try:
            import boto3
        except ImportError as exc:
            raise KmsUnavailable(
                "the aws backend needs boto3 installed on this host") from exc
        client = self.client or boto3.client("kms")
        try:
            out = client.decrypt(
                CiphertextBlob=self.wrapped(),
                KeyId=self.resolved_key_id(),
                EncryptionContext=self.encryption_context())
        except Exception as exc:
            raise KmsUnavailable(f"kms:Decrypt failed: {exc}") from exc
        return out["Plaintext"]

    def _pkcs11(self) -> bytes:  # pragma: no cover - needs a hardware token
        try:
            import pkcs11
        except ImportError as exc:
            raise KmsUnavailable(
                "the pkcs11 backend needs python-pkcs11 installed") from exc
        lib_path = os.environ.get("PDI_PKCS11_LIB")
        if not lib_path:
            raise KmsUnavailable("PDI_PKCS11_LIB is unset")
        lib = pkcs11.lib(lib_path)
        token = lib.get_token(token_label=os.environ.get("PDI_PKCS11_TOKEN"))
        with token.open(user_pin=os.environ.get("PDI_PKCS11_PIN")) as session:
            wrapping = session.get_key(label=self.resolved_key_id())
            return bytes(wrapping.decrypt(self.wrapped()))

    def _injected(self) -> bytes:
        """The path the tests drive: whatever client was handed in.

        Deliberately the same contract as boto3's — `decrypt(CiphertextBlob=,
        KeyId=, EncryptionContext=) -> {"Plaintext": bytes}` — so a double
        that satisfies this is a double that would satisfy AWS, and the tests
        are testing the real shape rather than a shape invented for them.
        """
        out = self.client.decrypt(
            CiphertextBlob=self.wrapped(),
            KeyId=self.resolved_key_id(),
            EncryptionContext=self.encryption_context())
        return out["Plaintext"]

    # -- the door ------------------------------------------------------------

    def kek(self) -> bytes:
        key_id = self.resolved_key_id()
        cached = _KEK_CACHE.get(key_id)
        if cached and (time.time() - cached[1]) < KEK_CACHE_SECONDS:
            return cached[0]

        backend = os.environ.get("PDI_KMS_BACKEND", "aws")
        if self.client is not None:
            key = self._injected()
        elif backend == "aws":
            key = self._aws()
        elif backend == "pkcs11":
            key = self._pkcs11()
        else:
            raise KmsUnavailable(
                f"no such KMS backend: {backend} (aws, pkcs11)")

        if len(key) != 32:
            # Caught here rather than at first use, where the failure would be
            # an AES error three layers down naming nothing useful.
            raise KmsUnavailable(
                f"the KMS returned a {len(key)}-byte key; this vault seals "
                f"under AES-256 and needs 32")
        _KEK_CACHE[key_id] = (key, time.time())
        return key


# --------------------------------------------------------------------------- #
# customer key custody (BYOK)
# --------------------------------------------------------------------------- #
def custody(tenant_id: str) -> dict:
    """Who holds the key for this tenant, and what that actually guarantees.

    Written to be quotable in a security review, because "encrypted at rest"
    is true of all three rows below and means something different in each.
    """
    row = db.connect().execute(
        "SELECT provider, config, adopted_at FROM tenant_keys WHERE tenant_id=?",
        (tenant_id,)).fetchone()
    if row is None:
        return {
            "provider": "deployment", "customer_managed": False,
            "operator_can_decrypt": True,
            "note": "sealed under the deployment's own key — the operator "
                    "holds it and can decrypt these records",
        }
    if row["provider"] == "held":
        return {
            "provider": "held", "customer_managed": True,
            "operator_can_decrypt": False,
            "adopted_at": row["adopted_at"],
            "note": "sealed under a key the customer presents per request and "
                    "the deployment never stores. Disk, backups and snapshots "
                    "are unreadable without the customer.",
            "limits": [
                "The operator runs the process, so a modified deployment could "
                "capture the key while it is presented. This protects data at "
                "rest, not against a hostile running operator.",
                "Background jobs cannot touch these records: a retention sweep "
                "still deletes them, but reseal and rotation need the key.",
                "Lose the key and the records are unrecoverable. That is the "
                "point of it, and there is no escrow.",
            ],
        }
    return {
        "provider": "kms", "customer_managed": True,
        "operator_can_decrypt": True,
        "adopted_at": row["adopted_at"],
        "config": json.loads(row["config"] or "{}"),
        "note": "the KEK lives in the customer's KMS; the operator can decrypt "
                "while the customer's grant is live, and cannot once it is "
                "revoked",
        "limits": [
            "The KEK is unwrapped through kms:Decrypt on a stored wrapped "
            "blob and cached in memory for at most "
            f"{KEK_CACHE_SECONDS}s, so a revoked grant stops opening records "
            "within that window rather than instantly.",
            "The aws and pkcs11 call sites are written to their documented "
            "signatures and have no verified live run in this repository. "
            "The contract around them — unwrap not fetch, encryption "
            "context, cache scoping, and every refusal path — is driven by "
            "tests against an injected client.",
        ],
    }


def _check_value(kek: bytes, tenant_id: str) -> str:
    """A witness that a presented key is the right one, computed so that it
    reveals nothing about the key: HMAC over a fixed label, keyed by the KEK.
    Storing this is not storing the key."""
    return hmac.new(kek, f"pdi-byok-check:{tenant_id}".encode(),
                    hashlib.sha256).hexdigest()


def _tenant_kek(tenant_id: str, presented: bytes | None) -> bytes | None:
    """The KEK for a tenant's own keyring, or None when the tenant is under
    deployment custody (the ordinary case)."""
    row = db.connect().execute(
        "SELECT provider, config, check_value FROM tenant_keys WHERE tenant_id=?",
        (tenant_id,)).fetchone()
    if row is None:
        return None
    if row["provider"] == "kms":
        cfg = json.loads(row["config"] or "{}")
        return KmsKeyProvider(cfg.get("key_id")).kek()
    if presented is None:
        raise CustomerKeyRequired(
            "this tenant's records are sealed under a customer-managed key; "
            "present it in the x-tenant-key header (base64 of 32 bytes)")
    if len(presented) != 32:
        raise CustomerKeyMismatch("customer key must be base64 of 32 bytes")
    if row["check_value"] and not hmac.compare_digest(
            _check_value(presented, tenant_id), row["check_value"]):
        raise CustomerKeyMismatch(
            "that is not the key this tenant's records are sealed under — "
            "refusing before use, so a wrong key cannot write records that "
            "nothing can open later")
    return presented


def parse_key(raw: str | None) -> bytes | None:
    """Decode a presented customer key. Invalid base64 is a mismatch, not a
    crash."""
    if not raw:
        return None
    try:
        return base64.b64decode(raw, validate=True)
    except Exception as exc:
        raise CustomerKeyMismatch("customer key must be base64") from exc


# --------------------------------------------------------------------------- #
# keyring — versioned DEKs, wrapped by the KEK
# --------------------------------------------------------------------------- #
def _wrap(dek: bytes, kek: bytes | None = None) -> str:
    aes = AESGCM(kek or _kek())
    nonce = os.urandom(12)
    return base64.b64encode(nonce + aes.encrypt(nonce, dek, b"pdi-dek")).decode()


def _unwrap(wrapped: str, kek: bytes | None = None) -> bytes:
    blob = base64.b64decode(wrapped)
    return AESGCM(kek or _kek()).decrypt(blob[:12], blob[12:], b"pdi-dek")


def _ensure_keyring(tenant_id: str | None = None,
                    kek: bytes | None = None) -> None:
    conn = db.connect()
    if tenant_id is None:
        row = conn.execute("SELECT COUNT(*) n FROM key_versions").fetchone()
        if row["n"] == 0:
            dek = AESGCM.generate_key(bit_length=256)
            conn.execute(
                "INSERT INTO key_versions (version, wrapped_dek, active,"
                " created_at) VALUES (1, ?, 1, ?)", (_wrap(dek), db.utcnow()))
            conn.commit()
        return
    row = conn.execute(
        "SELECT COUNT(*) n FROM tenant_key_versions WHERE tenant_id=?",
        (tenant_id,)).fetchone()
    if row["n"] == 0:
        dek = AESGCM.generate_key(bit_length=256)
        conn.execute(
            "INSERT INTO tenant_key_versions (tenant_id, version, wrapped_dek,"
            " active, created_at) VALUES (?, 1, ?, 1, ?)",
            (tenant_id, _wrap(dek, kek), db.utcnow()))
        conn.commit()


def active_version(tenant_id: str | None = None,
                   kek: bytes | None = None) -> int:
    _ensure_keyring(tenant_id, kek)
    if tenant_id is None:
        row = db.connect().execute(
            "SELECT version FROM key_versions WHERE active=1"
            " ORDER BY version DESC LIMIT 1").fetchone()
    else:
        row = db.connect().execute(
            "SELECT version FROM tenant_key_versions WHERE tenant_id=?"
            " AND active=1 ORDER BY version DESC LIMIT 1", (tenant_id,)
        ).fetchone()
    return row["version"]


def _dek(version: int, tenant_id: str | None = None,
         kek: bytes | None = None) -> bytes:
    if tenant_id is None:
        row = db.connect().execute(
            "SELECT wrapped_dek FROM key_versions WHERE version=?", (version,)
        ).fetchone()
    else:
        row = db.connect().execute(
            "SELECT wrapped_dek FROM tenant_key_versions WHERE tenant_id=?"
            " AND version=?", (tenant_id, version)).fetchone()
    if row is None:
        raise KeyError(f"unknown key version {version}")
    return _unwrap(row["wrapped_dek"], kek)


def rewrap(new_kek: bytes, old_kek: bytes | None = None, *,
           tenant_id: str | None = None) -> dict:
    """Rotate the **key-encryption key**, without opening a single record.

    The operation the envelope model exists for and the one this module did
    not have. `rotate` mints a new *DEK* and `vault.reseal_all` then decrypts
    and re-encrypts every record under it — which is the right answer when a
    DEK is suspect, and the wrong one for the routine annual rotation a
    security review asks about. Bulk plaintext, once a year, to change a key
    that never touched the records in the first place.

        asked     can the key be rotated
        mattered  can it be rotated without decrypting anything

    Here the records are not read at all. Each stored `wrapped_dek` is opened
    with the old KEK and sealed again under the new one; the DEK inside is
    unchanged, so every existing ciphertext still decrypts and no plaintext
    record is ever formed.

    **All or nothing.** Every unwrap is done and checked *before* anything is
    written. A keyring half-rotated is a keyring where half the records are
    unopenable and nothing says which half — the failure this could cause is
    categorically worse than the failure it protects against, so a single bad
    unwrap aborts the whole operation with the keyring untouched.

    Without an old KEK that opens what is there, this refuses rather than
    guessing: re-wrapping under a key nobody can verify produces a keyring
    that looks healthy and opens nothing.
    """
    conn = db.connect()
    if tenant_id is None:
        rows = conn.execute(
            "SELECT version, wrapped_dek FROM key_versions ORDER BY version"
        ).fetchall()
        table, where = "key_versions", ()
    else:
        rows = conn.execute(
            "SELECT version, wrapped_dek FROM tenant_key_versions"
            " WHERE tenant_id=? ORDER BY version", (tenant_id,)).fetchall()
        table, where = "tenant_key_versions", (tenant_id,)
    if not rows:
        raise CustomerKeyMismatch(
            "there is no keyring here to rotate — nothing has been sealed yet")

    # Open everything first. Nothing is written until all of it succeeded.
    opened: list[tuple[int, bytes]] = []
    for row in rows:
        try:
            opened.append((row["version"], _unwrap(row["wrapped_dek"], old_kek)))
        except Exception as exc:                       # noqa: BLE001
            raise CustomerKeyMismatch(
                f"the old key does not open key version {row['version']}, so "
                "this rotation would seal the keyring shut — nothing was "
                "changed") from exc

    for version, dek in opened:
        if tenant_id is None:
            conn.execute("UPDATE key_versions SET wrapped_dek=? WHERE version=?",
                         (_wrap(dek, new_kek), version))
        else:
            conn.execute(
                "UPDATE tenant_key_versions SET wrapped_dek=?"
                " WHERE tenant_id=? AND version=?",
                (_wrap(dek, new_kek), tenant_id, version))
    conn.commit()

    from . import audit
    audit.record("key.rewrap", tenant_id=tenant_id, ref=str(len(opened)))
    return {"rewrapped": len(opened), "records_decrypted": 0,
            "keyring": table, "tenant_id": tenant_id}


def rotate() -> dict:
    """Mint a new key version + DEK and make it active. Existing ciphertext
    still decrypts under its own (now-inactive) version; call ``reseal`` to move
    records onto the new version.

    This is **DEK** rotation, and it is the expensive one: moving records onto
    the new version means reading each of them. For rotating the key that
    wraps the DEKs — the routine one, with no plaintext formed — see
    :func:`rewrap`.
    """
    _ensure_keyring()
    conn = db.connect()
    cur = conn.execute("SELECT MAX(version) m FROM key_versions").fetchone()
    new_v = cur["m"] + 1
    dek = AESGCM.generate_key(bit_length=256)
    conn.execute("UPDATE key_versions SET active=0")
    conn.execute(
        "INSERT INTO key_versions (version, wrapped_dek, active, created_at)"
        " VALUES (?, ?, 1, ?)", (new_v, _wrap(dek), db.utcnow()))
    conn.commit()
    return {"active_version": new_v}


def key_versions() -> list[dict]:
    rows = db.connect().execute(
        "SELECT version, active, created_at FROM key_versions ORDER BY version"
    ).fetchall()
    provider = os.environ.get("PDI_KEY_PROVIDER", "env")
    # `generation` and not `version`: `/health` answers a `version` too,
    # and that one is a semantic version string while this counts key
    # rotations. One wire name carrying two types is the defect
    # `test_no_wire_name_carries_two_types` was written for — the column
    # stays `version`, because the ambiguity was never in the database.
    return [{"generation": r["version"], "active": bool(r["active"]),
             "created_at": r["created_at"], "provider": provider} for r in rows]


def retire_old_versions() -> int:
    """Delete non-active key versions. Safe only after ``reseal`` has moved
    every record onto the active version. Returns versions retired."""
    conn = db.connect()
    n = conn.execute("DELETE FROM key_versions WHERE active=0").rowcount
    conn.commit()
    return n


# --------------------------------------------------------------------------- #
# seal / open
# --------------------------------------------------------------------------- #
def _scope(tenant_id: str | None, presented: bytes | None
           ) -> tuple[str | None, bytes | None]:
    """Resolve which keyring a tenant's records live on.

    Returns ``(None, None)`` for deployment custody — the ordinary case, and
    byte-for-byte the behaviour before BYOK existed — or ``(tenant_id, kek)``
    for a tenant that brought its own key.
    """
    if tenant_id is None:
        return None, None
    kek = _tenant_kek(tenant_id, presented)
    return (None, None) if kek is None else (tenant_id, kek)


def seal(plaintext: str, aad: str | None = None, tenant_id: str | None = None,
         customer_key: bytes | None = None) -> str:
    """Encrypt plaintext under the active key version, returning
    ``"<version>:" + base64(nonce || ciphertext)``.

    ``tenant_id`` selects the keyring: a tenant under BYOK seals under its own
    key, everyone else under the deployment's.
    """
    scope, kek = _scope(tenant_id, customer_key)
    version = active_version(scope, kek)
    aesgcm = AESGCM(_dek(version, scope, kek))
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode(), aad.encode() if aad else None)
    return f"{version}:{base64.b64encode(nonce + ct).decode()}"


def open_(sealed: str, aad: str | None = None, tenant_id: str | None = None,
          customer_key: bytes | None = None) -> str:
    """Decrypt a sealed blob back to plaintext. Handles both the versioned
    format and legacy blobs (no version prefix) sealed by earlier releases."""
    scope, kek = _scope(tenant_id, customer_key)
    version, _, body = sealed.partition(":")
    if body and version.isdigit():
        key = _dek(int(version), scope, kek)
    else:                       # legacy blob: sealed directly with the KEK
        key, body = (kek or _kek()), sealed
    blob = base64.b64decode(body)
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(blob[:12], blob[12:], aad.encode() if aad else None).decode()


def sealed_version(sealed: str) -> int | None:
    version, _, body = sealed.partition(":")
    return int(version) if body and version.isdigit() else None


# --------------------------------------------------------------------------- #
# adopting and releasing a customer key
# --------------------------------------------------------------------------- #
def adopt_customer_key(tenant_id: str, provider: str,
                       key: bytes | None = None,
                       config: dict | None = None) -> dict:
    """Move a tenant onto its own KEK.

    Every one of the tenant's records is re-sealed under the new keyring in
    the same transaction. A half-migrated tenant would be the worst possible
    state — some records openable by the operator, some not, with no way to
    tell which from the outside — so this is all-or-nothing.
    """
    if db.connect().execute(
            "SELECT 1 FROM tenant_keys WHERE tenant_id=?", (tenant_id,)
    ).fetchone():
        raise ValueError("this tenant already has a customer-managed key; "
                         "release it before adopting another")
    if provider == "held":
        if key is None or len(key) != 32:
            raise CustomerKeyMismatch("customer key must be base64 of 32 bytes")
    elif provider != "kms":
        raise ValueError("provider must be 'held' or 'kms'")

    conn = db.connect()
    # Read everything out under the *old* (deployment) custody first: once the
    # tenant_keys row exists, that path is closed.
    records = conn.execute(
        "SELECT id, key, ciphertext FROM records WHERE tenant_id=?",
        (tenant_id,)).fetchall()
    plain = [(r["id"], r["key"], open_(r["ciphertext"],
                                       aad=f"{tenant_id}:{r['key']}"))
             for r in records]

    conn.execute(
        "INSERT INTO tenant_keys (tenant_id, provider, config, check_value,"
        " adopted_at) VALUES (?,?,?,?,?)",
        (tenant_id, provider, json.dumps(config or {}),
         _check_value(key, tenant_id) if key else None, db.utcnow()))
    conn.execute("DELETE FROM tenant_key_versions WHERE tenant_id=?", (tenant_id,))
    _ensure_keyring(tenant_id, key)
    for rid, rkey, value in plain:
        conn.execute("UPDATE records SET ciphertext=? WHERE id=? AND tenant_id=?",
                     (seal(value, aad=f"{tenant_id}:{rkey}",
                           tenant_id=tenant_id, customer_key=key), rid,
                      tenant_id))
    conn.commit()
    return {"provider": provider, "resealed": len(plain),
            "custody": custody(tenant_id)}


def release_customer_key(tenant_id: str, key: bytes | None = None) -> dict:
    """Hand custody back to the deployment, re-sealing every record under the
    deployment's own key. Requires the customer key, because the records have
    to be opened before they can be re-sealed — which is the guarantee working
    as intended, not an obstacle to route around."""
    row = db.connect().execute(
        "SELECT provider FROM tenant_keys WHERE tenant_id=?", (tenant_id,)
    ).fetchone()
    if row is None:
        raise ValueError("this tenant is already under deployment custody")

    conn = db.connect()
    records = conn.execute(
        "SELECT id, key, ciphertext FROM records WHERE tenant_id=?",
        (tenant_id,)).fetchall()
    plain = [(r["id"], r["key"],
              open_(r["ciphertext"], aad=f"{tenant_id}:{r['key']}",
                    tenant_id=tenant_id, customer_key=key))
             for r in records]

    conn.execute("DELETE FROM tenant_keys WHERE tenant_id=?", (tenant_id,))
    conn.execute("DELETE FROM tenant_key_versions WHERE tenant_id=?", (tenant_id,))
    for rid, rkey, value in plain:
        conn.execute("UPDATE records SET ciphertext=? WHERE id=? AND tenant_id=?",
                     (seal(value, aad=f"{tenant_id}:{rkey}"), rid, tenant_id))
    conn.commit()
    return {"provider": "deployment", "resealed": len(plain),
            "custody": custody(tenant_id)}
