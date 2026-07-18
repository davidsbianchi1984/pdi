"""Encrypted record vault + tenant registry + deployment record."""

from __future__ import annotations

import secrets

from . import audit, crypto, db


# -- deployments ------------------------------------------------------------

def create_deployment(body: dict) -> dict:
    conn = db.connect()
    dep_id = db.new_id("dep")
    conn.execute(
        "INSERT INTO deployments (id, name, option, facility, tier, created_at)"
        " VALUES (?,?,?,?,?,?)",
        (dep_id, body["name"], body["option"], body.get("facility"),
         body.get("tier"), db.utcnow()),
    )
    conn.commit()
    audit.record("deployment.create", ref=dep_id)
    return dict(conn.execute("SELECT * FROM deployments WHERE id=?", (dep_id,)).fetchone())


# -- tenants (integrating AI systems) ---------------------------------------

def create_tenant(name: str) -> dict:
    conn = db.connect()
    tenant_id = db.new_id("ten")
    token = "pdi_" + secrets.token_urlsafe(24)
    conn.execute(
        "INSERT INTO tenants (id, name, token, created_at) VALUES (?,?,?,?)",
        (tenant_id, name, token, db.utcnow()),
    )
    conn.commit()
    audit.record("tenant.create", tenant_id=tenant_id, ref=name)
    # The token is returned once, here — it authenticates the tenant's requests.
    return {"id": tenant_id, "name": name, "token": token}


def tenant_by_token(token: str) -> dict | None:
    row = db.connect().execute(
        "SELECT * FROM tenants WHERE token=?", (token,)
    ).fetchone()
    return dict(row) if row else None


# -- encrypted records ------------------------------------------------------

def put(tenant: dict, key: str, value: str) -> dict:
    conn = db.connect()
    # AAD binds the ciphertext to this tenant+key, so a record can't be moved.
    sealed = crypto.seal(value, aad=f"{tenant['id']}:{key}")
    existing = conn.execute(
        "SELECT id FROM records WHERE tenant_id=? AND key=?", (tenant["id"], key)
    ).fetchone()
    now = db.utcnow()
    if existing:
        conn.execute(
            "UPDATE records SET ciphertext=?, updated_at=? WHERE id=?",
            (sealed, now, existing["id"]),
        )
        rec_id = existing["id"]
    else:
        rec_id = db.new_id("rec")
        conn.execute(
            "INSERT INTO records (id, tenant_id, key, ciphertext, created_at, updated_at)"
            " VALUES (?,?,?,?,?,?)",
            (rec_id, tenant["id"], key, sealed, now, now),
        )
    conn.commit()
    audit.record("put", tenant_id=tenant["id"], ref=key)
    return {"id": rec_id, "key": key, "stored": True}


def get(tenant: dict, key: str) -> dict | None:
    row = db.connect().execute(
        "SELECT * FROM records WHERE tenant_id=? AND key=?", (tenant["id"], key)
    ).fetchone()
    if row is None:
        return None
    value = crypto.open_(row["ciphertext"], aad=f"{tenant['id']}:{key}")
    audit.record("get", tenant_id=tenant["id"], ref=key)
    return {"key": key, "value": value, "updated_at": row["updated_at"]}


def delete(tenant: dict, key: str) -> bool:
    conn = db.connect()
    cur = conn.execute(
        "DELETE FROM records WHERE tenant_id=? AND key=?", (tenant["id"], key)
    )
    conn.commit()
    if cur.rowcount:
        audit.record("delete", tenant_id=tenant["id"], ref=key)
        return True
    return False


def list_keys(tenant: dict) -> list[str]:
    rows = db.connect().execute(
        "SELECT key FROM records WHERE tenant_id=? ORDER BY key", (tenant["id"],)
    ).fetchall()
    return [r["key"] for r in rows]


def export_snapshot(tenant: dict) -> dict:
    """Disaster-recovery export: ciphertext only (never plaintext)."""
    rows = db.connect().execute(
        "SELECT key, ciphertext, updated_at FROM records WHERE tenant_id=?",
        (tenant["id"],),
    ).fetchall()
    audit.record("snapshot.export", tenant_id=tenant["id"])
    return {"tenant_id": tenant["id"], "records": [dict(r) for r in rows]}
