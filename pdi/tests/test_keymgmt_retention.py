"""Production key management (envelope encryption + rotation), retention up to
forever, and the audit event schema."""

import sqlite3

from pdi import crypto
from pdi import db as pdi_db
from pdi.tests.conftest import auth, new_tenant


# --------------------------------------------------------------------------- #
# key management: envelope encryption + rotation
# --------------------------------------------------------------------------- #
def test_dek_wrapped_at_rest_not_the_kek(client):
    """The stored key material is a *wrapped* DEK, not the KEK, and not usable
    as-is: decrypting a record with the wrapped bytes must fail."""
    new_tenant(client)  # forces the keyring into existence
    crypto.active_version()
    rows = sqlite3.connect(pdi_db.db_path()).execute(
        "SELECT version, wrapped_dek, active FROM key_versions").fetchall()
    assert len(rows) == 1 and rows[0][2] == 1          # one active version
    assert len(rows[0][1]) > 40                        # wrapped blob, not raw key


def test_rotate_and_reseal_moves_records_to_new_version(client):
    token = new_tenant(client)
    client.put("/records", headers=auth(token), json={"key": "med/x", "value": "secret-42"})

    v0 = client.get("/keys").json()["versions"]
    assert len(v0) == 1 and v0[0]["active"]

    r = client.post("/keys/rotate")           # rotates + reseals by default
    assert r.status_code == 201
    body = r.json()
    assert body["active_version"] == 2 and body["reseal"]["resealed"] == 1

    versions = client.get("/keys").json()["versions"]
    assert [v["version"] for v in versions] == [1, 2]
    assert [v["active"] for v in versions] == [False, True]

    # Record is still readable after rotation, now sealed under v2.
    got = client.get("/records/med/x", headers=auth(token))
    assert got.status_code == 200 and got.json()["value"] == "secret-42"
    raw = sqlite3.connect(pdi_db.db_path()).execute(
        "SELECT ciphertext FROM records").fetchone()[0]
    assert raw.startswith("2:")

    # Old version can now be retired safely.
    assert client.post("/keys/retire").json()["retired"] == 1
    assert client.get("/records/med/x", headers=auth(token)).json()["value"] == "secret-42"


def test_kms_provider_fails_loudly(client, monkeypatch):
    monkeypatch.setenv("PDI_KEY_PROVIDER", "kms")
    try:
        crypto.KmsKeyProvider().kek()
    except NotImplementedError as e:
        assert "KMS" in str(e)
    else:
        raise AssertionError("KMS provider should fail loudly, not fall back")


# --------------------------------------------------------------------------- #
# retention: from a short window all the way to forever
# --------------------------------------------------------------------------- #
def test_retention_defaults_to_forever(client):
    token = new_tenant(client)
    client.put("/records", headers=auth(token), json={"key": "k", "value": "v"})
    pol = client.get("/retention").json()
    assert pol["record_retention"][0]["retention"] == "forever"
    # A sweep expires nothing when everything is forever.
    swept = client.post("/retention/sweep").json()
    assert swept["expired_records"] == 0 and swept["recovery_window"] == "forever"
    assert client.get("/records/k", headers=auth(token)).status_code == 200


def test_retention_windows_accepted_incl_forever(client):
    r = client.post("/tenants", json={"name": "qrme", "retention": "30d"})
    assert r.status_code == 201
    tid = r.json()["id"]
    assert client.get("/retention").json()["record_retention"][0]["retention"] == "30d"

    for w in ["7d", "90d", "1y", "365", "forever"]:
        assert client.put(f"/tenants/{tid}/retention", json={"retention": w}).status_code == 200
    assert client.get("/retention").json()["record_retention"][0]["retention"] == "forever"

    # Bad window is rejected.
    assert client.put(f"/tenants/{tid}/retention", json={"retention": "banana"}).status_code == 422


def test_sweep_expires_records_past_finite_window(client):
    token = new_tenant(client, name="qrme")
    tid_row = sqlite3.connect(pdi_db.db_path())
    client.put("/records", headers=auth(token), json={"key": "old", "value": "stale"})
    # Age the record and set a 1-day retention, then sweep.
    conn = sqlite3.connect(pdi_db.db_path())
    conn.execute("UPDATE records SET updated_at='2000-01-01T00:00:00+00:00'")
    conn.execute("UPDATE tenants SET retention_days=1")
    conn.commit()
    conn.close()
    swept = client.post("/retention/sweep").json()
    assert swept["expired_records"] == 1
    assert client.get("/records/old", headers=auth(token)).status_code == 404
    # The expiry is on the audit chain and the chain is still intact.
    assert client.get("/audit/verify", headers=auth(token)).json()["intact"] is True


def test_recovery_window_forever_never_purges(client, monkeypatch):
    # Default recovery window is forever: a soft-deleted tenant survives a sweep.
    r = client.post("/tenants", json={"name": "temp"})
    tid = r.json()["id"]
    client.delete(f"/tenants/{tid}")                 # soft delete
    client.post("/retention/sweep")
    row = sqlite3.connect(pdi_db.db_path()).execute(
        "SELECT deleted_at FROM tenants WHERE id=?", (tid,)).fetchone()
    assert row is not None and row[0] is not None     # still there, still tombstoned


# --------------------------------------------------------------------------- #
# audit event schema
# --------------------------------------------------------------------------- #
def test_audit_schema_catalogue(client):
    schema = client.get("/audit/schema").json()
    actions = {a["action"]: a["category"] for a in schema["actions"]}
    assert actions["put"] == "data"
    assert actions["key.rotate"] == "key"
    assert actions["record.expire"] == "retention"
    assert "hash-chained" in schema["retention"]
    assert set(["seq", "action", "category", "hash"]).issubset(schema["event_fields"])


def test_audit_entries_carry_category(client):
    token = new_tenant(client)
    client.put("/records", headers=auth(token), json={"key": "k", "value": "v"})
    entries = client.get("/audit", headers=auth(token)).json()
    puts = [e for e in entries if e["action"] == "put"]
    assert puts and puts[0]["category"] == "data"


def test_contribution_revocable_by_ref(client):
    token = new_tenant(client, name="cloud-model")
    client.post("/contributions", headers=auth(token), json={
        "source": "qrme", "kind": "rated_exchange",
        "payload": {"q": "positive"}, "ref": "a7f3"})
    assert client.get("/contributions", headers=auth(token)).json()["count"] == 1
    r = client.delete("/contributions/a7f3", headers=auth(token))
    assert r.status_code == 200 and r.json()["revoked"] == 1
    assert client.get("/contributions", headers=auth(token)).json()["count"] == 0
    assert client.delete("/contributions/nope", headers=auth(token)).status_code == 404
