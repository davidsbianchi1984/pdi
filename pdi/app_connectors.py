"""Connected-app connectors.

A tenant links to an AI-integrated app from the catalog (``catalog.py``) — Apple
Photos, Google Calendar, Microsoft 365, Canva, … — and its agents use it:

- **collect** — pull context in and seal each item as a vault record
  (``app/<provider>/<app>/<connector>/<id>``), encrypted at rest;
- **act** — drive the app agentically;
- **produce** — generate media.

Everything tenant-scoped: a connector is only usable under its owning tenant's
token, and collected items land in that tenant's vault.
"""

from __future__ import annotations

import json

from . import catalog, db, vault


def entry(provider: str, app: str) -> dict | None:
    return catalog.BY_KEY.get((provider, app))


def get(cid: str, tenant_id: str) -> dict | None:
    """This tenant's connector or nothing — the scope is in the SQL, so the
    statement cannot return another tenant's row for a check to forget."""
    row = db.connect().execute(
        "SELECT * FROM app_connectors WHERE id=? AND tenant_id=?",
        (cid, tenant_id)).fetchone()
    return dict(row) if row else None


def _out(row: dict) -> dict:
    return {
        "id": row["id"], "tenant_id": row["tenant_id"], "provider": row["provider"],
        "app": row["app"], "label": row["label"],
        "capabilities": json.loads(row["capabilities"]),
        "directions": json.loads(row["directions"]), "status": row["status"],
        "collected": row["collected"], "actions": row["actions"],
    }


def create(tenant_id: str, e: dict, capabilities: list[str]) -> dict:
    caps = capabilities or list(e["capabilities"])
    conn = db.connect()
    cid = db.new_id("app")
    conn.execute(
        "INSERT INTO app_connectors (id, tenant_id, provider, app, label,"
        " capabilities, directions, status, collected, actions, created_at)"
        " VALUES (?,?,?,?,?,?,?, 'active', 0, 0, ?)",
        (cid, tenant_id, e["provider"], e["app"], e["label"],
         json.dumps(caps), json.dumps(e["directions"]), db.utcnow()),
    )
    conn.commit()
    return _out(get(cid, tenant_id))


def for_tenant(tenant_id: str) -> list[dict]:
    rows = db.connect().execute(
        "SELECT * FROM app_connectors WHERE tenant_id=? ORDER BY created_at, rowid",
        (tenant_id,)).fetchall()
    return [_out(dict(r)) for r in rows]


def revoke(cid: str, tenant_id: str) -> dict:
    db.connect().execute(
        "UPDATE app_connectors SET status='revoked' WHERE id=? AND tenant_id=?",
        (cid, tenant_id))
    db.connect().commit()
    return {"id": cid, "status": "revoked"}


def ingest(tenant: dict, row: dict, items: list[dict]) -> dict:
    keys = []
    for item in items:
        item_id = db.new_id("itm")
        key = f"app/{row['provider']}/{row['app']}/{row['id']}/{item_id}"
        vault.put(tenant, key, json.dumps({
            "content": item.get("content", ""),
            "ref": item.get("ref"),
            "app": f"{row['provider']}:{row['app']}",
        }))
        keys.append(key)
    conn = db.connect()
    conn.execute("UPDATE app_connectors SET collected = collected + ?"
                 " WHERE id=? AND tenant_id=?",
                 (len(keys), row["id"], row["tenant_id"]))
    conn.commit()
    return {"connector": row["id"], "app": row["app"], "sealed": len(keys),
            "keys": keys, "note": "collected items are encrypted at rest in the vault"}


def invoke(row: dict, capability: str, inp: str | None) -> dict:
    db.connect().execute(
        "UPDATE app_connectors SET actions = actions + 1"
        " WHERE id=? AND tenant_id=?", (row["id"], row["tenant_id"]))
    db.connect().commit()
    return {"connector": row["id"], "provider": row["provider"], "app": row["app"],
            "capability": capability, "directions": json.loads(row["directions"]),
            "status": "performed", "input": inp,
            "result": f"{row['label']} · {capability} performed"}
