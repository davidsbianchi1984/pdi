"""The console's helper dock.

The third of three, and the two tests that matter here are the ones specific to
an operator console: that the pane never acts, and that it cannot read a
record. The second is the same rule the guide and the assistant hold, and it is
worth holding in three places because it is the product's whole claim — under
BYOK the operator reading this console frequently cannot decrypt the data, so a
pane that showed a record would be asserting a capability the design denies.
"""

import inspect
import re

import pytest

from pdi import dock, vault
from pdi.tests.conftest import auth, new_tenant


def _tenant_id(token: str) -> str:
    return vault.tenant_by_token(token)["id"]


# -- it cannot act, and it cannot read ----------------------------------------

def test_the_dock_cannot_reach_the_vault(client):
    """Read from the AST rather than the text, so that writing the rule down
    in a docstring does not trip the guard enforcing it — the mistake the
    console guide's first version made."""
    import ast

    forbidden = {"vault", "crypto"}
    tree = ast.parse(inspect.getsource(dock))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                assert alias.name.split(".")[-1] not in forbidden
        elif isinstance(node, ast.Name):
            assert node.id not in forbidden, f"dock names {node.id!r} in code"


def test_the_dock_writes_nothing_but_where_it_sits(client):
    """The buttons this floats over rotate keys, revoke tokens and wipe
    vaults. `pdi/gate.py`'s ceiling — whatever a wrong answer cannot undo —
    puts every one of them far above a pane in a corner."""
    src = inspect.getsource(dock)
    written = set(re.findall(r"(?:INSERT INTO|DELETE FROM)\s+(\w+)", src))
    written |= set(re.findall(r"(?<!DO )\bUPDATE\s+(\w+)\s+SET", src))
    assert written <= {"dock_prefs"}, (
        f"the dock writes outside its own preferences: {written}")


def test_every_face_says_it_neither_acts_nor_reads(client):
    token = new_tenant(client)
    tid = _tenant_id(token)
    for name in dock.FACES:
        out = dock.face(tid, name)
        assert out["acts"] is False and out["reads_records"] is False
    assert dock.vocabulary()["acts"] is False
    assert dock.vocabulary()["reads_records"] is False


def test_what_may_never_be_in_the_pane_is_published(client):
    """Console screenshots go into tickets, runbooks and vendor threads — a
    wider audience than a phone's camera roll."""
    for key in ("record_contents", "record_keys", "tenant_names", "tokens",
                "audit_payloads", "customer_keys"):
        assert key in dock.NEVER
    assert set(dock.vocabulary()["never"]) == set(dock.NEVER)


def test_the_faces_are_counts_and_states_not_contents(client):
    """What an operator is watching for anyway."""
    joined = " ".join(dock.FACES.values()).lower()
    assert "count" in joined
    assert "no names" in joined


# -- the corner ----------------------------------------------------------------

def test_it_opens_on_the_lights_like_the_panel_it_replaced(client):
    """An operator has no wrist, and a chain that stopped verifying is exactly
    the state nobody thinks to go and check."""
    assert dock.DEFAULT_STATE == "open"
    assert dock.DEFAULT_FACE == "agents"
    token = new_tenant(client)
    out = client.get(f"/dock/{_tenant_id(token)}", headers=auth(token)).json()
    assert out["state"] == "open" and out["face"] == "agents"
    assert out["set"] is False


def test_the_pane_can_only_sit_at_the_bottom(client):
    assert set(dock.CORNERS) == {"bottom_right", "bottom_left"}
    token = new_tenant(client)
    with pytest.raises(dock.DockError):
        dock.configure(_tenant_id(token), corner="top_left")


def test_every_face_has_a_route_to_a_screen_that_exists(client):
    import os

    root = os.path.join(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))), "docs", "screens")
    drawn = {int(f.split("-", 1)[0]) for f in os.listdir(root)
             if f.endswith(".svg") and f.split("-", 1)[0].isdigit()}
    for name in dock.FACES:
        assert dock.route(name)["screen"] in drawn, name


def test_an_unknown_face_is_refused(client):
    token = new_tenant(client)
    tid = _tenant_id(token)
    with pytest.raises(dock.DockError):
        dock.face(tid, "nonsense")
    with pytest.raises(dock.DockError):
        dock.configure(tid, faces=["nonsense"])


def test_a_pane_with_no_faces_is_the_button_on_its_own(client):
    token = new_tenant(client)
    with pytest.raises(dock.DockError):
        dock.configure(_tenant_id(token), faces=[])


# -- over the wire -------------------------------------------------------------

def test_the_vocabulary_and_routing_table_are_public(client):
    assert client.get("/dock/faces").status_code == 200
    r = client.get("/dock/where/chain")
    assert r.status_code == 200 and r.json()["screen"] == 9
    assert client.get("/dock/where/nonsense").status_code == 404


def test_another_tenant_cannot_read_or_move_your_pane(client):
    mine = new_tenant(client, name="qrme")
    theirs = new_tenant(client, name="jim-mini")
    my_id = _tenant_id(mine)

    assert client.get(f"/dock/{my_id}", headers=auth(theirs)).status_code == 403
    assert client.put(f"/dock/{my_id}", json={"state": "hidden"},
                      headers=auth(theirs)).status_code == 403
    assert client.get(f"/dock/{my_id}/face/vault",
                      headers=auth(theirs)).status_code == 403


def test_moving_it_round_trips(client):
    token = new_tenant(client)
    tid = _tenant_id(token)
    r = client.put(f"/dock/{tid}",
                   json={"corner": "bottom_left", "state": "handle",
                         "face": "chain",
                         "faces": ["helper", "chain", "agents"]},
                   headers=auth(token))
    assert r.status_code == 200, r.text
    out = client.get(f"/dock/{tid}", headers=auth(token)).json()
    assert out["corner"] == "bottom_left" and out["face"] == "chain"
    assert out["state"] == "handle"
