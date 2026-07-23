"""Robotics catalog & robot data intake — the home's robots, vault-backed.

The same registry QRME and JIM-mini carry (each repo ships its own copy).
In PDI a bound robot is a **data source**: the maps, camera snapshots, and
sensor logs it collects while working a home are exactly the kind of intimate
data that must never sit in plaintext on a vendor cloud. Ingest seals every
item into the tenant's vault (AES-256-GCM at rest) and hash-chains the action
in the audit log, so what a robot saw — and who touched it — is provable.
"""

from __future__ import annotations

import json

from . import audit, db, vault

# (key, label, maker, kind, capabilities, llm_capable)
_ROWS: list[tuple[str, str, str, str, list[str], bool]] = [
    ("isaac_1", "Isaac 1", "Weave Robotics", "home_robot",
     ["mobility", "manipulation", "voice", "vision", "tidying"], True),
    ("neo", "NEO", "1X Technologies", "humanoid",
     ["mobility", "manipulation", "voice", "vision", "chores"], True),
    ("u1_lite", "UWorld U1 Lite", "UBTech Robotics", "humanoid",
     ["mobility", "voice", "vision"], True),
    ("u1_pro", "UWorld U1 Pro", "UBTech Robotics", "humanoid",
     ["mobility", "manipulation", "voice", "vision"], True),
    ("u1_ultra", "UWorld U1 Ultra", "UBTech Robotics", "humanoid",
     ["mobility", "manipulation", "voice", "vision", "chores"], True),
    ("memo", "Memo", "Sunday Robotics", "home_robot",
     ["mobility", "manipulation", "voice", "vision", "tidying"], True),
    ("saros_20", "Saros 20", "Roborock", "vacuum",
     ["mapping", "navigation", "vacuum", "mop", "camera_patrol"], True),
    ("saros_20_sonic", "Saros 20 Sonic", "Roborock", "vacuum",
     ["mapping", "navigation", "vacuum", "sonic_mop", "camera_patrol"], True),
    ("qrevo_curv_2_flow", "Qrevo Curv 2 Flow", "Roborock", "vacuum",
     ["mapping", "navigation", "vacuum", "mop"], False),
]

BY_KEY: dict[str, dict] = {
    key: {"model": key, "label": label, "maker": maker, "kind": kind,
          "capabilities": caps, "llm_capable": llm}
    for key, label, maker, kind, caps, llm in _ROWS
}

# The kinds of data a robot may deposit; anything else is refused.
DATA_KINDS = ("map", "snapshot", "sensor_log")


def robot_catalog() -> dict:
    makers: dict[str, list[dict]] = {}
    for row in BY_KEY.values():
        makers.setdefault(row["maker"], []).append(row)
    return {"robots": list(BY_KEY.values()), "by_maker": makers,
            "data_kinds": list(DATA_KINDS)}


def get(model: str) -> dict | None:
    return BY_KEY.get(model)


def create(tenant_id: str, spec: dict, name: str | None) -> dict:
    conn = db.connect()
    robot_id = db.new_id("rob")
    robot_name = name or spec["label"]
    conn.execute(
        "INSERT INTO robots (id, tenant_id, model, name, status, collected,"
        " created_at) VALUES (?,?,?,?,'active',0,?)",
        (robot_id, tenant_id, spec["model"], robot_name, db.utcnow()))
    conn.commit()
    audit.record("robot.bind", tenant_id=tenant_id, ref=robot_id)
    return {"id": robot_id, "model": spec["model"], "label": spec["label"],
            "maker": spec["maker"], "kind": spec["kind"], "name": robot_name,
            "data_kinds": list(DATA_KINDS)}


def for_tenant(tenant_id: str) -> list[dict]:
    rows = db.connect().execute(
        "SELECT * FROM robots WHERE tenant_id=? ORDER BY created_at, rowid",
        (tenant_id,)).fetchall()
    return [dict(r) for r in rows]


def by_id(robot_id: str, tenant_id: str) -> dict | None:
    row = db.connect().execute(
        "SELECT * FROM robots WHERE id=? AND tenant_id=?",
        (robot_id, tenant_id)).fetchone()
    return dict(row) if row else None


def ingest(tenant: dict, row: dict, kind: str, content: str,
           ref: str | None = None) -> dict:
    """Seal one item the robot collected into the vault. The vault write is
    hash-chained by the audit log, so custody of what the robot saw is
    provable end to end."""
    item_id = db.new_id("itm")
    key = f"robot/{row['model']}/{row['id']}/{kind}/{item_id}"
    vault.put(tenant, key, json.dumps({
        "kind": kind, "content": content, "ref": ref,
        "robot": f"{row['maker']}:{row['model']}" if "maker" in row
                 else row["model"],
    }))
    conn = db.connect()
    conn.execute("UPDATE robots SET collected = collected + 1 WHERE id=?",
                 (row["id"],))
    conn.commit()
    audit.record("robot.ingest", tenant_id=tenant["id"], ref=key)
    return {"robot": row["id"], "kind": kind, "sealed": True, "key": key,
            "note": "robot data is encrypted at rest in the vault"}


def data_keys(tenant: dict, row: dict) -> list[str]:
    """The vault keys this robot has deposited (values stay sealed; read them
    through GET /records/{key})."""
    prefix = f"robot/{row['model']}/{row['id']}/"
    return [k for k in vault.list_keys(tenant) if k.startswith(prefix)]


def unbind(tenant_id: str, robot_id: str) -> dict:
    conn = db.connect()
    conn.execute("UPDATE robots SET status='revoked' WHERE id=?", (robot_id,))
    conn.commit()
    audit.record("robot.unbind", tenant_id=tenant_id, ref=robot_id)
    return {"id": robot_id, "status": "revoked",
            "note": "sealed data remains in the vault under tenant control"}
