"""A tab whose label is its own key, in Latin letters, in every language.

Found in the sibling product, not this one: JIM-mini's navigation strip grew a
`presence` tab and its table never grew a `nav.presence` row, so the strip read
`nav.presence` between two real words. `t()` falls back to the key when the
table has no row, which is right — a missing row should look like a bug — and
that is exactly how a missing row reaches a person's screen.

    asked     does every key in the table reach a screen
    mattered  does every key a screen asks for exist

This console does not have the defect. The guard is here anyway, because a
guard that only exists where the bug was found is a guard that catches the bug
once. This navigation has fifteen tabs and the table has fifteen rows; the
check is what keeps the sixteenth honest.

The completeness guards next door have been hunting the opposite failure for
releases — a key translated into ten languages and used nowhere. Nothing
looked the other way. A table can be complete in every language and still be
missing the row a screen actually asks for, and that failure is the visible
one: a dead key wastes a translation nobody reads, while a missing row puts an
identifier on screen in front of a person.
"""

from __future__ import annotations

import re
from pathlib import Path

from .ratchets import floor

SRC = Path(__file__).resolve().parents[2] / "app" / "src"


def _table() -> set[str]:
    return set(re.findall(r'^  "([\w.]+)":',
                          (SRC / "l10n.ts").read_text("utf-8"), re.M))


def _tab_ids() -> list[str]:
    """The navigation's own list, read where it is declared.

    Deliberately the `{ id: … }` rows rather than any union above them: a union
    is a type and the rows are what renders, and in the sibling it was the rows
    that grew a member the table never got.
    """
    return re.findall(r'\{\s*id:\s*"(\w+)"',
                      (SRC / "App.tsx").read_text("utf-8"))


def test_the_tab_scan_is_finding_tabs():
    """A guard on the guard: a walk that stopped matching would report every
    tab labelled by finding none of them."""
    assert len(_tab_ids()) >= floor("console.nav_tabs"), (
        f"only {len(_tab_ids())} tab(s) parsed — this console has more, and "
        "the check below would pass on almost nothing")


def test_every_tab_has_a_label():
    """The defect, directly. A tab with no row is an identifier in the
    navigation, in all ten languages at once."""
    table = _table()
    bare = [f"nav.{i}" for i in _tab_ids() if f"nav.{i}" not in table]
    assert not bare, (
        f"{len(bare)} tab(s) render their own key as their label:\n    "
        + "\n    ".join(bare)
        + "\n  `t()` falls back to the key, so this shows in every language.")


def test_no_key_is_translated_into_ten_languages_and_used_nowhere():
    """The other direction, which this file's own header has named since it
    was written and nothing checked: a key in the table that no screen looks
    up. Ported on the night it found two here — `pr.nocollector`, superseded
    by the status map's `pr.out.nocollector` and left behind, and
    `acc.review.sealed`, a label for reports "sealed to the vault" when the
    route stores them plainly on the deployment and the code beside it says
    there is no second place to seal to. Ten languages each, read by nobody,
    one of them describing a design this product deliberately does not have.

    A key is reachable here four ways: a literal lookup, a template-literal
    prefix, a concatenation prefix — `t("pos.cap." + k)` is this console's
    own spelling — and a quoted appearance in a status map whose values are
    keys. The last is covered by counting any quoted appearance outside the
    table itself, which is also what keeps this from the trap the estate
    keeps finding: the one corpus excluded is the one that declares the name.
    """
    table_src = (SRC / "l10n.ts").read_text(encoding="utf-8")
    table = set(re.findall(r'^  "([\w.]+)":', table_src, re.M))
    used, prefixes = set(), set()
    for screen in list(SRC.rglob("*.tsx")) + list(SRC.rglob("*.ts")):
        if screen.name == "l10n.ts":
            continue
        text = screen.read_text(encoding="utf-8")
        used |= {k for k in re.findall(r'"([\w.]+)"', text) if k in table}
        used |= {k for k in re.findall(r"'([\w.]+)'", text) if k in table}
        prefixes |= set(re.findall(r'\(\s*`([\w.]+)\$\{', text))
        prefixes |= set(re.findall(r'\(\s*"([\w.]+\.)"\s*\+', text))
    dead = sorted(k for k in table - used
                  if not any(k.startswith(p) for p in prefixes))
    assert not dead, (
        f"{len(dead)} key(s) are translated and looked up by nothing:\n    "
        + "\n    ".join(dead)
        + "\n  Wire them, or delete them — but a translated string nobody "
          "reads is the English still being read instead.")


def test_no_literal_lookup_is_missing_its_row():
    """The general case, of which the tab was one instance.

    Only literal keys — `t("a.b", lang)` — because a composed key cannot be
    resolved without running the app, and a check that guessed at those would
    fail on working code. The literal ones are most of them and were enough to
    have caught the sibling's.

    The comma at the end of the pattern is what makes "literal" mean it. This
    console builds keys by concatenation — `t("pos.cap." + k, lang)` — and a
    pattern that stopped at the closing quote read `pos.cap.` as a key in its
    own right, then reported six of them missing. Every one of those prefixes
    is live, and the six rows the check wanted would have been six rows
    nothing reads. A guard against identifiers on screen that would have put
    six more into the table.
    """
    table, asked = _table(), set()
    for f in list(SRC.rglob("*.tsx")) + list(SRC.rglob("*.ts")):
        if f.name == "l10n.ts":
            continue
        asked |= set(re.findall(r'\b(?:t|tr|L)\(\s*"([\w.]+)"\s*,',
                                f.read_text(encoding="utf-8")))
    missing = sorted(asked - table)
    assert not missing, (
        f"{len(missing)} key(s) are looked up and have no row:\n    "
        + "\n    ".join(missing)
        + "\n  Each renders as its own name on screen, in every language.")
