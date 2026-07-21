"""Data-retention policy — from a short window all the way up to **forever**.

Two independent knobs:

- **Soft-delete recovery window** (``PDI_RECOVERY_WINDOW``, global): how long a
  soft-deleted tenant stays restorable before ``sweep`` purges it. ``forever``
  (the default) means a soft-deleted tenant is *never* auto-purged — an operator
  must explicitly ``wipe`` it.
- **Per-tenant record retention** (``retention_days`` on the tenant): records
  older than the window are auto-expired on ``sweep``. ``forever`` (the default,
  stored as NULL) means records live until explicitly deleted.

Retention is expressed as a named window (``7d``/``30d``/``90d``/``180d``/``1y``
/``forever``) or a raw positive day count; ``forever`` / ``0`` / unset all mean
no expiry. The tamper-evident audit chain itself is always kept forever —
pruning it would break its guarantee — so retention never touches it.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from . import audit, db

WINDOWS = {"7d": 7, "30d": 30, "90d": 90, "180d": 180, "1y": 365, "forever": None}


def parse_window(value) -> int | None:
    """Normalise a window to a day count, or ``None`` for forever."""
    if value in (None, "", "forever", "0", 0):
        return None
    if isinstance(value, str) and value in WINDOWS:
        return WINDOWS[value]
    try:
        n = int(value)
    except (TypeError, ValueError):
        raise ValueError(
            f"retention must be one of {sorted(WINDOWS)} or a positive day count")
    return None if n <= 0 else n


def fmt(days: int | None) -> str:
    return "forever" if days is None else f"{days}d"


def recovery_window_days() -> int | None:
    return parse_window(os.environ.get("PDI_RECOVERY_WINDOW", "forever"))


def _age_days(iso: str) -> float:
    then = datetime.fromisoformat(iso)
    if then.tzinfo is None:
        then = then.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - then).total_seconds() / 86400


def policy() -> dict:
    conn = db.connect()
    rows = conn.execute(
        "SELECT id, name, retention_days FROM tenants WHERE deleted_at IS NULL"
    ).fetchall()
    return {
        "recovery_window": fmt(recovery_window_days()),
        "windows": sorted(WINDOWS, key=lambda w: (WINDOWS[w] is None, WINDOWS[w] or 0)),
        "record_retention": [
            {"tenant_id": r["id"], "name": r["name"],
             "retention": fmt(r["retention_days"])} for r in rows],
    }


def set_tenant_retention(tenant_id: str, value) -> dict | None:
    days = parse_window(value)
    conn = db.connect()
    if conn.execute("SELECT 1 FROM tenants WHERE id=?", (tenant_id,)).fetchone() is None:
        return None
    conn.execute("UPDATE tenants SET retention_days=? WHERE id=?", (days, tenant_id))
    conn.commit()
    audit.record("retention.set", tenant_id=tenant_id, ref=fmt(days))
    return {"tenant_id": tenant_id, "retention": fmt(days)}


def sweep() -> dict:
    """Enforce retention now: purge soft-deleted tenants past the recovery
    window, and expire records past their tenant's retention. ``forever``
    windows purge/expire nothing."""
    conn = db.connect()
    purged_tenants, expired_records = 0, 0

    rw = recovery_window_days()
    if rw is not None:
        for r in conn.execute(
                "SELECT id, deleted_at FROM tenants WHERE deleted_at IS NOT NULL"
        ).fetchall():
            if _age_days(r["deleted_at"]) >= rw:
                conn.execute("DELETE FROM records WHERE tenant_id=?", (r["id"],))
                conn.execute("DELETE FROM tenant_tokens WHERE tenant_id=?", (r["id"],))
                conn.execute("DELETE FROM tenants WHERE id=?", (r["id"],))
                purged_tenants += 1
                audit.record("tenant.purge", tenant_id=r["id"])

    for t in conn.execute(
            "SELECT id, retention_days FROM tenants"
            " WHERE retention_days IS NOT NULL AND deleted_at IS NULL").fetchall():
        for rec in conn.execute(
                "SELECT id, key, updated_at FROM records WHERE tenant_id=?",
                (t["id"],)).fetchall():
            if _age_days(rec["updated_at"]) >= t["retention_days"]:
                conn.execute("DELETE FROM records WHERE id=?", (rec["id"],))
                expired_records += 1
                audit.record("record.expire", tenant_id=t["id"], ref=rec["key"])

    conn.commit()
    return {"purged_tenants": purged_tenants, "expired_records": expired_records,
            "recovery_window": fmt(rw)}
