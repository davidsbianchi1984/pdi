"""Bequests: vault access that begins only when a condition is attested.

The properties under test: no credential exists before activation, the
activation reference is mandatory and audited, the grant reads only its
named shelf, and the owner can change their mind while alive.
"""

from __future__ import annotations

from pdi import db

from .conftest import new_tenant


def _auth(token):
    return {"authorization": f"Bearer {token}"}


def _put(client, token, key, value):
    r = client.put("/records", json={"key": key, "value": value},
                   headers=_auth(token))
    assert r.status_code in (200, 201), r.text


def _bequest(client, token, **over):
    body = {"grantee_name": "June Bianchi",
            "key_prefixes": ["jim/u1/medical/"],
            "note": "For my daughter — the medical records, nothing else."}
    body.update(over)
    r = client.post("/bequests", json=body, headers=_auth(token))
    assert r.status_code == 201, r.text
    return r.json()


def test_a_bequest_at_rest_holds_no_credential(client):
    token = new_tenant(client)
    b = _bequest(client, token)
    assert "grant_token" not in b
    row = db.connect().execute("SELECT grant_hash FROM bequests WHERE id=?",
                               (b["id"],)).fetchone()
    assert row["grant_hash"] is None


def test_a_bequest_needs_a_grantee_and_a_bounded_shelf(client):
    token = new_tenant(client)
    r = client.post("/bequests", json={"grantee_name": "",
                                       "key_prefixes": ["a/"]},
                    headers=_auth(token))
    assert r.status_code == 422
    r = client.post("/bequests", json={"grantee_name": "June",
                                       "key_prefixes": []},
                    headers=_auth(token))
    assert r.status_code == 422
    assert "unbounded" in r.json()["detail"]


def test_activation_requires_a_reference(client):
    token = new_tenant(client)
    b = _bequest(client, token)
    r = client.post(f"/bequests/{b['id']}/activate",
                    json={"activation_ref": ""})
    assert r.status_code == 422
    assert "attested" in r.json()["detail"]


def test_the_grant_reads_its_shelf_and_only_its_shelf(client):
    token = new_tenant(client)
    _put(client, token, "jim/u1/medical/allergies", "penicillin")
    _put(client, token, "jim/u1/journal/private", "not for anyone")
    b = _bequest(client, token)
    act = client.post(f"/bequests/{b['id']}/activate",
                      json={"activation_ref": "vigil:evt_abc123"}).json()
    grant = {"x-grant-token": act["grant_token"]}
    keys = client.get("/bequests/grant/keys", headers=grant).json()
    assert keys["keys"] == ["jim/u1/medical/allergies"]
    assert "daughter" in keys["note"]
    rec = client.get("/bequests/grant/read",
                     params={"key": "jim/u1/medical/allergies"},
                     headers=grant).json()
    assert rec["value"] == "penicillin"
    out = client.get("/bequests/grant/read",
                     params={"key": "jim/u1/journal/private"}, headers=grant)
    assert out.status_code == 403


def test_the_grant_token_is_shown_once_and_only_hashes_rest(client):
    token = new_tenant(client)
    b = _bequest(client, token)
    act = client.post(f"/bequests/{b['id']}/activate",
                      json={"activation_ref": "cert:2026-041"}).json()
    assert act["grant_token"]
    row = db.connect().execute("SELECT grant_hash FROM bequests WHERE id=?",
                               (b["id"],)).fetchone()
    assert row["grant_hash"] != act["grant_token"]
    again = client.post(f"/bequests/{b['id']}/activate",
                        json={"activation_ref": "cert:2026-041"})
    assert again.status_code == 409          # once means once


def test_the_owner_can_revoke_while_alive_and_not_after(client):
    token = new_tenant(client)
    b = _bequest(client, token)
    r = client.delete(f"/bequests/{b['id']}", headers=_auth(token))
    assert r.status_code == 200 and r.json()["revoked"]
    # a revoked bequest cannot be activated
    r = client.post(f"/bequests/{b['id']}/activate",
                    json={"activation_ref": "cert:1"})
    assert r.status_code == 409
    # after activation the tenant token no longer revokes
    b2 = _bequest(client, token)
    client.post(f"/bequests/{b2['id']}/activate",
                json={"activation_ref": "cert:2"})
    r = client.delete(f"/bequests/{b2['id']}", headers=_auth(token))
    assert r.status_code == 409
    assert "admin" in r.json()["detail"]


def test_admin_revocation_kills_the_grant(client):
    token = new_tenant(client)
    _put(client, token, "jim/u1/medical/list", "x")
    b = _bequest(client, token)
    act = client.post(f"/bequests/{b['id']}/activate",
                      json={"activation_ref": "cert:3"}).json()
    client.delete(f"/bequests/{b['id']}/grant")
    r = client.get("/bequests/grant/keys",
                   headers={"x-grant-token": act["grant_token"]})
    assert r.status_code == 404              # revoked and wrong look alike


def test_a_wrong_grant_token_is_a_404(client):
    new_tenant(client)
    r = client.get("/bequests/grant/keys",
                   headers={"x-grant-token": "not-a-grant"})
    assert r.status_code == 404


def test_every_step_lands_in_the_audit_chain(client):
    token = new_tenant(client)
    _put(client, token, "jim/u1/medical/a", "x")
    b = _bequest(client, token)
    act = client.post(f"/bequests/{b['id']}/activate",
                      json={"activation_ref": "vigil:evt_9"}).json()
    client.get("/bequests/grant/read",
               params={"key": "jim/u1/medical/a"},
               headers={"x-grant-token": act["grant_token"]})
    actions = [r["action"] for r in db.connect().execute(
        "SELECT action FROM audit ORDER BY seq").fetchall()]
    for needed in ("bequest_created", "bequest_activated", "bequest_read"):
        assert needed in actions
    ref = db.connect().execute(
        "SELECT ref FROM audit WHERE action='bequest_activated'").fetchone()
    assert "vigil:evt_9" in ref["ref"]        # the attestation is the record


def test_bequests_of_one_tenant_are_invisible_to_another(client):
    token_a, token_b = new_tenant(client, "a"), new_tenant(client, "b")
    b = _bequest(client, token_a)
    assert client.get("/bequests", headers=_auth(token_b)).json() == []
    r = client.delete(f"/bequests/{b['id']}", headers=_auth(token_b))
    assert r.status_code == 404
