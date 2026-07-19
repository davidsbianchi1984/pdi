"""Role-based access control (scoped tokens) and disaster-recovery restore."""

from pdi.tests.conftest import new_tenant


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_read_only_token_cannot_write(client):
    write_token = new_tenant(client)
    client.put("/records", json={"key": "a", "value": "secret"},
               headers=_auth(write_token))
    # Issue a scoped read token for the same tenant.
    tenant = client.get("/audit", headers=_auth(write_token)).json()[0]["tenant_id"]
    read = client.post(f"/tenants/{tenant}/tokens", json={"role": "read"}).json()

    r = client.get("/records/a", headers=_auth(read["token"]))
    assert r.status_code == 200 and r.json()["value"] == "secret"
    assert client.put("/records", json={"key": "b", "value": "x"},
                      headers=_auth(read["token"])).status_code == 403
    assert client.delete("/records/a",
                         headers=_auth(read["token"])).status_code == 403

    # Revoking the scoped token kills it; the primary token still works.
    assert client.delete(f"/tokens/{read['token']}").status_code == 204
    assert client.get("/records/a",
                      headers=_auth(read["token"])).status_code == 401
    assert client.get("/records/a",
                      headers=_auth(write_token)).status_code == 200


def test_snapshot_restore_roundtrip(client):
    token = new_tenant(client)
    for key, value in (("users/1", "alpha"), ("users/2", "beta")):
        client.put("/records", json={"key": key, "value": value},
                   headers=_auth(token))
    snapshot = client.get("/snapshot", headers=_auth(token)).json()
    assert len(snapshot["records"]) == 2
    assert all("alpha" not in r["ciphertext"] for r in snapshot["records"])

    # Disaster: the records are lost.
    for key in ("users/1", "users/2"):
        client.delete(f"/records/{key}", headers=_auth(token))
    assert client.get("/records", headers=_auth(token)).json()["keys"] == []

    # Restore from the ciphertext-only snapshot.
    r = client.post("/restore", json={"records": snapshot["records"]},
                    headers=_auth(token))
    assert r.status_code == 200 and r.json()["restored"] == 2
    assert client.get("/records/users/1",
                      headers=_auth(token)).json()["value"] == "alpha"
    assert client.get("/records/users/2",
                      headers=_auth(token)).json()["value"] == "beta"
    # The whole story is in the audit chain, still intact.
    verify = client.get("/audit/verify", headers=_auth(token)).json()
    assert verify["intact"] is True


def test_admin_token_guards_tenant_creation(client, monkeypatch):
    """With PDI_ADMIN_TOKEN set, admin endpoints require it."""
    monkeypatch.setenv("PDI_ADMIN_TOKEN", "admin_secret")
    assert client.post("/tenants", json={"name": "x"}).status_code == 401
    assert client.post("/tenants", json={"name": "x"},
                       headers={"Authorization": "Bearer wrong"}).status_code == 403
    ok = client.post("/tenants", json={"name": "cloud-model"},
                     headers={"Authorization": "Bearer admin_secret"})
    assert ok.status_code == 201 and ok.json()["token"].startswith("pdi_")


def test_tenant_soft_delete_and_restore(client):
    token = new_tenant(client)
    client.put("/records", json={"key": "k", "value": "v"}, headers=_auth(token))
    tenant = client.get("/audit", headers=_auth(token)).json()[0]["tenant_id"]

    # Soft delete: token stops resolving, data retained.
    r = client.delete(f"/tenants/{tenant}")
    assert r.status_code == 200 and r.json()["mode"] == "soft"
    assert client.get("/records/k", headers=_auth(token)).status_code == 401

    # Restore within the window: access returns, data intact.
    assert client.post(f"/tenants/{tenant}/restore").json()["restored"] is True
    assert client.get("/records/k", headers=_auth(token)).json()["value"] == "v"


def test_tenant_wipe_is_permanent(client):
    token = new_tenant(client)
    client.put("/records", json={"key": "k", "value": "v"}, headers=_auth(token))
    tenant = client.get("/audit", headers=_auth(token)).json()[0]["tenant_id"]

    r = client.delete(f"/tenants/{tenant}", params={"mode": "wipe"})
    assert r.status_code == 200 and r.json()["records_wiped"] == 1
    assert client.get("/records/k", headers=_auth(token)).status_code == 401
    # A wiped tenant cannot be restored.
    assert client.post(f"/tenants/{tenant}/restore").status_code == 404
    assert client.delete(f"/tenants/{tenant}").status_code == 404
