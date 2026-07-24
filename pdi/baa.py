"""Per-customer BAA execution records — and the gate that makes them real.

Under HIPAA the PDI operator is a Business Associate of each covered-entity
customer (each tenant), and the BAA must be signed **before** production PHI
flows. The template lives at docs/baa-template.md; this module is the
enforcement: the operator records each executed agreement against the
tenant, and any HIPAA-program transfer or intake for a tenant with no
active BAA on file is refused. "Execute it per customer before production
PHI" stops being a checklist item and becomes machine-enforced.

Only execution *metadata* is stored (parties, signatories, effective date,
and the SHA-256 of the signed document so the paper copy stays verifiable)
— the signed instrument itself stays with counsel.
"""

from __future__ import annotations

from . import audit, db


def record(tenant_id: str, fields: dict) -> dict:
    """Record one executed BAA for a tenant. A new record supersedes a
    terminated one; recording over an active one replaces it (re-execution,
    e.g. after renegotiation)."""
    conn = db.connect()
    conn.execute("UPDATE baa_records SET status='superseded'"
                 " WHERE tenant_id=? AND status='executed'", (tenant_id,))
    baa_id = db.new_id("baa")
    conn.execute(
        "INSERT INTO baa_records (id, tenant_id, customer_legal_name,"
        " operator_legal_name, effective_date, customer_signatory,"
        " operator_signatory, document_sha256, status, created_at)"
        " VALUES (?,?,?,?,?,?,?,?,'executed',?)",
        (baa_id, tenant_id, fields["customer_legal_name"],
         fields["operator_legal_name"], fields["effective_date"],
         fields.get("customer_signatory"), fields.get("operator_signatory"),
         fields.get("document_sha256"), db.utcnow()))
    conn.commit()
    audit.record("baa.execute", tenant_id=tenant_id, ref=baa_id)
    return dict(conn.execute("SELECT * FROM baa_records WHERE id=?",
                             (baa_id,)).fetchone())


def active(tenant_id: str) -> dict | None:
    row = db.connect().execute(
        "SELECT * FROM baa_records WHERE tenant_id=? AND status='executed'"
        " ORDER BY created_at DESC, rowid DESC LIMIT 1",
        (tenant_id,)).fetchone()
    return dict(row) if row else None


def terminate(tenant_id: str) -> bool:
    conn = db.connect()
    n = conn.execute(
        "UPDATE baa_records SET status='terminated', terminated_at=?"
        " WHERE tenant_id=? AND status='executed'",
        (db.utcnow(), tenant_id)).rowcount
    conn.commit()
    if n:
        audit.record("baa.terminate", tenant_id=tenant_id)
    return bool(n)


def blocks(tenant_id: str, programs: list[str]) -> str | None:
    """The gate: a HIPAA-program flow for a tenant with no active BAA is
    refused. Returns the refusal message, or None when clear."""
    if "hipaa" in programs and active(tenant_id) is None:
        return ("a HIPAA-program flow requires an executed Business "
                "Associate Agreement on file for this tenant — see "
                "docs/baa-template.md; the operator records the executed "
                "agreement at POST /tenants/{tenant_id}/baa")
    return None
