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
    # Every supported language now carries hand-translated notes.
    assert all(l["notes_translated"] for l in cat["languages"])

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


def test_japanese_notes_localize(client):
    token = new_tenant(client)
    client.put("/language", json={"language": "ja"}, headers=auth(token))
    robot = client.post("/robots", json={"model": "neo"},
                        headers=auth(token)).json()
    r = client.post(f"/robots/{robot['id']}/ingest",
                    json={"kind": "map", "content": "hi"},
                    headers=auth(token)).json()
    assert "暗号化" in r["note"]


def test_unknown_strings_pass_through_untouched(client):
    from pdi import i18n
    assert i18n.tr("a string nobody translated", "ja") == \
        "a string nobody translated"


def test_every_language_has_complete_note_coverage(client):
    from pdi import i18n
    langs = set(i18n.SUPPORTED) - {i18n.DEFAULT}
    for source, translations in i18n._STRINGS.items():
        missing = langs - set(translations)
        assert not missing, f"{source[:40]!r} missing {sorted(missing)}"


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


# ---- delivery mode and the dictionary translate endpoint --------------------

def test_on_demand_mode_keeps_english_notes(client):
    token = new_tenant(client)
    client.put("/language", json={"language": "es", "mode": "on_demand"},
               headers=auth(token))
    assert client.get("/language", headers=auth(token)).json()["mode"] == \
        "on_demand"
    robot = client.post("/robots", json={"model": "neo"},
                        headers=auth(token)).json()
    r = client.post(f"/robots/{robot['id']}/ingest",
                    json={"kind": "map", "content": "hi"},
                    headers=auth(token)).json()
    assert "encrypted at rest" in r["note"]
    # Flipping back to pre restores translated notes.
    client.put("/language", json={"language": "es", "mode": "pre"},
               headers=auth(token))
    r = client.post(f"/robots/{robot['id']}/ingest",
                    json={"kind": "map", "content": "hola"},
                    headers=auth(token)).json()
    assert "cifrados" in r["note"]


def test_translate_endpoint_is_dictionary_only_and_honest(client):
    token = new_tenant(client)
    client.put("/language", json={"language": "es"}, headers=auth(token))
    r = client.post("/translate", json={
        "text": "robot data is encrypted at rest in the vault"},
        headers=auth(token)).json()
    assert r["engine"] == "hand" and "cifrados" in r["translation"]
    r = client.post("/translate", json={"text": "arbitrary tenant prose"},
                    headers=auth(token)).json()
    assert r["engine"] == "none" and "no machine translation" in r["note"]
    r = client.post("/translate", json={"text": "hi", "to": "xx"},
                    headers=auth(token))
    assert r.status_code == 422
