"""A prompt too long to send loses evidence, never the question.

    asked     does the prompt fit
    mattered  is the question still in it

`ask_grounded` ended with `infer(prompt[:8000])` over a string it had built
question-LAST: the caller's persona, then the grounding block, then
`"Question: …"`. Past the ceiling the slice took the question off the end and
the model was handed a system prompt, ten sealed records and nothing to
answer. It answered anyway, because a model always does — and the caller got
a confident paragraph with `drew_on` naming every key, as though the whole
thing had worked.

Reachable rather than theoretical. Ten records at five hundred characters is
about five thousand, and a QRME persona prompt — identity, sources, packs,
clinical notes — runs to a few thousand more.

The parts are sacrificed in a stated order now:

* the **question**, never;
* the **records**, dropped whole and from the back, because half a sealed
  record wearing a whole one's key is a worse answer than one fewer record;
* the caller's **persona** last, at a boundary, and told that it was.

And `drew_on` names only what the model actually saw. That list is the door's
own promise — *an answer that will be relied on should say what it stood on* —
and a key that was dropped for room is not something it stood on.
"""

from __future__ import annotations

import pytest

from pdi import resident, vault


def _tenant(client) -> dict:
    made = client.post("/tenants", json={"name": "prompt-probe"})
    assert made.status_code == 201, made.text
    return made.json()


@pytest.fixture()
def seen(monkeypatch):
    """Every prompt handed to the local model."""
    caught: list[str] = []

    def fake(prompt: str) -> dict:
        caught.append(prompt)
        return {"model": "stub", "text": "an answer"}

    monkeypatch.setattr(resident, "infer", fake)
    return caught


def _fill(client, tenant, how_many, size=500):
    """Seal AND embed. Sealing alone leaves nothing for `search` to rank, so
    the grounded path is never entered — which is how the first version of
    this file passed five tests without exercising the thing it is named
    for."""
    for i in range(how_many):
        body = f"Record {i} about the roof policy. " + ("detail " * (size // 7))
        vault.put(tenant, f"memory/long/entry-{i:03d}", body)
        resident.embed(tenant, f"memory/long/entry-{i:03d}", body)


QUESTION = "Which of my policies covers the roof?"


def test_the_question_survives_a_persona_that_fills_the_ceiling(client, seen):
    tenant = _tenant(client)
    _fill(client, tenant, 10)
    resident.ask_grounded(tenant, QUESTION, top_k=10,
                          system="P" * 6000)
    assert seen, "nothing was sent to the model"
    assert QUESTION in seen[-1], (
        "the question was cut off the end of the prompt — the model was "
        "handed evidence and nothing to answer"
    )


def test_the_prompt_stays_under_the_ceiling(client, seen):
    tenant = _tenant(client)
    _fill(client, tenant, 10)
    resident.ask_grounded(tenant, QUESTION, top_k=10, system="P" * 6000)
    assert len(seen[-1]) <= resident.PROMPT_CEILING


def test_records_are_dropped_whole_rather_than_sliced(client, seen):
    """Half a sealed record under a whole one's key is a worse answer than
    one fewer record, and it is the shape that reads as complete."""
    tenant = _tenant(client)
    _fill(client, tenant, 10)
    out = resident.ask_grounded(tenant, QUESTION, top_k=10,
                                system="P" * 6000)
    for key in out["drew_on"]:
        assert f"[{key}]" in seen[-1], key
    assert out["dropped_for_room"], (
        "nothing was dropped, so this is not exercising the squeeze"
    )


def test_drew_on_names_only_what_the_model_saw(client, seen):
    """The door's own promise. A key dropped for room is not something the
    answer stood on, and claiming it is the one dishonesty this exists to
    avoid."""
    tenant = _tenant(client)
    _fill(client, tenant, 10)
    out = resident.ask_grounded(tenant, QUESTION, top_k=10,
                                system="P" * 6000)
    for key in out["drew_on"]:
        assert f"[{key}]" in seen[-1]
    for key in out["dropped_for_room"]:
        assert f"[{key}]" not in seen[-1], (
            f"{key} is reported as dropped and is in the prompt"
        )
    assert not set(out["drew_on"]) & set(out["dropped_for_room"])


def test_a_persona_too_long_on_its_own_is_trimmed_and_says_so(client, seen):
    """Not even the question and the persona fit. The persona gives way —
    the question never does — and a profile finding itself thinking in half
    sentences is told why."""
    tenant = _tenant(client)
    out = resident.ask_grounded(tenant, QUESTION,
                                system="P" * (resident.PROMPT_CEILING + 4000))
    assert QUESTION in seen[-1]
    assert "were shortened here" in seen[-1]
    assert len(seen[-1]) <= resident.PROMPT_CEILING
    assert out["text"] == "an answer"


def test_an_ordinary_ask_is_untouched(client, seen):
    """Most asks fit easily, and nothing about them should change."""
    tenant = _tenant(client)
    vault.put(tenant, "memory/roof", "The roof policy is HO-3.")
    resident.embed(tenant, "memory/roof", "The roof policy is HO-3.")
    out = resident.ask_grounded(tenant, QUESTION, system="You are a coach.")
    assert QUESTION in seen[-1]
    assert "were shortened here" not in seen[-1]
    assert out["dropped_for_room"] == []
