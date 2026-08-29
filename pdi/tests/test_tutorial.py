"""The console walkthrough and the assistant that delivers it.

The tests that matter are the two structural ones: that the guide cannot reach
the vault, and that it cannot quietly fall behind the console. Everything else
here is ordinary.

The first is the one specific to this product. QRME's guide must not become a
character; JIM's must not give medical advice; PDI's must not read the data,
and under BYOK it is the only one of the three where the *operator asking* is
frequently unable to read it either. An assistant that offered to look would be
promising something the product exists to prevent.
"""

import inspect
import os
import re

import pytest

from pdi import assistant, tutorial


# -- what it cannot reach ------------------------------------------------------

def test_the_guide_cannot_reach_the_vault(client):
    """Not "it is careful": there is no code path. Asserted against the parsed
    module rather than its text, because a careful implementation is one
    refactor away from a careless one and the import is what a reviewer misses.

    Read from the AST specifically so that *writing down the rule* does not
    trip it. A substring sweep flagged these modules for the sentences in their
    own docstrings explaining that they never touch the vault — a guard that
    punishes documenting the invariant is one somebody deletes.
    """
    import ast

    forbidden = {"vault", "crypto"}
    for module in (tutorial, assistant):
        tree = ast.parse(inspect.getsource(module))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    assert alias.name not in forbidden, (
                        f"{module.__name__} imports {alias.name!r}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[-1] not in forbidden, (
                        f"{module.__name__} imports {alias.name!r}")
            elif isinstance(node, ast.Attribute):
                base = node.value
                assert not (isinstance(base, ast.Name)
                            and base.id in forbidden), (
                    f"{module.__name__} calls {base.id}.{node.attr}")
            elif isinstance(node, ast.Name):
                assert node.id not in forbidden, (
                    f"{module.__name__} names {node.id!r} in code")


def test_the_walkthrough_writes_nothing_but_progress(client):
    """No token issued, no key rotated, no retention set. The only table it
    may write is its own."""
    src = inspect.getsource(tutorial)
    written = set(re.findall(r"(?:INSERT INTO|DELETE FROM)\s+(\w+)", src))
    written |= set(re.findall(r"(?<!DO )\bUPDATE\s+(\w+)\s+SET", src))
    assert written <= {"console_tutorial"}, (
        f"the walkthrough writes outside its own progress: {written}")


def test_the_assistant_writes_nothing_at_all(client):
    """Not even progress — that lives in the tutorial. A model can change the
    words on this surface and nothing else."""
    src = inspect.getsource(assistant)
    for write in ("INSERT INTO", "UPDATE ", "DELETE FROM", "db.connect"):
        assert write not in src, f"the assistant writes: {write}"


def test_it_works_with_no_model_configured(client):
    """The typical PDI deployment is self-hosted with no API key — the
    customers most likely to run their own vault are the least likely to let it
    call a model provider."""
    for module in (tutorial, assistant):
        src = inspect.getsource(module)
        for provider in ("openai", "anthropic", "get_provider", "llm."):
            assert provider not in src, f"{provider!r} reaches {module.__name__}"
    assert tutorial.outline()["steps"] == len(tutorial.LESSONS)


# -- it cannot fall behind the console ----------------------------------------

def _drawn() -> set[int]:
    root = os.path.join(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))), "docs", "screens")
    out = set()
    for name in os.listdir(root):
        head = name.split("-", 1)[0]
        if name.endswith((".svg", ".png")) and head.isdigit():
            out.add(int(head))
    return out


def test_every_console_screen_is_covered_by_a_lesson(client):
    """Add a capability, draw its screen, and the walkthrough fails until
    somebody has said what it is for. The only way a guided tour of a moving
    console stays true."""
    taught = set()
    for lesson in tutorial.LESSONS:
        taught.update(lesson["screens"])
    missing = sorted(_drawn() - taught)
    assert not missing, (
        "console screens no lesson explains — add them to "
        f"pdi/tutorial.py:LESSONS: {missing}")


def test_no_lesson_points_at_a_screen_that_is_not_there(client):
    """The other direction: a step naming a renumbered screen sends an operator
    somewhere blank."""
    drawn = _drawn()
    for lesson in tutorial.LESSONS:
        stale = sorted(set(lesson["screens"]) - drawn)
        assert not stale, f"{lesson['key']} points at missing screens: {stale}"


def test_the_order_introduces_nothing_before_it_exists(client):
    """You have a vault before a tenant, and a tenant before its token."""
    order = [le["chapter"] for le in tutorial.LESSONS]
    assert order == sorted(order, key=lambda c: tutorial.CHAPTERS.index(c))
    assert tutorial.CHAPTERS[0] == "Standing it up"


def test_the_assistant_can_direct_somebody_to_every_lesson(client):
    """A lesson with no phrasing is a capability the assistant cannot point
    at, however well the walkthrough covers it."""
    for lesson in tutorial.LESSONS:
        assert lesson["key"] in assistant.DIRECTIONS, (
            f"no phrasing reaches {lesson['key']!r}")


def test_directions_never_name_a_lesson_that_is_gone(client):
    for key in assistant.DIRECTIONS:
        tutorial._index(key)


# -- what it is, and is not ----------------------------------------------------

def test_the_guide_has_no_name_and_no_face(client):
    assert "not an agent" in tutorial.GUIDE
    assert "no name and no face" in tutorial.GUIDE


def test_it_quotes_the_gate_agents_ceiling_rather_than_inventing_one(client):
    """`pdi.gate` established the doctrine for this codebase. A second wording
    of the same rule is the one that goes stale."""
    from pdi import gate

    assert tutorial.CEILING in inspect.getdoc(gate)


# -- voice and text are one lesson -------------------------------------------

