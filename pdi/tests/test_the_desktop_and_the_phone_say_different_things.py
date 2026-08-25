"""Two tables, one product, and nothing compared them.

## The finding

0.48.0 compared keys *inside* one table and found 54 English strings carried
by two or more keys on iOS, 43 of them already drifted. This round asks the
same question one level out.

The desktop console has its own table — `app/src/l10n.ts`, 1,882 rows — and
the three shells have theirs. **223 English strings live in both the console
table and the iOS table, and 102 of them had no translation the two tables
agreed on.** Android 104, Windows 103. A person who opens QRME on their laptop
and then on their phone is reading two different products in their own
language, and reading one product in English.

    asked     does each table say the same thing twice the same way
    mattered  do the tables say the same thing as each other

Fifty keys are *the same key in both tables*. Two of those disagreed:
`corner.send` (ar) and `plc.venues` (fr, *Espaces* on the desktop and *Lieux*
on the phone). Identical key, identical English, different word.

## The register

The largest systematic cause is not vocabulary. It is **who the product thinks
it is talking to.**

| German | Sie / Ihnen / Ihre | du / dein / dich |
|---|---|---|
| console | **204** | 32 |
| phone | 7 | **60** |

The desktop addresses a German reader formally and the phone informally. That
is not a synonym choice; in a language with a T–V distinction it is a claim
about the relationship, and this product made both claims at once — *Wo Sie
stehen* on the desktop and *Wo du stehst* on the phone, *Ihre
Signatur-Berechtigungen* against *Deine Signaturberechtigungen*.

Spanish is milder and mostly settled: 20 rows say *usted* against 47 that say
*tú* in the console, 2 against 13 on the phone. French and Portuguese are
formal on both sides; Italian informal on both.

This round moves every row it reconciles onto the phones' wording, which means
onto *du* and *tú*. The whole-table register sweep is recorded rather than
done: converting German T–V is not a pronoun substitution — *Wo Sie stehen*
becomes *Wo du stehst* — and this repo's rule against machine-mangling text a
person relies on applies to 204 rows as much as to fourteen.

## What 0.48.0 did to this number

Widened it. Reconciling the Desk and the Counter inside the native tables
picked *Theke* for the Desk, so that German would stop naming two tab-bar
entries *Schalter*. The console still said *Schalter*, and nothing compared
them, so a fix in one table opened a gap with a table no guard could see.

That is this arc's shape exactly, committed once more inside its own fix, and
it is the argument for this file: the previous round could not have known.

## The measurement was nearly the bug again

The first version of this check compared source bytes. JIM-mini's console
table writes some rows escaped — `"\\u7834\\u68c4\\u3059\\u308b"` — which in
TypeScript **is** 破棄する and renders correctly. Nine of that repo's
thirty-four "disagreements" were the same string spelled two ways, and this
guard would have shipped demanding they be "fixed".

    asked     are these two source strings identical
    mattered  do these two strings render the same

So `_decode` came first and the count came second: JIM's number fell from 34
to 25 before a line of the fix was written. `test_the_escape_decoder_reads_each_syntax`
exists so that a decoder that quietly stopped decoding cannot bring the false
number back.

## Why this file is in this repo too, and what it found instead

The finding and the guard are the sibling product's. This repo cannot have the
defect they have, because **it has no console table at all.**

`app/src/l10n.ts` does not exist here. The desktop console is fourteen screens
of English — around 250 strings by the count in
`console_untranslated.txt` — while the three native shells each carry a
ten-language table, and `qrme` and `jim-mini` each drove their console records
down to a floor rounds ago.

The sharp part is not that it is English. It is that `Guiding.tsx` renders a
**language picker**, backed by `GET /languages` and `PUT /language`. A tenant
opens the vault's console, chooses Spanish, and the backend begins answering
in Spanish inside a frame that stays entirely English — which is the finding
this whole arc opened with (*the tab bar answers in your language and nothing
behind it does*), one step worse: here the tab bar does not answer either, and
until this round nothing had ever counted it.

    asked     do this product's two tables agree
    mattered  does this product have two tables

So the split record below is an empty floor, and it must not be read as
agreement. `test_the_absent_console_table_is_recorded_not_assumed` exists to
make sure a zero here always comes with the reason.

## What this file checks

1. **the two tables agree** — per shell, matched exactly against
   `console_native_split.txt` in both directions;
2. **the total only shrinks** — against the record's `# ceiling:`;
3. **both tables still parse** — a floor and a probe row, because every false
   pass in this audit came from a pattern that stopped matching;
4. **the decoder still decodes** — on the case that produced the false count.
"""

