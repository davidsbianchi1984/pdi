"""The operations journal: coordination records QRME sealed into a tenant's
vault, readable in place — a view over ``qrme/coordination/*``, never a side
door around the audit chain.
"""

from __future__ import annotations

import json

from pdi.tests.conftest import new_tenant


def _seal(client, token, key, body):
    r = client.put("/records", json={"key": key, "value": json.dumps(body)},
                   headers={"authorization": f"Bearer {token}"})
    assert r.status_code in (200, 201), r.text


def test_the_journal_lists_only_coordination_records(client):
    token = new_tenant(client, "qrme")
    _seal(client, token, "qrme/coordination/crd_1", {
        "org": "Bianchi & Sons", "goal": "quote the pew restoration",
        "plan": "Workshop measures; Finance quotes.",
        "contributions": [{"department": "Workshop"},
                          {"department": "Finance"}]})
    _seal(client, token, "medical/biometric/x", {"heart_rate": 60})
    r = client.get("/operations",
                   headers={"authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    out = r.json()
    assert len(out["entries"]) == 1
    entry = out["entries"][0]
    assert entry["org"] == "Bianchi & Sons"
    assert entry["departments"] == ["Workshop", "Finance"]
    assert "audit chain" in out["note"]


def test_journal_reads_land_on_the_audit_chain(client):
    token = new_tenant(client, "qrme")
    _seal(client, token, "qrme/coordination/crd_1", {
        "org": "X", "goal": "g", "plan": "p", "contributions": []})
    client.get("/operations", headers={"authorization": f"Bearer {token}"})
    r = client.get("/provenance/qrme/coordination/crd_1",
                   headers={"authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    actions = [e["action"] for e in r.json()["audit"]["events"]]
    assert "get" in actions          # the journal read was audited


def test_the_journal_needs_the_tenant_s_own_token(client):
    token = new_tenant(client, "qrme")
    _seal(client, token, "qrme/coordination/crd_1",
          {"org": "X", "goal": "g", "plan": "p", "contributions": []})
    other = new_tenant(client, "somebody-else")
    r = client.get("/operations",
                   headers={"authorization": f"Bearer {other}"})
    assert r.status_code == 200
    assert r.json()["entries"] == []     # tenant isolation: nothing leaks
