"""Append-only, hash-chained audit log for compliance / tamper evidence.

Each entry's hash covers the previous entry's hash, so any retroactive edit or
deletion breaks the chain and is detectable by ``verify()``.
"""

from __future__ import annotations

import hashlib
import json

from . import db

_GENESIS = "0" * 64

# ---- event schema -------------------------------------------------------- #
# The catalogue of audit actions: action -> (category, human description).
# Every write to the vault goes through one of these. The stored/hashed fields
# are fixed (see EVENT_FIELDS); `category` is derived at read time from the
# action, so enriching this catalogue never alters — or breaks — the chain.
ACTIONS: dict[str, tuple[str, str]] = {
    "put": ("data", "record sealed / updated"),
    "get": ("data", "record read (decrypted)"),
    "delete": ("data", "record deleted"),
    "record.expire": ("retention", "record auto-expired by retention policy"),
    "tenant.create": ("tenant", "tenant registered"),
    "tenant.soft_delete": ("tenant", "tenant soft-deleted (recovery window)"),
    "tenant.restore": ("tenant", "soft-deleted tenant restored"),
    "tenant.wipe": ("tenant", "tenant permanently wiped"),
    "tenant.purge": ("retention", "soft-deleted tenant purged after the recovery window"),
    "token.issue": ("access", "scoped token issued"),
    "token.revoke": ("access", "token revoked"),
    "retention.set": ("retention", "tenant retention policy changed"),
    "key.rotate": ("key", "key version rotated"),
    "key.rewrap": ("key", "key-encryption key rotated; DEKs re-wrapped, no record decrypted"),
    "key.reseal": ("key", "records re-sealed under the active key version"),
    "key.retire": ("key", "old key versions retired"),
    "snapshot.export": ("dr", "ciphertext snapshot exported"),
    "snapshot.restore": ("dr", "snapshot restored"),
    "deployment.create": ("admin", "deployment recorded"),
    "contribution.add": ("contribution", "cloud-model contribution sealed"),
    "position.create": ("position", "role-mapping intake sealed, assistant blueprint derived"),
    "baa.execute": ("compliance", "Business Associate Agreement recorded as executed for a tenant"),
    "baa.terminate": ("compliance", "tenant's Business Associate Agreement terminated"),
    "beacon.place": ("custody", "custody beacon placed on a carrier or a gate"),
    "beacon.found": ("custody", "carrier reported found by a finder"),
    "beacon.ring": ("custody", "facility gate beacon rung"),
    "beacon.retire": ("custody", "custody beacon retired"),
    "agent.engage": ("agent", "gate agent took a ring"),
    "agent.decide": ("agent", "gate agent resolved a request within its ceiling"),
    "agent.refuse": ("agent", "gate agent declined, with a reason and a route"),
    "agent.handoff": ("agent", "gate agent escalated to a human"),
    # Three actions, not one, because "a human was told" and "a human was not
    # told" are the two outcomes an auditor is actually asking about, and a
    # single `agent.page` would have hidden the second inside the first.
    "agent.page": ("agent", "hand-off delivered to the notification channel"),
    "agent.page_queued": ("agent", "hand-off queued — no notification channel configured, nobody was reached"),
    "agent.page_failed": ("agent", "hand-off page could not be delivered, nobody was reached"),
    # Who can be summoned to a controlled facility is a governance fact, not a
    # preference — it belongs on the chain beside who was let in.
    "gate.roster": ("agent", "facility gate roster or timezone changed"),
    # The resident intelligence (pdi/resident.py): plans, steps and the two
    # acts an auditor asks about by name — what left the host, and what was
    # written where the app can query it.
    "resident.plan": ("agent", "resident task planned (steps stored, nothing run)"),
    "resident.step": ("agent", "resident step finished (done, failed or skipped)"),
    "resident.task": ("agent", "resident task finished"),
    "resident.fetch": ("agent", "resident fetched an external page (sealed to the vault)"),
    "resident.rows": ("agent", "resident wrote rows into a queryable dataset"),
    "resident.embed": ("agent", "resident stored an embedding (hash of the text, never the text)"),
    "resident.forget": ("agent", "resident removed embedding vector(s) — one key or a prefix"),
    # What the resident makes of the tandems' banked corpus (3.0.1).
    "resident.learn": ("agent", "resident indexed the sealed training corpus — examples learned beside the vault's vectors"),
    "resident.export": ("agent", "resident sealed a fine-tune set from the corpus"),
    "resident.train": ("agent", "resident handed a sealed training set to the local trainer"),
}

EVENT_FIELDS = {
    "seq": "monotonic sequence number (chain order)",
    "tenant_id": "tenant the event belongs to (null for admin/global events)",
    "action": "one of the catalogued actions",
    "category": "derived group for the action (data, tenant, access, key, retention, dr, contribution, position, admin, compliance, custody, agent)",
    "ref": "resource reference — record key, tenant id, or a small detail",
    "at": "UTC ISO-8601 timestamp",
    "prev_hash": "SHA-256 of the previous entry (chain link)",
    "hash": "SHA-256 over prev_hash + {tenant_id, action, ref, at}",
}


def category(action: str) -> str:
    return ACTIONS.get(action, ("other", ""))[0]


def schema() -> dict:
    """The audit event schema: fields, the action catalogue, and the retention
    stance (the chain is kept forever; pruning it would break tamper-evidence)."""
    return {
        "event_fields": EVENT_FIELDS,
        "actions": [{"action": a, "category": c, "description": d}
                    for a, (c, d) in sorted(ACTIONS.items())],
        "retention": ("append-only and SHA-256 hash-chained; kept forever. "
                      "Retention policies apply to records and soft-deleted "
                      "tenants, never to the audit chain."),
    }


def _hash(prev_hash: str, entry: dict) -> str:
    payload = prev_hash + json.dumps(entry, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def record(action: str, *, tenant_id: str | None = None, ref: str | None = None) -> dict:
    conn = db.connect()
    row = conn.execute(
        "SELECT hash FROM audit ORDER BY seq DESC LIMIT 1"  # tenant-unscoped: the chain is one deployment-wide sequence by design — each entry hashes its predecessor across tenants, which is what makes per-tenant deletion tamper-evident
    ).fetchone()
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


def entries(tenant_id: str) -> list[dict]:
    """One tenant's entries, never the deployment's. The bare branch this
    function used to carry answered every tenant's rows to whoever forgot
    the argument — nothing called it, and now nothing can."""
    rows = db.connect().execute(
        "SELECT * FROM audit WHERE tenant_id=? ORDER BY seq", (tenant_id,)
    ).fetchall()
    return [{**dict(r), "category": category(r["action"])} for r in rows]


def verify() -> dict:
    """Recompute the chain; report whether it is intact."""
    conn = db.connect()
    rows = conn.execute(
        "SELECT * FROM audit ORDER BY seq"  # tenant-unscoped: verifying the chain means walking all of it — the hashes span tenants on purpose
    ).fetchall()
    prev_hash = _GENESIS
    for r in rows:
        entry = {"tenant_id": r["tenant_id"], "action": r["action"],
                 "ref": r["ref"], "at": r["at"]}
        expected = _hash(prev_hash, entry)
        if r["prev_hash"] != prev_hash or r["hash"] != expected:
            return {"intact": False, "broken_at_seq": r["seq"], "entries": len(rows)}
        prev_hash = r["hash"]
    return {"intact": True, "entries": len(rows)}
