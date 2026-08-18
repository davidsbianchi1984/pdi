"""Who answers this facility's gate, and when.

`PDI_GATE_ONCALL` named one contact for the whole deployment. In a
single-tenant install that is merely thin; in PDI it is wrong, because PDI is
**multi-tenant** — one vault, many customers, each with their own facility. A
deployment-wide environment variable meant a courier at customer A's loading
dock was handed off to a name belonging to whoever set the variable, which in a
colocation facility is the operator rather than the tenant. Everything else in
this product is scoped to a tenant and enforced by a token; the one name a
stranger at a door gets routed to was global.

So the roster lives in the database, per tenant, written with the tenant's own
write token — same authority as placing a beacon. `PDI_GATE_ONCALL` stays as
the fallback when a tenant has no roster, so nothing already deployed changes.

**Validation happens on write.** JIM-mini's `jim/rota.py` solves the same
who-is-on-shift problem, and it has to parse its rota out of an environment
variable at the moment somebody needs help — which is why it needs a
never-raises read path and a loud degradation story. PDI has an API, so a
malformed shift is refused at `POST /gate/roster` with a 422 the operator reads
in the afternoon. The bad rota never reaches the door. That is the same
property JIM buys with a guard, bought here with a gate instead.

:func:`entries` still skips a row it cannot read rather than raising, because a
database can be edited by hand and a gate must answer regardless.

Three things this gets right, each of them a way of paging the wrong person —
the same three JIM had to get right, because the problem is genuinely shared:

**Shifts cross midnight.** ``18:00–06:00`` is the shift a facility gate exists
for, and ``start <= now <= end`` is false for every minute of it. A wrapping
shift is two intervals, and it belongs to the day it *started*: at 02:00 on
Saturday it is Friday's night porter on the desk, not the weekend rota.

**A facility is somewhere.** A tenant sets its own timezone; the rota is
evaluated there. Without it a rota written in local time is read in UTC, which
shifts every boundary by the offset — and by a *different* offset in summer, so
it would look correct for half the year.

**A rota has gaps.** Nobody is rostered at 4am on a public holiday. The gate
then tries everybody on the roster rather than nobody — better to wake the
wrong person than leave a stranger at a door — and says `on_shift: false` so
whoever it wakes knows they were a guess.
"""

from __future__ import annotations

import os
from datetime import datetime, time, timezone

from . import audit, db

DAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")

# What a roster entry is for. Not a permission — the gate's ceiling does not
# move for anybody on this list, and a `security` entry can no more grant entry
# than the agent can. It is a label for whoever reads the page.
ROLES = ("on-call", "supervisor", "reception", "security", "site lead")


class RosterError(ValueError):
    """A roster entry that cannot be stored. Raised at write time, by design —
    see the module docstring: the point is that it never reaches the door."""


def fallback() -> str:
    """The pre-roster behaviour, kept for tenants that have not set one."""
    return os.environ.get("PDI_GATE_ONCALL", "the site's on-call contact")


# --- parsing (write path) --------------------------------------------------

def parse_days(spec) -> tuple[str, ...]:
    if spec is None:
        return DAYS
    s = str(spec).strip().lower()
    if not s or s == "all":
        return DAYS
    out: list[str] = []
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, _, b = part.partition("-")
            a, b = a.strip()[:3], b.strip()[:3]
            if a not in DAYS or b not in DAYS:
                raise RosterError(f"unknown day range {part!r}")
            i, j = DAYS.index(a), DAYS.index(b)
            # fri-mon wraps the week the same way a night shift wraps a day.
            out.extend(DAYS[i:j + 1] if i <= j else DAYS[i:] + DAYS[:j + 1])
        else:
            d = part[:3]
            if d not in DAYS:
                raise RosterError(f"unknown day {part!r}")
            out.append(d)
    if not out:
        raise RosterError("a shift needs at least one day")
    return tuple(dict.fromkeys(out))


def parse_time(spec, fallback_t: time) -> time:
    if spec is None or str(spec).strip() == "":
        return fallback_t
    s = str(spec).strip()
    # 24:00 is a legal way to write "the end of the day"; datetime will not
    # parse it, so it is normalised rather than rejected.
    if s in ("24:00", "2400"):
        return time(23, 59, 59)
    for fmt in ("%H:%M", "%H%M", "%H"):
        try:
            return datetime.strptime(s, fmt).time()
        except ValueError:
            continue
    raise RosterError(f"unreadable time {spec!r} — use HH:MM")


