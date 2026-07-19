"""Bearer tokens are stored hashed, never in plaintext — a leak of PDI's own
database must not yield credentials that unlock the vault."""

import hashlib

from pdi import db
from pdi.tests.conftest import auth, new_tenant


def _sha(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def test_primary_token_is_stored_hashed(client):
    token = new_tenant(client)                       # plaintext, returned once
    rows = db.connect().execute("SELECT token FROM tenants").fetchall()
    stored = {r["token"] for r in rows}
    assert token not in stored                        # plaintext never persisted
    assert _sha(token) in stored                      # only the hash is
    # And the hashed token still authenticates a real request.
    assert client.put("/records", json={"key": "k", "value": "v"},
                      headers=auth(token)).status_code in (200, 201)


def test_scoped_token_is_stored_hashed(client):
    write = new_tenant(client)
    tenant = client.get("/audit", headers=auth(write)).json()[0]["tenant_id"]
    read = client.post(f"/tenants/{tenant}/tokens",
                       json={"role": "read"}).json()["token"]
    stored = {r["token"] for r in
              db.connect().execute("SELECT token FROM tenant_tokens").fetchall()}
    assert read not in stored
    assert _sha(read) in stored


def test_resolved_tenant_never_exposes_token_material(client):
    from pdi import vault
    token = new_tenant(client)
    resolved = vault.tenant_by_token(token)
    assert resolved is not None
    assert "token" not in resolved                    # not even the hash leaks
