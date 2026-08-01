"""The stranger's page was already right. The tenant's was not.

## The finding

A tenant picks a language and PDI honours it: `_STRINGS` translates the
console's chrome, `_PAGE_STRINGS` translates the recipient's server-rendered
page against their browser's header, and the recipient's own two refusals —
`RECEIVE_NO`, `RECEIVE_REVOKED` — are localized at the route that raises them,
from the round that gave the recipient a door at all.

The tenant's refusals were English. All sixty of them, on an account where the
language picker had been answered and every other surface honoured it.

    asked     is the stranger answered in their language
    mattered  is the tenant

The direction is the reverse of the usual one, and worth naming for that
reason. Three rounds across these repositories found a stranger being served
the language of somebody who *had* an account — the accountless screen, the
care beacon, the objection form. Here the stranger's page was already correct
and the account-holder's was not, because the stranger's page was built as a
localization problem from the first line and the vault's own refusals were
never looked at as text a person reads.

## Three handlers, three shapes

`create_app` had three exception handlers and they built their responses three
different ways: two hand-rolled `Response`s with `json.dumps`, one
`JSONResponse`. None of that was wrong on its own, and it is exactly how a
fourth arrives with a fourth shape and no translation — the sibling repository
found the same drift at eight.

    asked     are the refusals localized
    mattered  are all of them

All of them now return through `i18n.refuse`, and
`test_every_handler_returns_through_the_one_place` fails the next one that
does not.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from pdi import i18n

#: Error classes whose messages are refusals a person reads. The class a
#: sentence is raised through says nothing about who reads it, so they are
#: counted alongside `HTTPException` details.
DOMAIN_ERRORS = ("BeaconError", "BequestError", "DockError", "HostingError",
                 "NotifyError", "RosterError", "TutorialError",
                 "CustomerKeyRequired", "CustomerKeyMismatch")


def _repo_root() -> Path:
    for d in Path(__file__).resolve().parents:
        if (d / "pyproject.toml").exists():
            return d
    raise RuntimeError("no pyproject.toml above this test")


REPO = _repo_root()
PKG = REPO / "pdi"
SNAPSHOT = Path(__file__).resolve().parent / "refusals_untranslated.txt"


def _details(root: Path) -> tuple[set[str], int]:
    """Every literal refusal sentence in the package, and how many are built
    by interpolation instead.

    From Python's own parser. Refusals wrap across source lines by
    construction — they are long sentences inside an indented `raise` — and a
    regex over the source is how the language audit in the sibling
    repositories missed real text three separate times.
    """
    literals: set[str] = set()
    interpolated = 0
    for path in sorted(root.rglob("*.py")):
        if "tests" in path.parts:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Call):
                continue
            name = getattr(node.func, "id", "") or getattr(node.func, "attr", "")
            if name == "HTTPException":
                detail = node.args[1] if len(node.args) >= 2 else None
                for kw in node.keywords:
                    if kw.arg == "detail":
                        detail = kw.value
                candidates = [detail]
            elif name in DOMAIN_ERRORS:
                candidates = list(node.args) + [k.value for k in node.keywords]
            else:
                continue
            for arg in candidates:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    literals.add(arg.value)
                elif isinstance(arg, ast.JoinedStr):
                    interpolated += 1
    return literals, interpolated


def _translated() -> set[str]:
    """All three tables, because `tr_refusal` consults all three. A sentence
    already translated for the recipient's page is not owed a second entry —
    two copies of one sentence are free to drift, with nothing to say which
    reader got which."""
    return set(i18n._REFUSALS) | set(i18n._STRINGS) | set(i18n._PAGE_STRINGS)


def _recorded() -> set[str]:
    return {line.rstrip("\n") for line in
            SNAPSHOT.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")}


def test_every_refusal_is_translated_or_written_down():
    """Both directions. A refusal that is neither is a sentence somebody will
    read in a language they did not choose, that nobody decided about."""
    literals, _ = _details(PKG)
    undecided = sorted(literals - _translated() - _recorded())
    stale = sorted(_recorded() - literals)
    problems = []
    if undecided:
        problems.append(
            f"{len(undecided)} refusal(s) that are neither translated nor "
            "recorded:\n    " + "\n    ".join(s[:90] for s in undecided[:30])
            + "\n  Add it to i18n._REFUSALS, or to "
              f"{SNAPSHOT.name} — but adding there is ratcheted.")
    if stale:
        problems.append(
            f"{len(stale)} recorded refusal(s) are no longer raised anywhere "
            f"— strike them from {SNAPSHOT.name}:\n    "
            + "\n    ".join(s[:90] for s in stale[:30]))
    assert not problems, "\n\n".join(problems)


def test_the_backlog_only_shrinks():
    ceiling = int(re.search(r"# ceiling: (\d+)",
                            SNAPSHOT.read_text(encoding="utf-8")).group(1))
    assert len(_recorded()) <= ceiling, (
        f"{len(_recorded())} untranslated refusals, above the {ceiling} this "
        "guard started at")


def test_every_handler_returns_through_the_one_place():
    """The structural half, and the only part of this file that is a fix.

    Checked structurally rather than by driving each handler: a driven check
    would cover the ones that exist today and say nothing about the next.
    """
    tree = ast.parse((PKG / "api.py").read_text(encoding="utf-8"))
    handlers: list[tuple[str, bool]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not any(isinstance(d, ast.Call)
                   and getattr(d.func, "attr", "") == "exception_handler"
                   for d in node.decorator_list):
            continue
        routed = any(
            isinstance(n, ast.Call)
            and getattr(n.func, "attr", "") == "refuse"
            and getattr(getattr(n.func, "value", None), "id", "") == "i18n"
            for n in ast.walk(node))
        handlers.append((node.name, routed))

    assert len(handlers) >= 4, (
        f"only {len(handlers)} exception handlers found in api.py — the "
        "pattern has stopped matching, so this check would pass on nothing")
    astray = sorted(name for name, routed in handlers if not routed)
    assert not astray, (
        f"{astray} build their own response instead of returning through "
        "i18n.refuse. Every sentence they carry is a refusal somebody reads, "
        "and it will be in English no matter what language they chose.")


def test_the_extractor_can_still_see(tmp_path):
    """A guard on the guard, against a fixture whose answer is known.

    If the walk stops recognising a call shape, `_details` returns a small
    set, the backlog looks solved, and the record fills with strings nobody
    raises — which the staleness half would report as *progress*.
    """
    (tmp_path / "shapes.py").write_text(
        'from fastapi import HTTPException\n'
        'def a(): raise HTTPException(404, "positional")\n'
        'def b(): raise HTTPException(403, detail="by keyword")\n'
        'def c(): raise HTTPException(422, "wrapped across "\n'
        '                                  "two source lines")\n'
        'def d(x): raise HTTPException(400, f"built from {x}")\n'
        'def e(): raise BequestError(409, "a domain refusal")\n'
        'def f(): raise crypto.CustomerKeyRequired("a dotted refusal")\n',
        encoding="utf-8")
    literals, interpolated = _details(tmp_path)
    assert literals == {"positional", "by keyword",
                        "wrapped across two source lines", "a domain refusal",
                        "a dotted refusal"}, (
        f"the extractor no longer reads the shapes it documents:\n{literals}")
    assert interpolated == 1


def test_every_translated_refusal_has_every_language():
    """No partial rows. A row missing four languages serves English to four
    readers while the table says the sentence is handled."""
    langs = [c for c in i18n.SUPPORTED if c != i18n.DEFAULT]
    gaps = {k: [c for c in langs if c not in v]
            for k, v in i18n._REFUSALS.items()}
    gaps = {k: v for k, v in gaps.items() if v}
    assert not gaps, (
        "these refusals are missing languages:\n    "
        + "\n    ".join(f"{k[:60]}: {', '.join(v)}"
                        for k, v in sorted(gaps.items())))
    assert len(i18n._REFUSALS) >= 8


def test_the_recipients_sentence_is_not_translated_twice():
    """`RECEIVE_NO` lives in `_PAGE_STRINGS` and must not be copied here.

    `tr_refusal` consults all three tables for exactly this reason. Two
    entries for one sentence are two translations free to drift, and the
    reader who got the stale one would have no way to tell.
    """
    from pdi.api import RECEIVE_NO, RECEIVE_REVOKED
    for sentence in (RECEIVE_NO, RECEIVE_REVOKED):
        assert sentence not in i18n._REFUSALS, (
            f"{sentence!r} is in both _REFUSALS and _PAGE_STRINGS")
        assert i18n.tr_refusal(sentence, "fr") != sentence, (
            f"{sentence!r} no longer resolves through _PAGE_STRINGS — the "
            "recipient is back to English on the one page written for them")


# --- driven, not read ------------------------------------------------------

def test_a_tenant_is_refused_in_their_own_language(client):
    """The defect, driven end to end.

    A read-only token doing a write is a refusal every tenant can meet, and
    the token is a real one, so the vault has a stored language to read. The
    browser header says `en-US` throughout, because that is what a console
    operator's browser sends whatever they chose in the app — if this passes
    while the header decides, the fix is a no-op.
    """
    from pdi import vault
    from .conftest import auth, new_tenant

    write_token = new_tenant(client)
    assert client.put("/language", json={"language": "es"},
                      headers=auth(write_token)).status_code == 200

    tenant = vault.tenant_by_token(write_token)
    reader = vault.issue_token(tenant["id"], "read")["token"]

    refused = client.put("/records", json={"key": "k", "value": "v"},
                         headers={**auth(reader),
                                  "accept-language": "en-US,en;q=0.9"})
    assert refused.status_code == 403, refused.text
    assert refused.json()["detail"] == (
        i18n._REFUSALS["this token is read-only"]["es"]), (
        f"the tenant set Spanish and was refused in "
        f"{refused.json()['detail']!r}. The browser header said en-US, which "
        "is exactly why the header cannot be what decides this.")


def test_a_caller_with_no_token_gets_their_browsers_language(client):
    """No credential means no stored setting, so the header is all there is —
    and it is genuinely theirs. This is the branch that keeps the recipient's
    page correct now that refusals pass through one handler."""
    refused = client.get("/records",
                         headers={"accept-language": "fr-FR,fr;q=0.9"})
    assert refused.status_code == 401, refused.text
    assert refused.json()["detail"] == (
        i18n._REFUSALS["missing tenant bearer token"]["fr"])


def test_an_unknown_sentence_falls_through_as_english():
    """The 49 in the record, and anything added tomorrow. English is a visible
    gap; a guessed translation is a confident error, and a refusal is where
    being confidently wrong costs somebody the most."""
    assert i18n.tr_refusal("a sentence nobody has translated", "es") == (
        "a sentence nobody has translated")


def test_resolving_a_language_never_raises():
    """This runs inside every exception handler. If it can throw, a refusal
    becomes a 500 — telling somebody the vault broke when it was really
    telling them no."""
    class _Odd:
        headers = {"authorization": "Bearer nope"}

    class _Worse:
        @property
        def headers(self):
            raise RuntimeError("no headers here")

    assert i18n.refusal_language(_Odd()) == "en"
    assert i18n.refusal_language(_Worse()) == "en"
