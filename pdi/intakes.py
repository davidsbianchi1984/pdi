"""Inbound compliant intake.

The outbound side (``transfers.py``) lets a corporation seal a file *out* to a
recipient. Intake is the reverse: a corporation requests a file *in* from a
broadband **subscriber** or a **partner company**, and that party submits it
safely — sealed in the vault under the same compliance controls, with a one-shot
submit token and full chain of custody.

So PDI carries files both directions for both parties: for users and for
companies, under HIPAA / OSHA / CPNI / ….
"""

from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone

from . import audit, compliance, db, transfers, vault


class UnknownProgram(Exception):
    pass


def _mint() -> tuple[str, str]:
    token = "pdi_submit_" + secrets.token_urlsafe(24)
    return token, hashlib.sha256(token.encode()).hexdigest()


def get(iid: str) -> dict | None:
    row = db.connect().execute("SELECT * FROM intakes WHERE id=?", (iid,)).fetchone()
    return dict(row) if row else None


def _out(row: dict) -> dict:
    return {
        "id": row["id"],
        "tenant_id": row["tenant_id"],
        "from_party": row["from_party"],
        "party_type": row["party_type"],
        "purpose": row["purpose"],
        "programs": json.loads(row["programs"]),
        "status": row["status"],
        "filename": row["filename"],
        "classification": row["classification"],
        "retention_days": row["retention_days"],
        "expires_at": row["expires_at"],
        "created_at": row["created_at"],
    }


def create(tenant: dict, from_party: str, party_type: str | None,
           purpose: str | None, programs: list[str]) -> dict:
    unknown = [p for p in programs if compliance.get(p) is None]
    if unknown:
        raise UnknownProgram(f"unknown compliance program(s): {unknown}")
    iid = db.new_id("intk")
    token, token_hash = _mint()
    retention = compliance.retention_days(programs)
    db.connect().execute(
        "INSERT INTO intakes (id, tenant_id, from_party, party_type, purpose,"
        " programs, submit_token_hash, status, retention_days, created_at)"
        " VALUES (?,?,?,?,?,?,?, 'open', ?,?)",
        (iid, tenant["id"], from_party, party_type, purpose,
         json.dumps(programs), token_hash, retention, db.utcnow()))
    db.connect().commit()
    transfers._receipt(iid, "requested", tenant.get("name"))
    audit.record("intake.request", tenant_id=tenant["id"], ref=iid)
    out = _out(get(iid))
    out["submit_token"] = token                    # shown exactly once
    out["controls"] = compliance.controls_for(programs)
    return out


def for_tenant(tenant_id: str) -> list[dict]:
    rows = db.connect().execute(
        "SELECT * FROM intakes WHERE tenant_id=? ORDER BY created_at, rowid",
        (tenant_id,)).fetchall()
    return [_out(dict(r)) for r in rows]


def submit(row: dict, token: str, filename: str, content: str,
           classification: str | None):
    """A subscriber or partner submits their file in with the submit token."""
    if hashlib.sha256(token.encode()).hexdigest() != row["submit_token_hash"]:
        return None
    if row["status"] != "open":
        return "closed"
    tenant = {"id": row["tenant_id"]}
    vault_key = f"intakes/{row['id']}"
    vault.put(tenant, vault_key, content)          # sealed AES-256-GCM at rest
    retention = row["retention_days"]
    expires = (datetime.now(timezone.utc) + timedelta(days=retention)).isoformat() \
        if retention else None
    db.connect().execute(
        "UPDATE intakes SET status='submitted', vault_key=?, filename=?,"
        " classification=?, expires_at=? WHERE id=?",
        (vault_key, filename, classification, expires, row["id"]))
    db.connect().commit()
    transfers._receipt(row["id"], "submitted", row["from_party"])
    audit.record("intake.submit", tenant_id=row["tenant_id"], ref=row["id"])
    return {"id": row["id"], "status": "submitted", "sealed": True,
            "filename": filename, "programs": json.loads(row["programs"]),
            "note": "your file was sealed in the vault, encrypted at rest"}


def read(tenant: dict, row: dict):
    """The corporation retrieves the submitted file (audited)."""
    if row["status"] != "submitted" or not row["vault_key"]:
        return None
    rec = vault.get(tenant, row["vault_key"])
    transfers._receipt(row["id"], "read", None)
    audit.record("intake.read", tenant_id=row["tenant_id"], ref=row["id"])
    return {"id": row["id"], "filename": row["filename"],
            "content": rec["value"] if rec else None,
            "programs": json.loads(row["programs"])}


def custody(row: dict) -> dict:
    receipts = db.connect().execute(
        "SELECT event, actor, at FROM transfer_receipts WHERE transfer_id=?"
        " ORDER BY at, rowid", (row["id"],)).fetchall()
    programs = json.loads(row["programs"])
    return {
        "intake": row["id"],
        "from_party": row["from_party"],
        "party_type": row["party_type"],
        "filename": row["filename"],
        "programs": programs,
        "controls": compliance.controls_for(programs),
        "retention_days": row["retention_days"],
        "retained_until": row["expires_at"],
        "status": row["status"],
        "chain_of_custody": [dict(r) for r in receipts],
        "audit_chain_intact": audit.verify()["intact"],
    }


def close(row: dict) -> dict:
    db.connect().execute("UPDATE intakes SET status='closed' WHERE id=?", (row["id"],))
    db.connect().commit()
    transfers._receipt(row["id"], "closed", None)
    audit.record("intake.close", tenant_id=row["tenant_id"], ref=row["id"])
    return {"id": row["id"], "status": "closed"}