# --- timezone --------------------------------------------------------------

def tz_is_valid(name: str) -> bool:
    if not name or name.upper() == "UTC":
        return True
    try:
        from zoneinfo import ZoneInfo
        ZoneInfo(name)
        return True
    except Exception:
        return False


def timezone_name(tenant_id: str) -> str:
    row = db.connect().execute(
        "SELECT timezone FROM gate_settings WHERE tenant_id=?",
        (tenant_id,)).fetchone()
    return row["timezone"] if row else "UTC"


def set_timezone(tenant: dict, name: str) -> dict:
    """Refused rather than silently treated as UTC. An unrecognised zone that
    quietly falls back is the failure mode that looks correct for half the year
    and pages the wrong person for the other half."""
    name = (name or "UTC").strip()
    if not tz_is_valid(name):
        raise RosterError(
            f"{name!r} is not a timezone this system knows — use an IANA name "
            f"like 'Europe/Lisbon'")
    conn = db.connect()
    conn.execute(
        "INSERT INTO gate_settings (tenant_id, timezone, updated_at)"
        " VALUES (?,?,?) ON CONFLICT (tenant_id) DO UPDATE SET"
        " timezone=excluded.timezone, updated_at=excluded.updated_at",
        (tenant["id"], name, db.utcnow()))
    conn.commit()
    audit.record("gate.roster", tenant_id=tenant["id"], ref=f"timezone={name}")
    return {"tenant_id": tenant["id"], "timezone": name}


def _tz(tenant_id: str):
    name = timezone_name(tenant_id)
    if name.upper() == "UTC":
        return timezone.utc
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(name)
    except Exception:
        # Only reachable if the zone database shrank under a stored name that
        # validated when it was written. The gate still answers.
        return timezone.utc


# --- the roster ------------------------------------------------------------

def add(tenant: dict, name: str, role: str = "on-call", days=None,
        from_time=None, to_time=None, position: int | None = None) -> dict:
    name = (name or "").strip()
    if not name:
        raise RosterError("a roster entry needs a name")
    role = (role or "on-call").strip()
    if role not in ROLES:
        raise RosterError(f"role must be one of {', '.join(ROLES)}")
    d = parse_days(days)
    f = parse_time(from_time, time(0, 0))
    t = parse_time(to_time, time(23, 59, 59))

    conn = db.connect()
    if position is None:
        row = conn.execute(
            "SELECT COALESCE(MAX(position), -1) AS p FROM gate_roster"
            " WHERE tenant_id=?", (tenant["id"],)).fetchone()
        position = row["p"] + 1
    rid = db.new_id("rost")
    conn.execute(
        "INSERT INTO gate_roster (id, tenant_id, name, role, position, days,"
        " from_time, to_time, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (rid, tenant["id"], name, role, position, ",".join(d),
         f.strftime("%H:%M:%S"), t.strftime("%H:%M:%S"), db.utcnow()))
    conn.commit()
    # Who can be summoned to a controlled facility is a governance fact, so it
    # lands on the chain like every other one.
    audit.record("gate.roster", tenant_id=tenant["id"], ref=rid)
    return out(rid, tenant["id"])


def remove(tenant: dict, entry_id: str) -> bool:
    conn = db.connect()
    n = conn.execute("DELETE FROM gate_roster WHERE id=? AND tenant_id=?",
                     (entry_id, tenant["id"])).rowcount
    conn.commit()
    if n:
        audit.record("gate.roster", tenant_id=tenant["id"],
                     ref=f"removed {entry_id}")
    return bool(n)


def row(entry_id: str, tenant_id: str) -> dict | None:
    """This tenant's roster entry or nothing — the scope is in the SQL."""
    r = db.connect().execute(
        "SELECT * FROM gate_roster WHERE id=? AND tenant_id=?",
        (entry_id, tenant_id)).fetchone()
    return dict(r) if r else None


def out(entry_id: str, tenant_id: str) -> dict:
    r = row(entry_id, tenant_id)
    return {
        "id": r["id"],
        "name": r["name"],
        "role": r["role"],
        "position": r["position"],
        "days": r["days"].split(","),
        "from": r["from_time"][:5],
        "to": r["to_time"][:5],
        "crosses_midnight": r["to_time"] <= r["from_time"],
    }


