"""`test_a_binding_is_not_a_door.py`, for the other three clients.

That file exists because `clientpaths.doorless` counts **call sites**, so a
function written in `api.ts` and wired to no screen takes its route off the
backlog whether or not anything ever calls it. Its own docstring puts the cost
plainly:

    A round that adds thirty bindings and five screens will report thirty
    doors and have built five.

It checks `app/src/api.ts`. There are four clients, and the other three have
`ApiClient.swift`, `ApiClient.kt` and `ApiClient.cs` — files of exactly the
same kind, with exactly the same property, and nothing had ever looked at
them.

This is the third time in this audit that a guard turned out to cover one
surface of four. The union guard did it, the door guard did it, and now the
binding guard. The lesson is not that somebody was careless; it is that
"client" reads as singular when you are writing the check and there are four
of them when somebody runs the app.

## What it found in PDI on its first run

Two bindings, one route, the same half missing on both shells:
`android.robotKeys` and `windows.RobotKeys` — `GET /robots/{rid}/data`,
written in both shells and called in neither.

The route reads back the vault keys a bound robot has deposited. Sealing hands
one key back, once, at the moment of sealing. Close the app and that key is
gone from the screen; the server is the only thing that still knows it, and
this was the call that asks. Both shells could put a robot's maps, snapshots
and sensor logs into the vault and neither could list what it had put there.
iOS could — `RobotsView` calls `robotData` to count each robot's keys — which
is why the gap survived a per-shell door audit: the route had a door, on one
phone of three.

Both now have a **Sealed keys** button on each robot card. They list the keys
rather than counting them, since the key is what `Vault → read a record` takes.
"""

from __future__ import annotations

import re
from pathlib import Path

from . import ratchets


def _repo_root() -> Path:
    for d in Path(__file__).resolve().parents:
        if (d / "pyproject.toml").exists():
            return d
    raise RuntimeError("no pyproject.toml above this test")


REPO = _repo_root()
SNAPSHOT = Path(__file__).resolve().parent / "unused_native_bindings.txt"

#: Where it stood when this guard was written.
STARTED_AT = 2

#: Where each shell declares the calls it can make, and how that language
#: spells a declaration. Held here rather than inside the guard below so the
#: floor under each can measure the same thing the guard counts.
API_CLIENTS = {
    "ios": (REPO / "native/ios/Sources/ApiClient.swift",
            r"^\s{4}func (\w+)\("),
    "windows": (REPO / "native/windows/ApiClient.cs",
                r"^\s{4}public (?:async )?Task[^\s]*\s+(\w+)\("),
}
_android = list((REPO / "native/android").rglob("ApiClient.kt"))
if _android:
    API_CLIENTS["android"] = (_android[0],
                              r"^\s{4}(?:suspend )?fun (\w+)\(")


def _api_functions(shell: str) -> list[str]:
    path, pattern = API_CLIENTS[shell]
    return re.findall(pattern, path.read_text(encoding="utf-8"), re.M)


def _swift() -> list[str]:
    api = REPO / "native/ios/Sources/ApiClient.swift"
    if not api.exists():
        return []
    names = set(re.findall(r"^\s{4}func (\w+)\(", api.read_text(encoding="utf-8"), re.M))
    callers = "\n".join(
        p.read_text(encoding="utf-8", errors="ignore")
        for p in (REPO / "native/ios").rglob("*.swift") if p != api)
    return [f"ios.{n}" for n in sorted(names)
            if not re.search(rf"\.{n}\s*\(", callers)]


def _kotlin() -> list[str]:
    found = list((REPO / "native/android").rglob("ApiClient.kt"))
    if not found:
        return []
    api = found[0]
    names = set(re.findall(r"^\s{4}(?:suspend )?fun (\w+)\(",
                           api.read_text(encoding="utf-8"), re.M))
    callers = "\n".join(
        p.read_text(encoding="utf-8", errors="ignore")
        for p in (REPO / "native/android").rglob("*.kt") if p != api)
    return [f"android.{n}" for n in sorted(names)
            if not re.search(rf"\.{n}\s*\(", callers)]


def _csharp() -> list[str]:
    api = REPO / "native/windows/ApiClient.cs"
    if not api.exists():
        return []
    names = set(re.findall(r"^\s{4}public (?:async )?Task[^\s]*\s+(\w+)\(",
                           api.read_text(encoding="utf-8"), re.M))
    callers = "\n".join(
        p.read_text(encoding="utf-8", errors="ignore")
        for p in (REPO / "native/windows").rglob("*.cs") if p != api)
    return [f"windows.{n}" for n in sorted(names)
            if not re.search(rf"\.{n}\s*\(", callers)]


def _unused() -> list[str]:
    return sorted(_swift() + _kotlin() + _csharp())


