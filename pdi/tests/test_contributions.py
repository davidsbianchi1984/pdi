"""Cloud-model contribution intake: sealed, tenant-scoped, audited."""

import sqlite3

from pdi import db as pdi_db
from pdi.tests.conftest import new_tenant


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_contributions_sealed_and_listed(client):
    token = new_tenant(client, name="cloud-model")
    r = client.post("/contributions", headers=_auth(token), json={
        "source": "qrme", "kind": "rated_exchange",
        "payload": {"quality": "positive",
                    "exchange": [{"role": "interactor", "content": "hi PERSONA"}]}})
    assert r.status_code == 201
    body = r.json()
    assert body["sealed"] is True and body["key"].startswith("contributions/qrme/")

    client.post("/contributions", headers=_auth(token), json={
        "source": "jim-mini", "kind": "guidance_outcome",
        "payload": {"condition": "anxiety", "rating": "up"}})

    listing = client.get("/contributions", headers=_auth(token)).json()
    assert listing["count"] == 2
    assert any(k.startswith("contributions/jim-mini/") for k in listing["keys"])

    # Encrypted at rest: the plaintext never appears in the database file.
    raw = sqlite3.connect(pdi_db.db_path()).execute(
        "SELECT ciphertext FROM records").fetchall()
    blob = " ".join(r[0] for r in raw)
    assert "anxiety" not in blob and "PERSONA" not in blob

    # And the intake is on the audit chain.
    assert client.get("/audit/verify", headers=_auth(token)).json()["intact"] is True


def test_read_only_token_cannot_contribute(client):
    token = new_tenant(client)
    tenant = client.get("/audit", headers=_auth(token)).json()[0]["tenant_id"]
    read = client.post(f"/tenants/{tenant}/tokens", json={"role": "read"}).json()
    r = client.post("/contributions", headers=_auth(read["token"]), json={
        "source": "qrme", "kind": "rated_exchange", "payload": {}})
    assert r.status_code == 403