def entries(tenant_id: str) -> list[dict]:
    """This tenant's roster, in order. Scoped by `tenant_id` in the query — a
    roster is as much this tenant's data as a sealed record is.

    A row that cannot be parsed is skipped rather than raised: everything here
    was validated on the way in, so this only fires for a hand-edited database,
    and a gate that refuses to answer because of one bad row is worse than a
    gate that answers with the rest.
    """
    rows = db.connect().execute(
        "SELECT * FROM gate_roster WHERE tenant_id=? ORDER BY position, rowid",
        (tenant_id,)).fetchall()
    out_rows = []
    for r in rows:
        try:
            out_rows.append({
                "id": r["id"], "name": r["name"], "role": r["role"],
                "days": tuple(r["days"].split(",")),
                "from": parse_time(r["from_time"][:5], time(0, 0)),
                "to": parse_time(r["to_time"][:5], time(23, 59, 59)),
            })
        except RosterError:
            continue
    return out_rows


def configured(tenant_id: str) -> bool:
    return bool(entries(tenant_id))


def _wraps(e: dict) -> bool:
    return e["to"] <= e["from"]


def _covers(e: dict, at: datetime) -> bool:
    """Is this shift running at ``at``? ``at`` is facility-local and aware.

    A wrapping shift is two intervals and is attributed to the day it started —
    the half after midnight belongs to *yesterday's* rostered day. Checking the
    wrapped half against today's weekday is the bug that asks whether Saturday
    is rostered at 2am on Saturday, decides it is not, and leaves the night
    porter who is actually on the desk unpaged.
    """
    today = DAYS[at.weekday()]
    yesterday = DAYS[(at.weekday() - 1) % 7]
    clock = at.time()
    if not _wraps(e):
        return today in e["days"] and e["from"] <= clock <= e["to"]
    if today in e["days"] and clock >= e["from"]:
        return True                        # tonight's shift, before midnight
    return yesterday in e["days"] and clock <= e["to"]   # last night's, after


def now(tenant_id: str) -> datetime:
    return datetime.now(_tz(tenant_id))


def on_now(tenant_id: str, at: datetime | None = None) -> list[dict]:
    """Who is on the desk, in roster order. Possibly nobody."""
    at = at or now(tenant_id)
    tz = _tz(tenant_id)
    at = at.replace(tzinfo=tz) if at.tzinfo is None else at.astimezone(tz)
    return [{"name": e["name"], "role": e["role"]}
            for e in entries(tenant_id) if _covers(e, at)]


def order(tenant_id: str, at: datetime | None = None) -> tuple[list[dict], bool]:
    """``(people to try, in order, whether anybody was actually on shift)``.

    On shift first, then everybody else — a gap must not mean nobody is
    reached, it means the gate is guessing, and the second element is how it
    admits that. A tenant with no roster gets the single `PDI_GATE_ONCALL`
    name, which is exactly what every tenant got before this existed.
    """
    people = entries(tenant_id)
    if not people:
        return ([{"name": fallback(), "role": "on-call"}], False)
    on = on_now(tenant_id, at)
    on_names = {p["name"] for p in on}
    rest = [{"name": e["name"], "role": e["role"]}
            for e in people if e["name"] not in on_names]
    return (on + rest, bool(on))


def describe(tenant_id: str, at: datetime | None = None) -> dict:
    """The roster as an operator should be able to read it, *and* who it would
    reach right now — so "who answers the gate at 3am?" is a question with an
    answer in the afternoon."""
    at = at or now(tenant_id)
    people, anybody = order(tenant_id, at)
    tz = timezone_name(tenant_id)
    return {
        "configured": configured(tenant_id),
        "timezone": tz,
        "evaluated_at": at.astimezone(_tz(tenant_id)).isoformat(),
        "on_now": on_now(tenant_id, at),
        "escalation_order": [p["name"] for p in people],
        "anybody_on_shift": anybody,
        "roster": [out(e["id"], tenant_id) for e in entries(tenant_id)],
        "note": (
            "no roster — hand-offs go to PDI_GATE_ONCALL, the same single "
            "name every tenant shared before a roster could be set"
            if not configured(tenant_id) else
            "nobody is rostered right now — the gate will try the whole "
            "roster rather than nobody, and say it was guessing"
            if not anybody else
            "this facility's roster"),
    }
