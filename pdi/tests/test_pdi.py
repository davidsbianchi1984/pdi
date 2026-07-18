"""Private Data Infrastructure — standalone service tests."""

import base64

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from pdi import crypto
from pdi.tests.conftest import auth, new_tenant


def test_seal_open_roundtrip(monkeypatch):
    monkeypatch.setenv("PDI_MASTER_KEY",
                       base64.b64encode(AESGCM.generate_key(bit_length=256)).decode())
    sealed = crypto.seal("secret value", aad="ten_1:emergency")
    assert sealed != "secret value"
    assert crypto.open_(sealed, aad="ten_1:emergency") == "secret value"


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_data_endpoints_require_tenant_token(client):
    assert client.get("/records/x").status_code == 401
    assert client.put("/records", json={"key": "x", "value": "y"}).status_code == 401


def test_deployment_record(client):
    r = client.post("/deployments", json={
        "name": "Any Corp colo", "option": "colocation",
        "facility": "Tier III+ DC", "tier": "Tier III+"})
    assert r.status_code == 201
    assert r.json()["option"] == "colocation"


def test_put_get_encrypted_record(client):
    token = new_tenant(client)
    client.put("/records", json={"key": "api_key", "value": "sk-secret-123"},
               headers=auth(token))
    got = client.get("/records/api_key", headers=auth(token)).json()
    assert got["value"] == "sk-secret-123"


def test_values_are_encrypted_at_rest(client, tmp_path):
    token = new_tenant(client)
    client.put("/records", json={"key": "k", "value": "TOPSECRET"}, headers=auth(token))
    # The plaintext must not appear anywhere in the database file.
    import glob
    dbfile = glob.glob(str(tmp_path / "*.db"))[0]
    with open(dbfile, "rb") as f:
        assert b"TOPSECRET" not in f.read()


def test_tenants_are_isolated(client):
    t1 = new_tenant(client, "jim-mini")
    t2 = new_tenant(client, "qrme")
    client.put("/records", json={"key": "shared_name", "value": "jim-data"},
               headers=auth(t1))
    # t2 has no record under that key.
    assert client.get("/records/shared_name", headers=auth(t2)).status_code == 404


def test_delete_record(client):
    token = new_tenant(client)
    client.put("/records", json={"key": "k", "value": "v"}, headers=auth(token))
    assert client.delete("/records/k", headers=auth(token)).status_code == 204
    assert client.get("/records/k", headers=auth(token)).status_code == 404


def test_snapshot_contains_only_ciphertext(client):
    token = new_tenant(client)
    client.put("/records", json={"key": "k", "value": "PLAINTEXT"}, headers=auth(token))
    snap = client.get("/snapshot", headers=auth(token)).json()
    assert snap["records"]
    assert all("PLAINTEXT" not in r["ciphertext"] for r in snap["records"])


def test_audit_log_is_hash_chained_and_verifies(client):
    token = new_tenant(client)
    client.put("/records", json={"key": "k", "value": "v"}, headers=auth(token))
    client.get("/records/k", headers=auth(token))
    log = client.get("/audit", headers=auth(token)).json()
    actions = [e["action"] for e in log]
    assert "put" in actions and "get" in actions
    assert client.get("/audit/verify", headers=auth(token)).json()["intact"] is True


def test_audit_tamper_is_detected(client, tmp_path):
    import sqlite3
    token = new_tenant(client)
    client.put("/records", json={"key": "k", "value": "v"}, headers=auth(token))
    # Tamper directly with the audit table, bypassing the API.
    dbfile = str(tmp_path / "pdi.db")
    con = sqlite3.connect(dbfile)
    con.execute("UPDATE audit SET ref='forged' WHERE action='put'")
    con.commit()
    con.close()
    from pdi import db as pdi_db
    pdi_db.reset()
    assert client.get("/audit/verify", headers=auth(token)).json()["intact"] is False
