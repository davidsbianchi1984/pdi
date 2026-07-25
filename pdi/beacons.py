"""Custody beacons — a printed code on a physical thing.

QRME's desk beacon puts a QR on a shop door and reveals a person. The gesture
ports here; what it resolves to inverts. PDI's subject is custody of data, and
custody keeps escaping into the physical world where PDI cannot see it: a
records box in a courier's van, a decommissioned drive on a pallet, a robot out
for service. The moment a payload has a handle, custody has a gap.

A beacon closes it, and the governing rule is what the card **withholds**:

* It says that the thing is under custody, which compliance programs govern it,
  what state the seal is in, and how to hand it in.
* It never says the filename, the classification, the counterparty, or a byte
  of the payload. Nothing here reaches :func:`pdi.vault.get`; a beacon holds no
  key and never touches ciphertext, which is also why BYOK changes nothing
  about it.

Two other decisions live in this module rather than in the caller:

**A scan is cheap; a `found` report is a link in the chain.** The audit log is
hash-chained tamper evidence, and a barcode gun sweeping a pallet would write
hundreds of rows into it for one lorry. Scans land in ``beacon_scans``; only a
finder's report reaches :mod:`pdi.audit`, and only a few times an hour.

**Blind by default.** Naming the tenant can itself be the disclosure — a drive
labelled with an oncology practice has told you something about the people
inside it before anyone scanned anything. QRME's default is the opposite for
the opposite reason. Naming a regulated carrier is a decision somebody makes,
never one they inherit.

See docs/beacons.md.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from . import audit, compliance, db, intakes, transfers

KINDS = ("transfer", "intake", "object", "facility")
DISCLOSE = ("blind", "contact")
STATES = ("sealed", "in_transit", "opened", "closed")
RING_KINDS = ("delivery", "access", "collection", "other")

# A finder reporting the same carrier repeatedly is one event, not many. The
# cap is on chain links rather than on scans, because the chain is the thing
# whose value degrades with volume.
FOUND_CAP = 4
FOUND_WINDOW_MINUTES = 60

# The positive claim on the card. Absence of detail is not a disclosure on its
# own — a stranger cannot tell "sealed" from "we forgot to say" — so the card
# states it, the same way QRME's desk beacon states "Live person — not AI"
# rather than relying on the missing AI mark.
BADGE = "Sealed — this code proves custody, not contents."

# A gate is not a carrier, so the carrier's claim is the wrong one to make at a
# door: nothing there is sealed, and nobody standing outside is wondering what
# is inside a building. The claim that matters is the one they might actually
# get wrong — and it is stated positively, for the same reason as above.
GATE_BADGE = "Ringing this does not open anything."


class BeaconError(Exception):
    pass


def _row(beacon_id: str) -> dict | None:
    row = db.connect().execute(
        "SELECT * FROM custody_beacons WHERE id=?", (beacon_id,)).fetchone()
    return dict(row) if row else None


def _out(row: dict) -> dict:
    return {
        "id": row["id"],
        "tenant_id": row["tenant_id"],
        "ref_kind": row["ref_kind"],
        "ref_id": row["ref_id"],
        "label": row["label"],
        "disclose": row["disclose"],
        "programs": json.loads(row["programs"]),
        "state": row["state"],
        "scans": row["scans"],
        "active": bool(row["active"]),
        "created_at": row["created_at"],
        "scan_url": f"/s/{row['id']}",
        "qr_svg": f"/s/{row['id']}/qr.svg",
    }


def _parent(ref_kind: str, ref_id: str, tenant_id: str) -> dict:
    """The transfer or intake a carrier beacon is placed on.

    Its programs become the beacon's, rather than being passed in again: the
    record already knows what governs it, and two sources for one fact is how
    they end up disagreeing on the card a stranger reads.
    """
    row = transfers.get(ref_id) if ref_kind == "transfer" else intakes.get(ref_id)
    if row is None or row["tenant_id"] != tenant_id:
        raise BeaconError(f"no such {ref_kind}")
    return row


def place(tenant: dict, ref_kind: str, ref_id: str | None = None,
          label: str = "", disclose: str = "blind",
          programs: list[str] | None = None) -> dict:
    """Print this carrier — or this gate — onto something."""
    if ref_kind not in KINDS:
        raise BeaconError(f"ref_kind must be one of {', '.join(KINDS)}")
    if disclose not in DISCLOSE:
        raise BeaconError(f"disclose must be one of {', '.join(DISCLOSE)}")
    if not label.strip():
        raise BeaconError(
            "a beacon needs a label so its owner can tell their codes apart "
            "once several are printed and stuck to different things")

    if ref_kind in ("transfer", "intake"):
        if not ref_id:
            raise BeaconError(f"a {ref_kind} beacon needs a {ref_kind} to point at")
        parent = _parent(ref_kind, ref_id, tenant["id"])
        programs = json.loads(parent["programs"])
    else:
        # A bare object or a gate has no record behind it, so its programs are
        # declared here. This is the case that lets a physical thing enter
        # custody at all: the chain starts before anything is sealed, and for a
        # decommissioned drive nothing ever will be.
        ref_id = None
        programs = list(programs or [])
        unknown = [p for p in programs if compliance.get(p) is None]
        if unknown:
            raise BeaconError(f"unknown compliance program(s): {unknown}")

    bid = db.new_id("bcn")
    conn = db.connect()
    conn.execute(
        "INSERT INTO custody_beacons (id, tenant_id, ref_kind, ref_id, label,"
        " disclose, programs, state, scans, active, created_at)"
        " VALUES (?,?,?,?,?,?,?, 'sealed', 0, 1, ?)",
        (bid, tenant["id"], ref_kind, ref_id, label.strip(), disclose,
         json.dumps(programs), db.utcnow()))
    conn.commit()
    transfers._receipt(bid, "beacon placed", tenant.get("name"))
    audit.record("beacon.place", tenant_id=tenant["id"], ref=bid)
    return _out(_row(bid))


def for_tenant(tenant_id: str) -> list[dict]:
    rows = db.connect().execute(
        "SELECT * FROM custody_beacons WHERE tenant_id=?"
        " ORDER BY created_at, rowid", (tenant_id,)).fetchall()
    return [_out(dict(r)) for r in rows]


def get(beacon_id: str) -> dict | None:
    return _row(beacon_id)


def set_state(row: dict, state: str) -> dict:
    if state not in STATES:
        raise BeaconError(f"state must be one of {', '.join(STATES)}")
    conn = db.connect()
    conn.execute("UPDATE custody_beacons SET state=? WHERE id=?",
                 (state, row["id"]))
    conn.commit()
    transfers._receipt(row["id"], f"state: {state}", None)
    return _out(_row(row["id"]))


def retire(row: dict) -> dict:
    """Peel the code off. It stops resolving; the record it pointed at is
    untouched, and the chain keeps everything it already recorded."""
    conn = db.connect()
    conn.execute("UPDATE custody_beacons SET active=0 WHERE id=?", (row["id"],))
    conn.commit()
    transfers._receipt(row["id"], "beacon retired", None)
    audit.record("beacon.retire", tenant_id=row["tenant_id"], ref=row["id"])
    return {"id": row["id"], "active": False}


def seal_card(beacon_id: str) -> dict | None:
    """Resolve a scanned code, counting the scan. The public surface.

    Returns ``None`` for a code that never existed or has been retired — the
    caller turns both into the same "nothing here" answer, because a stranger
    holding a phone at a dead sticker should not be able to tell which.
    """
    row = _row(beacon_id)
    if row is None or not row["active"]:
        return None

    conn = db.connect()
    conn.execute("UPDATE custody_beacons SET scans = scans + 1 WHERE id=?",
                 (beacon_id,))
    conn.execute("INSERT INTO beacon_scans (id, beacon_id, at) VALUES (?,?,?)",
                 (db.new_id("bscn"), beacon_id, db.utcnow()))
    conn.commit()

    programs = json.loads(row["programs"])
    card = {
        "reference": row["id"],
        "kind": row["ref_kind"],
        "state": row["state"],
        "under_custody": True,
        "programs": programs,
        "controls": compliance.controls_for(programs),
        "badge": BADGE,
        "contents": None,
        "note": ("This code identifies a sealed carrier. It cannot open it, "
                 "and neither can whoever is holding it."),
    }
    if row["ref_kind"] == "facility":
        card["gate"] = True
        card["badge"] = GATE_BADGE
        card["ring_url"] = f"/s/{row['id']}/ring"
        card["note"] = ("This is a controlled facility. Ring, and someone — "
                        "or something answering for them — will respond.")
    else:
        card["found_url"] = f"/s/{row['id']}/found"

    if row["disclose"] == "contact":
        holder = db.connect().execute(
            "SELECT name FROM tenants WHERE id=?", (row["tenant_id"],)).fetchone()
        card["held_by"] = holder["name"] if holder else None
        card["label"] = row["label"]
    else:
        # Blind: the finder gets a route back through PDI and never learns
        # whose it is. The label is the owner's own filing note and can name
        # the site, so it stays behind the wall with everything else.
        card["held_by"] = None
        card["return_via"] = "report it here and the holder will be told"
    return card


def _recent_found(beacon_id: str) -> int:
    since = (datetime.now(timezone.utc)
             - timedelta(minutes=FOUND_WINDOW_MINUTES)).isoformat()
    row = db.connect().execute(
        "SELECT COUNT(*) AS n FROM transfer_receipts"
        " WHERE transfer_id=? AND event='found' AND at >= ?",
        (beacon_id, since)).fetchone()
    return row["n"]


def found(beacon_id: str, where: str | None = None,
          contact: str | None = None) -> dict | None:
    """The finder's receipt — the one thing a stranger can do with a carrier.

    Not a message. It records that this object was in someone's hands at a
    stated time and that they reported it, which is what later answers *where
    was this between Wednesday and the following month*. It is worth something
    in an audit even if nobody ever replies to it.
    """
    row = _row(beacon_id)
    if row is None or not row["active"]:
        return None
    if row["ref_kind"] == "facility":
        raise BeaconError("a gate is not a carrier — ring it instead")

    if _recent_found(beacon_id) >= FOUND_CAP:
        return {"beacon": beacon_id, "recorded": False,
                "note": ("this carrier was already reported in the last hour; "
                         "the holder has been told and nothing is lost by "
                         "your not reporting it again")}

    detail = " · ".join(p for p in (where, contact) if p) or None
    transfers._receipt(beacon_id, "found", detail)
    audit.record("beacon.found", tenant_id=row["tenant_id"], ref=beacon_id)
    return {
        "beacon": beacon_id,
        "recorded": True,
        "note": ("recorded in this carrier's chain of custody, timestamped and "
                 "hash-chained; the holder can see it and you cannot change it"),
    }


def custody(row: dict) -> dict:
    """The compliance record for a beacon: what it points at, what governs it,
    and every event on it — with the audit chain's integrity attested."""
    receipts = db.connect().execute(
        "SELECT event, actor, at FROM transfer_receipts WHERE transfer_id=?"
        " ORDER BY at, rowid", (row["id"],)).fetchall()
    scans = db.connect().execute(
        "SELECT COUNT(*) AS n FROM beacon_scans WHERE beacon_id=?",
        (row["id"],)).fetchone()["n"]
    programs = json.loads(row["programs"])
    return {
        "beacon": row["id"],
        "ref_kind": row["ref_kind"],
        "ref_id": row["ref_id"],
        "label": row["label"],
        "programs": programs,
        "controls": compliance.controls_for(programs),
        "state": row["state"],
        "active": bool(row["active"]),
        "scans": scans,
        "chain_of_custody": [dict(r) for r in receipts],
        "audit_chain_intact": audit.verify()["intact"],
    }


