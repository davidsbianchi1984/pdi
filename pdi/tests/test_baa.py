"""BAA enforcement: no production PHI before the signature. HIPAA-program
transfers and intakes are refused for a tenant with no executed BAA on
file; recording one (admin) unblocks them; terminating re-blocks."""

from pdi.tests.conftest import auth, new_tenant

BAA = {"customer_legal_name": "Acme Health Inc.",
       "operator_legal_name": "Vault Operations LLC",
       "effective_date": "2026-07-24",
       "customer_signatory": "J. Doe, CIO",
       "operator_signatory": "R. Roe, CEO",
       "document_sha256": "ab" * 32}


def _tenant_with_id(client):
    r = client.post("/tenants", json={"name": "acme-health"})
    return r.json()["id"], r.json()["token"]


def test_hipaa_flows_blocked_until_baa_then_unblocked(client):
    tid, token = _tenant_with_id(client)

    # HIPAA transfer refused with a pointer at the template.
    r = client.post("/transfers", json={
        "recipient": "clinic-7", "filename": "chart.pdf",
        "content": "PHI bytes", "programs": ["hipaa"]}, headers=auth(token))
    assert r.status_code == 403
    assert "Business Associate Agreement" in r.json()["detail"]

    # HIPAA intake refused the same way; the tenant sees their standing.
    assert client.post("/intakes", json={
        "from_party": "subscriber-9", "programs": ["hipaa"]},
        headers=auth(token)).status_code == 403
    assert client.get("/baa", headers=auth(token)).json()["executed"] is False

    # The operator records the executed BAA (admin; dev mode = open).
    rec = client.post(f"/tenants/{tid}/baa", json=BAA)
    assert rec.status_code == 201
    assert rec.json()["status"] == "executed"

    # Both flows now clear, and the tenant's standing reflects it.
    assert client.post("/transfers", json={
        "recipient": "clinic-7", "filename": "chart.pdf",
        "content": "PHI bytes", "programs": ["hipaa"]},
        headers=auth(token)).status_code == 201
    assert client.post("/intakes", json={
        "from_party": "subscriber-9", "programs": ["hipaa"]},
        headers=auth(token)).status_code == 201
    mine = client.get("/baa", headers=auth(token)).json()
    assert mine["executed"] is True and mine["effective_date"] == "2026-07-24"

    # Execution is in the tamper-evident audit chain.
    entries = client.get("/audit", headers=auth(token)).json()
    assert any(e["action"] == "baa.execute" for e in entries)


def test_non_hipaa_programs_never_need_a_baa(client):
    _, token = _tenant_with_id(client)
    r = client.post("/transfers", json={
        "recipient": "site-lead", "filename": "incident.log",
        "content": "OSHA record", "programs": ["osha"]}, headers=auth(token))
    assert r.status_code == 201


def test_termination_reblocks_and_keeps_history(client):
    tid, token = _tenant_with_id(client)
    client.post(f"/tenants/{tid}/baa", json=BAA)
    assert client.delete(f"/tenants/{tid}/baa").json()["status"] == "terminated"

    # Blocked again; the admin read now 404s (no *active* record).
    assert client.post("/transfers", json={
        "recipient": "clinic-7", "filename": "chart.pdf",
        "content": "PHI", "programs": ["hipaa"]},
        headers=auth(token)).status_code == 403
    assert client.get(f"/tenants/{tid}/baa").status_code == 404

    # Re-execution works (renegotiation), superseding nothing active.
    assert client.post(f"/tenants/{tid}/baa", json=BAA).status_code == 201
    assert client.get(f"/tenants/{tid}/baa").json()["status"] == "executed"


def test_unknown_tenant_404s(client):
    assert client.post("/tenants/ten_nope/baa", json=BAA).status_code == 404
    assert client.get("/tenants/ten_nope/baa").status_code == 404
