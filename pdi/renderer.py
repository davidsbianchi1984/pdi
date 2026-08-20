"""The deployment's eyes — a page rendered the way a person meets it.

The plain fetch (:func:`pdi.resident._fetch_text`) reads what the server
sends. For a JavaScript application that is an empty shell and a title —
roughly a dozen characters standing where a whole console is — and a
"complete scrape" built on it completely scrapes nothing.

    asked     what does the page say
    mattered  what a person would see, not what the server sent first

Where the eyes live is configuration, not code: ``PDI_RENDERER_URL`` names
a rendering sidecar (the beta stack ships one — ``docker/renderer`` in the
deploy repo) that runs the page in a real browser and answers with the text
a person would meet. The vault's own image stays lean — no browser is
installed here — and a deployment without the sidecar says so honestly
instead of pretending a shell was the page.

The offline gate vets the *target* — that is what leaves. The sidecar
itself is deployment infrastructure on the stack's own network, the same
standing an Ollama daemon has.
"""

from __future__ import annotations

import json
import os
import urllib.request

from . import offline

#: Rendered pages can be heavy; the cap keeps a runaway page from becoming
#: a runaway seal.
MAX_RENDER_BYTES = 2_000_000


class RendererUnavailable(Exception):
    """No eyes on this deployment, or the eyes did not answer."""


def url() -> str | None:
    return os.environ.get("PDI_RENDERER_URL", "").strip() or None


def available() -> bool:
    return url() is not None


def render_text(target: str) -> str:
    """The page at ``target`` as a person would meet it, via the sidecar."""
    base = url()
    if not base:
        raise RendererUnavailable(
            "no renderer is configured (PDI_RENDERER_URL is unset)")
    offline.allow(target, "a rendered fetch")
    req = urllib.request.Request(
        base.rstrip("/") + "/render",
        data=json.dumps({"url": target}).encode("utf-8"),
        headers={"content-type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            raw = resp.read(MAX_RENDER_BYTES)
        out = json.loads(raw.decode("utf-8", errors="replace"))
    except Exception as exc:  # noqa: BLE001 — one honest reason, not a stack
        raise RendererUnavailable(f"the renderer did not answer ({exc})")
    text = out.get("text")
    if not isinstance(text, str) or not text.strip():
        raise RendererUnavailable("the renderer answered without text")
    return text.strip()
