"""The capture grows eyes.

A JavaScript application answers a plain fetch with an empty shell and a
title — a dozen characters standing where a whole console is. `fetch.render`
asks the deployment's rendering sidecar for the page as a person meets it,
and a deployment without eyes says so in the seal instead of pretending a
shell was the page.

    asked     what does the page say
    mattered  what a person would see, not what the server sent first
"""

import json

from pdi import renderer, resident

from .conftest import auth, new_tenant


def _render_task(client, token, url="https://console.example/app/"):
    return client.post("/resident/tasks", json={
        "goal": "see the console",
        "steps": [{"tool": "fetch.render", "args": {"url": url}}],
    }, headers=auth(token)).json()


def _run(client, token, task_id):
    r = client.post(f"/resident/tasks/{task_id}/run", headers=auth(token))
    assert r.status_code == 200, r.text
    task = [t for t in client.get("/resident/tasks",
                                  headers=auth(token)).json()
            if t["id"] == task_id][0]
    step = task["plan_steps"][0]
    sealed = client.get(f"/records/{step['result_ref']}",
                        headers=auth(token)).json()
    return json.loads(sealed["value"]), step["summary"]


def test_a_rendered_page_is_the_page_a_person_sees(client, monkeypatch):
    """With eyes deployed, the seal carries the rendered text and says so."""
    monkeypatch.setenv("PDI_RENDERER_URL", "http://renderer:8400")
    monkeypatch.setattr(renderer, "render_text",
                        lambda url: "Vault online · 3 lookouts standing")
    token = new_tenant(client)
    body = _render_task(client, token)
    seal, summary = _run(client, token, body["id"])
    assert seal["rendered"] is True
    assert "render_fallback" not in seal
    assert seal["text"] == "Vault online · 3 lookouts standing"
    assert "(rendered)" in summary


def test_without_eyes_the_seal_says_the_shell_stood_in(client, monkeypatch):
    """No sidecar configured: the plain fetch stands in, and the seal —
    not just the summary — records that this reading was the shell."""
    monkeypatch.delenv("PDI_RENDERER_URL", raising=False)
    monkeypatch.setattr(resident, "_fetch_text", lambda url: "JIM Guardian")
    token = new_tenant(client)
    body = _render_task(client, token)
    seal, summary = _run(client, token, body["id"])
    assert seal["rendered"] is False
    assert "PDI_RENDERER_URL is unset" in seal["render_fallback"]
    assert seal["text"] == "JIM Guardian"
    assert "plain fetch stood in" in summary


def test_dead_eyes_fall_back_with_the_reason(client, monkeypatch):
    """A configured sidecar that does not answer is a reason, not a crash:
    the capture still happens, and the seal carries why it is the shell."""
    monkeypatch.setenv("PDI_RENDERER_URL", "http://renderer:8400")

    def dead(url):
        raise renderer.RendererUnavailable("the renderer did not answer "
                                           "(connection refused)")
    monkeypatch.setattr(renderer, "render_text", dead)
    monkeypatch.setattr(resident, "_fetch_text", lambda url: "JIM Guardian")
    token = new_tenant(client)
    body = _render_task(client, token)
    seal, summary = _run(client, token, body["id"])
    assert seal["rendered"] is False
    assert "did not answer" in seal["render_fallback"]
    assert "plain fetch stood in" in summary


def _make_due(task_id):
    from pdi import db
    conn = db.connect()
    conn.execute("UPDATE resident_tasks SET"
                 " next_run_at='2000-01-01T00:00:00+00:00' WHERE id=?",
                 (task_id,))
    conn.commit()


def _cycle(client, token, task_id):
    _make_due(task_id)
    assert resident.pulse()["ran"] == 1
    task = [t for t in client.get("/resident/tasks",
                                  headers=auth(token)).json()
            if t["id"] == task_id][0]
    step = task["plan_steps"][0]
    sealed = client.get(f"/records/{step['result_ref']}",
                        headers=auth(token)).json()
    return json.loads(sealed["value"]), step["summary"]


def test_a_rendered_recapture_remembers_when_it_changed(client, monkeypatch):
    """A standing rendered lookout keeps the plain fetch's memory: an
    identical rendering keeps its change date; a different one moves it."""
    monkeypatch.setenv("PDI_RENDERER_URL", "http://renderer:8400")
    page = {"text": "Vault online"}
    monkeypatch.setattr(renderer, "render_text", lambda url: page["text"])
    token = new_tenant(client)
    body = client.post("/resident/tasks", json={
        "goal": "keep eyes on the console",
        "every_hours": 1.0,
        "steps": [{"tool": "fetch.render",
                   "args": {"url": "https://console.example/app/"}}],
    }, headers=auth(token)).json()

    first, summary = _cycle(client, token, body["id"])
    assert summary.endswith("(first capture)")
    second, summary = _cycle(client, token, body["id"])
    assert summary.endswith("(unchanged)")
    assert second["changed_at"] == first["changed_at"]
    page["text"] = "Vault online · 1 letter waiting"
    third, summary = _cycle(client, token, body["id"])
    assert summary.endswith("(changed)")
    assert third["changed_at"] > first["changed_at"]


def test_the_registry_publishes_the_eyes_honestly(client):
    """fetch.render is in the published vocabulary, marked as leaving the
    host, and its own description says the shell stands in when it must."""
    token = new_tenant(client)
    tools = client.get("/resident", headers=auth(token)).json()["tools"]
    row = next(t for t in tools if t["name"] == "fetch.render")
    assert row["leaves_host"] is True
    assert "stands in" in row["means"]


def test_the_planner_hears_render_as_eyes(client, monkeypatch):
    """A goal that says render (or see) plans the eyes tool; plain verbs
    keep the plain fetch."""
    monkeypatch.delenv("PDI_OLLAMA_URL", raising=False)
    token = new_tenant(client)
    planned = client.post("/resident/tasks", json={
        "goal": "render https://console.example/app/ then fetch "
                "https://example.com/prices.csv"},
        headers=auth(token)).json()
    assert [s["tool"] for s in planned["plan_steps"]] == [
        "fetch.render", "fetch.url"]


def test_no_renderer_means_no_render_call_leaves(client, monkeypatch):
    """The fallback still passes the offline gate through _fetch_text —
    the rendered path refuses the same URLs the plain path refuses."""
    monkeypatch.setenv("PDI_RENDERER_URL", "")
    called = {"n": 0}

    def counting(url):
        called["n"] += 1
        return "shell"
    monkeypatch.setattr(resident, "_fetch_text", counting)
    token = new_tenant(client)
    body = _render_task(client, token)
    _run(client, token, body["id"])
    assert called["n"] == 1
