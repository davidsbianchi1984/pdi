"""Where the vault physically runs, and what that costs.

QRME and JIM-mini sell memberships. PDI does not: it is the layer underneath
both, and what it offers is a **place to put the bytes**. Four of them, and the
first is free.

* **Colocation** — our facility, and **free** for holding and sharing the data
  of JIM-mini and QRME users. Free is not a trial and not a loss-leader with a
  cliff at the end: the tandem is the reason those two products can promise
  that sensitive material never sits in their own database, and putting a price
  on the only place it can go would make that promise conditional on somebody's
  card.
* **Leased space** — a rack, a cage or a suite in a facility we own, tied into
  the same control plane. Quoted rather than listed, because floor space is
  priced by the room.
* **Your own facility** — you own the building, you host the vault, we tie into
  it. Also quoted.
* **Your own device** — a phone or a computer on your own broadband, holding
  its own vault. Free, because it is your hardware and your electricity.

**The encouragement to lease must not become a reason to make the free option
worse**, and this module is written to make that hard rather than to promise
it. Every mode runs the same code: the same AES-256-GCM, the same AAD binding,
the same tamper-evident chain, the same BYOK. :data:`GUARANTEES` is one list
shared by all four, and a test asserts no mode can drop an entry from it. If
self-hosting is ever degraded relative to colocation, it will not be by
accident here.

**What genuinely differs is availability, not security**, and saying so plainly
is the honest version of the sales pitch. A phone in a pocket is not a Tier III
facility: it goes flat, it goes through a washing machine, it is on a domestic
line that the household's video calls contend with. The bytes on it are exactly
as encrypted as ours. Whether they are *there tomorrow* is a different
question, and it is the customer's to answer. :data:`MODES` states that per
mode as `you_are_responsible_for`, because a hosting page that listed only
upside would be selling the wrong thing to the person most likely to need the
other kind.
"""

from __future__ import annotations

from . import audit, db
from . import i18n

# True of every mode. One list, shared, so a mode cannot quietly hold less.
GUARANTEES: tuple[str, ...] = (
    "AES-256-GCM at rest, AAD-bound to the tenant and key",
    "tamper-evident hash-chained audit log",
    "tenant isolation scoped before the query runs, not filtered after",
    "bring-your-own-key: the customer key travels per request, never stored",
    "bearer tokens held only as SHA-256 hashes",
    "retention you set, and deletion that leaves the audit trail intact",
)

# The four places a vault can live.
#
# `price` is `free`, or `quoted` where floor space is involved. A number is not
# invented for the leased options: a rack in one city is not a rack in another,
# and a made-up figure on a page like this is the kind of thing somebody plans
# a budget around.
MODES: dict[str, dict] = {
    "colocation": {
        "title": "Our facility",
        "price": "free",
        "means": "we hold it, in a facility we operate",
        "free_because": "the tandem is the only place JIM-mini and QRME may "
                        "put sensitive material, and a price here would make "
                        "their promise conditional on somebody's card",
        "we_are_responsible_for": ("power", "cooling", "network", "hardware",
                                   "backups", "physical access control"),
        "you_are_responsible_for": ("your key, if you bring one",),
        "availability": "facility-grade, redundant power and network",
    },
    "leased_space": {
        "title": "Leased space",
        "price": "quoted",
        "means": "a rack, cage or suite in a facility we own, tied into the "
                 "same control plane",
        "we_are_responsible_for": ("power", "cooling", "network",
                                   "physical access control"),
        "you_are_responsible_for": ("your hardware", "your backups",
                                    "your key"),
        "availability": "facility-grade, on hardware you own",
    },
    "own_facility": {
        "title": "Your facility",
        "price": "quoted",
        "means": "you own the building and host the vault; we tie into it",
        "we_are_responsible_for": ("the tie-in", "software updates"),
        "you_are_responsible_for": ("the building", "power", "network",
                                    "hardware", "backups", "your key"),
        "availability": "whatever your site provides",
    },
    "own_device": {
        "title": "Your own device",
        "price": "free",
        "means": "a phone or a computer on your own broadband, holding its "
                 "own vault",
        "free_because": "it is your hardware and your electricity",
        "we_are_responsible_for": (),
        "you_are_responsible_for": ("the device", "your broadband",
                                    "backups", "your key",
                                    "it being switched on"),
        "availability": "a domestic line and a battery — the bytes are as "
                        "encrypted as ours, and whether they are there "
                        "tomorrow is yours to answer",
    },
}
DEFAULT_MODE = "colocation"

