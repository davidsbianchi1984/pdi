"""The posture proves the model answers, instead of repeating the promise.

    asked     is the local model there
    mattered  proven by a round trip, or read off the environment

`GET /resident` used to answer `local_model` alone — the name an operator
wrote into `PDI_RESIDENT_MODEL`. The deploy runbook's §8 produces exactly
two failures that name cannot show: the daemon is down (or on the wrong
Docker network), or the daemon is up and the model was never pulled. Both
used to surface the same way — a raw socket error out of the ask door,
mid-conversation. Now `local_model_standing` makes the round trip
(`/api/tags`, three seconds), says which of the two it is, and names the
fix; and `infer` answers a sentence instead of raising when the server
dies between the posture read and the ask.
"""

from __future__ import annotations

import io
import json
import urllib.error
import urllib.request

from pdi import resident

from .conftest import auth, new_tenant

OLLAMA = "http://127.0.0.1:11434"


class _Resp(io.BytesIO):
    """urlopen's context-manager shape over canned bytes."""

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _daemon_with(monkeypatch, names):
    """A fake Ollama whose /api/tags lists exactly these model names."""
    body = json.dumps({"models": [{"name": n} for n in names]}).encode()

    def fake(req, timeout=None):
        assert req.full_url.endswith("/api/tags")
        return _Resp(body)

    monkeypatch.setattr(urllib.request, "urlopen", fake)


def _daemon_down(monkeypatch):
    def fake(req, timeout=None):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", fake)


# -- the standing itself -----------------------------------------------------

def test_no_server_configured_is_not_a_diagnosis(monkeypatch):
    monkeypatch.delenv("PDI_OLLAMA_URL", raising=False)
    assert resident.model_standing() is None


def test_a_pulled_model_stands(monkeypatch):
    monkeypatch.setenv("PDI_OLLAMA_URL", OLLAMA)
    monkeypatch.setenv("PDI_RESIDENT_MODEL", "llama3.2")
    _daemon_with(monkeypatch, ["llama3.2:latest", "nomic-embed-text:latest"])
    s = resident.model_standing()
    assert s == {"reachable": True, "model": "llama3.2",
                 "pulled": True, "note": None}


def test_the_note_names_the_pull_when_the_model_is_missing(monkeypatch):
    monkeypatch.setenv("PDI_OLLAMA_URL", OLLAMA)
    monkeypatch.setenv("PDI_RESIDENT_MODEL", "llama3.2")
    _daemon_with(monkeypatch, ["mistral:latest"])
    s = resident.model_standing()
    assert s["reachable"] is True
    assert s["pulled"] is False
    assert "ollama pull llama3.2" in s["note"]


def test_a_dead_daemon_is_named_not_raised(monkeypatch):
    monkeypatch.setenv("PDI_OLLAMA_URL", OLLAMA)
    _daemon_down(monkeypatch)
    s = resident.model_standing()
    assert s["reachable"] is False
    assert s["pulled"] is False
    assert "PDI_OLLAMA_URL" in s["note"]
    assert "container" in s["note"]


# -- the posture door wears it ----------------------------------------------

def test_the_posture_carries_the_standing(client, monkeypatch):
    monkeypatch.setenv("PDI_OLLAMA_URL", OLLAMA)
    monkeypatch.setenv("PDI_RESIDENT_MODEL", "llama3.2")
    _daemon_with(monkeypatch, ["llama3.2:latest"])
    token = new_tenant(client)
    body = client.get("/resident", headers=auth(token)).json()
    assert body["local_model"] == "llama3.2"
    assert body["local_model_standing"]["reachable"] is True
    assert body["local_model_standing"]["pulled"] is True


def test_the_stub_posture_carries_no_standing(client, monkeypatch):
    monkeypatch.delenv("PDI_OLLAMA_URL", raising=False)
    monkeypatch.delenv("PDI_RESIDENT_MODEL", raising=False)
    token = new_tenant(client)
    body = client.get("/resident", headers=auth(token)).json()
    assert body["local_model"] is None
    assert body["local_model_standing"] is None


def test_a_dead_daemon_cannot_take_the_posture_page_down(client, monkeypatch):
    monkeypatch.setenv("PDI_OLLAMA_URL", OLLAMA)
    _daemon_down(monkeypatch)
    token = new_tenant(client)
    r = client.get("/resident", headers=auth(token))
    assert r.status_code == 200
    assert r.json()["local_model_standing"]["reachable"] is False


# -- the ask door stops raising ----------------------------------------------

def test_infer_answers_a_sentence_when_the_server_dies(monkeypatch):
    monkeypatch.setenv("PDI_OLLAMA_URL", OLLAMA)
    monkeypatch.setenv("PDI_RESIDENT_MODEL", "llama3.2")
    _daemon_down(monkeypatch)
    out = resident.infer("hello")
    assert out["model"] == "local-unreachable"
    assert "did not answer" in out["text"]
    assert "still work" in out["text"]
