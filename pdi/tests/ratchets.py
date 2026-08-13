"""One home for the numbers that say *the reader is still reading*.

## Where this came from

Two rounds running found the same defect in two different instruments, and
0.58.9 closed by naming the general case rather than the instance: a floor
written when the surface was small, never raised as the surface grew. The
route reader's floor was set when the console was the only client. The
localizer's was ten, against nine hundred and forty-five.

Both were fixed one file at a time. This is the sweep, and the sweep needed a
convention before it needed code, because a floor is spelled a dozen ways —
`assert len(found) > 20`, `assert total >= 40`, a `FLOORS` tuple, a bare
`_MIN_PATHS`. Nothing could walk them all and ask the only question that
matters about a floor:

    asked     is the number satisfied
    mattered  is the number still near what it measures

## What a Ratchet is

A floor plus **the way to measure the same quantity now**. That second half is
the whole convention: a number with no attached measurement cannot be audited,
which is why 58 of them in this product, across 29 files, had never been
compared against anything.

Registering one has three effects. The number lives in one place instead of
inside an assertion. `test_a_floor_is_within_sight_of_what_it_measures.py`
checks it against reality every run. And it leaves the unregistered-floor
backlog, which only shrinks.

## What the sweep found on its first run

What the same standard finds here is not quite the same picture, and the
difference is the interesting part:

    l10n asked, per shell        10 against 48-62        ratio 0.19
    l10n held, per shell         10 against 51-64        ratio 0.18
    path literals, all surfaces  40 against 183          ratio 0.22
    console call sites          100 against 121          ratio 0.83  held
    native call sites            20 against 35-36        ratio 0.57  held

Two of those rows passed, and this is the product where they would. The
native floor of twenty is the one `test_the_console_is_a_client_too.py`
explained in its own docstring: it was set low deliberately *because the three
products' shells differ by a factor of three in size*, and this is the small
one — PDI's whole API is thirty-four bindings, so twenty against thirty-five
is a real floor.

The same literal in QRME holds against four hundred and thirty. **One number
written to work in three repositories is a number calibrated for whichever of
them was smallest**, which means it is honest here and decoration there, and
nothing in either repository could tell the difference because neither had the
measurement attached.

That is why these live per product, measured per product, and not in a shared
constant.

## The floors are ratchets, not targets

Each records what its reader reaches today, set at roughly four-fifths. Raising
one when the surface grows is ordinary. Lowering one is a deliberate edit that
shows up in a diff, and the only honest reason is a surface that genuinely got
smaller.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Ratchet:
    """A floor, and how to read the same quantity now.

    `measure` is deliberately a callable rather than a recorded number. A
    recorded number would go stale in exactly the way this file exists to
    catch — it would be a second floor needing its own audit.
    """

    name: str
    floor: int
    measure: Callable[[], int]
    why: str


def _l10n(shell: str, half: str) -> Callable[[], int]:
    def go() -> int:
        from . import test_a_shell_asks_for_a_key_it_has as m
        return len((m._asked if half == "asked" else m._held)(shell))
    return go


def _calls(lang: str) -> Callable[[], int]:
    def go() -> int:
        from . import clientpaths
        return len(clientpaths.calls(getattr(clientpaths, lang.upper())))
    return go


def _route_table() -> int:
    from pdi.api import app

    from . import clientpaths
    return len(clientpaths.all_routes(app))


def _path_literals() -> int:
    from . import clientpaths
    from .test_the_extractor_knows_every_call_shape import SURFACES
    return sum(len(clientpaths.paths(lang)) for lang in SURFACES.values())


def _console_files() -> int:
    from .test_a_value_in_a_script_is_not_markup import console_files
    return len(console_files())


def _markup_strings() -> int:
    from .test_a_page_never_prints_what_it_was_given import scanned
    return scanned()


def _erase_planted() -> int:
    from .test_an_erase_is_measured_against_the_schema import plantable
    return plantable()


def _erase_scoped() -> int:
    from .test_an_erase_is_measured_against_the_schema import scoped_tables
    return len(scoped_tables())


def _route_shapes() -> int:
    from .test_a_screen_expects_the_shape_the_route_returns import route_shapes
    return len(route_shapes())


def _calls_typed() -> int:
    from .test_a_screen_expects_the_shape_the_route_returns import calls
    return len(calls())


def _guard_names() -> int:
    from .test_the_three_suites_ask_the_same_questions import TESTS, guard_names
    return len(guard_names(TESTS))


def _files_swept() -> int:
    from .test_a_floor_is_within_sight_of_what_it_measures import parsed_files
    return parsed_files()


#: The registry. Every entry replaced a bare literal inside an assertion; the
#: assertion now reads its number from here, which is what takes it out of the
#: unregistered backlog.
RATCHETS: tuple[Ratchet, ...] = (
    Ratchet("l10n.asked.ios", 120, _l10n("ios", "asked"),
            "screens on the iPhone that call the localizer"),
    Ratchet("l10n.asked.android", 125, _l10n("android", "asked"),
            "screens on Android that call the localizer"),
    Ratchet("l10n.asked.windows", 130, _l10n("windows", "asked"),
            "screens on the desktop that call the localizer"),
    Ratchet("l10n.held.ios", 130, _l10n("ios", "held"),
            "rows in the iPhone's own L10n table"),
    Ratchet("l10n.held.android", 135, _l10n("android", "held"),
            "rows in Android's own L10n table"),
    Ratchet("l10n.held.windows", 140, _l10n("windows", "held"),
            "rows in the desktop's own L10n table"),
    Ratchet("route.calls.console", 95, _calls("console"),
            "call sites the route audit reads out of the console"),
    Ratchet("route.calls.ios", 45, _calls("ios"),
            "call sites the route audit reads out of the iPhone shell"),
    Ratchet("route.calls.android", 45, _calls("android"),
            "call sites the route audit reads out of the Android shell"),
    Ratchet("route.calls.windows", 45, _calls("windows"),
            "call sites the route audit reads out of the desktop shell"),
    Ratchet("route.table", 110, _route_table,
            "routes reachable by walking the included routers"),
    Ratchet("extractor.path_literals", 254, _path_literals,
            "path literals found across all four surfaces"),
    Ratchet("console.source_files", 19, _console_files,
            "TypeScript sources the console sink sweep reads"),
    Ratchet("console.calls_typed", 90, _calls_typed,
            "console calls that declare the shape they expect back"),
    Ratchet("erase.tables_planted", 14, _erase_planted,
            "tables this suite can put a probe row into"),
    Ratchet("erase.scoped_tables", 16, _erase_scoped,
            "tables the schema scopes to a single tenant"),
    Ratchet("route.declared_shapes", 105, _route_shapes,
            "routes whose answer is decisively a list or an object"),
    Ratchet("markup.strings_scanned", 8, _markup_strings,
            "f-strings in this package that build markup"),
    Ratchet("suite.guard_names", 560, _guard_names,
            "test functions this suite declares"),
    Ratchet("sweep.files_parsed", 78, _files_swept,
            "test files the bare-floor sweep can read"),
)

_BY_NAME = {r.name: r for r in RATCHETS}


def floor(name: str) -> int:
    """The registered floor, by name.

    Assertions call this instead of carrying a literal. A name that is not
    registered is a mistake worth failing on rather than defaulting past — a
    silent default here would be a floor of nothing, which is the whole
    subject of this file.
    """
    try:
        return _BY_NAME[name].floor
    except KeyError:
        raise KeyError(
            f"no ratchet named {name!r}; registered: "
            + ", ".join(sorted(_BY_NAME))) from None
