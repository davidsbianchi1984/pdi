"""Shortening text without lying about it.

The third copy of this in the trio, and deliberately a copy: these are three
repositories with no shared library, the same way each has its own `db.py`
and its own `i18n.py`. What is shared is the ladder — the boundaries and
their order are identical in all three on purpose, because a vault, a coach
and a profile disagreeing about where it is safe to stop would be three
answers to one question.

The finding behind it, first written down in QRME's wall: a cut inside a word
is the one outcome this refuses. The marker is the other half — a whole-word
cut still inverts *"no history of"* — and only the caller knows how to word
that for where the text is going.
"""

from __future__ import annotations

_BREAKS = ("\n\n", "\n", ". ", " ")


def clipped(text: str, cap: int) -> tuple[str, bool]:
    """`(text, was_cut)` — shortened at a boundary, never inside a word."""
    text = (text or "").strip()
    if len(text) <= cap:
        return text, False
    window = text[:cap]
    # Prefer a boundary in the second half so what comes back is not a stub;
    # accept one anywhere rather than break a word. Only a genuinely unbroken
    # run — a URL, an identifier — reaches the raw cut below.
    for floor in (cap // 2, -1):
        for mark in _BREAKS:
            cut = window.rfind(mark)
            if cut > floor:
                return window[:cut].rstrip(), True
    return window.rstrip(), True
