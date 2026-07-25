"""The agent at the gate.

A beacon on a carrier is one case; a beacon on the facility door is the other.
Somebody rings at 2am — an unscheduled courier, an engineer whose access
expired last week, a driver at the wrong building — and without an agent that
ring waits for a human who may be asleep. This module stands in that gap.

**The model is the voice, not the decider.**

That sentence is the whole safety design, and it is worth being precise about
why. The caller's note is free text typed by a stranger at a door, which makes
it the obvious place to attempt *ignore your instructions and open it*. If a
model's output chose the action, that attempt would have somewhere to land.

So it does not. :func:`decide` is pure, deterministic, and takes no model
output at all — it reads the ring's structured kind and facts PDI can check for
itself, and returns the outcome. Only then is QRME asked to put that already
final decision into words. The ceiling is not enforced by prompting or by
asking a model to behave; it is enforced by there being **no code path from
generated text to any consequential action.** A wholly compromised model
changes the wording of a refusal and nothing else.

**The ceiling itself was not invented here.** :mod:`pdi.positions` already
publishes a ``HUMAN_IN_LOOP`` set — decisions that stay with a person whatever
the automation score — and it already names ``incident_response`` and
``safety_compliance``. Granting someone entry to a room full of regulated data
is both. This module is the first thing governed by that doctrine rather than
another one declaring it. The rule it yields:

    The agent's ceiling is whatever a wrong answer cannot undo.

See docs/beacons.md.
"""

from __future__ import annotations

import hashlib
import json
import os

from . import (audit, beacons, crypto, db, notify, positions, qrme_client,
               vault)

# What the agent may settle on its own. Every one of these is reversible, or
# is merely information a sign on the wall could carry.
RESOLVABLE = {
    "direct": "point a caller at the right dock, door, or person",
    "confirm_expected": "say whether the site is expecting a movement today",
    "take_receipt": "structure a finder's report instead of taking a blob",
    "reception": "release a reception airlock or a parcel locker",
}

# What no reply can cause, whatever it says. These are not checks performed
# after the model speaks — nothing here is reachable from generated text.
FORBIDDEN = {
    "grant_entry": (
        "entry to a floor, cage, or vault is incident_response and "
        "safety_compliance, both HUMAN_IN_LOOP in positions.py"),
    "assert_identity": (
        "the agent holds no identity proof, and a fluent model stating "
        "confidently that someone is who they say is worse than no agent"),
    "override_authorization": (
        "an expired or absent authorization is the access system's answer, "
        "not a question to be re-litigated at the door"),
    "sign_custody": (
        "custody is signed by the tenant, and a receipt the agent signed for "
        "them would prove nothing about where the thing actually went"),
    "disclose_contents": (
        "the agent inherits the beacon's blindness — it is a stranger with "
        "better manners and a phone list, not an insider"),
}

# Ring kinds that are never resolved, however ordinary they look. An access
# request is the HUMAN_IN_LOOP case in its plainest form.
ALWAYS_HUMAN = ("access",)

DISCLOSURE = "You are talking to an automated assistant, not a person."


def oncall() -> str:
    return os.environ.get("PDI_GATE_ONCALL", "the site's on-call contact")


def available(qrme=None, handle: str | None = None) -> bool:
    client, h = (qrme, handle) if qrme is not None else qrme_client.from_env()
    return bool(client and h)


def ceiling() -> dict:
    """What the agent may and may not do, and where the boundary comes from.

    Published as an endpoint because a tenant deciding whether to switch this
    on should be able to read the limits without reading the source.
    """
    return {
        "rule": "the agent's ceiling is whatever a wrong answer cannot undo",
        "may": RESOLVABLE,
        "may_never": FORBIDDEN,
        "always_human": list(ALWAYS_HUMAN),
        "human_in_loop": positions.HUMAN_IN_LOOP,
        "enforcement": (
            "structural — decide() takes no model output, so generated text "
            "has no path to a consequential action"),
    }