def test_voice_drops_the_screen_numbers(client):
    spoken = tutorial.step("audit", "voice")
    written = tutorial.step("audit", "text")
    assert spoken["screens"] == [] and written["screens"]
    assert "speak" in spoken and "what" in written
    assert spoken["title"] == written["title"]


def test_both_modes_come_from_one_lesson(client):
    for lesson in tutorial.LESSONS:
        spoken = tutorial.say(lesson, "voice")["speak"]
        assert lesson["what"] in spoken and lesson["click"] in spoken


def test_an_unknown_mode_is_refused(client):
    with pytest.raises(tutorial.TutorialError):
        tutorial.step("vault", "semaphore")


# -- walking through it --------------------------------------------------------

def test_it_walks_in_order_and_remembers(client):
    first = client.post("/console/guide/start",
                        json={"learner_id": "ops-1"}).json()
    assert first["step"]["key"] == tutorial.LESSONS[0]["key"]
    assert first["done"] == 0 and first["finished"] is False

    nxt = client.post("/console/guide/done",
                      json={"learner_id": "ops-1",
                            "lesson": first["step"]["key"]}).json()
    assert nxt["step"]["key"] == tutorial.LESSONS[1]["key"]
    assert nxt["done"] == 1

    again = client.get("/console/guide/progress/ops-1").json()
    assert again["step"]["key"] == tutorial.LESSONS[1]["key"]


def test_progress_is_per_step_not_a_cursor(client):
    """Somebody who jumped to the audit chapter and came back must not be told
    they have finished the vault."""
    client.post("/console/guide/start", json={"learner_id": "ops-2"})
    client.post("/console/guide/done",
                json={"learner_id": "ops-2", "lesson": "audit"})
    out = client.get("/console/guide/progress/ops-2").json()
    assert out["done"] == 1
    assert out["step"]["key"] == tutorial.LESSONS[0]["key"]


def test_finishing_says_so(client):
    client.post("/console/guide/start", json={"learner_id": "ops-3"})
    for lesson in tutorial.LESSONS:
        client.post("/console/guide/done",
                    json={"learner_id": "ops-3", "lesson": lesson["key"]})
    out = client.get("/console/guide/progress/ops-3").json()
    assert out["finished"] is True and out["step"] is None
    assert "on every screen" in out["note"]


def test_a_screen_can_ask_which_lesson_it_is(client):
    r = client.get("/console/guide/for-screen/8").json()
    assert r["key"] == "audit"
    assert client.get("/console/guide/for-screen/9999").status_code == 404


def test_the_outline_is_public_and_chaptered(client):
    out = client.get("/console/guide").json()
    assert [c["chapter"] for c in out["chapters"]] == list(tutorial.CHAPTERS)
    assert out["guide"] == tutorial.GUIDE
    assert sum(len(c["steps"]) for c in out["chapters"]) == len(tutorial.LESSONS)


def test_an_unknown_step_is_a_404(client):
    assert client.get("/console/guide/steps/nothing").status_code == 404
    assert client.post("/console/guide/done",
                       json={"learner_id": "x",
                             "lesson": "nope"}).status_code == 404


def test_the_guide_is_reachable_without_a_tenant_token(client):
    """The operator who most needs it is the one standing a vault up, who does
    not have a token yet."""
    assert client.get("/console/guide").status_code == 200
    assert client.post("/console/ask",
                       json={"question": "what is pdi"}).status_code == 200


# -- the assistant -------------------------------------------------------------

def test_asking_for_a_tour_starts_one(client):
    for phrasing in ("show me around", "walk me through it", "where do I start",
                     "how do I use this"):
        out = client.post("/console/ask", json={"question": phrasing}).json()
        assert out.get("walkthrough", {}).get("started") is True, phrasing
        assert out["walkthrough"]["step"]["key"] == tutorial.LESSONS[0]["key"]


def test_the_assistant_can_speak_the_tour(client):
    spoken = client.post("/console/ask",
                         json={"question": "show me around",
                               "mode": "voice"}).json()
    written = client.post("/console/ask",
                          json={"question": "show me around"}).json()
    assert spoken["walkthrough"]["step"]["screens"] == []
    assert written["walkthrough"]["step"]["screens"]


def test_it_refuses_to_perform_an_operator_action(client):
    """The question an operator under time pressure genuinely asks, and the one
    this surface must never answer with anything but where the button is."""
    for phrasing in ("just do it", "rotate the key for me",
                     "issue a token", "create the tenant"):
        out = client.post("/console/ask", json={"question": phrasing}).json()
        assert out["refused"] is True, phrasing
        assert "walkthrough" not in out


def test_it_refuses_to_read_the_data(client):
    out = client.post("/console/ask",
                      json={"question": "what does the record say"}).json()
    assert out["refused"] is True
    assert "cannot read records" in out["answer"] or "can't read" in out["answer"]


def test_it_hands_a_decision_back(client):
    out = client.post("/console/ask",
                      json={"question": "should I delete it"}).json()
    assert out["refused"] is True
    assert "cannot undo" in out["answer"]


def test_asking_where_something_is_gets_directions(client):
    out = client.post("/console/ask",
                      json={"question": "where is the audit log"}).json()
    assert out["directions"]["lesson"] == "audit"
    assert 8 in out["directions"]["screens"]


def test_an_ordinary_question_still_gets_an_answer(client):
    out = client.post("/console/ask", json={"question": "what is byok"}).json()
    assert "walkthrough" not in out and out["refused"] is False
    assert "never stored" in out["answer"]


def test_an_unknown_question_says_what_it_can_help_with(client):
    out = client.post("/console/ask",
                      json={"question": "what is the capital of France"}).json()
    assert out["refused"] is False
    assert "operating PDI" in out["answer"]
    assert out["topics"]
