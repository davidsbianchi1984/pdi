"""And so is each phone. The console guard's question, one surface over.

`test_the_console_is_a_client_too.py` exists because the union guard answered
*some client can reach this*, which was true, in place of *this client can
reach this*, which was not. It fixed that for the console, and the console
backlog is now zero.

It fixed it for **one** client. There are four.

                      at the start of this round
    union doorless                         0
    console                                0
    ios                                   86
    android                               86
    windows                               85

Three quarters of PDI's routes are unreachable from a phone. That is not a
list of things to build — an owner's workshop has no business on a handset —
it is a list of things **nobody has decided about**. This file makes the split
deliberate: one ratcheted snapshot per shell, so deferring a route takes an
edit and shows in a diff.

## What it found on its first run: nothing to build

Unlike QRME and JIM-mini, where this guard immediately turned up a block that
had to be built — a paged responder who could not answer an alarm, a person
who could not object to a synthetic profile of themselves — PDI's phone
backlog contains nothing indefensible, and that is worth writing down rather
than leaving as an absence.

The reason is what PDI is. Its shells are **operator** apps: the person
holding one runs the vault. There is no equivalent of the member of the public
who needs a door, because PDI's public-facing surface is not an app at all —
it is a page. `GET /s/{bid}` is served `response_class=HTMLResponse`, and the
courier holding a sealed crate meets it through a phone **camera**, in a
browser, with nothing installed. The `/s/…` family sitting in these snapshots
is therefore correctly absent from the shells, not missing from them.

So this file is preventive here rather than corrective. It exists so that the
next capability added to the vault has to answer the question out loud —
*which surfaces is this for?* — instead of defaulting into whichever one
somebody happened to build first. Two of the three products needed that
question asked retroactively. This one gets it asked in advance.

## What this file is not

It is not a demand that every route reach every client. It is the ratchet that
makes the split a decision. The difference between a decision and an oversight
is whether anybody made it.
"""

from __future__ import annotations

from pathlib import Path

from pdi.api import app

from . import clientpaths

HERE = Path(__file__).resolve().parent

#: One snapshot per shell. Separate files rather than one, because the shells
#: diverge for real reasons — a camera roll, a Health store, a desktop-only
#: signing ceremony — and a single list would hide which shell a line is for.
SNAPSHOTS = {
    "ios": HERE / "ios_doorless.txt",
    "android": HERE / "android_doorless.txt",
    "windows": HERE / "windows_doorless.txt",
}

#: Where each stood when this guard was written, so the direction of travel is
#: a fact in the file rather than a claim in a commit message.
# Raised by one in the round that added GET /r/{tid}. Deliberately, which is
# the whole point of a ratchet: the route's door is a browser opening an
# emailed link, exactly like GET /s/{bid} beside it, and a phone shell is not
# where somebody who was sent one file should have to go.
STARTED_AT = {"ios": 87, "android": 87, "windows": 86}


def _surface(name: str):
    for lang in clientpaths.NATIVE:
        if lang.name == name:
            return lang
    raise AssertionError(f"no native surface named {name!r}")


def _recorded(name: str) -> list[str]:
    return [line.strip() for line in
            SNAPSHOTS[name].read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")]


def _actual(name: str) -> list[str]:
    return clientpaths.doorless(app, surfaces=(_surface(name),))


def test_each_shell_backlog_matches_its_record():
    """Both directions, per shell. A route that has *gained* a door on a phone
    is as much a change to report as one that has lost it — a file only
    checked for growth becomes a list of things that were true once."""
    problems = []
    for name in SNAPSHOTS:
        actual, recorded = set(_actual(name)), set(_recorded(name))
        appeared, resolved = sorted(actual - recorded), sorted(recorded - actual)
        if appeared:
            problems.append(
                f"{name}: {len(appeared)} route(s) the shell cannot reach:\n    "
                + "\n    ".join(appeared)
                + "\n  (build the door, or record it here with the reason)")
        if resolved:
            problems.append(
                f"{name}: {len(resolved)} route(s) now have a door — strike "
                f"them from {SNAPSHOTS[name].name}:\n    "
                + "\n    ".join(resolved))
    assert not problems, "\n\n".join(problems)


def test_each_backlog_only_shrinks():
    """A ratchet per shell. None is zero and none has to be — what they must
    not do is grow."""
    for name, started in STARTED_AT.items():
        assert len(_recorded(name)) <= started, (
            f"the {name} backlog is {len(_recorded(name))}, above the "
            f"{started} it started at — routes are being added faster than "
            "doors")


def test_the_union_is_never_worse_than_any_single_shell():
    """Arithmetic, not policy: every shell is one of the union's own surfaces,
    so the union cannot be missing something a shell reaches."""
    union = set(clientpaths.doorless(app))
    for name in SNAPSHOTS:
        assert union <= set(_actual(name)), (
            f"a route is doorless everywhere but reachable from {name}, which "
            "means the two are computed over different route tables")


