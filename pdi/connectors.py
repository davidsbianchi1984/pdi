"""Social-platform connectors.

PDI is the storage layer, so a connector's job is data custody. A tenant links
a platform in one of two directions:

- **collect** — pull the account's content *in* and seal each item as a vault
  record (``social/<platform>/<connector>/<id>``). This is where the raw social
  data other systems build profiles from actually lands: encrypted at rest,
  AAD-bound to the tenant, and covered by the same audit chain and retention as
  every other record.
- **publish** — share an update *on* the platform, reachable by a QR beacon.

Everything is tenant-scoped: a connector is only visible and usable under the
token of the tenant that owns it.
"""

from __future__ import annotations

import json

from . import db, vault

_PLATFORM_URL = {
    "instagram": "https://instagram.com/{h}",
    "x": "https://x.com/{h}",
    "tiktok": "https://tiktok.com/@{h}",
    "facebook": "https://facebook.com/{h}",
    "linkedin": "https://linkedin.com/in/{h}",
    "youtube": "https://youtube.com/@{h}",
    "reddit": "https://reddit.com/user/{h}",
    "threads": "https://threads.net/@{h}",
}


def _out(row: dict) -> dict:
    return {
        "id": row["id"],
        "tenant_id": row["tenant_id"],
        "platform": row["platform"],
        "direction": row["direction"],
        "handle": f"@{row['handle']}" if row["handle"] else None,
        "scope": json.loads(row["scope"]),
        "status": row["status"],
        "collected": row["collected"],
        "published": row["published"],
        "beacon": f"/connectors/{row['id']}/beacon" if row["direction"] == "publish" else None,
    }


def get(cid: str) -> dict | None:
    row = db.connect().execute(
        "SELECT * FROM connectors WHERE id=?", (cid,)).fetchone()
    return dict(row) if row else None


def create(tenant_id: str, platform: str, direction: str,
           handle: str | None, scope: list[str]) -> dict:
    conn = db.connect()
    cid = db.new_id("con")
    handle = (handle or "").lstrip("@") or None
    conn.execute(
        "INSERT INTO connectors (id, tenant_id, platform, direction, handle,"
        " scope, status, collected, published, created_at)"
        " VALUES (?,?,?,?,?,?, 'active', 0, 0, ?)",
        (cid, tenant_id, platform, direction, handle, json.dumps(scope), db.utcnow()),
    )
    conn.commit()
    return _out(get(cid))


def for_tenant(tenant_id: str) -> list[dict]:
    rows = db.connect().execute(
        "SELECT * FROM connectors WHERE tenant_id=? ORDER BY created_at, rowid",
        (tenant_id,)).fetchall()
    return [_out(dict(r)) for r in rows]


def revoke(cid: str) -> dict:
    db.connect().execute("UPDATE connectors SET status='revoked' WHERE id=?", (cid,))
    db.connect().commit()
    return {"id": cid, "status": "revoked"}


def ingest(tenant: dict, row: dict, items: list[dict]) -> dict:
    """Seal each collected item as a vault record under this connector."""
    keys = []
    for item in items:
        item_id = db.new_id("itm")
        key = f"social/{row['platform']}/{row['id']}/{item_id}"
        vault.put(tenant, key, json.dumps({
            "content": item.get("content", ""),
            "ref": item.get("ref"),
            "platform": row["platform"],
        }))
        keys.append(key)
    conn = db.connect()
    conn.execute("UPDATE connectors SET collected = collected + ? WHERE id=?",
                 (len(keys), row["id"]))
    conn.commit()
    return {"connector": row["id"], "platform": row["platform"],
            "sealed": len(keys), "keys": keys,
            "note": "collected items are encrypted at rest in the vault"}


def publish(row: dict, content: str, topic: str | None) -> dict:
    conn = db.connect()
    conn.execute("UPDATE connectors SET published = published + 1 WHERE id=?",
                 (row["id"],))
    conn.commit()
    return {"connector": row["id"], "platform": row["platform"],
            "topic": topic, "content": content, "status": "published"}


def presence_url(row: dict, public_base: str) -> str:
    if row["handle"] and row["platform"] in _PLATFORM_URL:
        return _PLATFORM_URL[row["platform"]].format(h=row["handle"])
    return f"{public_base}/connectors/{row['id']}"
