"""Robots as vault-backed data sources: bind, sealed ingest, custody."""

from pdi.tests.conftest import auth, new_tenant


def test_catalog_lists_platforms_and_data_kinds(client):
    cat = client.get("/robotics/catalog").json()
    models = {r["model"] for r in cat["robots"]}
    assert {"isaac_1", "neo", "u1_lite", "u1_pro", "u1_ultra", "memo",
            "saros_20", "saros_20_sonic", "qrevo_curv_2_flow"} <= models
    assert cat["data_kinds"] == ["map", "snapshot", "sensor_log"]


def test_bind_ingest_seals_into_the_vault(client):
    tok = new_tenant(client)
    rob = client.post("/robots", json={"model": "saros_20", "name": "runner"},
                      headers=auth(tok)).json()
    assert rob["maker"] == "Roborock"

    r = client.post(f"/robots/{rob['id']}/ingest",
                    json={"kind": "map", "content": '{"rooms": 5}'},
                    headers=auth(tok))
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["sealed"] is True
    key = body["key"]
    assert key.startswith(f"robot/saros_20/{rob['id']}/map/")

    # The sealed item is readable through the normal (audited) record path.
    import json
    rec = client.get(f"/records/{key}", headers=auth(tok)).json()
    stored = json.loads(rec["value"])
    assert stored["kind"] == "map" and json.loads(stored["content"])["rooms"] == 5

    # Custody: the ingest is in the hash-chained audit log, chain intact.
    entries = client.get("/audit", headers=auth(tok)).json()
    assert any(e["action"] == "robot.ingest" and e["ref"] == key
               for e in entries)
    assert client.get("/audit/verify", headers=auth(tok)).json()["intact"] is True


def test_robot_data_lists_only_this_robots_keys(client):
    tok = new_tenant(client)
    a = client.post("/robots", json={"model": "memo"}, headers=auth(tok)).json()
    b = client.post("/robots", json={"model": "neo"}, headers=auth(tok)).json()
    client.post(f"/robots/{a['id']}/ingest",
                json={"kind": "snapshot", "content": "kitchen"}, headers=auth(tok))
    client.post(f"/robots/{b['id']}/ingest",
                json={"kind": "sensor_log", "content": "steps"}, headers=auth(tok))

    keys_a = client.get(f"/robots/{a['id']}/data", headers=auth(tok)).json()["keys"]
    assert len(keys_a) == 1 and f"/{a['id']}/" in keys_a[0]


def test_unknown_kind_and_model_are_refused(client):
    tok = new_tenant(client)
    assert client.post("/robots", json={"model": "terminator"},
                       headers=auth(tok)).status_code == 404
    rob = client.post("/robots", json={"model": "u1_pro"},
                      headers=auth(tok)).json()
    assert client.post(f"/robots/{rob['id']}/ingest",
                       json={"kind": "video_feed", "content": "x"},
                       headers=auth(tok)).status_code == 422


def test_unbind_stops_ingest_but_keeps_sealed_data(client):
    tok = new_tenant(client)
    rob = client.post("/robots", json={"model": "isaac_1"},
                      headers=auth(tok)).json()
    key = client.post(f"/robots/{rob['id']}/ingest",
                      json={"kind": "map", "content": "m"},
                      headers=auth(tok)).json()["key"]
    client.delete(f"/robots/{rob['id']}", headers=auth(tok))
    # Further ingest refused; the sealed record is still tenant-readable.
    assert client.post(f"/robots/{rob['id']}/ingest",
                       json={"kind": "map", "content": "m2"},
                       headers=auth(tok)).status_code == 409
    assert client.get(f"/records/{key}", headers=auth(tok)).status_code == 200


def test_tenant_isolation(client):
    tok_a, tok_b = new_tenant(client, "acme"), new_tenant(client, "globex")
    rob = client.post("/robots", json={"model": "neo"}, headers=auth(tok_a)).json()
    # Tenant B cannot see or feed tenant A's robot.
    assert client.get("/robots", headers=auth(tok_b)).json() == []
    assert client.post(f"/robots/{rob['id']}/ingest",
                       json={"kind": "map", "content": "spy"},
                       headers=auth(tok_b)).status_code == 404


def test_robot_endpoints_require_a_token(client):
    assert client.post("/robots", json={"model": "neo"}).status_code == 401
    assert client.get("/robots").status_code == 401
