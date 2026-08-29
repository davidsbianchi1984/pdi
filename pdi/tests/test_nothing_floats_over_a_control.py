"""The vault light, sitting on the menu — and the rule that said it wasn't.

    asked     does the console render
    mattered  can a person reach every control on it

## Two field reports, both answered, neither fixed

The first was a photograph of this beta on a phone: the vault light
squarely over the first three tabs of the bottom bar, taking the taps.

    "It seems to be blocking the PDI menus"

The second was the same photograph one state along:

    "Same thing with the small green circle when minimized"

Both were answered in the same round, in a rule that lifted the light off
the bar and shrank the minimized state to a true dot. The rule was written
inside the layout media block near the top of the stylesheet. The base
`.vault-light { position: fixed; left: 22px; bottom: 22px }` was declared
two hundred lines below it.

Same specificity. Later wins. **Neither answer ever applied.** Both reports
were closed against a fix a person reading the file could see and a browser
could not.

## Why the guard next door passed

`test_the_light_sat_on_the_menu` reads every phone block, finds a rule that
clears the bar, and says so. It asks whether a lifting rule *exists*. It
existed. What nobody asked was whether the browser uses it.

    asked     is there a rule that lifts the light off the bar
    mattered  is that the rule the browser uses

So this file reads the stylesheet for what *wins*, not for what it says. A
phone override declared before the base rule it overrides is not a fix; it
is a comment that reads like one, which is worse than nothing, because the
next person believes it and closes the report.

## And the number

`76px` was a guess about how tall the bar is, and the bar is as tall as its
labels. Every label is translated into ten languages and the longer ones
wrap to two lines, which pushes it past 76. So the bar measures itself and
publishes `--tabbar-h`; the guess survives only as what `:root` declares
for a browser with no ResizeObserver, which is the case it was written for.

## Deliberately narrow

It does not judge whether the console is well laid out — a guard that tried
would fail on every deliberate overlay and be switched off within a month.
It holds one line: a float clears the bar by measuring it, with a rule that
actually applies.
"""

from __future__ import annotations

import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
CSS = REPO / "app" / "src" / "styles.css"
APP = REPO / "app" / "src" / "App.tsx"

#: The floating things, by class. Each is `position: fixed`, and each has
#: to clear the bottom bar on a phone.
FLOATS = (".vault-light", ".vl-dot")


def _blocks() -> list[tuple[int, str]]:
    """Every `max-width: 760px` block, with where in the file it starts."""
    text = CSS.read_text(encoding="utf-8")
    out, at = [], 0
    while True:
        start = text.find("@media (max-width: 760px) {", at)
        if start < 0:
            return out
        depth, i = 0, start
        while i < len(text):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        out.append((start, text[start:i + 1]))
        at = i + 1


def _winning_rule(name: str) -> tuple[int, str]:
    """The phone rule for `name` that the browser actually uses: the last
    one declared, since every rule here carries the same specificity."""
    found = [(at, block) for at, block in _blocks() if name + " " in block
             or name + "," in block or name + "\n" in block]
    assert found, f"no phone rule for {name} at all"
    at, block = found[-1]
    rule = block[block.index(name):]
    return at, rule[:rule.index("}")]


def _base_at(name: str) -> int:
    """Where the desktop rule for `name` is declared."""
    text = CSS.read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith(name + " {") or line.startswith(name + ","):
            return text.index(line)
    raise AssertionError(f"no base rule for {name}")


def _phone_block() -> str:
    """Every phone block joined — for the presence checks below."""
    return "\n".join(block for _, block in _blocks())


def test_every_floating_thing_clears_the_bar_on_a_phone():
    """A float with no phone rule keeps its desktop offset, and on a phone
    the bottom of the screen is the tab bar."""
    block = _phone_block()
    adrift = [name for name in FLOATS if name not in block]
    assert not adrift, (
        f"{len(adrift)} floating element(s) have no phone rule and keep "
        f"their desktop offset: {adrift}. On a phone the bottom of the "
        "screen is the tab bar, so a float placed against the bottom on a "
        "desktop is placed against the menu here.")


def test_the_phone_rule_is_declared_after_the_rule_it_overrides():
    """The one that would have caught it.

    `.vault-light` had a phone rule lifting it clear of the tab bar, and
    the base `bottom: 22px` was declared two hundred lines later. Same
    specificity, later wins, so the lift never applied — while the comment
    above it quoted the field report it was answering.
    """
    late = []
    for name in FLOATS:
        try:
            base = _base_at(name)
        except AssertionError:
            continue
        at, _ = _winning_rule(name)
        if at < base:
            late.append(f"{name} (phone rule at {at}, base at {base})")
    assert not late, (
        "these phone rules are declared BEFORE the rule they override, so "
        "the browser uses the desktop one and the override does nothing:\n"
        "    " + "\n    ".join(late)
        + "\n  Same specificity means later wins. Move them below the base "
          "rules — a rule that cannot win is a comment that reads like a fix.")


def test_the_clearance_is_measured_rather_than_guessed():
    """`76px` was a guess about the bar's height. The bar is as tall as its
    labels, and its labels are translated into ten languages."""
    for name in FLOATS:
        _, rule = _winning_rule(name)
        assert "--tabbar-h" in rule, (
            f"{name} clears the bar by a hard-coded number rather than by "
            "`--tabbar-h`. That number is a guess about how tall the bar "
            "is; the bar is as tall as its labels, and a language with "
            "longer words wraps them sooner.")


def test_the_bar_actually_publishes_its_height():
    """The custom property is only worth reading if something writes it."""
    app = APP.read_text(encoding="utf-8")
    assert "--tabbar-h" in app, (
        "nothing sets --tabbar-h, so every float silently falls back to "
        "the guess this round replaced")
    assert "ResizeObserver" in app, (
        "the height is set once rather than observed — the bar's height "
        "changes when the language changes and when the viewport turns")
    assert re.search(r"ref=\{bar\}", app), (
        "the observer has nothing to watch: the sidebar carries no ref")


def test_the_fallback_is_the_number_it_replaced():
    """A browser with no ResizeObserver is exactly the case the old guess
    was written for, so that is what it falls back to — not zero, which
    would drop every float onto the bar.

    The default lives in `:root` rather than being spelled as a
    `var(--tabbar-h, 76px)` fallback at each place that reads it: a number
    repeated inside `calc()` is one nobody can find to change."""
    root = re.search(r":root\s*\{(.*?)\}", CSS.read_text(encoding="utf-8"), re.S)
    assert root, "the stylesheet has no :root block"
    assert re.search(r"--tabbar-h\s*:\s*76px", root.group(1)), (
        "the fallback is missing or different — without one, a browser "
        "that cannot observe the bar puts the vault light on the menu")
    assert "var(--tabbar-h)" in _phone_block(), (
        "the phone rule no longer reads the published height, so the bar "
        "measuring itself changes nothing")
