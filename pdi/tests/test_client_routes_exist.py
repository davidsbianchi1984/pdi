"""Every path PDI's clients call must resolve to a route that exists.

This guard exists because of a bug in a sibling. QRME's community wall shipped
its like, comment and share buttons dead: the console asked for `/post/{id}/…`
where only `/posts/{id}/…` is mapped, the backend tests passed because they used
the reachable form, and the console compiled because a template literal is only
a string. Nobody was comparing the two halves.

PDI's surface is the smallest of the three and its exposure is the same in kind.
The console is a thin vault viewer, but the three native shells reach a couple of
dozen routes each in Swift, Kotlin and C#, where `native.yml` proves they
*compile* and cannot say whether they *resolve*. For a vault that matters more
rather than less: a dead button on a seal or a key rotation is not a cosmetic
failure.

Extraction and matching live in :mod:`pdi.tests.clientpaths`, byte-identical
with qrme's and jim-mini's copies.
"""

from __future__ import annotations

from pdi.api import app

from . import clientpaths
from .clientpaths import CONSOLE, NATIVE, normalise, paths

# PDI's console is deliberately thin, so its floor is low; the shells carry the
# real surface. Both are here to catch a pattern that has stopped matching, not
# to demand growth.
_MIN_CONSOLE_PATHS = 3
_MIN_NATIVE_PATHS = 15


def test_every_console_path_reaches_a_route():
    missing = clientpaths.unresolved(app, CONSOLE)
    assert not missing, (
        "the console builds these paths and no route accepts them:\n  "
        + "\n  ".join(missing)
        + "\n(a 404 the user meets as a button that does nothing)"
    )


def test_every_native_path_reaches_a_route():
    """All three shells reported together, with the platform named.

    A path added to two shells and mistyped in the third is the likely shape of
    this failure, and the message should say which one drifted.
    """
    missing: list[str] = []
    for lang in NATIVE:
        for line in clientpaths.unresolved(app, lang):
            missing.append(f"[{lang.name}] {line}")
    assert not missing, (
        "the native shells build these paths and no route accepts them:\n  "
        + "\n  ".join(missing)
    )


def test_every_surface_is_actually_being_scanned():
    """A guard on the guard.

    An extraction pattern that silently matches nothing turns this file into a
    test that always passes — the worst kind, because the coverage it claims
    reads exactly like the coverage it has.
    """
    counted = {CONSOLE.name: len(paths(CONSOLE))}
    counted.update({lang.name: len(paths(lang)) for lang in NATIVE})
    floors = {CONSOLE.name: _MIN_CONSOLE_PATHS}
    floors.update({lang.name: _MIN_NATIVE_PATHS for lang in NATIVE})
    thin = {k: v for k, v in counted.items() if v < floors[k]}
    assert not thin, (
        f"suspiciously few paths extracted: {thin} — the literal or "
        f"interpolation pattern for that language has probably stopped "
        f"matching. All counts: {counted}"
    )


def test_an_interpolated_query_does_not_truncate_the_path():
    """The extractor's own blind spot, pinned.

    An earlier version of this check cut a literal at its first interpolation
    whenever a query followed, which leaves a bare prefix — one that resolves
    for the wrong reason and takes the real tail with it. PDI has no path of that
    shape today; the fixtures are the siblings' live ones, kept here so the three
    copies of the extractor cannot drift apart silently.
    """
    assert normalise("/vault/${id}/records?limit=${n}", CONSOLE) == (
        "/vault/x/records"
    )
    assert normalise('/vault/${id}/feed${all ? "?all=true" : ""}', CONSOLE) == (
        "/vault/x/feed"
    )
    assert normalise("/health?verbose=${v}", CONSOLE) == "/health"
