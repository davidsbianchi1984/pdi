"""QRME's agent-lights lesson, applied on arrival rather than re-learned.

The sibling widget vanished silently when its *first* fetch failed — a
field report said so. The vault's light arrives with the fix built in:
one lamp, always on screen, and unreachable is a state it shows (the
unlit dot, retrying on press), never a silent absence.
"""

from __future__ import annotations

import re
from pathlib import Path


def _repo_root() -> Path:
    for d in Path(__file__).resolve().parents:
        if (d / "pyproject.toml").exists():
            return d
    raise RuntimeError("no pyproject.toml above this test")


REPO = _repo_root()
WIDGET = (REPO / "app/src/VaultLight.tsx").read_text(encoding="utf-8")


def test_the_widget_is_mounted_in_the_shell():
    app = (REPO / "app/src/App.tsx").read_text(encoding="utf-8")
    assert "<VaultLight />" in app, (
        "the vault light is no longer part of the shell")


def test_a_failed_first_fetch_leaves_a_dot_not_a_blank():
    m = re.search(r"if \(!health\) \{(.*?)\n  \}", WIDGET, re.S)
    assert m, "VaultLight no longer has a no-health branch to check"
    branch = m.group(1)
    assert "vl-dot-off" in branch, (
        "the no-health branch renders nothing — a first fetch that fails "
        "removes the light from every screen, silently")
    nulls = re.findall(r"^\s*(.*return null.*)$", branch, re.M)
    assert len(nulls) == 1 and "!unreachable" in nulls[0], (
        "the no-health branch returns null on a path other than the "
        "guarded one — the unlit dot is written but unreachable:\n    "
        + "\n    ".join(nulls))


def test_the_failure_is_tracked_not_swallowed():
    assert "setUnreachable(true)" in WIDGET


def test_the_dot_retries_when_pressed():
    m = re.search(r"if \(!health\) \{(.*?)\n  \}", WIDGET, re.S)
    assert m and re.search(r"onClick=\{load\}", m.group(1))


def test_the_light_opens_no_new_door():
    """It reads /health, the open route the version guard already reads —
    nothing new for any client to owe a door for."""
    assert "api.health()" in WIDGET
    assert not re.search(r"req[<(]", WIDGET), (
        "the widget calls the transport directly — that is a new door")
