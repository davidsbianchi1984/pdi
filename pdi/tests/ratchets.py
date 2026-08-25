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


def _tenant_tables_read() -> int:
    from .test_the_other_tenants_shelf import _tenant_tables
    return len(_tenant_tables())


def _tenant_statements() -> int:
    from . import test_the_other_tenants_shelf as m
    import ast, re
    tables = m._tenant_tables()
    count = 0
    for path in sorted(m.PKG.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr in ("execute", "executemany")
                    and node.args):
                for sql in m._branches(node.args[0]):
                    if sql and any(re.search(rf"\b{t}\b", sql)
                                   for t in tables):
                        count += 1
                        break
    return count


def _files_swept() -> int:
    from .test_a_floor_is_within_sight_of_what_it_measures import parsed_files
    return parsed_files()


def _nav_tabs() -> int:
    from .test_a_key_with_no_row_reads_as_itself import _tab_ids
    return len(_tab_ids())

#: The registry. Every entry replaced a bare literal inside an assertion; the
#: assertion now reads its number from here, which is what takes it out of the
#: unregistered backlog.

def _literal_refusals() -> int:
    """Refusal sentences written as a plain string, as the classifier counts
    them now. The floor is here rather than inside the assertion because a
    number in an assertion is a number nothing compares against what it
    measures — and this one guards the walk that every other refusal check
    is built on."""
    from pathlib import Path

    from .test_the_vault_refuses_in_one_language import REPO, _refusals
    return len(_refusals(REPO / "pdi")["literal"])


def _translated_refusals() -> int:
    """Rows in the hand-translated refusal table.

    Its assertion carried a literal 8 while the table held 84 — a floor at a
    tenth of what it measures, which answers "is the number satisfied" every
    run and would not notice the table being gutted. Registered so the
    comparison happens rather than being assumed.
    """
    from pdi import i18n
    return len(i18n._REFUSALS)


# -- the shells, the shapes, and the release table --------------------------
#
# Measured here rather than carried over from a sibling. The README pair is
# the shared-literal case this file's header predicted, and it is the same
# number in two products: a floor of 40 against 254 history rows here and 256
# in JIM-mini. Neither was calibrated for this table; both were written once
# and never asked again.


def _shell_files(kind: str):
    def go() -> int:
        from . import test_the_shells_still_parse as m
        return len(getattr(m, kind))
    return go


def _xaml_named() -> int:
    from .test_the_shells_still_parse import XAML, _XNAME
    return sum(len(set(_XNAME.findall(p.read_text(encoding="utf-8"))))
               for p in XAML)


def _xaml_handlers() -> int:
    from .test_the_shells_still_parse import XAML, _handlers
    return _handlers(XAML)[0]


def _xaml_driveable() -> int:
    from .test_the_shells_still_parse import XAML, _undriveable
    return _undriveable(XAML)[0]


def _swift_structs() -> int:
    from .test_the_shape_the_swift_client_expects import _structs
    return len(_structs())


def _swift_fields() -> int:
    from .test_the_shape_the_swift_client_expects import _structs
    return sum(len(f) for f in _structs().values())


def _swift_bindings() -> int:
    from .test_the_shape_the_swift_client_expects import _bindings
    return len(_bindings())


def _console_shapes() -> int:
    from .test_the_shape_the_console_expects import _shapes
    return len(_shapes())


def _console_shape_fields() -> int:
    from .test_the_shape_the_console_expects import _shapes
    return sum(len(f) for f in _shapes().values())


def _console_gets() -> int:
    from .test_the_shape_the_console_expects import _gets
    return len(_gets())


def _readme_rows() -> int:
    from .test_the_readme_says_what_shipped import _rows
    return len(_rows())


def _readme_released() -> int:
    from .test_the_readme_says_what_shipped import _released
    return len(_released())


# -- the wire and the console's bindings ------------------------------------
#
# Both were holding roughly a quarter of what they measure. `wire.declared` at
# 45 against 175 is the vault's version of the widest gap this sweep found in
# the guardian: the names four clients agree on, floored at a number written
# when there were far fewer of them.


