"""The console assistant: answers about operating PDI, and nothing else.

The counterpart to :mod:`pdi.tutorial` — that is the guided walkthrough for
somebody who does not yet know what to ask; this answers the question of
somebody who does. Same guide, same posture, and the posture is the whole
design.

**It cannot read the vault.** There is no import of :mod:`pdi.vault` here and
a test asserts its absence, for the reason `tutorial.py` sets out at length:
under BYOK the customer's key travels per request and is never stored, so an
assistant that offered to look at the data would be promising something the
product is built to prevent. It answers about the *console*.

**It never acts.** No token issued, no key rotated, no tenant created, no
retention window set. It writes nothing at all — not even progress, which
lives in the tutorial. A model can change the words on this surface and
nothing else, which is `pdi.gate`'s rule arriving in the least dangerous
place it applies: *the model is the voice, not the decider.*

**Written prose first.** :data:`TOPICS` answers without a provider, because a
self-hosted vault with no API key configured is the *typical* PDI deployment
rather than a degraded one — the customers most likely to run their own vault
are the least likely to let it call out to a model.

**It refuses to be a colleague.** :data:`REFUSALS` catches *are you real*,
*decide this for me*, *just do it* — the last one being the question an
operator under time pressure genuinely asks, and the one this surface must
never answer with anything but where the button is.
"""

from __future__ import annotations

DISCLOSURE = ("Automated help for operating PDI. Not an agent and not a "
              "person: it explains the console, it cannot read the vault, and "
              "it changes nothing.")

# Checked before anything else. An operator console is exactly where a
# confident voice gets believed about something consequential.
REFUSALS: dict[str, tuple[tuple[str, ...], str]] = {
    "identity": (
        ("are you real", "are you human", "are you an agent", "who are you",
         "are you ai"),
        "I'm the console help — automated, no persona, no memory. I explain "
        "the console; I don't operate it and I can't read anything in the "
        "vault.",
    ),
    "do_it_for_me": (
        ("do it for me", "just do it", "go ahead and", "rotate the key",
         "delete it for me", "issue a token", "create the tenant"),
        "I can't perform operator actions — no tokens, no keys, no retention, "
        "no deletions. I'll tell you which screen does it and what it will "
        "change before you confirm.",
    ),
    "read_the_data": (
        ("what does the record say", "show me the record", "read the record",
         "what is in the vault", "decrypt", "what did they store"),
        "I can't read records, and under a customer-managed key nobody here "
        "can — the key travels with the request and is never stored. The "
        "console shows that a record exists and when it moved, never what it "
        "says.",
    ),
    "decide": (
        ("should i", "what would you do", "decide", "is it safe to",
         "do you think"),
        "That's an operator decision and it stays with you. I can tell you "
        "what a screen does and what it cannot undo — the gate agent's rule "
        "applies here too: the ceiling is whatever a wrong answer cannot "
        "undo.",
    ),
}

# Written answers to the questions an operator actually arrives with.
TOPICS: dict[str, tuple[tuple[str, ...], str]] = {
    "what_is_pdi": (
        ("what is pdi", "what is this", "what does this do", "explain pdi"),
        "PDI is an encrypted vault with a tamper-evident audit log and a "
        "tenant registry. Other systems — QRME, JIM-mini — store sensitive "
        "data here instead of in their own database, reached only over this "
        "API.",
    ),
    "byok": (
        ("byok", "customer key", "bring your own key", "own key", "key"),
        "Bring your own key: the customer key travels per request in the "
        "`X-Tenant-Key` header and is never stored. A copy of this database "
        "is not a copy of the data, and the operator cannot read a record "
        "sealed under a key they do not hold.",
    ),
    "tenants": (
        ("tenant", "tenants", "token", "bearer", "namespace"),
        "Each integrating system is a tenant with its own bearer token and "
        "namespace. One tenant cannot read another's records — the query is "
        "scoped before it runs, not filtered after.",
    ),
    "audit": (
        ("audit", "audit log", "chain", "verify", "tamper", "hash chain"),
        "Every access appends a hash-chained entry. Verifying the chain shows "
        "whether anything was altered or removed, including by whoever runs "
        "the server.",
    ),
    "retention": (
        ("retention", "delete", "deletion", "purge", "snapshot", "restore"),
        "Retention windows remove data on a schedule, and snapshots let you "
        "restore. A deletion leaves the audit trail intact — that is the only "
        "kind worth having.",
    ),
    "isolation": (
        ("isolation", "separate", "leak", "cross tenant", "other tenant"),
        "Tenant isolation is structural: a tenant's token resolves to its "
        "namespace and every query is scoped to it before it runs. There is "
        "no endpoint that takes a tenant id from a caller and trusts it.",
    ),
    "gate": (
        ("gate", "door", "ring", "beacon", "courier", "entry"),
        "The gate agent answers a ring at a facility door. It settles only "
        "what a wrong answer could not break and hands a person everything "
        "else — and the decision is made in code before a model is asked to "
        "put it into words.",
    ),
    "connect": (
        ("connect", "connector", "integrate", "qrme", "jim", "tandem"),
        "QRME seals profile source material here and JIM-mini vaults its "
        "medical payloads, each as its own tenant with its own token. See the "
        "tandem page for one payload followed end to end.",
    ),
    "hosting": (
        ("hosting", "colocation", "colo", "rack", "lease", "facility",
         "where does it run", "self host", "self-hosted", "own device"),
        "A vault can live in our facility (free for JIM-mini and QRME data), "
        "in leased space we own, in a facility you own and host, or on your "
        "own phone or computer. The encryption, audit chain and BYOK are the "
        "same on all four — what differs is uptime and who does the backups.",
    ),
    "compliance": (
        ("hipaa", "baa", "compliance", "transfer", "regulated"),
        "A tenant in a HIPAA programme needs a BAA on file before transfers "
        "or intakes are accepted. It is a precondition rather than a warning: "
        "the request is refused without it.",
    ),
}