def _rows() -> list[str]:
    return [line.strip() for line in
            SNAPSHOT.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")]


def _recorded() -> list[str]:
    """The binding names, without the reasons that now sit beside them."""
    return [row.split(" — ", 1)[0].strip() for row in _rows()]


def test_every_recorded_binding_says_why_it_is_recorded():
    """The reasons for these used to live in this file's module docstring —
    true, careful, and one file away from the list they explained. A record
    whose justification is somewhere else reads, at the place somebody actually
    looks, as an unexplained backlog.

        asked     is the exemption explained
        mattered  is it explained where the exemption is
    """
    bare = [row for row in _rows() if " — " not in row or
            len(row.split(" — ", 1)[1].strip()) < 20]
    assert not bare, (
        f"{len(bare)} recorded binding(s) carry no reason on the row:\n    "
        + "\n    ".join(bare)
        + "\n  Write why it is here, after an em dash, or strike it.")


def test_the_unused_native_bindings_match_the_record():
    """Both directions. A binding that has *gained* a caller is as much a
    change to report as one that has lost it."""
    actual, recorded = set(_unused()), set(_recorded())
    appeared, resolved = sorted(actual - recorded), sorted(recorded - actual)

    problems = []
    if appeared:
        problems.append(
            f"{len(appeared)} native binding(s) nothing calls:\n    "
            + "\n    ".join(appeared)
            + "\n  (wire it to a screen, or record it here — but note that "
              "its route is being counted as doored either way)")
    if resolved:
        problems.append(
            f"{len(resolved)} native binding(s) now have a caller — strike "
            f"them from {SNAPSHOT.name}:\n    " + "\n    ".join(resolved))
    assert not problems, "\n\n".join(problems)


def test_it_only_shrinks():
    assert len(_recorded()) <= STARTED_AT, (
        f"{len(_recorded())} unused native bindings, above the {STARTED_AT} "
        "this guard started at — bindings are being written faster than the "
        "screens that call them, which is what inflates the door count")


def test_the_extractors_are_reading_something():
    """A guard on the guard, and it is not decorative: this file's whole job
    is to report an *absence*, and an extractor that finds no functions at all
    reports a beautiful zero.

    Five false positives in this audit have come from a pattern that quietly
    stopped matching. This one fails loudly instead.
    """
    for shell, (path, _) in API_CLIENTS.items():
        assert path.exists(), f"{shell}: {path.name} is gone"
        found = _api_functions(shell)
        assert len(found) >= ratchets.floor(f"native.api_functions.{shell}"), (
            f"only {len(found)} {shell} bindings found — the pattern has "
            "stopped matching, so an empty result here would mean nothing")


def test_the_shell_can_end_what_it_can_begin():
    """Ported from the siblings, where it was written after finding an iOS
    screen that links a child to a guardian and cannot unlink one.

    A screen that creates a standing relationship and cannot end it leaves
    the person who made it dependent on a surface they may not have. This
    vault's standing relationships are transfers, social connectors and
    bequests, and today every screen that begins one can end it — this holds
    that, because the next screen is the one that ships without its other
    half.

    **Excluding ApiClient.swift**, for the sibling's stated reason: searching
    a corpus that contains the declaration of a name is how six checks in
    this audit have been satisfied by the thing they were meant to look past.
    """
    ios = REPO / "native/ios/Sources"
    api = ios / "ApiClient.swift"
    text = "\n".join(p.read_text(encoding="utf-8", errors="ignore")
                     for p in ios.rglob("*.swift") if p != api)
    pairs = [
        ("createTransfer(", "revokeTransfer(",
         "a transfer can be offered and never withdrawn"),
        ("createConnector(", "revokeConnector(",
         "a social connector can be attached and never detached — a feed "
         "into the vault that outlives the decision to have it"),
        ("createBequest(", "revokeBequest(",
         "a bequest can be made and never revoked while the owner is alive, "
         "which the route itself allows"),
    ]
    broken = [why for begin, end, why in pairs
              if begin in text and end not in text]
    assert not broken, "\n    ".join([""] + broken)


def test_a_shell_that_can_seal_can_read_back_what_it_sealed():
    """The specific shape this guard was written after finding.

    PDI's version of the asymmetry is not power/no-power the way QRME's and
    JIM's are — it is write/no-read. A shell that deposits into the vault and
    cannot list what it deposited leaves the keys recoverable only from the
    one screen that was open at the moment of sealing.
    """
    # **Excluding each ApiClient.** The QRME version of this test did not, at
    # first, and passed — by matching each binding's own definition. That is
    # the sixth time in this audit that a check has been satisfied by the
    # thing it was meant to look past. The pattern is always the same shape:
    # searching a body of text for a name, in a corpus that contains the
    # declaration of the name.
    shells = {
        "android": ((REPO / "native/android"), "*.kt", "ApiClient.kt",
                    "ingest(", "robotKeys("),
        "windows": ((REPO / "native/windows"), "*.cs", "ApiClient.cs",
                    ".Ingest(", ".RobotKeys("),
        "ios": ((REPO / "native/ios"), "*.swift", "ApiClient.swift",
                "ingest(", "robotData("),
    }
    broken = []
    for name, (root, glob, api_name, seal, read) in shells.items():
        if not root.exists():
            continue
        text = "\n".join(p.read_text(encoding="utf-8", errors="ignore")
                         for p in root.rglob(glob) if p.name != api_name)
        if seal in text and read not in text:
            broken.append(
                f"{name} can seal a robot's intake into the vault and cannot "
                f"list the keys it sealed — the key is handed back once, at "
                f"the moment of sealing, and nothing on the shell asks again")
    assert not broken, "\n  ".join(broken)