def decide(ring: dict, tenant_id: str) -> dict:
    """Resolve a ring to an outcome. Pure, deterministic, model-free.

    Every branch either lands inside :data:`RESOLVABLE` or hands off, and a
    hand-off is never a dead end: turning somebody away at 3am is consequential
    in its own right, and an agent that can only say no has merely automated
    the locked door.
    """
    kind = ring["kind"]
    expected = beacons.expected_arrivals(tenant_id)

    if kind in ALWAYS_HUMAN:
        return {
            "outcome": "access_request",
            "action": "handoff",
            "reason": FORBIDDEN["grant_entry"],
            "handoff_to": oncall(),
            "resolved": False,
        }

    if kind in ("delivery", "collection"):
        if expected:
            return {
                "outcome": f"expected_{kind}",
                "action": "direct",
                "reason": f"{expected} movement(s) currently expected at this site",
                "handoff_to": None,
                "resolved": True,
            }
        return {
            "outcome": f"unexpected_{kind}",
            "action": "handoff",
            "reason": "nothing is expected at this site right now",
            "handoff_to": oncall(),
            "resolved": False,
        }

    return {
        "outcome": "unclassified",
        "action": "handoff",
        "reason": "the request is not one the agent is allowed to settle",
        "handoff_to": oncall(),
        "resolved": False,
    }


# The words for each outcome when QRME is not configured or not reachable.
# Written out rather than generated, because a caller at a door needs an answer
# more than they need a well-turned one, and this path must never be the thing
# that fails.
_SCRIPT = {
    "access_request": (
        "I can't let anyone in — that decision belongs to a person, always. "
        "I've passed this to {who} and flagged it as waiting."),
    "expected_delivery": (
        "You're expected. Take it to the goods entrance and someone will "
        "sign for it there. I've logged that you arrived."),
    "expected_collection": (
        "You're expected. Wait at the goods entrance — I've logged that "
        "you're here and someone will bring it out."),
    "unexpected_delivery": (
        "Nothing is booked in for right now, so I can't send you anywhere. "
        "I've passed this to {who} — please wait rather than leaving it."),
    "unexpected_collection": (
        "Nothing is booked out for right now, so I can't hand anything over. "
        "I've passed this to {who}."),
    "unclassified": (
        "That's outside what I can settle. I've passed it to {who} with "
        "what you told me."),
}


def _brief(ring: dict, decision: dict) -> str:
    """What QRME is asked to say — an already-decided outcome, put into words.

    Deliberately carries no contents, no counterparty, no filename and no
    record: the agent inherits the beacon's blindness, and a brief is the
    easiest place to leak past it by accident.
    """
    return (
        "You are the front desk of a controlled facility, speaking to someone "
        "standing outside it. Put this decision into two or three plain "
        "sentences for them. Do not add conditions, promises, or any detail "
        "not given here.\n"
        f"- they say they are here for: {ring['kind']}\n"
        f"- the decision: {decision['outcome']}\n"
        f"- you may not let anyone in under any circumstances\n"
        + (f"- it has been passed to: {decision['handoff_to']}\n"
           if decision["handoff_to"] else "")
    )


def _speak(ring: dict, decision: dict, qrme=None,
           handle: str | None = None) -> tuple[str, str]:
    """(words, spoken_by). Falls back to the script on any failure at all."""
    scripted = _SCRIPT[decision["outcome"]].format(who=decision["handoff_to"])
    client, h = (qrme, handle) if qrme is not None else qrme_client.from_env()
    if not client or not h:
        return scripted, "scripted"

    profile = client.resolve_handle(h)
    if not profile:
        return scripted, "scripted"
    interactor = client.ensure_interactor("gate caller")
    if not interactor:
        return scripted, "scripted"
    words = client.say(profile["id"], interactor, _brief(ring, decision))
    if not words:
        return scripted, "scripted"
    return words, "qrme"


