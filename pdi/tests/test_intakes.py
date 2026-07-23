"""Inbound intake: a broadband subscriber or partner company sends a file IN
to a corporation, sealed under compliance (HIPAA / OSHA / CPNI)."""

from pdi.tests.conftest import auth, new_tenant


def _intake(client, token, **body):
    r = client.post("/intakes", json=body, headers=auth(token))
    assert r.status_code == 201, r.text
    return r.json()


def test_subscriber_submits_file_in(client):
    token = new_tenant(client, name="att")
    intk = _intake(client, token, from_party="subscriber-9", party_type="subscriber",
                   purpose="ID verification", programs=["cpni", "hipaa"])
    assert intk["status"] == "open"
    assert intk["submit_token"].startswith("pdi_submit_")
    assert "encryption-at-rest" in intk["controls"]["satisfied_by_pdi"]

    # The subscriber submits their file in with the submit token — no tenant creds.
    r = client.post(f"/intakes/{intk['id']}/submit",
                    headers={"X-Submit-Token": intk["submit_token"]},
                    json={"filename": "id.jpg", "content": "BYTES", "classification": "PII"})
    assert r.status_code == 201, r.text
    assert r.json()["sealed"] is True

    # The corporation retrieves the sealed file (audited).
    got = client.get(f"/intakes/{intk['id']}/file", headers=auth(token)).json()
    assert got["content"] == "BYTES"
    assert got["filename"] == "id.jpg"


def test_partner_company_intake_and_custody(client):
    token = new_tenant(client, name="verizon")
    intk = _intake(client, token, from_party="acme-clinic", party_type="organization",
                   purpose="OSHA 300 logs", programs=["osha"])
    client.post(f"/intakes/{intk['id']}/submit",
                headers={"X-Submit-Token": intk["submit_token"]},
                json={"filename": "osha300.csv", "content": "rows"})
    client.get(f"/intakes/{intk['id']}/file", headers=auth(token))

    custody = client.get(f"/intakes/{intk['id']}/custody", headers=auth(token)).json()
    events = [e["event"] for e in custody["chain_of_custody"]]
    assert events == ["requested", "submitted", "read"]
    assert custody["party_type"] == "organization"
    assert custody["audit_chain_intact"] is True


def test_bad_token_unknown_program_and_resubmit(client):
    token = new_tenant(client)
    intk = _intake(client, token, from_party="p", programs=["cpni"])
    assert client.post(f"/intakes/{intk['id']}/submit",
                       headers={"X-Submit-Token": "pdi_submit_wrong"},
                       json={"filename": "f", "content": "x"}).status_code == 403
    assert client.post("/intakes", headers=auth(token),
                       json={"from_party": "p", "programs": ["nope"]}).status_code == 422
    # First submit closes intake to further submissions.
    client.post(f"/intakes/{intk['id']}/submit",
                headers={"X-Submit-Token": intk["submit_token"]},
                json={"filename": "f", "content": "x"})
    assert client.post(f"/intakes/{intk['id']}/submit",
                       headers={"X-Submit-Token": intk["submit_token"]},
                       json={"filename": "f", "content": "y"}).status_code == 409


def test_intakes_are_tenant_isolated(client):
    owner = new_tenant(client, name="tmobile")
    other = new_tenant(client, name="rival")
    intk = _intake(client, owner, from_party="sub", programs=["cpni"])
    assert client.get("/intakes", headers=auth(other)).json() == []
    assert client.get(f"/intakes/{intk['id']}", headers=auth(other)).status_code == 404


def test_outbound_transfer_carries_party_type(client):
    token = new_tenant(client)
    r = client.post("/transfers", headers=auth(token),
                    json={"recipient": "sub-1", "filename": "bill.pdf",
                          "content": "x", "programs": ["cpni"],
                          "party_type": "subscriber"})
    assert r.status_code == 201, r.text
    assert r.json()["party_type"] == "subscriber"
