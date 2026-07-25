"""Bring your own key — the claim that makes outsourced hosting different.

The claim is narrow and worth stating exactly: a tenant under ``held`` custody
has records the *operator's own database* cannot open. So the tests here are
mostly attempts to read that tenant's data the way an operator could — with
admin rights, with the deployment key, through the reseal job — and finding
ciphertext each time.
"""

import base64

import pytest

from pdi import crypto, db, vault

KEY = base64.b64encode(b"k" * 32).decode()
OTHER = base64.b64encode(b"j" * 32).decode()


def _tenant(client, name="acme"):
    body = client.post("/tenants", json={"name": name, "retention": "forever"}
                       ).json()
    return body["token"]


def _auth(token, key=None):
    h = {"authorization": f"Bearer {token}"}
    if key:
        h["x-tenant-key"] = key
    return h


def test_deployment_custody_is_the_default_and_says_so(client):
    """No BYOK = the operator can read. Said plainly rather than left to be
    inferred from silence."""
    token = _tenant(client)
    body = client.get("/key", headers=_auth(token)).json()
    assert body["provider"] == "deployment"
    assert body["customer_managed"] is False
    assert body["operator_can_decrypt"] is True


def test_adopting_a_key_reseals_everything_that_was_already_there(client):
    """A half-migrated tenant — some records the operator can still read, no
    way to tell which — is the worst state to be in. Adoption is all-or-
    nothing."""
    token = _tenant(client)
    for i in range(3):
        client.put("/records", json={"key": f"k{i}", "value": f"v{i}"},
                   headers=_auth(token))

    r = client.put("/key", json={"provider": "held", "key": KEY},
                   headers=_auth(token))
    assert r.status_code == 201, r.text
    assert r.json()["resealed"] == 3

    # Readable with the key...
    for i in range(3):
        got = client.get(f"/records/k{i}", headers=_auth(token, KEY))
        assert got.status_code == 200
        assert got.json()["value"] == f"v{i}"


def test_the_deployment_cannot_open_a_byok_tenants_records(client):
    """The whole point. Same valid tenant token, no customer key — and the
    deployment has nothing to decrypt with."""
    token = _tenant(client)
    client.put("/records", json={"key": "secret", "value": "hunter2"},
               headers=_auth(token))
    client.put("/key", json={"provider": "held", "key": KEY},
               headers=_auth(token))

    r = client.get("/records/secret", headers=_auth(token))
    assert r.status_code == 428          # bring the key
    assert "customer-managed" in r.json()["detail"]


def test_the_wrong_key_is_refused_before_it_can_write_junk(client):
    """A wrong key must not seal new records under itself — that would leave
    records nothing can ever open, discovered much later."""
    token = _tenant(client)
    client.put("/records", json={"key": "real", "value": "v"},
               headers=_auth(token))
    client.put("/key", json={"provider": "held", "key": KEY},
               headers=_auth(token))

    r = client.get("/records/real", headers=_auth(token, OTHER))
    assert r.status_code == 403
    assert "not the key" in r.json()["detail"]

    # The write path is the one that matters: sealing under a wrong key would
    # produce a record nothing can ever open, and nothing would notice today.
    w = client.put("/records", json={"key": "x", "value": "y"},
                   headers=_auth(token, OTHER))
    assert w.status_code == 403
    assert db.connect().execute(
        "SELECT COUNT(*) n FROM records WHERE key='x'").fetchone()["n"] == 0


def test_the_check_value_does_not_store_the_key(client):
    """What is on disk to verify a presented key must not be the key, or the
    guarantee is theatre."""
    token = _tenant(client)
    client.put("/key", json={"provider": "held", "key": KEY},
               headers=_auth(token))
    row = db.connect().execute(
        "SELECT check_value, config FROM tenant_keys").fetchone()
    stored = (row["check_value"] + row["config"]).encode()
    assert b"k" * 32 not in stored
    assert base64.b64decode(KEY) not in stored
    assert KEY.encode() not in stored


