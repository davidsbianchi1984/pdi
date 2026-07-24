""""Help us improve": product feedback on PDI itself — open to anyone,
private per submitter, with a public aggregate tally. Not tenant record
data, so it needs no token; a tenant token just lets a submitter find their
own words again."""

from pdi.tests.conftest import new_tenant, auth


def test_anyone_can_submit_and_it_tallies(client):
    # No token — an anonymous operator can still be heard.
    r = client.post("/improve", json={"category": "idea",
                                      "message": "a per-tenant usage dashboard"})
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "received"

    client.post("/improve", json={"category": "bug", "message": "audit export truncates"})

    state = client.get("/improve").json()
    assert state["total"] == 2
    assert state["tally"]["idea"] == 1
    assert state["tally"]["bug"] == 1
    # An anonymous caller sees the tally but none of the words.
    assert state["mine"] == []


def test_bad_category_and_rating_and_message_refused(client):
    assert client.post("/improve", json={"category": "rant",
                                         "message": "x"}).status_code == 422
    assert client.post("/improve", json={"category": "idea",
                                         "message": "   "}).status_code == 422
    assert client.post("/improve", json={"category": "idea", "message": "ok",
                                         "rating": 0}).status_code == 422
    assert client.post("/improve", json={"category": "praise", "message": "solid",
                                         "rating": 5}).status_code == 201


def test_authenticated_tenant_sees_only_their_own(client):
    token = new_tenant(client)
    client.post("/improve", json={"category": "improvement",
                                  "message": "clearer retention wording",
                                  "rating": 4}, headers=auth(token))
    state = client.get("/improve", headers=auth(token)).json()
    assert len(state["mine"]) == 1
    assert state["mine"][0]["message"] == "clearer retention wording"
    assert state["mine"][0]["status"] == "received"


def test_two_tenants_dont_see_each_others_words(client):
    a = new_tenant(client, name="acme")
    client.post("/improve", json={"category": "idea", "message": "acme's idea"},
                headers=auth(a))

    b = new_tenant(client, name="globex")
    client.post("/improve", json={"category": "bug", "message": "globex's bug"},
                headers=auth(b))

    b_view = client.get("/improve", headers=auth(b)).json()
    assert [m["message"] for m in b_view["mine"]] == ["globex's bug"]
    assert b_view["total"] == 2          # tally spans everyone

    a_view = client.get("/improve", headers=auth(a)).json()
    assert [m["message"] for m in a_view["mine"]] == ["acme's idea"]
    assert a_view["total"] == 2
