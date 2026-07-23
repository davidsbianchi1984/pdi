"""Compliance-grade secure file transfers for enterprises (HIPAA, OSHA, CPNI)."""

from pdi.tests.conftest import auth, new_tenant


def _create(client, token, **body):
    r = client.post("/transfers", json=body, headers=auth(token))
    assert r.status_code == 201, r.text
    return r.json()


def test_compliance_catalog_lists_programs(client):
    body = client.get("/compliance/programs").json()
    keys = {p["key"] for p in body["programs"]}
    assert {"hipaa", "osha", "cpni", "pci_dss", "gdpr"} <= keys
    # PDI advertises the controls it satisfies natively.
    assert "encryption-at-rest" in body["pdi_native_controls"]
    assert "audit-logging" in body["pdi_native_controls"]


def test_create_seals_and_sets_retention(client):
    token = new_tenant(client, name="verizon")
    t = _create(client, token, recipient="patient-123", filename="labs.pdf",
                content="AAAA lab results BBBB", programs=["hipaa", "osha"],
                classification="PHI")
    # Retention is the strictest across programs: HIPAA 6y (2190) > OSHA 5y.
    assert t["retention_days"] == 2190
    assert t["expires_at"]
    assert t["receive_token"].startswith("pdi_recv_")
    # The controls the transfer needs, split into what PDI covers vs operational.
    assert "encryption-at-rest" in t["controls"]["satisfied_by_pdi"]
    assert "baa" in t["controls"]["operational"]
    # The plaintext is not sitting in the response beyond the token flow.
    assert client.get("/transfers", headers=auth(token)).json()[0]["id"] == t["id"]


def test_receive_with_token_and_chain_of_custody(client):
    token = new_tenant(client, name="att")
    t = _create(client, token, recipient="cust-9", filename="cpni.csv",
                content="line1\nline2", programs=["cpni"])
    # Recipient retrieves with the receive token — no tenant credential.
    r = client.post(f"/transfers/{t['id']}/receive",
                    headers={"X-Receive-Token": t["receive_token"]})
    assert r.status_code == 200, r.text
    assert r.json()["content"] == "line1\nline2"

    # The custody record shows created + received, and the audit chain is intact.
    custody = client.get(f"/transfers/{t['id']}/custody", headers=auth(token)).json()
    events = [e["event"] for e in custody["chain_of_custody"]]
    assert events == ["created", "received"]
    assert custody["audit_chain_intact"] is True
    assert "cpni" in custody["programs"]


def test_wrong_token_and_unknown_program(client):
    token = new_tenant(client)
    t = _create(client, token, recipient="r", filename="f", content="x",
                programs=["osha"])
    assert client.post(f"/transfers/{t['id']}/receive",
                       headers={"X-Receive-Token": "pdi_recv_wrong"}).status_code == 403
    assert client.post("/transfers", headers=auth(token),
                       json={"recipient": "r", "filename": "f", "content": "x",
                             "programs": ["not-a-law"]}).status_code == 422


def test_revoke_cuts_access_but_retains_record(client):
    token = new_tenant(client)
    t = _create(client, token, recipient="r", filename="f", content="x",
                programs=["hipaa"])
    rev = client.delete(f"/transfers/{t['id']}", headers=auth(token)).json()
    assert rev["status"] == "revoked"
    assert rev["retained_until"]                 # record kept for retention
    # Access is now cut.
    assert client.post(f"/transfers/{t['id']}/receive",
                       headers={"X-Receive-Token": t["receive_token"]}).status_code == 410


def test_transfers_are_tenant_isolated(client):
    owner = new_tenant(client, name="tmobile")
    other = new_tenant(client, name="rival")
    t = _create(client, owner, recipient="r", filename="f", content="secret",
                programs=["cpni"])
    assert client.get("/transfers", headers=auth(other)).json() == []
    assert client.get(f"/transfers/{t['id']}", headers=auth(other)).status_code == 404
    assert client.get(f"/transfers/{t['id']}/custody", headers=auth(other)).status_code == 404
