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


class KmsKeyProvider:
    """Production key provider — the KEK stays inside a cloud KMS/HSM and is
    never materialised on the app host. Configure ``PDI_KMS_KEY_ID`` (and the
    cloud SDK's own credentials). This is the integration seam: wire the call
    below to e.g. AWS KMS ``Decrypt`` on a stored wrapped KEK, or a PKCS#11 HSM
    unwrap. Left unimplemented so a mis-set ``PDI_KEY_PROVIDER=kms`` fails
    loudly rather than silently falling back to a local key."""

    def __init__(self, key_id: str | None = None) -> None:
        # A per-tenant key id (BYOK) takes precedence over the deployment's.
        self.key_id = key_id

    def kek(self) -> bytes:
        key_id = self.key_id or os.environ.get("PDI_KMS_KEY_ID")
        raise NotImplementedError(
            "KMS key provider is a production integration seam. Wire it to your "
            f"HSM (key id: {key_id or 'PDI_KMS_KEY_ID unset'}) — e.g. AWS KMS "
            "Decrypt on a stored wrapped KEK, or a PKCS#11 unwrap.")


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
        "limits": ["Integration seam — KmsKeyProvider.kek() is not implemented."],
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


def rotate() -> dict:
    """Mint a new key version + DEK and make it active. Existing ciphertext
    still decrypts under its own (now-inactive) version; call ``reseal`` to move
    records onto the new version."""
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
    return [{"version": r["version"], "active": bool(r["active"]),
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
        conn.execute("UPDATE records SET ciphertext=? WHERE id=?",
                     (seal(value, aad=f"{tenant_id}:{rkey}",
                           tenant_id=tenant_id, customer_key=key), rid))
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
        conn.execute("UPDATE records SET ciphertext=? WHERE id=?",
                     (seal(value, aad=f"{tenant_id}:{rkey}"), rid))
    conn.commit()
    return {"provider": "deployment", "resealed": len(plain),
            "custody": custody(tenant_id)}
