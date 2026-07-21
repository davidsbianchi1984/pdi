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
"""

from __future__ import annotations

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from . import db

_EPHEMERAL: bytes | None = None


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

    def kek(self) -> bytes:
        key_id = os.environ.get("PDI_KMS_KEY_ID")
        raise NotImplementedError(
            "KMS key provider is a production integration seam. Wire it to your "
            f"HSM (key id: {key_id or 'PDI_KMS_KEY_ID unset'}) — e.g. AWS KMS "
            "Decrypt on a stored wrapped KEK, or a PKCS#11 unwrap.")


# --------------------------------------------------------------------------- #
# keyring — versioned DEKs, wrapped by the KEK
# --------------------------------------------------------------------------- #
def _wrap(dek: bytes) -> str:
    aes = AESGCM(_kek())
    nonce = os.urandom(12)
    return base64.b64encode(nonce + aes.encrypt(nonce, dek, b"pdi-dek")).decode()


def _unwrap(wrapped: str) -> bytes:
    blob = base64.b64decode(wrapped)
    return AESGCM(_kek()).decrypt(blob[:12], blob[12:], b"pdi-dek")


def _ensure_keyring() -> None:
    conn = db.connect()
    row = conn.execute("SELECT COUNT(*) n FROM key_versions").fetchone()
    if row["n"] == 0:
        dek = AESGCM.generate_key(bit_length=256)
        conn.execute(
            "INSERT INTO key_versions (version, wrapped_dek, active, created_at)"
            " VALUES (1, ?, 1, ?)", (_wrap(dek), db.utcnow()))
        conn.commit()


def active_version() -> int:
    _ensure_keyring()
    row = db.connect().execute(
        "SELECT version FROM key_versions WHERE active=1"
        " ORDER BY version DESC LIMIT 1").fetchone()
    return row["version"]


def _dek(version: int) -> bytes:
    row = db.connect().execute(
        "SELECT wrapped_dek FROM key_versions WHERE version=?", (version,)
    ).fetchone()
    if row is None:
        raise KeyError(f"unknown key version {version}")
    return _unwrap(row["wrapped_dek"])


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
def seal(plaintext: str, aad: str | None = None) -> str:
    """Encrypt plaintext under the active key version, returning
    ``"<version>:" + base64(nonce || ciphertext)``."""
    version = active_version()
    aesgcm = AESGCM(_dek(version))
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode(), aad.encode() if aad else None)
    return f"{version}:{base64.b64encode(nonce + ct).decode()}"


def open_(sealed: str, aad: str | None = None) -> str:
    """Decrypt a sealed blob back to plaintext. Handles both the versioned
    format and legacy blobs (no version prefix) sealed by earlier releases."""
    version, _, body = sealed.partition(":")
    if body and version.isdigit():
        key = _dek(int(version))
    else:                       # legacy blob: sealed directly with the KEK
        key, body = _kek(), sealed
    blob = base64.b64decode(body)
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(blob[:12], blob[12:], aad.encode() if aad else None).decode()


def sealed_version(sealed: str) -> int | None:
    version, _, body = sealed.partition(":")
    return int(version) if body and version.isdigit() else None