def test_ciphertext_on_disk_is_not_openable_with_the_deployment_key(client):
    """Reach past the API entirely — the way someone with the database file
    would — and confirm the deployment's own keyring cannot open it."""
    token = _tenant(client)
    client.put("/records", json={"key": "s", "value": "classified"},
               headers=_auth(token))
    client.put("/key", json={"provider": "held", "key": KEY},
               headers=_auth(token))

    row = db.connect().execute("SELECT tenant_id, ciphertext FROM records"
                               ).fetchone()
    assert b"classified" not in base64.b64decode(row["ciphertext"].split(":")[1])
    with pytest.raises(Exception):
        # No tenant scope = the deployment keyring, which is what an operator
        # holds. It must not decrypt this.
        crypto.open_(row["ciphertext"], aad=f"{row['tenant_id']}:s")


def test_an_operator_reseal_skips_byok_tenants_and_reports_it(client):
    """The operator's rotation job cannot touch records it cannot open. It
    must say so rather than silently leaving them behind."""
    plain_token = _tenant(client, "plain")
    byok_token = _tenant(client, "byok")
    client.put("/records", json={"key": "a", "value": "1"},
               headers=_auth(plain_token))
    client.put("/records", json={"key": "b", "value": "2"},
               headers=_auth(byok_token))
    client.put("/key", json={"provider": "held", "key": KEY},
               headers=_auth(byok_token))

    client.post("/keys/rotate?reseal=false")
    out = vault.reseal_all()
    assert out["customer_managed_skipped"] == 1
    assert out["resealed"] == 1

    # The BYOK tenant is untouched and still readable with its own key.
    got = client.get("/records/b", headers=_auth(byok_token, KEY))
    assert got.status_code == 200 and got.json()["value"] == "2"


def test_releasing_custody_needs_the_key_and_gives_the_data_back(client):
    """Handing custody back requires opening the records — the guarantee
    working, not an obstacle."""
    token = _tenant(client)
    client.put("/records", json={"key": "k", "value": "v"},
               headers=_auth(token))
    client.put("/key", json={"provider": "held", "key": KEY},
               headers=_auth(token))

    assert client.delete("/key", headers=_auth(token)).status_code == 428
    assert client.delete("/key", headers=_auth(token, OTHER)).status_code == 403

    out = client.delete("/key", headers=_auth(token, KEY))
    assert out.status_code == 200 and out.json()["resealed"] == 1
    # Back under deployment custody: readable with no key presented.
    assert client.get("/records/k", headers=_auth(token)).json()["value"] == "v"


def test_custody_states_its_own_limits(client):
    """A security review will quote this endpoint, so it has to be honest
    about what BYOK does not protect against."""
    token = _tenant(client)
    client.put("/key", json={"provider": "held", "key": KEY},
               headers=_auth(token))
    body = client.get("/key", headers=_auth(token)).json()
    assert body["operator_can_decrypt"] is False
    limits = " ".join(body["limits"]).lower()
    assert "at rest" in limits            # not against a hostile live operator
    assert "unrecoverable" in limits      # no escrow
    assert "reseal" in limits             # background jobs can't run


def test_kms_custody_is_honest_that_the_operator_can_still_decrypt(client):
    """Two very different guarantees both get called 'customer-managed' in
    the market. The distinction is reported, not blurred."""
    token = _tenant(client)
    r = client.put("/key", json={"provider": "kms",
                                 "config": {"key_id": "arn:aws:kms:..."}},
                   headers=_auth(token))
    assert r.status_code == 201
    body = client.get("/key", headers=_auth(token)).json()
    assert body["customer_managed"] is True
    assert body["operator_can_decrypt"] is True     # while the grant is live
    assert "revoked" in body["note"]


def test_adopting_twice_is_refused(client):
    token = _tenant(client)
    client.put("/key", json={"provider": "held", "key": KEY},
               headers=_auth(token))
    r = client.put("/key", json={"provider": "held", "key": OTHER},
                   headers=_auth(token, KEY))
    assert r.status_code == 409


def test_a_short_key_is_refused(client):
    token = _tenant(client)
    r = client.put("/key", json={"provider": "held",
                                 "key": base64.b64encode(b"tooshort").decode()},
                   headers=_auth(token))
    assert r.status_code == 400


def test_byok_does_not_change_tenant_isolation(client):
    """Cross-tenant reads stay 404 whoever holds which key."""
    a = _tenant(client, "a")
    b = _tenant(client, "b")
    client.put("/records", json={"key": "mine", "value": "secret"},
               headers=_auth(a))
    client.put("/key", json={"provider": "held", "key": KEY}, headers=_auth(a))
    assert client.get("/records/mine", headers=_auth(b, KEY)).status_code == 404
