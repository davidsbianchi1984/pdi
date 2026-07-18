"""Append-only, hash-chained audit log for compliance / tamper evidence.

Each entry's hash covers the previous entry's hash, so any retroactive edit or
deletion breaks the chain and is detectable by ``verify()``.
"""

from __future__ import annotations

import hashlib
import json

from . import db

_GENESIS = "0" * 64


def _hash(prev_hash: str, entry: dict) -> str:
    payload = prev_hash + json.dumps(entry, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def record(action: str, *, tenant_id: str | None = None, ref: str | None = None) -> dict:
    conn = db.connect()
    row = conn.execute("SELECT hash FROM audit ORDER BY seq DESC LIMIT 1").fetchone()
    prev_hash = row["hash"] if row else _GENESIS
    entry = {"tenant_id": tenant_id, "action": action, "ref": ref, "at": db.utcnow()}
    h = _hash(prev_hash, entry)
    conn.execute(
        "INSERT INTO audit (tenant_id, action, ref, at, prev_hash, hash)"
        " VALUES (?,?,?,?,?,?)",
        (tenant_id, action, ref, entry["at"], prev_hash, h),
    )
    conn.commit()
    return {**entry, "hash": h}


def entries(tenant_id: str | None = None) -> list[dict]:
    conn = db.connect()
    if tenant_id:
        rows = conn.execute(
            "SELECT * FROM audit WHERE tenant_id=? ORDER BY seq", (tenant_id,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM audit ORDER BY seq").fetchall()
    return [dict(r) for r in rows]


def verify() -> dict:
    """Recompute the chain; report whether it is intact."""
    conn = db.connect()
    rows = conn.execute("SELECT * FROM audit ORDER BY seq").fetchall()
    prev_hash = _GENESIS
    for r in rows:
        entry = {"tenant_id": r["tenant_id"], "action": r["action"],
                 "ref": r["ref"], "at": r["at"]}
        expected = _hash(prev_hash, entry)
        if r["prev_hash"] != prev_hash or r["hash"] != expected:
            return {"intact": False, "broken_at_seq": r["seq"], "entries": len(rows)}
        prev_hash = r["hash"]
    return {"intact": True, "entries": len(rows)}
