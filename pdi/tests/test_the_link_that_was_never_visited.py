"""The imported link, finally visited — the vault's side.

A ``collect`` connector has carried the account's public address since the
day it was made, and the ingest door only ever sealed what the tenant pasted.
``POST /connectors/{cid}/scrape`` goes to the address and seals what a
browser would show anybody — the title, the metadata bio, the visible text —
as one encrypted vault record with the URL and fetch time written in. PDI is
where the raw social data other systems build profiles from actually lands;
this is that data arriving from the page itself.

The fetch is monkeypatched throughout; the one path that must never touch
the network — an offline deployment — is tested by poisoning the fetcher.
The three refusal tests here share their names with the sibling products'
copies of this file, because the door is the same door three times.
"""

from pdi import offline, scrape
from pdi.tests.conftest import auth, new_tenant


def _create(client, token, **body):
    r = client.post("/connectors", json=body, headers=auth(token))
    assert r.status_code == 201, r.text
    return r.json()


_PAGE = """
<html><head><title>Dana Grows (@dana.grows)</title>
<meta property="og:description" content="Market gardener. Tomatoes, compost, patience." />
</head><body>
<script>ignore me entirely</script>
<p>Growing food in a small space since 2019.</p>
</body></html>
"""


def test_scrape_seals_the_public_page_into_the_vault(client, monkeypatch):
    token = new_tenant(client)
    conn = _create(client, token, platform="instagram", direction="collect",
                   handle="dana.grows")
    seen = {}

    def fake_fetch(url):
        seen["url"] = url
        return _PAGE
    monkeypatch.setattr(scrape, "fetch", fake_fetch)

    r = client.post(f"/connectors/{conn['id']}/scrape", headers=auth(token))
    assert r.status_code == 201, r.text
    out = r.json()
    assert out["sealed_count"] == 1
    assert out["url"] == "https://instagram.com/dana.grows"
    assert seen["url"] == out["url"]
    assert "Dana Grows" in out["title"]

    # One encrypted record, provenance included, readable back by its owner.
    key = out["keys"][0]
    rec = client.get(f"/records/{key}", headers=auth(token)).json()
    assert "Tomatoes, compost, patience" in rec["value"]
    assert "Fetched from https://instagram.com/dana.grows" in rec["value"]
    assert "ignore me entirely" not in rec["value"]

    assert client.get("/connectors", headers=auth(token)).json()[0]["collected"] == 1


def test_offline_refuses_before_any_socket(client, monkeypatch):
    token = new_tenant(client)
    conn = _create(client, token, platform="x", direction="collect",
                   handle="dana")

    def explode(url):
        raise AssertionError("offline deployment opened a socket")
    monkeypatch.setattr(scrape, "fetch", explode)
    monkeypatch.setattr(offline, "enabled", lambda: True)

    r = client.post(f"/connectors/{conn['id']}/scrape", headers=auth(token))
    assert r.status_code == 409
    assert "offline" in r.json()["detail"].lower()


def test_a_connection_without_an_address_is_told_so(client):
    token = new_tenant(client)
    conn = _create(client, token, platform="instagram", direction="collect")
    r = client.post(f"/connectors/{conn['id']}/scrape", headers=auth(token))
    assert r.status_code == 400
    assert "handle" in r.json()["detail"]


def test_publish_connections_do_not_scrape(client):
    token = new_tenant(client)
    conn = _create(client, token, platform="instagram", direction="publish",
                   handle="dana.grows")
    r = client.post(f"/connectors/{conn['id']}/scrape", headers=auth(token))
    assert r.status_code == 409
