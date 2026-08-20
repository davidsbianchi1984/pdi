"""The deployment's ears — audio or video turned into the words said in it.

The fetches read pages. A recording answers them with bytes: a plain fetch
of an .mp4 seals compressed video where a person hears a sentence, and no
markup-stripping makes words out of that.

    asked     what was said in this recording
    mattered  the words, sealed like any other capture — never the bytes

Where the ears live is configuration, not code: ``PDI_EARS_URL`` names a
transcription sidecar (the beta stack ships one — ``docker/ears`` in the
deploy repo) that downloads the recording, runs a local speech-to-text
model on the deployment's own hardware, and answers with the words. The
vault's image stays lean — no model, no ffmpeg here — and a deployment
without the sidecar refuses in words: unlike the eyes, there is no honest
stand-in (the shell of a page is still the page's text; the bytes of a
recording are not its words), so the tool fails saying why rather than
sealing silence or bytes.

The offline gate vets the *target* — that is what leaves. The sidecar
itself is deployment infrastructure on the stack's own network, the same
standing the renderer and an Ollama daemon have.
"""

from __future__ import annotations

import json
import os
import urllib.request

from . import offline

#: Transcripts are words, not archives; the cap keeps a runaway answer from
#: becoming a runaway seal.
MAX_TRANSCRIPT_BYTES = 2_000_000

#: Downloading a recording and transcribing it on CPU takes real time; the
#: sidecar enforces its own media-size cap, this only refuses to wait
#: forever for it.
TIMEOUT_SECONDS = 300


class EarsUnavailable(Exception):
    """No ears on this deployment, or the ears did not answer."""


#: URL suffixes that name a recording rather than a page — the same
#: canonical list the qrme briefcase and lookout read, ported rather than
#: reinvented so the two stacks call the same bytes a recording. Deduced
#: from the path alone (query stripped): a page that merely contains a
#: player is still a page.
_MEDIA_SUFFIXES = (".mp3", ".mp4", ".m4a", ".wav", ".ogg", ".webm", ".mov",
                   ".mkv", ".flac", ".aac", ".opus")


def looks_like_recording(url: str) -> bool:
    path = url.split("?", 1)[0].split("#", 1)[0].lower()
    return path.endswith(_MEDIA_SUFFIXES)


def url() -> str | None:
    return os.environ.get("PDI_EARS_URL", "").strip() or None


def available() -> bool:
    return url() is not None


def transcribe(target: str) -> dict:
    """The words said in the recording at ``target``, via the sidecar.

    Returns ``{"text", "duration_seconds", "language"}`` — duration and
    language absent when the sidecar does not know them; the text is the
    contract."""
    base = url()
    if not base:
        raise EarsUnavailable(
            "no transcriber is configured (PDI_EARS_URL is unset)")
    offline.allow(target, "a transcribed fetch")
    req = urllib.request.Request(
        base.rstrip("/") + "/transcribe",
        data=json.dumps({"url": target}).encode("utf-8"),
        headers={"content-type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            raw = resp.read(MAX_TRANSCRIPT_BYTES)
        out = json.loads(raw.decode("utf-8", errors="replace"))
    except Exception as exc:  # noqa: BLE001 — one honest reason, not a stack
        raise EarsUnavailable(f"the ears did not answer ({exc})")
    text = out.get("text")
    if not isinstance(text, str) or not text.strip():
        raise EarsUnavailable("the ears answered without words")
    return {"text": text.strip(),
            "duration_seconds": out.get("duration_seconds"),
            "language": out.get("language")}