# --- the gate -------------------------------------------------------------

def ring(row: dict, kind: str, note: str | None = None) -> dict:
    """Somebody is at the door. Opens a ring for the agent (or a human) to take."""
    if row["ref_kind"] != "facility":
        raise BeaconError("this code is on a carrier, not a gate")
    if kind not in RING_KINDS:
        raise BeaconError(f"kind must be one of {', '.join(RING_KINDS)}")

    rid = db.new_id("ring")
    conn = db.connect()
    conn.execute(
        "INSERT INTO beacon_rings (id, beacon_id, tenant_id, kind, note,"
        " state, created_at) VALUES (?,?,?,?,?, 'open', ?)",
        (rid, row["id"], row["tenant_id"], kind, note, db.utcnow()))
    conn.commit()
    audit.record("beacon.ring", tenant_id=row["tenant_id"], ref=rid)
    return ring_out(rid)


def ring_row(ring_id: str) -> dict | None:
    row = db.connect().execute(
        "SELECT * FROM beacon_rings WHERE id=?", (ring_id,)).fetchone()
    return dict(row) if row else None


def ring_out(ring_id: str) -> dict:
    row = ring_row(ring_id)
    return {
        "id": row["id"],
        "beacon_id": row["beacon_id"],
        "kind": row["kind"],
        "note": row["note"],
        "state": row["state"],
        "outcome": row["outcome"],
        "handed_to": row["handed_to"],
        "spoken_by": row["spoken_by"],
        "created_at": row["created_at"],
        "closed_at": row["closed_at"],
    }


