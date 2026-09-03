"""The resident learns from the corpus.

The tandems bank every exchange a person consents to and seal it here in
bundles (`jim/corpus.py`: `jim/{user}/corpus/{run}`, each holding
`examples` of system, prompt and completion). Until now the resident held
them the way it holds any record — sealed and unread. Three tools make
them its own:

    corpus.learn   every example becomes a sealed record under
                   resident/corpus/ and a vector beside it, so search ranks
                   it and a grounded ask stands on it — idempotent, bounded
    corpus.export  the corpus sealed as a fine-tune set, one chat-shaped
                   JSON line per example, recorded in `training_sets`
    corpus.train   a set handed to the trainer at PDI_TRAINER_URL — or, with
                   none wired, held with the sentence that says so

    asked     can the local model grow from what the coach said
    mattered  does it grow here, beside the data, and never by pretending
"""

from __future__ import annotations

import json

import pytest

from pdi import resident, vault

from .conftest import auth, new_tenant


def _tenant_of(client, token):
    return vault.tenant_by_token(token)


def _seal_bundle(client, token, user="u1", run="cor_1", examples=None):
    examples = examples if examples is not None else [
        {"system": "You are JIM-mini's life coach.",
         "prompt": "I slept badly again.",
         "completion": "Let's look at what the evenings hold — a short walk "
                       "after dinner tends to help.",
         "source": "coach", "provider": "anthropic", "at": "2026-09-01T08:00:00Z"},
        {"system": "You are JIM-mini's life coach.",
         "prompt": "How do I tell my sister about the diagnosis?",
         "completion": "Start with what you want her to know, and let her ask.",
         "source": "coach", "provider": "anthropic", "at": "2026-09-01T09:00:00Z"},
        {"prompt": "", "completion": "an empty prompt is not an example"},
    ]
    key = f"jim/{user}/corpus/{run}"
    # Sealed the way the tandem seals it — through the vault, as a record.
    vault.put(_tenant_of(client, token), key, json.dumps(
        {"examples": examples, "count": len(examples), "at": "now"}))
    return key


def _task(client, token, goal, steps=None, every_hours=None):
    body = {"goal": goal}
    if steps is not None:
        body["steps"] = steps
    if every_hours is not None:
        body["every_hours"] = every_hours
    r = client.post("/resident/tasks", json=body, headers=auth(token))
    assert r.status_code == 201, r.text
    return r.json()


def _run(client, token, task_id):
    return client.post(f"/resident/tasks/{task_id}/run", headers=auth(token)).json()


# --- learn ---------------------------------------------------------------------

def test_the_planner_knows_the_corpus_verbs(client):
    token = new_tenant(client)
    t = _task(client, token, "learn from the corpus")
    assert [s["tool"] for s in t["plan_steps"]] == ["corpus.learn"]
    t = _task(client, token, "export the training set then train the local model")
    assert [s["tool"] for s in t["plan_steps"]] == ["corpus.export", "corpus.train"]
    t = _task(client, token, "learn from the corpus every day", every_hours=24)
    assert t["every_hours"] == 24


def test_learning_indexes_every_example_and_only_once(client):
    token = new_tenant(client)
    _seal_bundle(client, token)
    tenant = _tenant_of(client, token)
    first = resident.learn(tenant)
    assert first == {"bundles": 1, "examples": 2, "learned": 2, "already": 0,
                     "left": 0, "index_prefix": "resident/corpus/"}
    keys = [k for k in vault.list_keys(tenant) if k.startswith("resident/corpus/")]
    assert keys == ["resident/corpus/cor_1/0000", "resident/corpus/cor_1/0001"]
    again = resident.learn(tenant)
    assert again["learned"] == 0 and again["already"] == 2


def test_a_learned_example_grounds_an_answer(client):
    token = new_tenant(client)
    _seal_bundle(client, token)
    tenant = _tenant_of(client, token)
    resident.learn(tenant)
    found = resident.search(tenant, "sleeping badly evenings walk", top_k=2)
    assert found["matches"][0]["key"].startswith("resident/corpus/cor_1/")
    got = resident.ask_grounded(tenant, "what helps when I sleep badly?",
                                prefix="resident/corpus/")
    assert got["drew_on"] and got["drew_on"][0].startswith("resident/corpus/")


def test_the_learned_record_carries_the_exchange_not_the_bundle(client):
    token = new_tenant(client)
    _seal_bundle(client, token)
    tenant = _tenant_of(client, token)
    resident.learn(tenant)
    rec = json.loads(vault.get(tenant, "resident/corpus/cor_1/0000")["value"])
    assert rec["line"].startswith("Q: I slept badly again.\nA: ")
    assert rec["source"] == "coach" and rec["bundle"] == "jim/u1/corpus/cor_1"


def test_a_learn_cycle_is_bounded_and_says_what_is_left(client):
    token = new_tenant(client)
    many = [{"prompt": f"question {i}", "completion": f"answer {i}"} for i in range(7)]
    _seal_bundle(client, token, run="cor_big", examples=many)
    tenant = _tenant_of(client, token)
    got = resident.learn(tenant, limit=5)
    assert got["learned"] == 5 and got["left"] == 2
    got = resident.learn(tenant, limit=5)
    assert got["learned"] == 2 and got["already"] == 5 and got["left"] == 0


def test_learning_over_the_task_door_is_a_step_with_a_summary(client):
    token = new_tenant(client)
    _seal_bundle(client, token)
    t = _task(client, token, "learn from the corpus")
    done = _run(client, token, t["id"])
    assert done["status"] == "done"
    assert "2 example(s) learned from 1 bundle(s)" in done["plan_steps"][0]["summary"]


# --- export --------------------------------------------------------------------

