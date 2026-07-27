"""The console guide: a walkthrough of PDI for the person operating it.

QRME's guide walks a consumer through a product full of synthetic people.
JIM's walks a patient through their own health record. This one walks an
**operator** through a vault holding somebody else's data — and that difference
is not decoration, it decides what the guide is allowed to be.

**It never opens the vault.** Not "it is careful with records", not "it only
reads what you are entitled to": there is no code path from this module to
:mod:`pdi.vault`, and a test asserts the import is absent. The reason is
sharper here than in the other two products. Under BYOK the customer's key
travels per request and is never stored, so the operator asking the question
frequently **cannot read the records themselves** — that is the product
working. An assistant offering to look at the data to be helpful would be
offering something the whole design exists to make impossible, and the first
person to notice would be the customer whose key was supposed to be the point.

So the guide explains the console. It never opens the vault, and it never acts
on a tenant: no token issued, no key rotated, no retention set, no record read.
Every lesson says *what to click*; none of them clicks it.

**It inherits the gate agent's doctrine rather than restating it.**
:mod:`pdi.gate` established the rule for this codebase — *the model is the
voice, not the decider*, and *the agent's ceiling is whatever a wrong answer
cannot undo*. A walkthrough sits comfortably under that ceiling because a wrong
sentence in a tutorial is undone by reading the next one. That is exactly why
it is allowed to exist without a human in the loop, and it is worth saying out
loud: this module is safe because of what it cannot reach, not because the
prose is good.

**No name and no face**, matching the other two guides. Less loaded here — PDI
has no synthetic profiles to be confused with — but an operator console is
precisely where a confident voice with a personality gets believed about
something consequential.

**Written prose, no model required.** A self-hosted vault with no API key
configured is the *typical* PDI deployment rather than a degraded one: the
customers most likely to run their own vault are the ones least likely to let
it call out to a model provider.
"""

from __future__ import annotations

from . import db

GUIDE = ("PDI's own console guide — not an agent, and not a person. It has no "
         "name and no face, it explains the console and nothing else, and it "
         "cannot read a single record in the vault. Under BYOK it could not "
         "read one even if it were asked to.")

# The doctrine this walkthrough sits under, quoted from `pdi.gate` rather than
# paraphrased, so the two cannot drift apart.
CEILING = "The agent's ceiling is whatever a wrong answer cannot undo."

# The walkthrough, in the order an operator actually meets the product: you
# have a vault before you have a tenant, a tenant before it has a token, and a
# token before anything is sealed with it.
LESSONS: tuple[dict, ...] = (
    dict(key="what_pdi_is", chapter="Standing it up", title="What PDI is",
         what="An encrypted vault, a tamper-evident audit log, and a tenant "
              "registry. Other systems store their sensitive data here "
              "instead of in their own database, reached only over this API.",
         screens=(1, 15, 19, 23),
         click="Open Overview and read the live tiles."),
    dict(key="sign_in", chapter="Standing it up", title="Getting in",
         what="Signing in to the console, and signing out of it. The console "
              "is an operator surface: it never shows a record's contents, "
              "because the operator is not who the record belongs to.",
         screens=(20, 21, 22),
         click="Sign in, then look at what the console does not show you."),
    dict(key="vault", chapter="The vault", title="The vault itself",
         what="Records go in sealed and come out only for a caller holding "
              "the right key. What you can see here is that a record exists, "
              "how big it is and when it moved — never what it says.",
         screens=(2, 3, 16),
         click="Store a record, then try to read it back without the key."),
    dict(key="encryption", chapter="The vault", title="Encryption and keys",
         what="AES-256-GCM, with the option that matters: bring your own key. "
              "A customer key travels per request and is never stored, so a "
              "copy of this database is not a copy of the data.",
         screens=(4, 13, 24),
         click="Set a customer key and watch a read fail without it."),
    dict(key="tenants", chapter="Who may reach it", title="Tenants and tokens",
         what="Each integrating system is a tenant with its own bearer token "
              "and its own namespace. One tenant cannot read another's "
              "records — not by policy, but because the query is scoped "
              "before it runs.",
         screens=(5, 6, 7, 14, 25),
         click="Create a tenant and try its token against another's data."),
    dict(key="audit", chapter="Proving it", title="The audit log",
         what="Every access appends a hash-chained entry. Verifying the chain "
              "tells you whether anything was altered or removed — including "
              "by whoever runs the server.",
         screens=(8, 9, 40),
         click="Verify the chain, then read what a break would look like."),
    dict(key="retention", chapter="Proving it", title="Keeping and deleting",
         what="Retention windows, snapshots and restore. A deletion that "
              "leaves the audit trail intact is the only kind worth having.",
         screens=(11, 30),
         click="Set a retention window and read what it will remove."),
    dict(key="connect", chapter="Connected systems", title="Connectors",
         what="The systems that store data here — QRME's profile source "
              "material, JIM-mini's medical payloads — each as its own tenant "
              "with its own token.",
         screens=(10, 18, 26, 28, 29),
         click="Open the tandem page and follow one payload end to end."),
    dict(key="apps", chapter="Connected systems", title="Apps and assistants",
         what="Apple Intelligence, Gemini and Copilot can be pointed at a "
              "tenant. What they get is what the tenant may see, which is not "
              "everything in the vault.",
         screens=(33, 34, 35),
         click="Connect one and read the scope it is granted."),
    dict(key="intake", chapter="Taking data in", title="Secure intake",
         what="A form, a file or a photo arriving from outside, sealed on the "
              "way in rather than after it lands.",
         screens=(31, 32),
         click="Open an intake and watch where the sealing happens."),
    dict(key="robots", chapter="Out in the world", title="Robots and custody",
         what="A robot body's data vaulted like anything else, and custody "
              "beacons for the things that move between people.",
         screens=(36, 37),
         click="Bind a robot and read what it may write."),
    dict(key="gate", chapter="Out in the world", title="The agent at the gate",
         what="Somebody rings the facility door at 2am. The agent settles "
              "what a wrong answer could not break, and hands a person "
              "everything else. The decision is made in code before a model "
              "is asked to put it into words.",
         screens=(38, 39),
         click="Open a ring and read which outcomes it may not choose."),
    dict(key="health", chapter="Running it", title="Deployment and health",
         what="Where it runs, whether it is well, and what to look at first "
              "when it is not.",
         screens=(12, 17),
         click="Open Deployment and read the health checks."),
    dict(key="all_set", chapter="Running it", title="Ready",
         what="The end of the setup path, and where to go back to. Every "
              "screen carries the guide, so a part of this can be re-read on "
              "its own.",
         screens=(27, 41),
         click="Ask the guide about anything you are looking at."),
)

