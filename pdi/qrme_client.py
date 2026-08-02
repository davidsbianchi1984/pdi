"""QRME tandem adapter — the voice of the gate agent.

The *only* connection between PDI and QRME. It speaks QRME's public HTTP API
and never imports QRME code, so the two remain separate products that merely
interoperate — the same arrangement JIM-mini has in ``jim/qrme_client.py``.

PDI grows no model of its own. Every arrow in docs/tandem.md points *into* PDI:
it is the bottom layer of the suite, and a vault whose availability depends on
a model provider is a worse vault. So when the gate needs words for somebody
standing outside it at 2am, it asks QRME for them.

Two consequences are the reason to do it this way rather than embed a model:

* The agent inherits QRME's **AI mark**. Somebody being talked to by software
  at a gate must know it is software, and the suite's oldest invariant already
  governs that surface.
* Absence degrades to nothing worse than silence. Every method here returns
  ``None`` rather than raising when QRME is unreachable, and :mod:`pdi.gate`
  falls back to its own written sentences. The unagented path is the floor.

A ``client`` may be injected (anything exposing ``post(path, json=...)`` and
``get(path)`` returning a response with ``.status_code`` and ``.json()`` — a
FastAPI ``TestClient`` or an ``httpx.Client``). Otherwise a small urllib client
is used against ``base_url``.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request


class _Response:
    def __init__(self, status_code: int, body: bytes):
        self.status_code = status_code
        self._body = body

    def json(self):
        return json.loads(self._body) if self._body else None


class _UrllibClient:
    def __init__(self, base_url: str, timeout: float = 5.0):
        self._base = base_url.rstrip("/")
        self._timeout = timeout

    def _request(self, method: str, path: str, body=None) -> _Response:
        data = json.dumps(body).encode() if body is not None else None
        from . import offline
        offline.allow(self._base + path, "the QRME tandem")
        req = urllib.request.Request(
            self._base + path, data=data, method=method,
            headers={"content-type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as r:
                return _Response(r.status, r.read())
        except urllib.error.HTTPError as e:
            return _Response(e.code, e.read())

    def post(self, path, json=None):
        return self._request("POST", path, json)

    def get(self, path):
        return self._request("GET", path)


class QRMEClient:
    def __init__(self, base_url: str | None = None, client=None):
        if client is None:
            if not base_url:
                raise ValueError("QRMEClient needs base_url or an injected client")
            client = _UrllibClient(base_url)
        self._client = client

    def resolve_handle(self, handle: str) -> dict | None:
        """Resolve a QRME @handle to its public profile card.

        Handles rather than ids because ids are deployment-specific: an
        operator configures ``PDI_GATE_PROFILE=@front_desk`` once and it keeps
        meaning the same profile across deployments.
        """
        ref = handle if handle.startswith("@") else "@" + handle
        try:
            r = self._client.get("/summon?ref=" + urllib.parse.quote(ref))
        except Exception:
            return None
        if r.status_code >= 300:
            return None
        out = r.json() or {}
        return out.get("profile") if out.get("type") == "handle" else None

    def ensure_interactor(self, display_name: str) -> str | None:
        try:
            r = self._client.post("/interactors", json={"display_name": display_name})
        except Exception:
            return None
        if r.status_code >= 300:
            return None
        return (r.json() or {}).get("id")

    def say(self, profile_id: str, interactor_id: str, message: str) -> str | None:
        """Ask the profile to put a decision into words.

        The reply has already passed QRME's moderation. ``None`` when QRME is
        unreachable, refused, or held the message for owner approval — every
        one of which the gate treats identically, because a caller waiting at a
        door does not care why the words did not arrive.
        """
        try:
            r = self._client.post(
                f"/profiles/{profile_id}/chat",
                json={"interactor_id": interactor_id, "message": message})
        except Exception:
            return None
        if r.status_code >= 300:
            return None
        body = r.json() or {}
        return (body.get("profile_message") or {}).get("content")


def from_env(client=None) -> tuple[QRMEClient | None, str | None]:
    """The configured gate voice, or ``(None, None)``.

    ``PDI_QRME_URL`` and ``PDI_GATE_PROFILE`` are both required: a deployment
    that wants no AI at its gate configures neither, and gets the human-routing
    path with nothing switched off.
    """
    handle = os.environ.get("PDI_GATE_PROFILE")
    base = os.environ.get("PDI_QRME_URL")
    if not handle or not (base or client):
        return None, None
    try:
        return QRMEClient(base, client=client), handle
    except ValueError:
        return None, None