from __future__ import annotations

import html
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

import pytest

from . import ratchets


def _repo_root() -> Path:
    for d in Path(__file__).resolve().parents:
        if (d / "pyproject.toml").exists():
            return d
    raise RuntimeError("no pyproject.toml above this test")


REPO = _repo_root()
RECORD = Path(__file__).resolve().parent / "console_native_split.txt"

CONSOLE = REPO / "app" / "src" / "l10n.ts"
TABLES = {
    "ios": REPO / "native" / "ios" / "Sources" / "L10n.swift",
    "android": (REPO / "native" / "android" / "app" / "src" / "main" / "java"
                / "com" / "pdi" / "vault" / "L10n.kt"),
    "windows": REPO / "native" / "windows" / "L10n.cs",
}

LANGS = ["en", "es", "fr", "de", "pt", "it", "ja", "zh", "hi", "ar"]

#: Floors under each parse, and a probe row per table in all ten languages —
#: one probe cannot serve both when the two tables share no key, which is the
#: state a console table starts in. Per repo; nothing else in this file is.
FLOOR, CONSOLE_FLOOR = 45, 30
NATIVE_PROBE, CONSOLE_PROBE = "nfil.content", "gd.title"

_STR = r'"((?:[^"\\]|\\.)*)"'
_NATIVE_HEAD = {
    "ios": re.compile(r'^\s*' + _STR + r'\s*:\s*\[', re.M),
    "android": re.compile(r'^\s*' + _STR + r'\s+to\s+mapOf\(', re.M),
    "windows": re.compile(r'^\s*\[' + _STR + r'\]\s*=\s*new\(\)\s*\{', re.M),
}
_NATIVE_PAIR = {
    "ios": re.compile(r'"(\w\w)"\s*:\s*' + _STR),
    "android": re.compile(r'"(\w\w)"\s+to\s+' + _STR),
    "windows": re.compile(r'\["(\w\w)"\]\s*=\s*' + _STR),
}
_CONSOLE_HEAD = re.compile(r'^\s*"([\w.]+)"\s*:\s*\{', re.M)
_CONSOLE_PAIR = re.compile(r'\b(\w\w)\s*:\s*' + _STR)

_SIMPLE = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\",
           "'": "'", "0": "\0"}


def _decode(text: str) -> str:
    """What the string renders as, not what its source bytes are.

    All four syntaxes here accept `\\uXXXX`, Swift also spells it `\\u{XXXX}`,
    and a table is free to write a row either way. Comparing the bytes counts
    a spelling difference as a wording difference — see the docstring.
    """
    out, i = [], 0
    while i < len(text):
        c = text[i]
        if c != "\\" or i + 1 >= len(text):
            out.append(c); i += 1; continue
        nxt = text[i + 1]
        if nxt == "u" and text[i + 2:i + 3] == "{":
            end = text.find("}", i + 3)
            if end != -1:
                try:
                    out.append(chr(int(text[i + 3:end], 16))); i = end + 1
                    continue
                except ValueError:
                    pass
        if nxt == "u" and re.match(r"[0-9a-fA-F]{4}", text[i + 2:i + 6]):
            out.append(chr(int(text[i + 2:i + 6], 16))); i += 6; continue
        if nxt in _SIMPLE:
            out.append(_SIMPLE[nxt]); i += 2; continue
        out.append(nxt); i += 2
    return "".join(out)


def _rows(text: str, head: re.Pattern, pair: re.Pattern) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    heads = list(head.finditer(text))
    for i, m in enumerate(heads):
        stop = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        langs: dict[str, str] = {}
        for p in pair.finditer(text[m.end():stop]):
            if p.group(1) in LANGS and p.group(1) not in langs:
                langs[p.group(1)] = _decode(p.group(2))
        if "en" in langs:
            out[m.group(1)] = langs
    return out