# What we recommend, and to whom. Said as a sentence rather than by making the
# alternatives inconvenient.
GUIDANCE = (
    "Colocation is free and is the right answer for most people storing "
    "JIM-mini or QRME data. Lease space or host it yourself when you have a "
    "reason to hold the hardware — a regulator, a contract, or a preference "
    "about who can walk up to the machine. Your own device is a real option "
    "and not a toy: the encryption is identical. What changes is who is "
    "awake at 3am when it stops. None of the four changes whose data it "
    "is: every mode is custody rather than ownership, and the statutory "
    "rights of the people the records are about survive all of them."
)


class HostingError(ValueError):
    """A hosting arrangement that cannot stand."""


def modes() -> dict:
    """The hosting page, generated rather than typed."""
    return {
        "modes": {k: {**v,
                      "we_are_responsible_for": list(v["we_are_responsible_for"]),
                      "you_are_responsible_for": list(v["you_are_responsible_for"]),
                      "guarantees": list(GUARANTEES)}
                  for k, v in MODES.items()},
        "default": DEFAULT_MODE,
        "guidance": GUIDANCE,
        "guarantees": list(GUARANTEES),
        "free": [k for k, v in MODES.items() if v["price"] == "free"],
    }


def choose(tenant_id: str, mode: str, note: str | None = None) -> dict:
    """Record where this tenant's vault lives.

    A record rather than a switch: nothing here moves data. Choosing a mode is
    a statement about an arrangement that gets made by people, and a function
    that silently migrated somebody's vault because a field changed would be
    the most alarming endpoint in this product.
    """
    if mode not in MODES:
        raise HostingError(
            i18n.fill(i18n.UNKNOWN_CHOICE, field="hosting mode", got=repr(mode), choices=', '.join(MODES)))
    conn = db.connect()
    now = db.utcnow()
    conn.execute(
        "UPDATE tenant_hosting SET ended_at=? WHERE tenant_id=? AND"
        " ended_at IS NULL", (now, tenant_id))
    conn.execute(
        "INSERT INTO tenant_hosting (id, tenant_id, mode, note, started_at)"
        " VALUES (?,?,?,?,?)",
        (db.new_id("hst"), tenant_id, mode, note, now))
    conn.commit()
    audit.record("hosting.choose", ref=tenant_id)
    return arrangement(tenant_id)


def mode_of(tenant_id: str) -> str:
    row = db.connect().execute(
        "SELECT mode FROM tenant_hosting WHERE tenant_id=? AND"
        " ended_at IS NULL", (tenant_id,)).fetchone()
    return row["mode"] if row else DEFAULT_MODE


def arrangement(tenant_id: str) -> dict:
    """Where this tenant sits, what it costs, and who holds what up."""
    mode = mode_of(tenant_id)
    spec = MODES[mode]
    row = db.connect().execute(
        "SELECT note, started_at FROM tenant_hosting WHERE tenant_id=? AND"
        " ended_at IS NULL", (tenant_id,)).fetchone()
    return {
        "tenant_id": tenant_id,
        "mode": mode,
        "title": spec["title"],
        "price": spec["price"],
        "means": spec["means"],
        "availability": spec["availability"],
        "we_are_responsible_for": list(spec["we_are_responsible_for"]),
        "you_are_responsible_for": list(spec["you_are_responsible_for"]),
        # Identical on every mode, and returned on every mode so that nobody
        # has to take that on trust from a sentence elsewhere.
        "guarantees": list(GUARANTEES),
        "note": row["note"] if row else None,
        "since": row["started_at"] if row else None,
        "chosen": row is not None,
    }


def history(tenant_id: str) -> list[dict]:
    """Every arrangement this tenant has had. Where a vault has lived is
    exactly the kind of question an auditor asks afterwards."""
    rows = db.connect().execute(
        "SELECT mode, note, started_at, ended_at FROM tenant_hosting"
        " WHERE tenant_id=? ORDER BY started_at", (tenant_id,)).fetchall()
    return [dict(r) for r in rows]
