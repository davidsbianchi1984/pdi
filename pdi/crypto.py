"""At-rest encryption for the private vault.

Records are sealed with AES-256-GCM (authenticated encryption). The master key
is supplied via the ``PDI_MASTER_KEY`` environment variable (base64, 32 bytes);
if unset, an ephemeral key is generated for the process — fine for local/dev,
never for production, where the key belongs in the corporation's own KMS/HSM
inside the private facility.
"""

from __future__ import annotations

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_EPHEMERAL: bytes | None = None


def _master_key() -> bytes:
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


def seal(plaintext: str, aad: str | None = None) -> str:
    """Encrypt plaintext, returning base64(nonce || ciphertext)."""
    aesgcm = AESGCM(_master_key())
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode(),
                        aad.encode() if aad else None)
    return base64.b64encode(nonce + ct).decode()


def open_(sealed: str, aad: str | None = None) -> str:
    """Decrypt base64(nonce || ciphertext) back to plaintext."""
    blob = base64.b64decode(sealed)
    nonce, ct = blob[:12], blob[12:]
    aesgcm = AESGCM(_master_key())
    return aesgcm.decrypt(nonce, ct, aad.encode() if aad else None).decode()
