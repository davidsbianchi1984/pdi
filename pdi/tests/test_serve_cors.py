"""``python -m pdi serve`` must answer the packaged console.

Ported from the sibling products at 0.59.1, where a sweep of test-function
names across the three suites found this file present in two of them and
absent here — and the code it guards absent with it.

## What was actually broken

The frozen backend in `packaging/backend_entry.py` has always set
``PDI_CORS_ORIGINS=*``, so the **installed** desktop app worked. ``serve`` —
the documented from-source path, and what `python -m pdi serve` gives you —
set nothing. With CORS closed the console's every request dies as "Failed to
fetch", and the failure is invisible to any test that calls the app in-process
because CORS is a browser rule, not a server one.

Measured over HTTP before the fix, with the console's origin on the request:

    OPTIONS /terms   →  405, no access-control headers at all
    GET     /terms   →  200, no access-control-allow-origin

and after:

    OPTIONS /terms   →  200, access-control-allow-origin: *

    asked     does this product answer its own routes
    mattered  can the console the installer ships reach them

## Loopback only, and that half matters more here than anywhere

A non-loopback bind is somebody serving a vault to a network. This is the last
of the three products where CORS should open itself by default, so the same
rule the siblings carry is carried here: loopback binds only, ``--no-cors``
restores the closed posture, and an explicit ``PDI_CORS_ORIGINS`` is never
overwritten.
"""

from __future__ import annotations

import pdi.__main__ as launcher


def _serve(monkeypatch, argv):
    """Run ``main(argv)`` with uvicorn.run captured instead of blocking."""
    calls: dict = {}

    def fake_run(app, host, port):
        calls["app"], calls["host"], calls["port"] = app, host, port

    import uvicorn

    monkeypatch.setattr(uvicorn, "run", fake_run)
    monkeypatch.delenv("PDI_CORS_ORIGINS", raising=False)
    assert launcher.main(argv) == 0
    assert calls["app"] == "pdi.api:app"
    return calls


def test_loopback_serve_defaults_cors_open_for_the_console(monkeypatch):
    _serve(monkeypatch, ["serve"])
    import os

    assert os.environ.get("PDI_CORS_ORIGINS") == "*"


def test_no_cors_keeps_the_closed_posture(monkeypatch):
    _serve(monkeypatch, ["serve", "--no-cors"])
    import os

    assert os.environ.get("PDI_CORS_ORIGINS") is None


def test_a_non_loopback_bind_never_defaults_cors_open(monkeypatch):
    _serve(monkeypatch, ["serve", "--host", "0.0.0.0"])
    import os

    assert os.environ.get("PDI_CORS_ORIGINS") is None


def test_an_explicit_allowlist_is_never_overwritten(monkeypatch):
    import os

    monkeypatch.setenv("PDI_CORS_ORIGINS", "https://example.test")

    def fake_run(app, host, port):
        pass

    import uvicorn

    monkeypatch.setattr(uvicorn, "run", fake_run)
    assert launcher.main(["serve"]) == 0
    assert os.environ["PDI_CORS_ORIGINS"] == "https://example.test"
