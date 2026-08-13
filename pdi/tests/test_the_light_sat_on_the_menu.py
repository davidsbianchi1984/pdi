"""Nothing the console pins to the bottom of the glass may cover the menu.

## The report

    "It seems to be blocking the PDI menus"

A photograph of the beta on a phone: the vault light — the pill that reads
*vault answering · v0.68.0* — sitting squarely over the first three tabs of
the bottom bar. Overview, Tenants and half of Bridges were under it. Not
dimmed, not behind: on top, and taking the taps.

## Why nothing caught it

Both halves were correct on their own. The light is `position: fixed` at
`bottom: 22px`, which on a desktop is empty page margin. The sidebar becomes
a bottom bar under `@media (max-width: 760px)`, which is the ordinary way to
put navigation on a phone. Neither rule knows about the other, and no test
in this suite had ever read the stylesheet — the console's guards all ask
what a screen *says*, and this was a question about where a thing *sits*.

    asked     is every screen wired, translated and reachable
    mattered  can the person's thumb reach the tab under the light

## What this checks

The bar's height is read out of the stylesheet rather than written here, so
the clearance tracks the bar: if somebody makes the tap targets taller, this
recomputes and the light has to move with them. Anything fixed to the bottom
of the viewport must, inside the mobile block, clear that height.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
CSS = REPO / "app" / "src" / "styles.css"

#: The breakpoint at which the sidebar becomes a bottom bar.
_MOBILE_HEAD = "@media (max-width: 760px) {"


def _stylesheet() -> str:
    """The stylesheet with its comments removed.

    Prose is not a selector, and this file's comments contain commas — the
    first draft split a selector list on them and read half a sentence as a
    rule name.
    """
    return re.sub(r"/\*.*?\*/", "", CSS.read_text(encoding="utf-8"), flags=re.S)


def _braced(text: str, head: str) -> str:
    """The body of a `head { … }` block, counting braces rather than
    stopping at the first `}` — a media query is full of nested rules, and
    the first draft of this guard read one of them and called it the block.
    """
    start = text.index(head) + len(head)
    depth, i = 1, start
    while depth:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    return text[start:i - 1]


def _mobile_block() -> str:
    css = _stylesheet()
    assert _MOBILE_HEAD in css, (
        "the mobile media query is gone from styles.css, so this guard is "
        "reading nothing — find the breakpoint and re-point it")
    return _braced(css, _MOBILE_HEAD)


def _base() -> str:
    """The stylesheet with its media queries removed, so a rule read here is
    the one that applies on a desktop."""
    css = _stylesheet()
    while _MOBILE_HEAD in css:
        body = _braced(css, _MOBILE_HEAD)
        css = css.replace(_MOBILE_HEAD + body + "}", "", 1)
    return re.sub(r"@media[^{]*\{", "", css)


def _rule(block: str, selector: str) -> str | None:
    """Every declaration written for one selector, or None when absent.

    A selector may be written more than once — the light's mobile rules are
    a shared `bottom` and its own `max-width` — so the readings are merged
    rather than taking the first and calling the rest absent.
    """
    found = [m.group(2) for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", block)
             if selector in [s.strip() for s in m.group(1).split(",")]]
    return " ".join(found) if found else None


def _px(declarations: str, prop: str) -> float | None:
    m = re.search(rf"\b{prop}:\s*([^;]+);", declarations)
    if not m:
        return None
    value = m.group(1)
    # `calc(76px + env(safe-area-inset-bottom))` — the safe-area term is a
    # phone's home indicator and only ever adds, so the literal px is the
    # floor of what the rule reserves.
    px = re.search(r"(\d+(?:\.\d+)?)px", value)
    return float(px.group(1)) if px else None


def _bar_height() -> float:
    """What the bottom bar occupies, from the stylesheet's own numbers."""
    block = _mobile_block()
    item = _rule(block, ".nav-item")
    sidebar = _rule(block, ".sidebar")
    assert item and sidebar, (
        "the bottom bar's rules have been renamed — this guard measures the "
        "bar out of `.sidebar` and `.nav-item`, and cannot see them")
    tap = _px(item, "min-height")
    assert tap, ".nav-item no longer declares a min-height to measure"
    pad = re.search(r"padding:\s*(\d+(?:\.\d+)?)px", sidebar)
    assert pad, ".sidebar no longer declares padding to measure"
    # Padding is shorthand: the first number is the top, and the bottom is
    # the same number plus the safe-area inset.
    return tap + 2 * float(pad.group(1))


#: Everything pinned to the bottom of the viewport. A new one is a new row
#: here, which is the point: the question is asked of the class of thing,
#: not of the one that was reported.
BOTTOM_FIXED = (".vault-light", ".vl-dot")


def test_the_stylesheet_still_pins_these_to_the_bottom():
    """The guard on the guard. If the light stopped being fixed — or was
    renamed — every assertion below would pass on an empty reading."""
    css = _base()
    for selector in BOTTOM_FIXED:
        rule = _rule(css, selector)
        assert rule, f"{selector} is not in styles.css any more"
        assert "position: fixed" in rule and _px(rule, "bottom") is not None, (
            f"{selector} is no longer fixed to the bottom of the viewport — "
            "either this list is stale or the light moved, and both want a "
            "person to look")


@pytest.mark.parametrize("selector", BOTTOM_FIXED)
def test_nothing_fixed_to_the_bottom_covers_the_bar(selector):
    """The defect, directly.

    On a phone the navigation *is* the bottom of the screen. Anything the
    console fixes there has to sit above it, or it is a lid on the menu.
    """
    rule = _rule(_mobile_block(), selector)
    assert rule, (
        f"{selector} keeps its desktop `bottom` at the mobile breakpoint, so "
        "it sits on top of the tab bar — the field report that produced this "
        'guard read "It seems to be blocking the PDI menus"')
    bottom = _px(rule, "bottom")
    bar = _bar_height()
    assert bottom is not None and bottom >= bar, (
        f"{selector} sits {bottom}px from the bottom and the tab bar is "
        f"{bar}px tall, so it covers the menu")


def test_the_light_stays_inside_the_glass():
    """A pill wider than the phone pushes the page sideways, which is the
    other way a fixed element takes a screen over."""
    rule = _rule(_mobile_block(), ".vault-light")
    assert rule and "max-width" in rule, (
        "the vault light has no width limit on a phone, so a long backend "
        "version can widen it past the viewport")
