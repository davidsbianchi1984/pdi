"""Where the vault physically lives, and the promise that the free option is
not the degraded one.

(Distinct from `test_hosting.py`, which is about network posture — whether a
deployment is safe on a routable address. This is about *which building*.)

The test that matters is `test_no_mode_holds_fewer_guarantees_than_another`.
PDI is the layer QRME and JIM-mini put sensitive material into, and the reason
a customer can trust that is BYOK plus the ability to hold their own hardware.
A hosting page that quietly made self-hosting weaker than colocation would be
selling the opposite of the product — and it would be an easy thing to do a
field at a time, which is why it is asserted rather than intended.
"""

import pytest

from pdi import hosting, vault
from pdi.tests.conftest import auth, new_tenant


def _tenant_id(token: str) -> str:
    return vault.tenant_by_token(token)["id"]


# -- the free option is not the worse option ----------------------------------

def test_no_mode_holds_fewer_guarantees_than_another(client):
    """One shared list, not a list per mode. A mode cannot drop an entry
    because there is no per-mode copy to drop it from."""
    page = client.get("/hosting").json()
    for name, spec in page["modes"].items():
        assert spec["guarantees"] == list(hosting.GUARANTEES), name


def test_the_guarantees_are_the_ones_the_product_is_sold_on(client):
    joined = " ".join(hosting.GUARANTEES).lower()
    for claim in ("aes-256-gcm", "tamper-evident", "isolation",
                  "bring-your-own-key", "sha-256", "retention"):
        assert claim in joined, claim


def test_colocation_and_your_own_device_are_free(client):
    """Free for holding JIM-mini and QRME data is the arrangement: a price
    there would make those products' promise conditional on somebody's card."""
    page = client.get("/hosting").json()
    assert set(page["free"]) == {"colocation", "own_device"}


def test_the_leased_options_are_quoted_rather_than_invented(client):
    """A rack in one city is not a rack in another, and a made-up figure on a
    page like this is the kind of thing somebody plans a budget around."""
    for mode in ("leased_space", "own_facility"):
        assert hosting.MODES[mode]["price"] == "quoted"


def test_every_mode_says_who_holds_what_up(client):
    """A hosting page listing only upside would be selling the wrong thing to
    the person most likely to need the other kind."""
    for name, spec in hosting.MODES.items():
        assert spec["availability"], name
        assert "we_are_responsible_for" in spec, name
        assert "you_are_responsible_for" in spec, name


def test_your_own_device_is_honest_about_what_changes(client):
    """The bytes on a phone are exactly as encrypted as ours. Whether they are
    there tomorrow is a different question, and it is the customer's."""
    own = hosting.MODES["own_device"]
    assert own["we_are_responsible_for"] == ()
    for thing in ("the device", "your broadband", "backups"):
        assert thing in own["you_are_responsible_for"], thing
    assert "encrypted as ours" in own["availability"]


def test_the_guidance_recommends_rather_than_obstructs(client):
    page = client.get("/hosting").json()
    assert "free" in page["guidance"]
    assert "not a toy" in page["guidance"]


# -- choosing one --------------------------------------------------------------

def test_a_tenant_starts_in_colocation(client):
    token = new_tenant(client)
    out = client.get(f"/hosting/{_tenant_id(token)}",
                     headers=auth(token)).json()
    assert out["mode"] == "colocation"
    assert out["price"] == "free"
    assert out["chosen"] is False


def test_choosing_records_rather_than_moves(client):
    """Nothing here migrates data. An endpoint that silently moved somebody's
    vault because a field changed would be the most alarming one in this
    product, so `choose` writes a row and stops."""
    import inspect

    src = inspect.getsource(hosting.choose).lower()
    body = src.split('"""', 2)[-1]          # past the docstring
    for verb in ("copy", "migrate", "transfer", "shutil", "ship"):
        assert verb not in body, f"choose() does something with {verb!r}"


def test_a_choice_round_trips(client):
    token = new_tenant(client)
    tid = _tenant_id(token)
    r = client.put(f"/hosting/{tid}",
                   json={"mode": "own_device", "note": "a phone in a drawer"},
                   headers=auth(token))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["mode"] == "own_device" and body["price"] == "free"
    assert body["note"] == "a phone in a drawer"
    assert body["guarantees"] == list(hosting.GUARANTEES)


def test_the_history_survives_a_move(client):
    """Where a vault has lived is exactly what an auditor asks afterwards."""
    token = new_tenant(client)
    tid = _tenant_id(token)
    client.put(f"/hosting/{tid}", json={"mode": "leased_space"},
               headers=auth(token))
    client.put(f"/hosting/{tid}", json={"mode": "own_facility"},
               headers=auth(token))
    out = client.get(f"/hosting/{tid}/history", headers=auth(token)).json()
    assert [h["mode"] for h in out["history"]] == ["leased_space",
                                                   "own_facility"]
    assert out["history"][0]["ended_at"] is not None
    assert out["history"][1]["ended_at"] is None


def test_one_live_arrangement_at_a_time(client):
    from pdi import db

    token = new_tenant(client)
    tid = _tenant_id(token)
    client.put(f"/hosting/{tid}", json={"mode": "leased_space"},
               headers=auth(token))
    client.put(f"/hosting/{tid}", json={"mode": "own_device"},
               headers=auth(token))
    live = db.connect().execute(
        "SELECT COUNT(*) AS n FROM tenant_hosting WHERE tenant_id=? AND"
        " ended_at IS NULL", (tid,)).fetchone()["n"]
    assert live == 1


def test_an_unknown_mode_is_refused(client):
    token = new_tenant(client)
    tid = _tenant_id(token)
    r = client.put(f"/hosting/{tid}", json={"mode": "the_moon"},
                   headers=auth(token))
    assert r.status_code == 422
    with pytest.raises(hosting.HostingError):
        hosting.choose(tid, "the_moon")


def test_another_tenant_cannot_read_or_set_your_arrangement(client):
    mine = new_tenant(client, name="qrme")
    theirs = new_tenant(client, name="jim-mini")
    my_id = _tenant_id(mine)

    assert client.get(f"/hosting/{my_id}",
                      headers=auth(theirs)).status_code == 403
    assert client.put(f"/hosting/{my_id}", json={"mode": "own_device"},
                      headers=auth(theirs)).status_code == 403
    assert client.get(f"/hosting/{my_id}/history",
                      headers=auth(theirs)).status_code == 403
    assert hosting.mode_of(my_id) == "colocation"


def test_the_hosting_page_is_public(client):
    """Somebody choosing where to put sensitive data has to be able to read
    the options before they have a tenant."""
    assert client.get("/hosting").status_code == 200


def test_choosing_lands_in_the_audit_chain(client):
    """Where a vault lives is a material fact about custody, so it belongs in
    the tamper-evident log rather than only in a mutable row."""
    from pdi import db

    token = new_tenant(client)
    tid = _tenant_id(token)
    client.put(f"/hosting/{tid}", json={"mode": "own_facility"},
               headers=auth(token))
    rows = db.connect().execute(
        "SELECT action FROM audit WHERE ref=?", (tid,)).fetchall()
    assert any(r["action"] == "hosting.choose" for r in rows)