def test_the_export_seals_a_chat_shaped_set_and_records_it(client):
    token = new_tenant(client)
    _seal_bundle(client, token)
    tenant = _tenant_of(client, token)
    out = resident.export_set(tenant)
    assert out["examples"] == 2 and out["format"] == "chat-jsonl"
    assert out["set_ref"].startswith("resident/corpus/sets/")
    body = vault.get(tenant, out["set_ref"])["value"]
    lines = [json.loads(ln) for ln in body.splitlines() if ln]
    assert len(lines) == 2
    assert [m["role"] for m in lines[0]["messages"]] == ["system", "user", "assistant"]
    assert lines[0]["messages"][1]["content"] == "I slept badly again."
    rows = resident.read_rows(tenant, "training_sets")["dataset_rows"]
    assert rows[0]["set_ref"] == out["set_ref"] and rows[0]["examples"] == 2


def test_an_empty_corpus_refuses_to_export_in_words(client):
    token = new_tenant(client)
    t = _task(client, token, "export the training set")
    done = _run(client, token, t["id"])
    assert done["status"] == "failed"
    assert "no examples to export" in done["plan_steps"][0]["error"]


# --- train ---------------------------------------------------------------------

def test_with_no_trainer_wired_the_set_is_held_and_the_sentence_says_so(client, monkeypatch):
    monkeypatch.delenv("PDI_TRAINER_URL", raising=False)
    token = new_tenant(client)
    _seal_bundle(client, token)
    t = _task(client, token, "export the training set then train the local model")
    done = _run(client, token, t["id"])
    assert done["status"] == "done"          # held is an answer, not a failure
    assert done["plan_steps"][1]["summary"].startswith("held: no trainer is wired")
    tenant = _tenant_of(client, token)
    assert resident.posture(tenant)["corpus"]["trainer_ready"] is False


def test_with_a_trainer_wired_the_set_is_handed_over_and_the_job_recorded(client, monkeypatch):
    monkeypatch.setenv("PDI_TRAINER_URL", "http://trainer:8800")
    posted = {}

    class _Resp:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return json.dumps({"job": "job_42"}).encode()

    def fake_open(req, timeout=60):
        posted["url"] = req.full_url
        posted["body"] = json.loads(req.data.decode())
        return _Resp()

    monkeypatch.setattr(resident.urllib.request, "urlopen", fake_open)
    token = new_tenant(client)
    _seal_bundle(client, token)
    tenant = _tenant_of(client, token)
    set_ref = resident.export_set(tenant)["set_ref"]
    out = resident.train(tenant, set_ref)
    assert out["submitted"] is True and out["job"] == "job_42"
    assert posted["url"] == "http://trainer:8800/train"
    assert posted["body"]["format"] == "chat-jsonl"
    assert "I slept badly again." in posted["body"]["set"]
    jobs = resident.read_rows(tenant, "training_jobs")["dataset_rows"]
    assert jobs[0]["job"] == "job_42" and jobs[0]["set_ref"] == set_ref


def test_training_needs_a_set_that_exists(client):
    token = new_tenant(client)
    tenant = _tenant_of(client, token)
    with pytest.raises(resident.ResidentError, match="export one first"):
        resident.train(tenant, "resident/corpus/sets/nothing.jsonl")


def test_a_trainer_that_refuses_is_a_failed_step_in_words(client, monkeypatch):
    monkeypatch.setenv("PDI_TRAINER_URL", "http://trainer:8800")

    def broken(req, timeout=60):
        raise OSError("connection refused")

    monkeypatch.setattr(resident.urllib.request, "urlopen", broken)
    token = new_tenant(client)
    _seal_bundle(client, token)
    t = _task(client, token, "export the training set then train the local model")
    done = _run(client, token, t["id"])
    assert done["status"] == "failed"
    assert "did not accept the set" in done["plan_steps"][1]["error"]


def test_offline_mode_keeps_the_trainer_home(client, monkeypatch):
    monkeypatch.setenv("PDI_TRAINER_URL", "http://trainer.example.com")
    monkeypatch.setenv("PDI_OFFLINE", "1")
    token = new_tenant(client)
    _seal_bundle(client, token)
    tenant = _tenant_of(client, token)
    set_ref = resident.export_set(tenant)["set_ref"]
    t = _task(client, token, "train",
              steps=[{"tool": "corpus.train", "args": {"set_ref": set_ref}}])
    done = _run(client, token, t["id"])
    assert done["status"] == "failed"
    assert "LeftTheHost" in done["plan_steps"][0]["error"]


# --- the posture and the registry ----------------------------------------------

def test_the_posture_counts_the_corpus_and_names_the_trainer(client, monkeypatch):
    monkeypatch.delenv("PDI_TRAINER_URL", raising=False)
    token = new_tenant(client)
    _seal_bundle(client, token)
    tenant = _tenant_of(client, token)
    resident.learn(tenant)
    resident.export_set(tenant)
    got = client.get("/resident", headers=auth(token)).json()
    assert got["corpus"] == {**got["corpus"], "bundles": 1, "learned": 2,
                             "sets": 1, "trainer": None, "trainer_ready": False}
    names = {t["name"] for t in got["tools"]}
    assert {"corpus.learn", "corpus.export", "corpus.train"} <= names
    assert all(not t["leaves_host"] for t in got["tools"]
               if t["name"].startswith("corpus."))


def test_the_resident_never_mistakes_its_own_records_for_a_bundle(client):
    token = new_tenant(client)
    _seal_bundle(client, token)
    tenant = _tenant_of(client, token)
    resident.learn(tenant)
    resident.export_set(tenant)
    assert resident.corpus_bundles(tenant) == ["jim/u1/corpus/cor_1"]