def _wire_declared() -> int:
    from .test_one_name_one_type_on_the_wire import _declared
    return len(_declared())


def _client_bindings() -> int:
    from .test_the_shape_the_client_expects import _bindings
    return len(_bindings())


def _validation_messages() -> int:
    from pdi import i18n
    return len(i18n._VALIDATION)


# -- what each receiver declares --------------------------------------------
#
# `RECEIVERS` already carries a floor per receiver, and
# `test_the_scan_reads_every_receiver` uses it — for the *reached* count. The
# line above it floored the *declared* count at a blanket 5, for receivers
# holding between eight and one thousand two hundred and fifty-two members.
#
#     asked     did the scan read this receiver
#     mattered  did it read enough of it to be reading it at all
#
# The number was in the data the whole time; the tuple's own floor sits one
# line below, doing this job for the other half of the check. Two quantities,
# one of them measured per receiver and one of them guessed at once for all of
# them — which is the same defect as a value handed to a function that never
# reads it, and this estate has now found that shape four times in a day.


def _receiver_declared(label: str):
    def go() -> int:
        from . import test_the_member_that_isnt_there as m
        for row in m.RECEIVERS:
            if row[0] == label:
                return len(m._declared(row[1], m.REPO / row[2]))
        raise KeyError(f"no receiver labelled {label!r}")
    return go


# -- the guards on the guards -----------------------------------------------
#
# Every floor below stands under a docstring that says, in its own file's
# words, that a reader which stopped reading would report a clean result. Four
# of them carried the same literal in all three products, and three carried
# some version of the same sentence:
#
#     Thresholds are kept low enough to hold in all three repositories, which
#     have consoles of very different sizes.
#
# This file's header diagnosed that sentence once already — a true sentence
# about why the number is small and a false one about what it holds. It was
# fixed in one file and never carried anywhere else. This is the smallest of
# the three consoles, the one those literals were calibrated for, and twenty
# is still a seventh of the 141 bindings here.
#
#     asked     does one number hold in all three products
#     mattered  does it hold anything in any of them
#
# Three more sat inside a loop, where one literal has to be four-fifths of
# three surfaces at once and settles for being four-fifths of none. Those are
# registered per surface.


def _console_bindings() -> int:
    from .test_a_binding_is_not_a_door import _bindings
    return len(_bindings())


def _api_functions(shell: str):
    def go() -> int:
        from .test_a_native_binding_is_not_a_door_either import _api_functions
        return len(_api_functions(shell))
    return go


def _path_segments() -> int:
    from .test_error_report_carries_nothing_private import _segments
    return len(_segments())


def _scanned_controls() -> int:
    from .test_a_form_that_asks_for_it_has_a_label_for_it import (
        _scanned_controls as go)
    return go()


def _shell_shown(shell: str):
    def go() -> int:
        from .test_a_shell_does_not_print_what_it_translated import (
            SHELLS, _shown)
        return len(_shown(SHELLS[shell]))
    return go


def _shell_fragments(shell: str):
    def go() -> int:
        from .test_a_shell_does_not_print_what_it_translated import (
            SHELLS, _fragments)
        return len(_fragments(SHELLS[shell]))
    return go


def _body_matched(slug: str):
    def go() -> int:
        from . import test_the_body_the_native_clients_send as m
        for client, short in m.SLUG.items():
            if short == slug:
                return m._writes_meeting_a_model(client)
        raise KeyError(f"no native client slugged {slug!r}")
    return go


def _egress_sites() -> int:
    from .test_nothing_leaves_the_host import _egress_sites
    return len(_egress_sites())


def _android_reads() -> int:
    from .test_the_keys_the_android_client_reads import _reads
    return len(_reads())


def _android_read_keychars() -> int:
    from .test_the_keys_the_android_client_reads import _reads
    return sum(len(k) for _, k in _reads())


