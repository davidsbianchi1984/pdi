"""Connected-app connectors: a tenant links a catalog app and its agents
collect (sealed to the vault), act, or produce through it."""

from pdi.tests.conftest import auth, new_tenant


def _connect(client, token, **body):
    r = client.post("/apps", json=body, headers=auth(token))
    assert r.status_code == 201, r.text
    return r.json()


def test_connect_and_ingest_seals_to_vault(client):
    token = new_tenant(client)
    conn = _connect(client, token, provider="apple", app="photos")
    assert "collect" in conn["directions"]

    r = client.post(f"/apps/{conn['id']}/ingest", headers=auth(token), json={
        "items": [{"content": "birthday album", "ref": "a1"},
                  {"content": "beach trip", "ref": "a2"}]})
    assert r.status_code == 201, r.text
    assert r.json()["sealed"] == 2

    keys = client.get("/records", headers=auth(token)).json()["keys"]
    app_keys = [k for k in keys if k.startswith("app/apple/photos/")]
    assert len(app_keys) == 2
    assert client.get("/apps", headers=auth(token)).json()[0]["collected"] == 2


def test_invoke_and_grants(client):
    token = new_tenant(client)
    conn = _connect(client, token, provider="canva", app="magic_studio",
                    capabilities=["magic-media"])
    r = client.post(f"/apps/{conn['id']}/invoke", headers=auth(token),
                    json={"capability": "magic-media", "input": "a poster"})
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "performed"
    assert client.post(f"/apps/{conn['id']}/invoke", headers=auth(token),
                       json={"capability": "magic-design"}).status_code == 422


def test_unknown_and_produce_only(client):
    token = new_tenant(client)
    assert client.post("/apps", headers=auth(token),
                       json={"provider": "apple", "app": "toaster"}).status_code == 404
    paint = _connect(client, token, provider="microsoft", app="paint")
    assert client.post(f"/apps/{paint['id']}/ingest", headers=auth(token),
                       json={"items": [{"content": "x"}]}).status_code == 409


def test_tenant_isolation_and_revoke(client):
    owner = new_tenant(client, name="owner")
    other = new_tenant(client, name="other")
    conn = _connect(client, owner, provider="google", app="gmail")
    # Another tenant can't see or touch it.
    assert client.get("/apps", headers=auth(other)).json() == []
    assert client.post(f"/apps/{conn['id']}/invoke", headers=auth(other),
                       json={"capability": "summaries"}).status_code == 404
    # Revoke stops use.
    assert client.delete(f"/apps/{conn['id']}", headers=auth(owner)).json()["status"] == "revoked"
    assert client.post(f"/apps/{conn['id']}/invoke", headers=auth(owner),
                       json={"capability": "summaries"}).status_code == 409