CHAPTERS = tuple(dict.fromkeys(lesson["chapter"] for lesson in LESSONS))
MODES = ("text", "voice")


class TutorialError(ValueError):
    """A step that does not exist. Text meant for a person."""


def _index(key: str) -> int:
    for i, lesson in enumerate(LESSONS):
        if lesson["key"] == key:
            return i
    raise TutorialError(f"no such step {key!r}")


def say(lesson: dict, mode: str = "text") -> dict:
    """One lesson, rendered for reading or for listening.

    The only place the two differ. Spoken, a screen number is noise, so voice
    drops the numbers and keeps the sentence. Two hand-written versions would
    drift, and the spoken one would be the one nobody re-read.
    """
    if mode not in MODES:
        raise TutorialError(f"unknown mode {mode!r} — one of {', '.join(MODES)}")
    out = {"key": lesson["key"], "chapter": lesson["chapter"],
           "title": lesson["title"], "click": lesson["click"], "mode": mode}
    if mode == "voice":
        out["speak"] = f"{lesson['title']}. {lesson['what']} {lesson['click']}"
        out["screens"] = []
    else:
        out["what"] = lesson["what"]
        out["screens"] = list(lesson["screens"])
    return out


def outline(mode: str = "text") -> dict:
    """The whole walkthrough at once, for an operator who would rather skim."""
    return {
        "guide": GUIDE,
        "ceiling": CEILING,
        "chapters": [
            {"chapter": c,
             "steps": [say(le, mode) for le in LESSONS if le["chapter"] == c]}
            for c in CHAPTERS],
        "steps": len(LESSONS),
    }


def start(learner_id: str, mode: str = "text") -> dict:
    """Begin, or begin again from the top."""
    conn = db.connect()
    conn.execute("DELETE FROM console_tutorial WHERE learner_id=?",
                 (learner_id,))
    conn.commit()
    return where(learner_id, mode)


def _done(learner_id: str) -> set[str]:
    rows = db.connect().execute(
        "SELECT lesson FROM console_tutorial WHERE learner_id=?",
        (learner_id,)).fetchall()
    return {r["lesson"] for r in rows}


def where(learner_id: str, mode: str = "text") -> dict:
    """The step this operator is on, with what is behind and ahead."""
    done = _done(learner_id)
    remaining = [le for le in LESSONS if le["key"] not in done]
    finished = not remaining
    return {
        "learner_id": learner_id,
        "guide": GUIDE,
        "step": None if finished else say(remaining[0], mode),
        "done": len(done),
        "total": len(LESSONS),
        "finished": finished,
        "note": ("that is all of it — the guide is on every screen if you want "
                 "one part again" if finished else
                 f"step {len(done) + 1} of {len(LESSONS)}"),
    }


def mark(learner_id: str, key: str, mode: str = "text") -> dict:
    """Mark one step done and hand back the next.

    Per step rather than as a cursor, so somebody who jumped to the audit
    chapter and came back is not told they have finished the vault.
    """
    _index(key)
    conn = db.connect()
    conn.execute(
        "INSERT INTO console_tutorial (learner_id, lesson, done_at)"
        " VALUES (?,?,?) ON CONFLICT (learner_id, lesson) DO NOTHING",
        (learner_id, key, db.utcnow()))
    conn.commit()
    return where(learner_id, mode)


def step(key: str, mode: str = "text") -> dict:
    """One named step, for a screen that wants to explain itself."""
    return say(LESSONS[_index(key)], mode)


def for_screen(number: int, mode: str = "text") -> dict | None:
    """The lesson covering a given screen, so a console screen's help button
    can open at the right place rather than at the beginning."""
    for lesson in LESSONS:
        if number in lesson["screens"]:
            return say(lesson, mode)
    return None