def rings_for(tenant_id: str, open_only: bool = False) -> list[dict]:
    sql = "SELECT id FROM beacon_rings WHERE tenant_id=?"
    if open_only:
        sql += " AND state='open'"
    sql += " ORDER BY created_at, rowid"
    return [ring_out(r["id"])
            for r in db.connect().execute(sql, (tenant_id,)).fetchall()]


def close_ring(row: dict, state: str, outcome: str | None = None,
               handed_to: str | None = None, spoken_by: str | None = None,
               vault_key: str | None = None,
               transcript_sha256: str | None = None) -> dict:
    conn = db.connect()
    conn.execute(
        "UPDATE beacon_rings SET state=?, outcome=?, handed_to=?, spoken_by=?,"
        " vault_key=?, transcript_sha256=?, closed_at=? WHERE id=?",
        (state, outcome, handed_to, spoken_by, vault_key, transcript_sha256,
         db.utcnow(), row["id"]))
    conn.commit()
    return ring_out(row["id"])


def expected_arrivals(tenant_id: str) -> int:
    """How many carriers this tenant is currently expecting to move.

    An outbound transfer still sealed is one waiting for a courier; an intake
    still open is one waiting to arrive. The agent is allowed to know the
    *count* — it is what makes "we are expecting a collection today" a checkable
    claim rather than a guess — and is never handed the records themselves.
    """
    conn = db.connect()
    out = conn.execute(
        "SELECT COUNT(*) AS n FROM transfers WHERE tenant_id=? AND status='sealed'",
        (tenant_id,)).fetchone()["n"]
    inn = conn.execute(
        "SELECT COUNT(*) AS n FROM intakes WHERE tenant_id=? AND status='open'",
        (tenant_id,)).fetchone()["n"]
    return out + inn
