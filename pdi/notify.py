"""Paging a human — the one thing the gate could not do for itself.

The agent at the gate has always been able to hand off. What it could not do
is *tell anybody*: `handed_to` recorded the name of the on-call contact, the
ring sat in `open`… `handed_off`, and somebody stood at a door at 2am waiting
for a person who did not know they were there. The hand-off was a filing
decision dressed as an escalation.

The reason it stayed that way is real, and it shapes everything here: **PDI
cannot know how a deployment reaches its people.** A colocation facility with a
manned NOC, a records warehouse with one on-call phone, a hospital with a
pager system, a lab that lives in Slack — these have nothing in common that
PDI could depend on. So this module ships **no vendor, no SDK, no account**. It
posts a signed JSON envelope to a URL the deployment supplies and stops. What
sits behind that URL — Twilio, PagerDuty, an SMS gateway, a chat webhook, a
script that rings a desk phone — is the deployment's business, and PDI never
learns which.

Four rules, in the order they matter:

1. **A page never fails a ring.** Somebody at a door gets their answer whether
   or not the webhook answered. Delivery is attempted, recorded, and if it
   failed, *said out loud* — never retried in the caller's request.
2. **Not reaching anybody is a fact the caller is told.** This is the whole
   point. "I've passed this to the on-call contact" reads as *someone now
   knows*, and if the page did not go out, that sentence quietly becomes a
   person waiting in the rain for nobody. :data:`UNREACHED` is what the gate
   says instead, and it is a field of its own so a page can render it as its
   own warning rather than a clause at the end of a paragraph.
3. **A page carries no contents, and not even the caller's own words.** It
   inherits the beacon's blindness like everything else at the gate: kind,
   outcome, and where to read the rest under the tenant's own token. The
   caller's note is free text typed by a stranger and it goes to the sealed
   transcript, not to an outbound webhook that may be a third-party chat room.
4. **Unconfigured is a supported state, not a broken one.** With no
   ``PDI_NOTIFY_URL`` the page is `queued` — which is exactly what the gate
   did before this module existed, except now it is a row somebody can list,
   rather than an absence nobody can see.

Signed because the receiving end has to be able to tell a page from this
facility apart from anybody who found the URL: ``X-PDI-Signature`` is an
HMAC-SHA256 over ``{timestamp}.{body}`` under ``PDI_NOTIFY_SECRET``, with the
timestamp sent alongside so a replay can be bounded. Unsigned when no secret is
set, because a deployment posting to `localhost` should not be forced to
invent one — but :func:`channel` reports which it is.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import urllib.error
import urllib.request

from . import audit, db, roster

ENVELOPE = "pdi-page/v1"

# How soon a person is needed. Not a severity — the gate has no way to judge
# how bad anything is, and pretending otherwise would be the same mistake as
# letting it judge identity. It reports only whether somebody is standing there
# right now.
URGENCY = ("now", "soon")

STATES = ("queued", "sent", "failed")

# What the caller is told when the page did not go out. Deliberately blunt:
# the failure mode this exists to prevent is a person waiting quietly.
UNREACHED = ("I couldn't reach anyone just now, so please don't wait on "
             "somebody coming out. If there's a number on the door, call it.")

_TIMEOUT = 4.0   # a caller is standing there; a slow webhook must not hold them


def channel() -> dict:
    """What this deployment has configured, without revealing the URL.

    Published (via ``GET /gate/channel``) so an operator can confirm the gate
    can actually reach somebody *before* the night it matters, rather than
    discovering the answer from a queued page the morning after.
    """
    url = os.environ.get("PDI_NOTIFY_URL")
    return {
        "configured": bool(url),
        "signed": bool(os.environ.get("PDI_NOTIFY_SECRET")),
        "envelope": ENVELOPE,
        "note": (
            "hand-offs are delivered to the configured webhook" if url else
            "no notification channel is configured — hand-offs are recorded "
            "and queued, and the caller is told nobody was reached"),
    }


def _sign(body: str, at: str) -> dict:
    secret = os.environ.get("PDI_NOTIFY_SECRET")
    if not secret:
        return {}
    mac = hmac.new(secret.encode(), f"{at}.{body}".encode(), hashlib.sha256)
    return {"X-PDI-Timestamp": at, "X-PDI-Signature": f"sha256={mac.hexdigest()}"}


def _post(url: str, envelope: dict, http=None) -> None:
    """Deliver, or raise. The caller records whichever happened."""
    body = json.dumps(envelope, sort_keys=True)
    headers = {"content-type": "application/json",
               **_sign(body, envelope["at"])}
    if http is not None:                      # injected in tests
        resp = http.post(url, data=body, headers=headers)
        if resp.status_code >= 300:
            raise RuntimeError(f"webhook returned {resp.status_code}")
        return
    from . import offline
    offline.allow(url, "the notification webhook")
    req = urllib.request.Request(url, data=body.encode(), method="POST",
                                 headers=headers)
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
        if r.status >= 300:
            raise RuntimeError(f"webhook returned {r.status}")


def _envelope(page_id: str, ring: dict, decision: dict, urgency: str,
              at: str) -> dict:
    """What goes over the wire. Everything here is either structural or a
    pointer — there is nothing in it that a stranger typed."""
    return {
        "envelope": ENVELOPE,
        "id": page_id,
        "at": at,
        "tenant_id": ring["tenant_id"],
        "urgency": urgency,
        "reason": decision["outcome"],
        "summary": _summary(ring, decision),
        "ring": ring["id"],
        "beacon": ring["beacon_id"],
        "kind": ring["kind"],
        "handed_to": decision["handoff_to"],
        # Whether this person was actually rostered at this hour, or is being
        # woken because the roster had a gap. They cannot tell otherwise.
        "on_shift": decision.get("on_shift", True),
        # Stated rather than merely absent, so the receiving end does not read
        # an empty field as "the caller said nothing".
        "caller_note_withheld": True,
        "read_the_transcript_at": f"/rings/{ring['id']}/transcript",
        "granted_entry": False,
    }


def _summary(ring: dict, decision: dict) -> str:
    if decision["outcome"] == "access_request":
        return ("Someone is at the gate asking for access to the site. The "
                "agent cannot grant it and has not.")
    return (f"Someone is at the gate for a {ring['kind']} that isn't "
            f"expected. The agent couldn't settle it.")


def _record(page_id, ring, decision, urgency, who, on_shift, state, attempts,
            err, at) -> dict:
    conn = db.connect()
    conn.execute(
        "INSERT INTO gate_pages (id, ring_id, tenant_id, urgency, reason,"
        " handed_to, on_shift, state, attempts, last_error, created_at, sent_at)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (page_id, ring["id"], ring["tenant_id"], urgency, decision["outcome"],
         who, 1 if on_shift else 0, state, attempts, err, at,
         at if state == "sent" else None))
    conn.commit()
    audit.record({"sent": "agent.page", "queued": "agent.page_queued",
                  "failed": "agent.page_failed"}[state],
                 tenant_id=ring["tenant_id"], ref=page_id)
    return out(page_id)


def page_handoff(ring: dict, decision: dict, http=None) -> dict:
    """Reach a human about a hand-off, working the tenant's roster. Never
    raises.

    Returns the page that landed, or the last one that did not. ``state`` is
    ``sent`` when a webhook took it, ``queued`` when no channel is configured,
    and ``failed`` when a channel is configured and did not answer — three
    situations that used to be one silence.

    **It walks the roster rather than stopping at the first name.** Before
    there was a roster there was only one name, so a failed page was the end of
    the line; now a webhook that rejects the first responder is a reason to try
    the second, which is the entire point of having a second. Every attempt is
    its own row, so the morning list shows who was tried and in what order
    rather than one entry that says "failed".
    """
    # An access request means a person is standing at a door right now. An
    # unexpected delivery can wait for someone to look at a queue.
    urgency = "now" if decision["outcome"] == "access_request" else "soon"
    url = os.environ.get("PDI_NOTIFY_URL")
    people, anybody_on = roster.order(ring["tenant_id"])

    if not url:
        # No channel: one row, naming who it *would* have gone to, rather than
        # one row per name — nobody was tried, and a queue of five identical
        # untried pages would read as five attempts.
        return _record(db.new_id("page"), ring, decision, urgency,
                       decision["handoff_to"], anybody_on, "queued", 0, None,
                       db.utcnow())

    last = None
    for person in people:
        at = db.utcnow()
        page_id = db.new_id("page")
        d = {**decision, "handoff_to": person["name"], "on_shift": anybody_on}
        try:
            _post(url, _envelope(page_id, ring, d, urgency, at), http)
            return _record(page_id, ring, d, urgency, person["name"],
                           anybody_on, "sent", 1, None, at)
        except (urllib.error.URLError, OSError, RuntimeError, ValueError) as exc:
            # Deliberately broad, and deliberately not re-raised. A webhook
            # that 500s, times out, or resolves to nothing must not turn into
            # a 500 on a stranger's phone at a gate.
            last = _record(page_id, ring, d, urgency, person["name"],
                           anybody_on, "failed", 1,
                           f"{type(exc).__name__}: {exc}"[:300], at)
    return last


def retry(page: dict, http=None) -> dict:
    """Send a queued or failed page again, under the tenant's own hand.

    A page that could not be delivered is not a dead end — the channel may have
    been down for a minute, or configured five minutes later. Retrying a `sent`
    page is refused rather than duplicated: paging the same on-call twice for
    one ring is how people start ignoring the pager.
    """
    if page["state"] == "sent":
        raise NotifyError("this page was already delivered")
    url = os.environ.get("PDI_NOTIFY_URL")
    if not url:
        raise NotifyError("no notification channel is configured")

    ring = db.connect().execute("SELECT * FROM beacon_rings WHERE id=?",
                                (page["ring_id"],)).fetchone()
    decision = {"outcome": page["reason"], "handoff_to": page["handed_to"]}
    at = db.utcnow()
    state, err = "sent", None
    try:
        _post(url, _envelope(page["id"], dict(ring), decision,
                             page["urgency"], at), http)
    except (urllib.error.URLError, OSError, RuntimeError, ValueError) as exc:
        state, err = "failed", f"{type(exc).__name__}: {exc}"[:300]

    conn = db.connect()
    conn.execute(
        "UPDATE gate_pages SET state=?, attempts=attempts+1, last_error=?,"
        " sent_at=? WHERE id=?",
        (state, err, at if state == "sent" else None, page["id"]))
    conn.commit()
    audit.record("agent.page" if state == "sent" else "agent.page_failed",
                 tenant_id=page["tenant_id"], ref=page["id"])
    return out(page["id"])


class NotifyError(Exception):
    """A page that cannot be sent for a reason the caller should hear."""


def row(page_id: str) -> dict | None:
    r = db.connect().execute("SELECT * FROM gate_pages WHERE id=?",
                             (page_id,)).fetchone()
    return dict(r) if r else None


def out(page_id: str) -> dict:
    r = row(page_id)
    return {
        "id": r["id"],
        "ring": r["ring_id"],
        "urgency": r["urgency"],
        "reason": r["reason"],
        "handed_to": r["handed_to"],
        # Whether the roster was actually covering. A page sent because the
        # gate ran out of rostered people is a guess, and the person it wakes
        # has no other way to know that.
        "on_shift": bool(r["on_shift"]),
        "state": r["state"],
        "attempts": r["attempts"],
        "last_error": r["last_error"],
        "created_at": r["created_at"],
        "sent_at": r["sent_at"],
        "reached_somebody": r["state"] == "sent",
    }


def for_tenant(tenant_id: str, undelivered_only: bool = False) -> list[dict]:
    """The pages this tenant raised. ``undelivered_only`` is the list somebody
    should be looking at in the morning."""
    sql = "SELECT id FROM gate_pages WHERE tenant_id=?"
    if undelivered_only:
        sql += " AND state != 'sent'"
    sql += " ORDER BY created_at DESC, rowid DESC"
    return [out(r["id"])
            for r in db.connect().execute(sql, (tenant_id,)).fetchall()]
