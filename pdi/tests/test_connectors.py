"""Social-platform connectors: collect seals content into the vault, publish
shares an update reachable by a QR beacon."""

from pdi.tests.conftest import auth, new_tenant


def _create(client, token, **body):
    r = client.post("/connectors", json=body, headers=auth(token))
    assert r.status_code == 201, r.text
    return r.json()


def test_collect_seals_into_the_vault(client):
    token = new_tenant(client)
    conn = _create(client, token, platform="instagram", direction="collect",
                   handle="@dana")
    assert conn["direction"] == "collect"
    assert conn["beacon"] is None

    r = client.post(f"/connectors/{conn['id']}/ingest", headers=auth(token), json={
        "items": [{"content": "Tomatoes are in.", "ref": "p1"},
                  {"content": "Compost tea.", "ref": "p2"}]})
    assert r.status_code == 201, r.text
    out = r.json()
    assert out["sealed"] == 2

    # Collected items are now encrypted records in this tenant's vault.
    keys = client.get("/records", headers=auth(token)).json()["keys"]
    social = [k for k in keys if k.startswith("social/instagram/")]
    assert len(social) == 2
    # And they read back decrypted.
    rec = client.get(f"/records/{social[0]}", headers=auth(token)).json()
    assert "content" in rec["value"]

    assert client.get("/connectors", headers=auth(token)).json()[0]["collected"] == 2


def test_publish_and_qr_beacon(client):
    token = new_tenant(client)
    conn = _create(client, token, platform="x", direction="publish", handle="dana")
    assert conn["beacon"] == f"/connectors/{conn['id']}/beacon"

    r = client.post(f"/connectors/{conn['id']}/publish", headers=auth(token),
                    json={"content": "Vault is live.", "topic": "status"})
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "published"

    beacon = client.get(f"/connectors/{conn['id']}/beacon", headers=auth(token)).json()
    assert beacon["presence_url"] == "https://x.com/dana"
    qr = client.get(f"/connectors/{conn['id']}/qr.svg", headers=auth(token))
    assert qr.status_code == 200
    assert qr.headers["content-type"] == "image/svg+xml"
    assert b"<svg" in qr.content


def test_direction_guards(client):
    token = new_tenant(client)
    collect = _create(client, token, platform="tiktok", direction="collect")
    publish = _create(client, token, platform="youtube", direction="publish")
    assert client.post(f"/connectors/{collect['id']}/publish", headers=auth(token),
                       json={"content": "x"}).status_code == 409
    assert client.post(f"/connectors/{publish['id']}/ingest", headers=auth(token),
                       json={"items": [{"content": "x"}]}).status_code == 409
    assert client.get(f"/connectors/{collect['id']}/beacon",
                      headers=auth(token)).status_code == 409


def test_revoke_stops_ingest(client):
    token = new_tenant(client)
    conn = _create(client, token, platform="threads", direction="collect")
    assert client.delete(f"/connectors/{conn['id']}",
                         headers=auth(token)).json()["status"] == "revoked"
    r = client.post(f"/connectors/{conn['id']}/ingest", headers=auth(token),
                    json={"items": [{"content": "x"}]})
    assert r.status_code == 409


def test_all_image_platforms_supported(client):
    token = new_tenant(client)
    platforms = ["instagram", "x", "tiktok", "facebook", "linkedin", "youtube",
                 "reddit", "threads", "whatsapp", "meta", "mastodon", "twitch",
                 "snapchat", "roblox", "pinterest", "discord"]
    for p in platforms:
        assert _create(client, token, platform=p, direction="collect")["platform"] == p
    for p, url in [("twitch", "https://twitch.tv/dana"),
                   ("discord", "https://discord.com/users/dana")]:
        conn = _create(client, token, platform=p, direction="publish", handle="dana")
        beacon = client.get(f"/connectors/{conn['id']}/beacon", headers=auth(token)).json()
        assert beacon["presence_url"] == url


def test_connectors_are_tenant_isolated(client):
    owner = new_tenant(client, name="owner")
    other = new_tenant(client, name="other")
    conn = _create(client, owner, platform="reddit", direction="collect")
    # Another tenant cannot see or touch this connector.
    assert client.get("/connectors", headers=auth(other)).json() == []
    assert client.post(f"/connectors/{conn['id']}/ingest", headers=auth(other),
                       json={"items": [{"content": "x"}]}).status_code == 404
