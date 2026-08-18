"""The resident intelligence: the agent beside the data, in one process.

`pdi/resident.py` is the opposite approach to the tandem's HTTP calls — the
planner, tool registry, queryable datasets, embeddings and local inference
running inside the vault process, behind the tenant fence, on the audit
chain. These tests hold the five promises its docstring makes, and the three
rules it inherits: tenant isolation in the SQL, offline refuses at the
socket, and a model is a voice rather than a decider — the plan reads the
same on a host with no model at all.
"""

from __future__ import annotations

import pytest

from pdi import resident

from .conftest import auth, new_tenant


def _fake_page(monkeypatch, text="alpha,beta\n1,2\n3,4"):
    fetched = {}

    def fake(url):
        fetched["url"] = url
        return text
    monkeypatch.setattr(resident, "_fetch_text", fake)
    return fetched


# -- planning ----------------------------------------------------------------

def test_a_goal_becomes_ordered_steps_without_a_model(client, monkeypatch):
    monkeypatch.delenv("PDI_OLLAMA_URL", raising=False)
    token = new_tenant(client)
    r = client.post("/resident/tasks", json={
        "goal": "fetch https://example.com/prices.csv then put the rows "
                "into table prices then embed as prices/latest"},
        headers=auth(token))
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "planned"
    assert body["planned_by"] == "rules-v1"
    assert [s["tool"] for s in body["plan_steps"]] == [
        "fetch.url", "table.append", "embed.text"]
    assert body["plan_steps"][0]["args"]["url"] == "https://example.com/prices.csv"
    assert body["plan_steps"][1]["args"]["dataset"] == "prices"
    assert body["plan_steps"][2]["args"]["key"] == "prices/latest"


def test_a_plan_naming_an_unknown_tool_refuses_before_anything_runs(client):
    token = new_tenant(client)
    r = client.post("/resident/tasks", json={
        "goal": "do the thing",
        "steps": [{"tool": "shell.exec", "args": {"cmd": "rm -rf /"}}]},
        headers=auth(token))
    assert r.status_code == 422
    assert "shell.exec" in r.text
    assert client.get("/resident/tasks", headers=auth(token)).json() == []


# -- the errand: fetch → table → query → embed → search ----------------------

def test_fetch_lands_in_a_table_the_app_can_query(client, monkeypatch):
    fetched = _fake_page(monkeypatch)
    token = new_tenant(client)
    planned = client.post("/resident/tasks", json={
        "goal": "prices",
        "steps": [
            {"tool": "fetch.url",
             "args": {"url": "https://example.com/prices.csv"}},
            {"tool": "table.append",
             "args": {"dataset": "prices", "derive": "csv"}},
        ]}, headers=auth(token)).json()
    ran = client.post(f"/resident/tasks/{planned['id']}/run",
                      headers=auth(token))
    assert ran.status_code == 200, ran.text
    out = ran.json()
    assert out["status"] == "done"
    assert fetched["url"] == "https://example.com/prices.csv"

    rows = client.get("/resident/datasets/prices/rows",
                      headers=auth(token)).json()["dataset_rows"]
    assert [r["alpha"] for r in rows] == ["1", "3"]
    assert all(r["_source"] == "https://example.com/prices.csv" for r in rows)

    listed = client.get("/resident/datasets", headers=auth(token)).json()
    assert listed == [{"dataset": "prices", "row_count": 2,
                       "last_write": listed[0]["last_write"]}]


def test_the_fetched_page_is_sealed_in_the_vault_and_the_step_carries_the_ref(
        client, monkeypatch):
    _fake_page(monkeypatch, text="the quick brown fox")
    token = new_tenant(client)
    planned = client.post("/resident/tasks", json={
        "goal": "read",
        "steps": [{"tool": "fetch.url",
                   "args": {"url": "https://example.com/a"}}]},
        headers=auth(token)).json()
    out = client.post(f"/resident/tasks/{planned['id']}/run",
                      headers=auth(token)).json()
    ref = out["plan_steps"][0]["result_ref"]
    assert ref.startswith("resident/")
    sealed = client.get(f"/records/{ref}", headers=auth(token))
    assert sealed.status_code == 200
    assert "the quick brown fox" in sealed.json()["value"]