RATCHETS: tuple[Ratchet, ...] = (
    Ratchet("console.bindings_scanned", 112, _console_bindings,
            "the bindings the console scan parses out of api.ts"),
    Ratchet("native.api_functions.ios", 113, _api_functions("ios"),
            "the calls the iPhone's ApiClient declares"),
    Ratchet("native.api_functions.windows", 108, _api_functions("windows"),
            "the calls the desktop's ApiClient declares"),
    Ratchet("native.api_functions.android", 112, _api_functions("android"),
            "the calls Android's ApiClient declares"),
    Ratchet("route.path_segments", 83, _path_segments,
            "the literal path segments this product's routes contribute"),
    Ratchet("form.controls_scanned", 4215, _scanned_controls,
            "the characters of form control the screen scan matches"),
    Ratchet("shell.shown.ios", 427, _shell_shown("ios"),
            "the literals the iOS scan finds on any screen"),
    Ratchet("shell.shown.android", 388, _shell_shown("android"),
            "the literals the Android scan finds on any screen"),
    Ratchet("shell.shown.windows", 1088, _shell_shown("windows"),
            "the literals the Windows scan finds on any screen"),
    Ratchet("shell.fragments.ios", 5, _shell_fragments("ios"),
            "the fragments split out of the iOS table's slotted rows"),
    Ratchet("shell.fragments.android", 5, _shell_fragments("android"),
            "the fragments split out of the Android table's slotted rows"),
    Ratchet("shell.fragments.windows", 7, _shell_fragments("windows"),
            "the fragments split out of the Windows table's slotted rows"),
    Ratchet("native.body_matched.windows", 32, _body_matched("windows"),
            "the desktop client's writes that meet a declared model"),
    Ratchet("native.body_matched.ios", 31, _body_matched("ios"),
            "the iPhone client's writes that meet a declared model"),
    Ratchet("native.body_matched.android", 31, _body_matched("android"),
            "the Android client's writes that meet a declared model"),
    # Registered late, and from outside the backlog. This one floored at four
    # against eleven — a ratio the sweep would have flagged on sight — and the
    # sweep never saw it, because it ignores floors under `SMALLEST_FLOOR` and
    # four is under five. That cutoff keeps the backlog free of the threes and
    # fours that are data checks rather than floors, and it buys that by being
    # blind to the small floors that are real. There are 113 comparisons under
    # five across the three suites; this is the one that was measured.
    Ratchet("host.egress_sites", 8, _egress_sites,
            "the calls in this package that can put bytes on a wire"),
    Ratchet("android.reads", 46, _android_reads,
            "the key reads the Android extractor finds"),
    Ratchet("android.read_keychars", 103, _android_read_keychars,
            "the characters across those keys, as a shape check on them"),
    Ratchet("receiver.declared.ios.state", 6, _receiver_declared("ios/state"),
            "the members ios/state declares"),
    Ratchet("receiver.declared.ios.api", 280, _receiver_declared("ios/api"),
            "the members ios/api declares"),
    Ratchet("receiver.declared.ios.theme", 12, _receiver_declared("ios/theme"),
            "the members ios/theme declares"),
    Ratchet("receiver.declared.android.state", 8, _receiver_declared("android/state"),
            "the members android/state declares"),
    Ratchet("receiver.declared.android.api", 290, _receiver_declared("android/api"),
            "the members android/api declares"),
    Ratchet("receiver.declared.android.theme", 14, _receiver_declared("android/theme"),
            "the members android/theme declares"),
    Ratchet("receiver.declared.windows.state", 7, _receiver_declared("windows/state"),
            "the members windows/state declares"),
    Ratchet("receiver.declared.windows.api", 197, _receiver_declared("windows/api"),
            "the members windows/api declares"),
    Ratchet("wire.declared", 140, _wire_declared,
            "every name declared on the wire, across all four clients"),
    Ratchet("console.bindings", 51, _client_bindings,
            "the console screens' bindings to route shapes"),
    Ratchet("i18n.validation_messages", 8, _validation_messages,
            "the validation sentences with a row in every language"),
    Ratchet("shells.swift_files", 16, _shell_files("SWIFT"),
            "the Swift sources the shell parser reads"),
    Ratchet("shells.kotlin_files", 5, _shell_files("KOTLIN"),
            "the Kotlin sources the shell parser reads"),
    Ratchet("shells.csharp_files", 12, _shell_files("CSHARP"),
            "the C# sources the shell parser reads"),
    Ratchet("shells.xaml_files", 8, _shell_files("XAML"),
            "the XAML screens the markup checks reach"),
    Ratchet("shells.xaml_named", 268, _xaml_named,
            "the named elements across those XAML screens"),
    Ratchet("shells.xaml_handlers", 79, _xaml_handlers,
            "the XAML handlers checked against their code-behind"),
    Ratchet("shells.xaml_driveable", 249, _xaml_driveable,
            "the XAML elements the drive check reaches"),
    Ratchet("swift.structs", 78, _swift_structs,
            "the Swift client's declared shapes"),
    Ratchet("swift.struct_fields", 244, _swift_fields,
            "the fields across the Swift client's shapes"),
    Ratchet("swift.bindings", 48, _swift_bindings,
            "the Swift screens' bindings to those shapes"),
    Ratchet("console.shapes", 30, _console_shapes,
            "the console's declared shapes"),
    Ratchet("console.shape_fields", 203, _console_shape_fields,
            "the fields across the console's shapes"),
    Ratchet("console.gets", 56, _console_gets,
            "the console's read calls"),
    Ratchet("readme.history_rows", 203, _readme_rows,
            "the release history rows the README table carries"),
    Ratchet("readme.released", 207, _readme_released,
            "the releases the CHANGELOG declares"),
    Ratchet("refusals.translated", 84, _translated_refusals,
            "rows in the hand-translated refusal table"),
    Ratchet("refusals.literal", 40, _literal_refusals,
            "refusals written as a plain string — the walk every other\n            refusal check stands on"),
    Ratchet("l10n.asked.ios", 200, _l10n("ios", "asked"),
            "screens on the iPhone that call the localizer"),
    Ratchet("l10n.asked.android", 205, _l10n("android", "asked"),
            "screens on Android that call the localizer"),
    Ratchet("l10n.asked.windows", 214, _l10n("windows", "asked"),
            "screens on the desktop that call the localizer"),
    Ratchet("l10n.held.ios", 210, _l10n("ios", "held"),
            "rows in the iPhone's own L10n table"),
    Ratchet("l10n.held.android", 220, _l10n("android", "held"),
            "rows in Android's own L10n table"),
    Ratchet("l10n.held.windows", 230, _l10n("windows", "held"),
            "rows in the desktop's own L10n table"),
    Ratchet("route.calls.console", 95, _calls("console"),
            "call sites the route audit reads out of the console"),
    Ratchet("route.calls.ios", 77, _calls("ios"),
            "call sites the route audit reads out of the iPhone shell"),
    Ratchet("route.calls.android", 77, _calls("android"),
            "call sites the route audit reads out of the Android shell"),
    Ratchet("route.calls.windows", 77, _calls("windows"),
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
    # 15 against 20 and 60 against ~112 — the same four-fifths posture as
    # console.nav_tabs below: room for legitimate removal, none for a
    # parser that quietly stopped matching.
    Ratchet("tenant.scoped_tables_read", 15, _tenant_tables_read,
            "tables the schema scopes to a tenant, read from db.py by the "
            "isolation guard"),
    Ratchet("tenant.statements_scanned", 105, _tenant_statements,
            "SQL statements on tenant-scoped tables the isolation guard "
            "can parse"),
    # 12 against 15 — four-fifths, and not the 15 this was first written
    # with. A floor set to exactly what is there today is one that fails on
    # the day somebody legitimately removes a tab, which teaches people to
    # edit the floor rather than read it.
    Ratchet("console.nav_tabs", 12, _nav_tabs,
            "tabs the console's navigation declares — the floor under "
            "the check that every one of them has a label"),
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
