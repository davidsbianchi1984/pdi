"""Per-tenant language + record provenance.

Language: a tenant sets a language and PDI's fixed explanatory note strings
localize in every JSON response (structured data untouched). Provenance:
GET /provenance/{key} returns a sealed record's derivation trail — origin,
cipher, tenant+key binding, and its tamper-evident audit history.
"""

from pdi.tests.conftest import auth, new_tenant


def test_language_catalog_and_choice(client):
    cat = client.get("/languages").json()
    assert cat["default"] == "en"
    codes = {l["code"]: l for l in cat["languages"]}
    assert codes["es"]["notes_translated"] is True
    assert codes["ja"]["notes_translated"] is False

    token = new_tenant(client)
    assert client.get("/language", headers=auth(token)).json()["language"] == "en"
    r = client.put("/language", json={"language": "klingon"}, headers=auth(token))
    assert r.status_code == 422
    r = client.put("/language", json={"language": "es"}, headers=auth(token)).json()
    assert r["label"] == "Español"


def test_notes_localize_in_responses(client):
    token = new_tenant(client)
    client.put("/language", json={"language": "es"}, headers=auth(token))
    # Robot ingest carries a fixed note; with es set, it arrives translated.
    robot = client.post("/robots", json={"model": "neo", "name": "hall NEO"},
                        headers=auth(token)).json()
    r = client.post(f"/robots/{robot['id']}/ingest",
                    json={"kind": "map", "content": "hola"},
                    headers=auth(token)).json()
    assert "cifrados" in r["note"]
    # Structured data is untouched.
    assert r["sealed"] is True and r["key"].startswith("robot/")


def test_unknown_language_keeps_english_notes(client):
    token = new_tenant(client)
    client.put("/language", json={"language": "ja"}, headers=auth(token))
    robot = client.post("/robots", json={"model": "neo"},
                        headers=auth(token)).json()
    r = client.post(f"/robots/{robot['id']}/ingest",
                    json={"kind": "map", "content": "hi"},
                    headers=auth(token)).json()
    assert "encrypted at rest" in r["note"]


def test_record_provenance_trail(client):
    token = new_tenant(client)
    h = auth(token)
    client.put("/records", json={"key": "jim/u1/medical/ev1",
                                 "value": "sealed payload"}, headers=h)
    client.get("/records/jim/u1/medical/ev1", headers=h)

    p = client.get("/provenance/jim/u1/medical/ev1", headers=h).json()
    assert "JIM Guardian" in p["origin"]
    assert "AES-256-GCM" in p["sealed"]["cipher"]
    assert "AAD" in p["sealed"]["bound_to"]
    assert p["sealed"]["ciphertext_bytes"] > 0
    actions = [e["action"] for e in p["audit"]["events"]]
    assert "put" in actions and "get" in actions
    assert p["chain"]["intact"] is True

    # Viewing provenance is itself audited.
    p2 = client.get("/provenance/jim/u1/medical/ev1", headers=h).json()
    assert "provenance.view" in [e["action"] for e in p2["audit"]["events"]]


def test_provenance_origin_for_direct_writes(client):
    token = new_tenant(client)
    h = auth(token)
    client.put("/records", json={"key": "notes/today", "value": "x"}, headers=h)
    p = client.get("/provenance/notes/today", headers=h).json()
    assert "direct API write" in p["origin"]


def test_provenance_missing_record_404(client):
    token = new_tenant(client)
    r = client.get("/provenance/never/stored", headers=auth(token))
    assert r.status_code == 404