def test_embeddings_index_and_search_rank_the_right_document(client):
    token = new_tenant(client)
    for key, text in [("doc/dog", "the dog barked at the mail carrier"),
                      ("doc/market", "quarterly market prices fell sharply"),
                      ("doc/cat", "a cat slept in the sunlight all day")]:
        r = client.post("/resident/embeddings",
                        json={"key": key, "text": text}, headers=auth(token))
        assert r.status_code == 201, r.text
        assert r.json()["embedder"] == resident.HASHED_EMBEDDER
    found = client.post("/resident/search",
                        json={"query": "market prices", "top_k": 2},
                        headers=auth(token)).json()
    assert found["matches"][0]["key"] == "doc/market"
    assert len(found["matches"]) == 2


def test_the_vector_stores_a_hash_and_never_the_text(client):
    token = new_tenant(client)
    client.post("/resident/embeddings",
                json={"key": "doc/secret", "text": "meet at the north gate"},
                headers=auth(token))
    from pdi import db
    row = db.connect().execute(
        "SELECT * FROM resident_vectors WHERE key='doc/secret'").fetchone()
    for field in row.keys():
        value = row[field]
        if isinstance(value, str):
            assert "north gate" not in value
    assert row["text_sha256"]


# -- failure and honesty -----------------------------------------------------

def test_a_failed_step_stops_the_chain_and_the_rest_say_skipped(client,
                                                                monkeypatch):
    def refuse(url):
        raise OSError("connection refused")
    monkeypatch.setattr(resident, "_fetch_text", refuse)
    token = new_tenant(client)
    planned = client.post("/resident/tasks", json={
        "goal": "doomed",
        "steps": [
            {"tool": "fetch.url", "args": {"url": "https://down.example"}},
            {"tool": "table.append", "args": {"dataset": "d", "derive": "lines"}},
        ]}, headers=auth(token)).json()
    out = client.post(f"/resident/tasks/{planned['id']}/run",
                      headers=auth(token)).json()
    assert out["status"] == "failed"
    assert out["plan_steps"][0]["status"] == "failed"
    assert "refused" in out["plan_steps"][0]["error"]
    assert out["plan_steps"][1]["status"] == "skipped"


def test_offline_mode_refuses_the_fetch_at_the_socket(client, monkeypatch):
    monkeypatch.setenv("PDI_OFFLINE", "1")
    token = new_tenant(client)
    planned = client.post("/resident/tasks", json={
        "goal": "leak",
        "steps": [{"tool": "fetch.url",
                   "args": {"url": "https://example.com/x"}}]},
        headers=auth(token)).json()
    out = client.post(f"/resident/tasks/{planned['id']}/run",
                      headers=auth(token)).json()
    assert out["status"] == "failed"
    assert "offline" in out["plan_steps"][0]["error"].lower()


def test_with_no_model_the_stub_answers_and_says_it_is_the_stub(client,
                                                                monkeypatch):
    monkeypatch.delenv("PDI_OLLAMA_URL", raising=False)
    token = new_tenant(client)
    planned = client.post("/resident/tasks", json={
        "goal": "summarise the situation"}, headers=auth(token)).json()
    assert planned["plan_steps"][0]["tool"] == "infer.local"
    out = client.post(f"/resident/tasks/{planned['id']}/run",
                      headers=auth(token)).json()
    assert out["status"] == "done"
    assert "No local model" in out["plan_steps"][0]["summary"] or \
        out["plan_steps"][0]["result_ref"]


