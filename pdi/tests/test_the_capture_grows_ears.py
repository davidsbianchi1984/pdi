"""The capture grows ears.

A recording answers the fetches with bytes: a plain fetch of an .mp4
seals compressed video where a person hears a sentence. `fetch.listen`
asks the deployment's transcription sidecar for the words said in it —
and unlike the eyes there is no honest stand-in (the shell of a page is
still the page's text; the bytes of a recording are not its words), so a
deployment without ears refuses in words rather than sealing silence.

    asked     what was said in this recording
    mattered  the words, sealed like any other capture — never the bytes
"""

import json

from pdi import ears, resident

from .conftest import auth, new_tenant


def _listen_task(client, token, url="https://cdn.example/briefing.mp4"):
    return client.post("/resident/tasks", json={
        "goal": "hear the briefing",
        "steps": [{"tool": "fetch.listen", "args": {"url": url}}],
    }, headers=auth(token)).json()


def _run(client, token, task_id):
    return client.post(f"/resident/tasks/{task_id}/run",
                       headers=auth(token)).json()


def _seal(client, token, step):
    sealed = client.get(f"/records/{step['result_ref']}",
                        headers=auth(token)).json()
    return json.loads(sealed["value"])


def test_a_transcribed_recording_seals_the_words(client, monkeypatch):
    """With ears deployed, the seal carries the words — with the
    recording's own duration and language beside them — and the summary
    says the capture was heard, not read."""
    monkeypatch.setenv("PDI_EARS_URL", "http://ears:8500")
    monkeypatch.setattr(ears, "transcribe", lambda url: {
        "text": "The vault held through the restore drill.",
        "duration_seconds": 12.4, "language": "en"})
    token = new_tenant(client)
    body = _listen_task(client, token)
    task = _run(client, token, body["id"])
    assert task["status"] == "done"
    step = task["plan_steps"][0]
    seal = _seal(client, token, step)
    assert seal["text"] == "The vault held through the restore drill."
    assert seal["transcribed"] is True
    assert seal["duration_seconds"] == 12.4
    assert seal["language"] == "en"
    assert "heard" in step["summary"] and "transcribed" in step["summary"]


def test_without_ears_the_step_fails_in_words(client, monkeypatch):
    """No sidecar configured: the step fails saying why — never a seal of
    silence, never the recording's bytes dressed as a transcript."""
    monkeypatch.delenv("PDI_EARS_URL", raising=False)
    token = new_tenant(client)
    body = _listen_task(client, token)
    task = _run(client, token, body["id"])
    assert task["status"] == "failed"
    step = task["plan_steps"][0]
    assert step["status"] == "failed"
    assert "no ears" in step["error"]
    assert "PDI_EARS_URL is unset" in step["error"]
    assert not step.get("result_ref")


def test_dead_ears_fail_with_the_reason(client, monkeypatch):
    monkeypatch.setenv("PDI_EARS_URL", "http://ears:8500")

    def dead(url):
        raise ears.EarsUnavailable("the ears did not answer "
                                   "(connection refused)")
    monkeypatch.setattr(ears, "transcribe", dead)
    token = new_tenant(client)
    body = _listen_task(client, token)
    task = _run(client, token, body["id"])
    assert task["status"] == "failed"
    step = task["plan_steps"][0]
    assert step["status"] == "failed"
    assert "did not answer" in step["error"]


def _make_due(task_id):
    from pdi import db
    conn = db.connect()
    conn.execute("UPDATE resident_tasks SET"
                 " next_run_at='2000-01-01T00:00:00+00:00' WHERE id=?",
                 (task_id,))
    conn.commit()


def test_a_standing_listen_remembers_when_the_words_changed(client,
                                                            monkeypatch):
    """The listen keeps the fetches' change-memory: identical words keep
    their change date; different words move it. A re-posted recording
    with the same sentences is not news."""
    monkeypatch.setenv("PDI_EARS_URL", "http://ears:8500")
    said = {"text": "Doors hold."}
    monkeypatch.setattr(ears, "transcribe",
                        lambda url: {"text": said["text"],
                                     "duration_seconds": 3.0,
                                     "language": "en"})
    token = new_tenant(client)
    body = client.post("/resident/tasks", json={
        "goal": "keep an ear on the briefing",
        "every_hours": 1.0,
        "steps": [{"tool": "fetch.listen",
                   "args": {"url": "https://cdn.example/briefing.mp4"}}],
    }, headers=auth(token)).json()

    def cycle():
        _make_due(body["id"])
        assert resident.pulse()["ran"] == 1
        task = [t for t in client.get("/resident/tasks",
                                      headers=auth(token)).json()
                if t["id"] == body["id"]][0]
        step = task["plan_steps"][0]
        return _seal(client, token, step), step["summary"]

    first, summary = cycle()
    assert summary.endswith("(first capture)")
    second, summary = cycle()
    assert summary.endswith("(unchanged)")
    assert second["changed_at"] == first["changed_at"]
    said["text"] = "Doors hold. One lookout is failing."
    third, summary = cycle()
    assert summary.endswith("(changed)")
    assert third["changed_at"] > first["changed_at"]


def test_the_planner_hears_listen_and_transcribe(monkeypatch):
    """"listen"/"transcribe"/"hear" route to the ears — checked before
    the fetch verbs, so "fetch and transcribe <url>" hears rather than
    reads. Plain fetch verbs still read."""
    for phrase in ("listen to https://cdn.example/a.mp4",
                   "fetch and transcribe https://cdn.example/a.mp4",
                   "hear https://cdn.example/town-hall.mp4"):
        step = resident._step_from(phrase)
        assert step["tool"] == "fetch.listen", phrase
        assert step["args"]["url"].startswith("https://cdn.example/")
    assert resident._step_from(
        "fetch https://example.com/page")["tool"] == "fetch.url"


def test_the_registry_says_the_listen_leaves_the_host():
    spec = resident.TOOLS["fetch.listen"]
    assert spec["leaves_host"] is True
    assert "refuses in words" in spec["means"]