# Asking for the walkthrough, in the words operators use.
_WALKTHROUGH: dict[str, tuple[tuple[str, ...], str]] = {
    "walk_me_through": (
        ("show me around", "walk me through", "give me a tour", "tutorial",
         "guide me", "how do i use this", "where do i start", "getting started",
         "walkthrough", "show me how", "set it up", "first time"),
        "",
    ),
}

# "Where is the thing that does X." Keyed by tutorial lesson, so directions
# cannot name a screen the walkthrough does not cover — and a test binds every
# lesson to an entry here.
DIRECTIONS: dict[str, tuple[str, ...]] = {
    "what_pdi_is": ("overview", "the dashboard", "home", "live tiles"),
    "sign_in": ("sign in", "log in", "sign out", "logout"),
    "vault": ("store a record", "the vault", "put data in", "a record"),
    "encryption": ("encryption", "keys", "rotate", "aes", "cipher"),
    "tenants": ("create a tenant", "new tenant", "issue a token",
                "access control", "permissions"),
    "audit": ("audit log", "verify the chain", "the chain", "tamper check"),
    "retention": ("retention", "snapshots", "restore", "purge", "schedule"),
    "connect": ("connectors", "connected systems", "tandem", "integrations"),
    "apps": ("apple intelligence", "gemini", "copilot", "connected apps"),
    "intake": ("intake", "upload", "files", "photos", "a form"),
    "robots": ("robot", "robots", "custody", "custody beacons"),
    "gate": ("the gate", "gate agent", "the door", "a ring"),
    "health": ("deployment", "health", "status", "is it up"),
    "hosting": ("hosting", "where it lives", "colocation", "colo", "rack",
                "lease", "on my own device", "self host", "self-hosted",
                "where does the data live", "facility"),
    "dock": ("the pane", "the corner", "the lights panel", "the overlay",
             "the dock", "little box", "close the panel"),
    "all_set": ("all set", "am i done", "finished setup", "the guide"),
    # The words somebody uses when something has just broken, and the ones
    # they use when they have noticed the reporting and want it stopped.
    "problems": ("what went wrong", "error", "errors", "it failed",
                 "something broke", "bug", "report a bug", "crash",
                 "stop sending", "stop reporting", "opt out", "diagnostics"),
}


def _match(question: str, table) -> str | None:
    """Best-matching answer, on whole words.

    Not a substring test, for the reason QRME's help box learned the hard way:
    short keys make substring matching actively wrong rather than imprecise —
    "key" is inside "monkey" and "keyboard".
    """
    import re

    q = (question or "").lower().strip()
    best, score = None, 0
    for keys, answer in table.values():
        hits = sum(1 for k in keys
                   if re.search(r"(?<!\w)" + re.escape(k) + r"(?!\w)", q))
        if hits > score:
            best, score = answer, hits
    return best


def topics() -> list[str]:
    """What it can answer about, so the console can offer them rather than
    leaving an operator guessing at a blank box."""
    return sorted(TOPICS)


def where_is(question: str) -> dict | None:
    """Directions to the screen that does a thing, rather than a description.

    An operator asking where retention lives has not asked what retention is.
    """
    import re

    from . import tutorial

    q = (question or "").lower().strip()
    if not q:
        return None
    key, hits = None, 0
    for lesson_key, phrases in DIRECTIONS.items():
        n = sum(1 for p in phrases
                if re.search(r"(?<!\w)" + re.escape(p) + r"(?!\w)", q))
        if n > hits:
            key, hits = lesson_key, n
    if key is None:
        return None
    lesson = tutorial.LESSONS[tutorial._index(key)]
    return {"lesson": key, "title": lesson["title"],
            "screens": list(lesson["screens"]),
            "say": f"{lesson['title']}: {lesson['click']}",
            "walkthrough_step": f"/console/guide/steps/{key}"}


def ask(question: str, mode: str = "text") -> dict:
    """Answer a question about operating PDI. Writes nothing, reads no record.

    Order is refusals, then the walkthrough, then directions, then topics.
    Refusals run first because *just do it* and *what does the record say* are
    exactly the questions this surface exists to turn down.
    """
    from . import tutorial

    question = (question or "").strip()
    if not question:
        return {"answer": "Ask me anything about operating PDI.",
                "source": "written", "refused": False,
                "disclosure": DISCLOSURE, "topics": topics()}

    refusal = _match(question, REFUSALS)
    if refusal:
        return {"answer": refusal, "source": "written", "refused": True,
                "disclosure": DISCLOSURE, "topics": topics()}

    if _match(question, _WALKTHROUGH) is not None:
        first = tutorial.LESSONS[0]
        step = tutorial.say(first, mode)
        return {
            "answer": step.get("speak") or f"{step['title']}. {step['what']}",
            "source": "written", "refused": False,
            "disclosure": DISCLOSURE, "topics": topics(),
            "walkthrough": {"started": True, "step": step,
                            "steps": len(tutorial.LESSONS),
                            "next": "/console/guide/done"},
        }

    directions = where_is(question)
    if directions is not None:
        return {"answer": directions["say"], "source": "written",
                "refused": False, "disclosure": DISCLOSURE,
                "topics": topics(), "directions": directions}

    written = _match(question, TOPICS)
    return {
        "answer": written or (
            "I can only help with operating PDI — the vault, keys, tenants, "
            "the audit chain, retention and the connected systems. Ask about "
            "one of those, or say 'show me around' for the walkthrough."),
        "source": "written", "refused": False,
        "disclosure": DISCLOSURE, "topics": topics(),
    }
