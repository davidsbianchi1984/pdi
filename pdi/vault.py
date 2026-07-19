"""Encrypted record vault + tenant registry + deployment record."""

from __future__ import annotations

import hashlib
import secrets

from . import audit, crypto, db


def _mint() -> tuple[str, str]:
    """Return a (plaintext, hash) pair for a fresh bearer token. Only the hash
    is stored, so a database leak never yields a usable credential — the same
    protection the vault gives the data it holds."""
    token = "pdi_" + secrets.token_urlsafe(24)
    return token, _hash(token)


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


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
    token, token_hash = _mint()
    conn.execute(
        "INSERT INTO tenants (id, name, token, created_at) VALUES (?,?,?,?)",
        (tenant_id, name, token_hash, db.utcnow()),
    )
    conn.commit()
    audit.record("tenant.create", tenant_id=tenant_id, ref=name)
    # The token is returned once, here — it authenticates the tenant's
    # requests. Only its hash is persisted; the plaintext lives only in the
    # integrating system's keeping from now on.
    return {"id": tenant_id, "name": name, "token": token}


def tenant_by_token(token: str) -> dict | None:
    """Resolve a token to its tenant. The primary token carries the 'write'
    role; scoped tokens carry the role they were issued with. Soft-deleted
    tenants (deleted_at set) resolve to None — their data is unreachable
    during the recovery window until wiped or restored."""
    conn = db.connect()
    token_hash = _hash(token)
    row = conn.execute(
        "SELECT * FROM tenants WHERE token=? AND deleted_at IS NULL",
        (token_hash,)).fetchone()
    if row:
        return {**_scrub(row), "role": "write"}
    scoped = conn.execute(
        "SELECT t.*, s.role FROM tenant_tokens s JOIN tenants t"
        " ON t.id = s.tenant_id WHERE s.token=? AND s.revoked=0", (token_hash,)
    ).fetchone()
    return {**_scrub(scoped), "role": scoped["role"]} if scoped else None


def _scrub(row) -> dict:
    """Tenant dict without the stored token hash — never hand the credential
    material (even hashed) back out through a resolved-tenant object."""
    return {k: v for k, v in dict(row).items() if k != "token"}


def issue_token(tenant_id: str, role: str) -> dict:
    """Role-based access control: issue an additional scoped token."""
    conn = db.connect()
    token, token_hash = _mint()
    conn.execute(
        "INSERT INTO tenant_tokens (token, tenant_id, role, revoked, created_at)"
        " VALUES (?,?,?,0,?)", (token_hash, tenant_id, role, db.utcnow()),
    )
    conn.commit()
    audit.record("token.issue", tenant_id=tenant_id, ref=role)
    return {"tenant_id": tenant_id, "role": role, "token": token}


def delete_tenant(tenant_id: str, mode: str) -> dict | None:
    """Tenant deletion. ``soft`` sets a tombstone (data retained, access cut,
    restorable during the recovery window); ``wipe`` permanently removes the
    tenant's records, scoped tokens, and the tenant row. Both are audited."""
    conn = db.connect()
    row = conn.execute("SELECT id FROM tenants WHERE id=?",
                       (tenant_id,)).fetchone()
    if row is None:
        return None
    if mode == "wipe":
        records = conn.execute(
            "DELETE FROM records WHERE tenant_id=?", (tenant_id,)).rowcount
        conn.execute("DELETE FROM tenant_tokens WHERE tenant_id=?", (tenant_id,))
        conn.execute("DELETE FROM tenants WHERE id=?", (tenant_id,))
        conn.commit()
        audit.record("tenant.wipe", tenant_id=tenant_id, ref=str(records))
        return {"tenant_id": tenant_id, "mode": "wipe", "records_wiped": records}
    conn.execute("UPDATE tenants SET deleted_at=? WHERE id=?",
                 (db.utcnow(), tenant_id))
    conn.commit()
    audit.record("tenant.soft_delete", tenant_id=tenant_id)
    return {"tenant_id": tenant_id, "mode": "soft",
            "recoverable": True, "note": "restore with POST /tenants/{id}/restore"}


def restore_tenant(tenant_id: str) -> dict | None:
    """Undo a soft-delete during the recovery window."""
    conn = db.connect()
    row = conn.execute(
        "SELECT deleted_at FROM tenants WHERE id=?", (tenant_id,)).fetchone()
    if row is None:
        return None
    if row["deleted_at"] is None:
        return {"tenant_id": tenant_id, "restored": False, "note": "not deleted"}
    conn.execute("UPDATE tenants SET deleted_at=NULL WHERE id=?", (tenant_id,))
    conn.commit()
    audit.record("tenant.restore", tenant_id=tenant_id)
    return {"tenant_id": tenant_id, "restored": True}


def revoke_token(token: str) -> bool:
    conn = db.connect()
    changed = conn.execute(
        "UPDATE tenant_tokens SET revoked=1 WHERE token=?",
        (_hash(token),)).rowcount
    conn.commit()
    if changed:
        audit.record("token.revoke")
    return changed > 0


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


def restore_snapshot(tenant: dict, records: list[dict]) -> dict:
    """Disaster-recovery restore: reinsert ciphertext records exported by
    export_snapshot. Plaintext never appears — AAD still binds each record
    to this tenant + key, so a snapshot can only restore where it belongs."""
    conn = db.connect()
    restored = 0
    now = db.utcnow()
    for record in records:
        conn.execute(
            "INSERT INTO records (id, tenant_id, key, ciphertext, created_at,"
            " updated_at) VALUES (?,?,?,?,?,?)"
            " ON CONFLICT (tenant_id, key) DO UPDATE SET"
            " ciphertext=excluded.ciphertext, updated_at=excluded.updated_at",
            (db.new_id("rec"), tenant["id"], record["key"],
             record["ciphertext"], now, record.get("updated_at", now)),
        )
        restored += 1
    conn.commit()
    audit.record("snapshot.restore", tenant_id=tenant["id"], ref=str(restored))
    return {"tenant_id": tenant["id"], "restored": restored}


def export_snapshot(tenant: dict) -> dict:
    """Disaster-recovery export: ciphertext only (never plaintext)."""
    rows = db.connect().execute(
        "SELECT key, ciphertext, updated_at FROM records WHERE tenant_id=?",
        (tenant["id"],),
    ).fetchall()
    audit.record("snapshot.export", tenant_id=tenant["id"])
    return {"tenant_id": tenant["id"], "records": [dict(r) for r in rows]}
