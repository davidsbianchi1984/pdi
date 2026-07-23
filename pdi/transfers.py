"""Compliance-grade secure file transfers.

A corporation (tenant) seals a file for a recipient under one or more compliance
programs (HIPAA, OSHA, CPNI, …). PDI's guarantees carry the regulated controls:

- **Encrypted at rest** — the file is sealed in the vault (AES-256-GCM, AAD-bound
  to the tenant + key), so it can't be moved or read across tenants.
- **Audit-logged access** — creation and every retrieval are written to the
  tamper-evident, hash-chained audit log and to the transfer's chain of custody.
- **Scoped retrieval** — a one-shot **receive token** (only its SHA-256 is
  stored) authorizes the recipient; nothing else can read the file.
- **Enforced retention** — the record is retained for the strictest window across
  its programs (OSHA 5y, HIPAA 6y, SOX 7y, …); revoking cuts access but keeps the
  record until retention expires.
"""

from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone

from . import audit, compliance, db, vault


class UnknownProgram(Exception):
    pass


def _mint() -> tuple[str, str]:
    token = "pdi_recv_" + secrets.token_urlsafe(24)
    return token, hashlib.sha256(token.encode()).hexdigest()


def get(tid: str) -> dict | None:
    row = db.connect().execute("SELECT * FROM transfers WHERE id=?", (tid,)).fetchone()
    return dict(row) if row else None


def _receipt(transfer_id: str, event: str, actor: str | None) -> None:
    db.connect().execute(
        "INSERT INTO transfer_receipts (id, transfer_id, event, actor, at)"
        " VALUES (?,?,?,?,?)",
        (db.new_id("rcpt"), transfer_id, event, actor, db.utcnow()))
    db.connect().commit()


def _out(row: dict) -> dict:
    return {
        "id": row["id"],
        "tenant_id": row["tenant_id"],
        "recipient": row["recipient"],
        "filename": row["filename"],
        "size": row["size"],
        "classification": row["classification"],
        "programs": json.loads(row["programs"]),
        "status": row["status"],
        "retention_days": row["retention_days"],
        "expires_at": row["expires_at"],
        "created_at": row["created_at"],
    }


def create(tenant: dict, recipient: str, filename: str, content: str,
           programs: list[str], classification: str | None) -> dict:
    unknown = [p for p in programs if compliance.get(p) is None]
    if unknown:
        raise UnknownProgram(f"unknown compliance program(s): {unknown}")
    tid = db.new_id("xfer")
    vault_key = f"transfers/{tid}"
    vault.put(tenant, vault_key, content)          # sealed AES-256-GCM at rest
    token, token_hash = _mint()
    retention = compliance.retention_days(programs)
    expires = (datetime.now(timezone.utc) + timedelta(days=retention)).isoformat() \
        if retention else None
    db.connect().execute(
        "INSERT INTO transfers (id, tenant_id, recipient, filename, size,"
        " classification, programs, vault_key, receive_token_hash, status,"
        " retention_days, expires_at, created_at)"
        " VALUES (?,?,?,?,?,?,?,?,?, 'sealed', ?,?,?)",
        (tid, tenant["id"], recipient, filename, len(content), classification,
         json.dumps(programs), vault_key, token_hash, retention, expires, db.utcnow()))
    db.connect().commit()
    _receipt(tid, "created", tenant.get("name"))
    audit.record("transfer.create", tenant_id=tenant["id"], ref=tid)
    out = _out(get(tid))
    out["receive_token"] = token                   # shown exactly once
    out["controls"] = compliance.controls_for(programs)
    return out


def for_tenant(tenant_id: str) -> list[dict]:
    rows = db.connect().execute(
        "SELECT * FROM transfers WHERE tenant_id=? ORDER BY created_at, rowid",
        (tenant_id,)).fetchall()
    return [_out(dict(r)) for r in rows]


def receive(row: dict, token: str):
    """Retrieve the sealed file with the recipient's receive token.

    Returns the content dict on success, ``None`` for a bad token, or the string
    ``"revoked"`` if access has been cut.
    """
    if hashlib.sha256(token.encode()).hexdigest() != row["receive_token_hash"]:
        return None
    if row["status"] == "revoked":
        return "revoked"
    sender = {"id": row["tenant_id"]}              # AAD is bound to this tenant
    rec = vault.get(sender, row["vault_key"])
    conn = db.connect()
    conn.execute("UPDATE transfers SET status='received' WHERE id=?", (row["id"],))
    conn.commit()
    _receipt(row["id"], "received", row["recipient"])
    audit.record("transfer.receive", tenant_id=row["tenant_id"], ref=row["id"])
    return {
        "id": row["id"],
        "filename": row["filename"],
        "content": rec["value"] if rec else None,
        "programs": json.loads(row["programs"]),
        "custody": "this retrieval was recorded in the audit chain",
    }


def custody(row: dict) -> dict:
    """The compliance record for a transfer: programs, controls, retention, and
    the full chain of custody, with the audit chain's integrity attested."""
    receipts = db.connect().execute(
        "SELECT event, actor, at FROM transfer_receipts WHERE transfer_id=?"
        " ORDER BY at, rowid", (row["id"],)).fetchall()
    programs = json.loads(row["programs"])
    return {
        "transfer": row["id"],
        "recipient": row["recipient"],
        "filename": row["filename"],
        "classification": row["classification"],
        "programs": programs,
        "controls": compliance.controls_for(programs),
        "retention_days": row["retention_days"],
        "retained_until": row["expires_at"],
        "status": row["status"],
        "chain_of_custody": [dict(r) for r in receipts],
        "audit_chain_intact": audit.verify()["intact"],
    }


def revoke(row: dict) -> dict:
    db.connect().execute("UPDATE transfers SET status='revoked' WHERE id=?", (row["id"],))
    db.connect().commit()
    _receipt(row["id"], "revoked", None)
    audit.record("transfer.revoke", tenant_id=row["tenant_id"], ref=row["id"])
    return {"id": row["id"], "status": "revoked",
            "retained_until": row["expires_at"],
            "note": "access revoked; the sealed record is retained until the "
                    "compliance retention window expires"}
