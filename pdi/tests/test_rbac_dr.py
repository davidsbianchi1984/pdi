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