def test_the_posture_names_the_registry_and_what_leaves_the_host(client):
    token = new_tenant(client)
    got = client.get("/resident", headers=auth(token)).json()
    assert got["resident"] is True
    assert {t["name"] for t in got["tools"]} == set(resident.TOOLS)
    leaves = [t["name"] for t in got["tools"] if t["leaves_host"]]
    assert leaves == ["fetch.url"], (
        "the published registry must say exactly which tools leave the "
        f"host, and only the fetch does: {leaves}")
    assert got["hosting_mode"] in ("colocation", "leased_space",
                                   "own_facility", "own_device")


def test_the_planner_is_rules_not_a_model(monkeypatch):
    """The plan must read identically on a host with no model: a probe on
    the source would rot, so probe the behaviour — decomposition happens
    with the environment stripped of every model hint."""
    monkeypatch.delenv("PDI_OLLAMA_URL", raising=False)
    monkeypatch.delenv("PDI_RESIDENT_MODEL", raising=False)
    steps = resident._decompose(
        "fetch https://example.com/a then rows into table t then search for a")
    assert [s["tool"] for s in steps] == ["fetch.url", "table.append",
                                          "search.vectors"]
    assert resident.local_model() is None


# -- the fence, again, for the new tables ------------------------------------

def test_another_tenants_tasks_datasets_and_vectors_are_invisible(client,
                                                                  monkeypatch):
    _fake_page(monkeypatch, text="one\ntwo")
    mine, theirs = new_tenant(client, "mine"), new_tenant(client, "theirs")
    planned = client.post("/resident/tasks", json={
        "goal": "gather",
        "steps": [
            {"tool": "fetch.url", "args": {"url": "https://example.com/l"}},
            {"tool": "table.append", "args": {"dataset": "lines",
                                              "derive": "lines"}},
        ]}, headers=auth(mine)).json()
    client.post(f"/resident/tasks/{planned['id']}/run", headers=auth(mine))
    client.post("/resident/embeddings",
                json={"key": "doc/a", "text": "alpha beta"},
                headers=auth(mine))

    assert client.get("/resident/tasks", headers=auth(theirs)).json() == []
    ran = client.post(f"/resident/tasks/{planned['id']}/run",
                      headers=auth(theirs))
    assert ran.status_code == 404
    assert client.get("/resident/datasets", headers=auth(theirs)).json() == []
    assert client.get("/resident/datasets/lines/rows",
                      headers=auth(theirs)).json()["dataset_rows"] == []
    found = client.post("/resident/search", json={"query": "alpha"},
                        headers=auth(theirs)).json()
    assert found["matches"] == []


def test_every_act_lands_on_the_audit_chain(client, monkeypatch):
    _fake_page(monkeypatch, text="x")
    token = new_tenant(client)
    planned = client.post("/resident/tasks", json={
        "goal": "gather",
        "steps": [{"tool": "fetch.url",
                   "args": {"url": "https://example.com/x"}}]},
        headers=auth(token)).json()
    client.post(f"/resident/tasks/{planned['id']}/run", headers=auth(token))
    client.post("/resident/embeddings",
                json={"key": "k", "text": "words"}, headers=auth(token))
    actions = {e["action"] for e in
               client.get("/audit", headers=auth(token)).json()}
    for expected in ("resident.plan", "resident.fetch", "resident.step",
                     "resident.task", "resident.embed"):
        assert expected in actions, f"{expected} never reached the chain"


def test_rows_that_are_not_flat_refuse_with_a_sentence(client):
    token = new_tenant(client)
    r = client.post("/resident/tasks", json={
        "goal": "bad rows",
        "steps": [{"tool": "table.append",
                   "args": {"dataset": "d",
                            "rows": [{"nested": {"a": 1}}]}}]},
        headers=auth(token)).json()
    out = client.post(f"/resident/tasks/{r['id']}/run",
                      headers=auth(token)).json()
    assert out["status"] == "failed"
    assert "flat" in out["plan_steps"][0]["error"]