def _console() -> dict[str, dict[str, str]]:
    if not CONSOLE.exists():
        return {}
    return _rows(CONSOLE.read_text(encoding="utf-8"), _CONSOLE_HEAD, _CONSOLE_PAIR)


def _native(shell: str) -> dict[str, dict[str, str]]:
    return _rows(TABLES[shell].read_text(encoding="utf-8"),
                 _NATIVE_HEAD[shell], _NATIVE_PAIR[shell])


def _by_english(table: dict[str, dict[str, str]]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = defaultdict(list)
    for key, row in table.items():
        out[row["en"]].append(key)
    return out


def _split(shell: str) -> list[str]:
    """Record rows: English strings both tables hold on which no console row
    and no native row share a wording, in some language."""
    con, nat = _console(), _native(shell)
    cb, nb = _by_english(con), _by_english(nat)
    rows = []
    for english in sorted(set(cb) & set(nb)):
        for lang in LANGS[1:]:
            cvals = {con[k].get(lang) for k in cb[english]} - {None}
            nvals = {nat[k].get(lang) for k in nb[english]} - {None}
            if cvals and nvals and not (cvals & nvals):
                rows.append(f"{shell}: {','.join(sorted(cb[english]))} "
                            f":: {','.join(sorted(nb[english]))}")
                break
    return rows


def _measured() -> set[str]:
    return {row for shell in TABLES for row in _split(shell)}


def _recorded() -> set[str]:
    return {line.split("  (")[0].strip()
            for line in RECORD.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")}


UNTRANSLATED = Path(__file__).resolve().parent / "console_untranslated.txt"

#: Attributes a person reads off this console. JSX *text* is not read here —
#: see `_console_english` below for why, and by what.
_JSX = [re.compile(r'placeholder=\{?"([^"]{3,})"'),
        re.compile(r'title=\{?"([^"]{3,})"')]
_HOLE = re.compile(r"\{[^}]*\}")
#: Phrases, or a single capitalised word — the same under-counting rule the
#: rest of this audit uses, because a lone token is as often an API value as
#: a word and a rule that raises a ratcheted count under-counts on purpose.
_WORDS = re.compile(r"[A-Za-z]\s[A-Za-z]|^[A-Z][a-z]{2,}$")
#: Two words joined by something other than a space, which `_WORDS` cannot
#: see because it asks for whitespace between two letters. Widened at 0.60.6
#: after the reader was found blind to four headings on the screen this
#: release localizes: `Role &amp; industry`, `Decision-making &amp;
#: oversight`, `Bottlenecks &amp; obsolescence`, `Human-in-the-loop`. Each
#: is English a person reads, and each has no letter-space-letter anywhere
#: in it — the gap always falls beside an entity or a hyphen.
#:
#:     asked     is there a space with a letter on both sides
#:     mattered  does this read as more than one word
#:
#: `/`, `_` and `.` are excluded from the joiner because they mark the three
#: things this reader must not count: a path (`POST /profiles/{id}/chat`),
#: an identifier (`PDI_ADMIN_TOKEN`) and a filename (`report.pdf`). Entities
#: are decoded first, so the reader sees the `&` the browser draws rather
#: than the `&amp;` the source stores.
_PHRASE = re.compile(r"[A-Za-z]{2,}[^A-Za-z0-9/_.]+[A-Za-z]{2,}")


def _is_english(s: str) -> bool:
    s = html.unescape(s)
    return bool(_WORDS.search(s) or _PHRASE.search(s))


#: The extractor QRME and JIM both moved to, ported here at 0.60.4.
#:
#: The regex it replaces was `>\s*([A-Z][^<>{}\n]{2,})\s*<`, and the three
#: things it forbids are the three shapes most of this console's prose takes:
#:
#:   * `\n` — every sentence long enough to wrap. The paragraph in
#:     `ProblemNotice` explaining what a problem report does and does not
#:     contain is four source lines, so it was one string to a reader and no
#:     string at all to the reader of the reader.
#:   * `{}` — every sentence with a value in the middle of it. `VersionGuard`
#:     says *This app is v{CONSOLE_VERSION}, but the backend at {getBase()} is
#:     v{backend} — an older install is still running*. The interpolations cut
#:     that into five fragments and the pattern rejected all five. That screen
#:     is the one that tells a person why their install is answering "Not
#:     Found", and it was invisible in every one of its six strings.
#:   * `[A-Z]` at the start — *no tenant selected*, *entries verified*,
#:     *what reaches into this vault*, *one per integrating system*.
#:
#: 233 strings against the 177 the regex reported: the number two localization
#: rounds were graded against was a quarter low, and low in the direction that
#: makes a ratchet look satisfied.
#:
#:     asked     how much English does this pattern match
#:     mattered  how much English does a person read
#:
#: The extractor parses the file with TypeScript's own parser and returns
#: every `JsxText` node, which is the same thing the browser lays out. It
#: fails loudly rather than returning nothing — see the fixture check below,
#: because an extractor that silently stopped would report a perfect zero.
def _jsx_text() -> dict[str, list[str]]:
    files = sorted((REPO / "app" / "src").rglob("*.tsx"))
    rel = [str(p.relative_to(REPO / "app")) for p in files]
    proc = subprocess.run(["node", "scripts/jsx-text.mjs", *rel],
                          cwd=REPO / "app", capture_output=True, text=True)
    assert proc.returncode == 0, (
        "the JSX text extractor failed, so this check would report a "
        f"comfortable zero:\n{proc.stderr}")
    return json.loads(proc.stdout)


def _english_by_file() -> dict[str, set[str]]:
    """The same reading as `_console_english`, kept per file.

    The total is what the ratchet records; the breakdown is what
    `test_a_screen_that_imports_the_translator_holds_no_english` needs, and
    reading them off one extractor means the guard and the count can never
    disagree about what English is.
    """
    text_nodes = _jsx_text()
    by_file: dict[str, set[str]] = {}
    for path in sorted((REPO / "app" / "src").rglob("*.tsx")):
        rel = str(path.relative_to(REPO / "app"))
        source = path.read_text(encoding="utf-8")
        found = set()
        for s in text_nodes.get(rel, []):
            s = _HOLE.sub("", s).strip()
            if _is_english(s):
                found.add(s)
        for pat in _JSX:
            for s in pat.findall(source):
                s = _HOLE.sub("", s).strip()
                if _is_english(s):
                    found.add(s)
        by_file[rel] = found
    return by_file


def _console_english() -> int:
    return sum(len(v) for v in _english_by_file().values())


#: A screen asking the table for a word. Matched on the *import* rather than
#: on a call, because a screen that imports `t` and then renders none of it
#: is exactly the state this guard exists to name.
_IMPORTS_T = re.compile(
    r"""import\s*\{[^}]*\bt\b[^}]*\}\s*from\s*['"][^'"]*l10n['"]""")


def test_the_absent_console_table_is_recorded_not_assumed():
    """A zero that means *nothing to compare* must never read as *nothing
    wrong*. That is the failure mode this whole audit is named after."""
    if CONSOLE.exists():
        return                      # the table arrived; the checks below apply
    text = RECORD.read_text(encoding="utf-8")
    assert "no console table" in text, (
        f"{CONSOLE} does not exist, so every comparison in this file is "
        "vacuous. The record has to say so — otherwise an empty file reads "
        "as two tables in agreement.")


def test_the_console_english_count_only_shrinks():
    """The measurement this repo gets instead of the comparison.

    Fourteen screens of English behind a language picker that changes what the
    backend says and nothing the console says.
    """
    text = UNTRANSLATED.read_text(encoding="utf-8")
    ceiling = int(re.search(r"^# ceiling: (\d+)$", text, re.M).group(1))
    found = _console_english()
    assert found <= ceiling, (
        f"{found} English strings on the console, above the {ceiling} recorded")
    assert found > ceiling - 60, (
        f"only {found} found against a ceiling of {ceiling} — a drop that "
        "large is an extractor that stopped matching, not a round of work; "
        "lower the ceiling deliberately when it is real")


def test_a_screen_that_imports_the_translator_holds_no_english():
    """Wired is not finished, and the ledger could not tell them apart.

    The ratchet above is a total. A total falls when any screen improves, so
    the way it was read — worst file first, localize it, watch the number
    drop — quietly assumed the other direction: that a screen already through
    a localization round was done with. Nothing ever asked.

    Eight of this console's files import `t` from `../l10n`. Six hold no
    English. Two have held some since 0.48.3, the round that claimed them:
    `Continuity.tsx` with ten and `Custody.tsx` with five. Both sat on the
    finished side of the ledger for twelve releases while the audit worked
    down a list neither was on, because the list was ordered by count and
    theirs had already been counted as spent.

        asked     does this screen import the translator
        mattered  does this screen still hold English

    So the claim is made once and then held: **a screen that asks the table
    for a word may not also hard-code one.** A file is free to be untranslated
    — the ratchet is where that is recorded, and it may take as many rounds as
    it takes. What it may not be is half-translated and counted as whole. The
    moment a screen imports `t`, this is the check it lives under.

    That makes the guard cheap in the only way that matters: it costs nothing
    until someone wires a screen and leaves a string behind, and then it names
    the file and the string on the same round rather than twelve releases
    later.
    """
    by_file = _english_by_file()
    claimed = {rel: sorted(found)
               for rel, found in by_file.items()
               if _IMPORTS_T.search((REPO / "app" / rel).read_text(encoding="utf-8"))
               and found}
    assert not claimed, (
        f"{len(claimed)} screen(s) import the translator and still hold "
        "English:\n"
        + "\n".join(
            f"    {rel} ({len(found)})\n"
            + "\n".join(f"        {s!r}" for s in found)
            for rel, found in sorted(claimed.items()))
        + "\n  A screen that asks the table for one word and hard-codes "
          "another reads as translated to everything that counts it, and as "
          "half-English to the person it is for.")


def test_the_jsx_extractor_can_still_see():
    """The guard on the reader that replaced the regex.

    Everything above trusts a subprocess. If node disappears, or the parser
    stops recognising `JsxText`, `_jsx_text` returns nothing and 225 strings
    read as translated. The quietest failures in this audit have all been a
    pattern that stopped matching, and the regex this replaced is one of
    them — it never stopped, it just never started on three quarters of the
    shapes.
    """
    proc = subprocess.run(
        ["node", "scripts/jsx-text.mjs", "scripts/jsx-text.fixture.tsx"],
        cwd=REPO / "app", capture_output=True, text=True)
    assert proc.returncode == 0, f"the extractor will not run:\n{proc.stderr}"
    found = json.loads(proc.stdout)["scripts/jsx-text.fixture.tsx"]
    assert "A heading" in found, found
    multiline = next((s for s in found if s.startswith("A paragraph")), None)
    assert multiline and "one sentence to whoever reads it." in multiline, (
        "the extractor stopped joining a wrapped sentence — the shape the "
        f"regex could not see at all:\n{found}")
    assert "an interpolated value." in found, (
        "the extractor stopped returning text after an interpolation — the "
        f"shape `VersionGuard` is made of:\n{found}")
    # The shape a field report found. A sentence chosen at render time sits
    # in child position: the browser lays it out as text, the parser calls it
    # an expression. Both branches count — a reader sees one of them, and the
    # untranslated one is as English as the other.
    for branch in ("a chosen branch", "the other branch", "a guarded phrase"):
        assert branch in found, (
            "the extractor stopped reading string literals in child "
            "expressions — the shape that let the vault light say `vault "
            f"answering` in English on a translated console:\n{found}")
    assert "not a rendered word" not in found, (
        "the extractor is reading call arguments, so every `t(key, lang)` "
        f"key would be counted as English a person reads:\n{found}")


def test_the_reader_reads_more_than_the_regex_did():
    """0.60.4's finding, kept as an assertion rather than a memory.

    The old pattern is reconstructed here and run beside the extractor. It is
    not a check that the console is translated — that is the ceiling above.
    It is a check that the *reason* the ceiling moved is still true, so a
    future round cannot quietly revert to the cheaper reader and read the
    fall as progress.
    """
    old = [re.compile(r'>\s*([A-Z][^<>{}\n]{2,})\s*<'),
           re.compile(r'placeholder=\{?"([^"]{3,})"'),
           re.compile(r'title=\{?"([^"]{3,})"')]
    regex_total = 0
    for path in sorted((REPO / "app" / "src").rglob("*.tsx")):
        text = path.read_text(encoding="utf-8")
        found = set()
        for pat in old:
            for hit in pat.findall(text):
                hit = _HOLE.sub("", hit).strip()
                if _WORDS.search(hit):
                    found.add(hit)
        regex_total += len(found)
    # The direction of this comparison flipped when the console reached zero,
    # and the flip is itself the finding. While English remained, the honest
    # extractor necessarily saw *more* than the regex, which was blind to three
    # quarters of the shapes. With the console fully wired the extractor
    # correctly sees none — and the regex still reports six, every one of them
    # the word `Promise` caught out of `=> Promise<…>` by a pattern that cannot
    # tell a type parameter from a sentence.
    #
    #     asked     does the extractor see more than the regex
    #     mattered  are these two readers still different
    #
    # So the assertion is inequality rather than a direction. A future round
    # that swaps the extractor back for the regex makes both report six and
    # fails here; a round that lets English back onto the console fails the
    # ceiling above. Neither can be read as progress.
    assert _console_english() != regex_total, (
        f"the extractor and the regex it replaced both see {regex_total} — "
        "either the reader has quietly gone back to being a regex, or the "
        "console has been rewritten into the shapes that regex can read")


def test_the_reader_reads_more_than_a_space():
    """0.60.6's finding, and the third time in this arc that the reader was
    the defect.

    Both halves are asserted, because a pattern wide enough to see the
    headings is also wide enough to start counting paths and identifiers,
    and a ratchet that counts `PDI_ADMIN_TOKEN` as a sentence is as wrong as
    one that misses `Role & industry`.
    """
    reads = ["Role &amp; industry", "Decision-making &amp; oversight",
             "Bottlenecks &amp; obsolescence", "Human-in-the-loop",
             "Re-verify", "publish — out", "hard — gone",
             "Keys &amp; Retention", "append-only · SHA-256 hash-chained"]
    for s in reads:
        assert _is_english(s), (
            f"{s!r} is English a person reads off this console and the "
            "reader cannot see it — which is how fourteen strings sat "
            "outside a ratchet that looked satisfied")

    not_sentences = ["report.pdf", "PDI_ADMIN_TOKEN",
                     "POST /profiles/&#123;id&#125;/chat → 500"]
    for s in not_sentences:
        assert not _is_english(s), (
            f"{s!r} is a filename, an identifier or a path — counting it "
            "would inflate the backlog with rows no translation can fix")


def test_every_console_row_is_complete_in_every_language():
    """A partial row is worse than a missing one.

    `t()` falls back to English when a language is absent, so a row with nine
    languages and a gap renders in English for exactly one reader and looks
    fine to everyone else — including to the count above, which reads the
    *screens* and sees a key rather than a sentence. A screen wired to a
    half-filled table subtracts from `console_untranslated.txt` and delivers
    nothing to the reader whose language is the missing one.

        asked     is the screen wired to the table
        mattered  does the table answer in the language the reader picked

    Until 0.60.5 the only completeness check here was a single probe key.
    That is a check on the parser, not on the table: it proves the reader can
    see ten languages somewhere, which is a different claim from every row
    having them. 0.60.5 added eighty-seven rows in one commit, which is the
    kind of change that makes the difference matter.
    """
    if not CONSOLE.exists():
        return
    gaps = {key: [c for c in LANGS if c not in row]
            for key, row in _console().items()}
    gaps = {k: v for k, v in gaps.items() if v}
    assert not gaps, (
        f"{len(gaps)} console row(s) are missing languages:\n    "
        + "\n    ".join(f"{k}: {', '.join(v)}" for k, v in sorted(gaps.items())[:20])
        + "\n  `t()` falls back to English, so each of these is a screen that "
          "reads as translated and is not, for one reader at a time.")


def test_both_tables_still_parse():
    """A guard on the guard. A table read as empty shares no strings with
    anything and would report two tables in perfect agreement."""
    con = _console()
    if CONSOLE.exists():
        assert len(con) > CONSOLE_FLOOR, (
            f"the console table parsed to {len(con)} rows, far below what "
            f"{CONSOLE.name} holds — the row pattern has stopped matching")
        assert con.get(CONSOLE_PROBE) and sorted(con[CONSOLE_PROBE]) == sorted(LANGS), (
            f"console: `{CONSOLE_PROBE}` did not parse into all ten languages")
    for shell in TABLES:
        nat = _native(shell)
        assert len(nat) > FLOOR, (
            f"{shell}'s table parsed to {len(nat)} rows, far below what it holds")
        assert nat.get(NATIVE_PROBE) and sorted(nat[NATIVE_PROBE]) == sorted(LANGS), (
            f"{shell}: `{NATIVE_PROBE}` did not parse into all ten languages")


def test_the_escape_decoder_reads_each_syntax():
    """The check this file nearly shipped without.

    `"\\u7834..."` in TypeScript is 破 — a spelling, not a wording. A decoder
    that stopped decoding would bring back the nine false disagreements it
    was written to remove, and every one of them would look like real work.
    """
    # Built from an explicit backslash rather than written as `r"破"`.
    # The first draft of this test was written with the escapes already
    # decoded — it asserted `_decode("破") == "破"`, which is true of any
    # function that returns its argument, and it passed with the decoder
    # switched off. This file's own subject, one level in.
    bs = chr(92)
    assert _decode(bs + "u7834" + bs + "u68c4" + bs + "u3059" + bs + "u308b") == "破棄する"
    assert _decode("Todav" + bs + "u00eda nada.") == "Todavía nada."
    assert _decode(bs + "u{0027}ok") == "'ok"       # Swift's braced form
    assert _decode("a" + bs + '"b') == 'a"b'
    assert _decode("plain") == "plain"
    assert _decode("A" + bs + "u0042C") == "ABC", (
        "a decoder that handles one escape and not the next is worse than "
        "one that handles none, because the count it produces looks sane")


def test_the_desktop_and_the_phone_say_the_same_thing():
    """The defect, directly, and in both directions."""
    measured, recorded = _measured(), _recorded()
    problems = []
    new = sorted(measured - recorded)
    if new:
        problems.append(
            f"{len(new)} English string(s) are in both the console table and "
            "a shell's, with no wording the two agree on, and are not in "
            "console_native_split.txt. The desktop and the phone say "
            "different things to the same reader:\n    "
            + "\n    ".join(new[:20]))
    stale = sorted(recorded - measured)
    if stale:
        problems.append(
            f"{len(stale)} recorded row(s) now agree — strike them from "
            "console_native_split.txt:\n    " + "\n    ".join(stale[:20]))
    assert not problems, "\n\n".join(problems)


def test_the_console_native_split_only_shrinks():
    text = RECORD.read_text(encoding="utf-8")
    ceiling = int(re.search(r"^# ceiling: (\d+)$", text, re.M).group(1))
    assert len(_measured()) <= ceiling, (
        f"{len(_measured())} split rows, above the {ceiling} recorded")


def _shared_with_console(shell: str) -> set:
    """English strings this shell's table and the console's both carry."""
    return set(_by_english(_console())) & set(_by_english(_native(shell)))


@pytest.mark.parametrize("shell", sorted(TABLES))
def test_the_two_tables_share_enough_to_be_worth_comparing(shell):
    """If the overlap collapsed, every check above would pass on nothing.

    The two tables are written independently and share around two hundred
    English strings; a number far below that means the extraction changed,
    not that the product did.
    """
    # This read `>= 0` while the paragraph above it said the tables share
    # around two hundred strings and that a number far below that means the
    # extraction changed. Both sentences were in the same docstring, and only
    # one of them was in the assertion. It is 216, 214 and 212.
    shared = _shared_with_console(shell)
    assert len(shared) >= ratchets.floor(
            f"table.shared_with_console.{shell}"), (
        f"{shell}: only {len(shared)} English strings are held by both the "
        "console table and this shell's, which is too few to conclude "
        "anything from — check the parse before the product")
