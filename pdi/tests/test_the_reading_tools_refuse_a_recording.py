"""The reading tools refuse a recording, by name of the door that hears it.

`fetch.listen` was built because a plain fetch of an .mp4 seals compressed
video where a person hears a sentence — the ears module's own first
paragraph. The planner learned to route media fragments to the listening
tool, and the direct doors never did: a `fetch.url` or `fetch.render`
called straight at a recording still stripped markup from binary and
sealed the mojibake as a capture.

    asked     can the readers tell a page from a recording
    mattered  a capture of noise wears the same seal as a capture of words

The suffix list is the same canonical one the qrme briefcase and lookout
read — ported, not reinvented, so the two stacks call the same bytes a
recording — and the refusal names `fetch.listen`, because "I cannot"
without "here is what can" is the menu problem inside a tool registry.
"""

from __future__ import annotations

import pytest

from pdi import ears, resident


def test_the_suffix_list_is_the_canonical_one():
    assert ears.looks_like_recording("https://x.example/a/clip.mp4")
    assert ears.looks_like_recording("https://x.example/memo.M4A?sig=1")
    assert ears.looks_like_recording("https://x.example/talk.ogg#t=10")
    assert not ears.looks_like_recording("https://x.example/page.html")
    # A page that merely contains a player is still a page.
    assert not ears.looks_like_recording("https://x.example/watch?v=clip.mp4")


@pytest.mark.parametrize("tool", ["fetch.url", "fetch.render"])
def test_the_direct_doors_refuse_and_name_the_listener(tool):
    run = resident.TOOLS[tool]["run"]
    with pytest.raises(resident.ResidentError) as caught:
        run({}, {"url": "https://x.example/episode.mp4"}, {})
    assert "fetch.listen" in str(caught.value)
    assert "recording" in str(caught.value)


def test_the_listener_itself_is_untouched():
    """The guard sits on the readers only — fetch.listen still takes the
    same url (and fails on its own terms when there are no ears, which is
    the standing behavior this test does not re-litigate)."""
    spec = resident.TOOLS["fetch.listen"]
    assert spec["run"] is not None