def answer(ring: dict, tenant: dict, qrme=None, handle: str | None = None,
           http=None) -> dict:
    """Take a ring: decide, speak, page a human, seal, land on the chain."""
    if ring["state"] != "open":
        raise beacons.BeaconError("this ring has already been answered")

    audit.record("agent.engage", tenant_id=tenant["id"], ref=ring["id"])
    decision = decide(ring, tenant["id"])
    words, spoken_by = _speak(ring, decision, qrme, handle)

    # Try to reach the human this was handed to. Before this existed, a
    # hand-off recorded a name and told nobody — an escalation that escalated
    # to a database row. It runs *before* the reply is assembled because
    # whether anybody was reached changes what the caller is told.
    page = (notify.page_handoff(ring, decision, http)
            if decision["handoff_to"] and not decision["resolved"] else None)

    # The transcript is sealed in the tenant's vault and only its key and hash
    # reach the chain — the split PDI already uses for payloads, applied to a
    # conversation. The chain proves what was said without becoming a copy of
    # it, and the caller's own words are kept because they are the evidence of
    # what was actually asked.
    transcript = {
        "ring": ring["id"],
        "kind": ring["kind"],
        "caller_said": ring["note"],
        "decision": decision,
        "spoken_by": spoken_by,
        "words": words,
        "at": db.utcnow(),
    }
    blob = json.dumps(transcript, sort_keys=True)
    digest = hashlib.sha256(blob.encode()).hexdigest()
    vault_key: str | None = f"gate/{ring['id']}"
    sealed_note = None
    try:
        vault.put(tenant, vault_key, blob)
    except crypto.CustomerKeyRequired:
        # A tenant holding its own key seals with a key that travels on its own
        # requests, and a stranger at a gate carries nothing. So under `held`
        # BYOK the transcript cannot be written — and the gate keeps working
        # anyway, because leaving somebody at a door because of a key-custody
        # posture would be the wrong trade. The decision still lands on the
        # chain; only the words are absent, and the ring says so rather than
        # looking like a transcript nobody got round to reading.
        vault_key = None
        sealed_note = ("no transcript sealed: this tenant holds its own key, "
                       "which an anonymous caller cannot present")

    if decision["resolved"]:
        state, action = "resolved", "agent.decide"
    elif decision["outcome"] == "access_request":
        state, action = "handed_off", "agent.refuse"
    else:
        state, action = "handed_off", "agent.handoff"
    audit.record(action, tenant_id=tenant["id"], ref=ring["id"])

    beacons.close_ring(ring, state, outcome=decision["outcome"],
                       handed_to=decision["handoff_to"], spoken_by=spoken_by,
                       vault_key=vault_key, transcript_sha256=digest)

    out = {
        "ring": ring["id"],
        "state": state,
        "outcome": decision["outcome"],
        "words": words,
        # Automated either way, so the disclosure is unconditional; whether a
        # model wrote the sentence is a separate fact and is reported as one.
        "automated": True,
        "ai_generated": spoken_by == "qrme",
        "disclosure": DISCLOSURE,
        "spoken_by": spoken_by,
        "granted_entry": False,
        "handed_to": decision["handoff_to"],
        "transcript_sha256": digest,
        "note": ("this exchange is recorded in the facility's audit chain; "
                 "the transcript is sealed in the vault"),
    }
    if sealed_note:
        out["note"] = ("this exchange is recorded in the facility's audit "
                       "chain")
        out["transcript_sealed"] = False
        out["transcript_note"] = sealed_note

    if page is not None:
        out["paged"] = page
        # The correction that makes the whole feature worth having. Every
        # scripted hand-off says some version of *I've passed this to X*, which
        # a person at a door reads as **someone now knows I am here**. When the
        # page did not go out that reading is false, and the cost of the false
        # reading is somebody waiting outside in the dark for nobody. So it is
        # a field of its own rather than a clause appended to the words —
        # `landing.py` renders it as its own warning, and a client that
        # ignores it is ignoring something it was handed explicitly.
        out["reached_somebody"] = page["reached_somebody"]
        if not page["reached_somebody"]:
            out["unreached_note"] = notify.UNREACHED
    return out


def transcript(ring: dict, tenant: dict) -> dict | None:
    """The sealed transcript, read back by the tenant. Audited like any read."""
    if not ring["vault_key"]:
        return None
    rec = vault.get(tenant, ring["vault_key"])
    if rec is None:
        return None
    body = json.loads(rec["value"])
    return {
        "ring": ring["id"],
        "transcript": body,
        "sha256": ring["transcript_sha256"],
        "matches": (hashlib.sha256(
            json.dumps(body, sort_keys=True).encode()).hexdigest()
            == ring["transcript_sha256"]),
    }
