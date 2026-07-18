"""Tandem: an AI system uses PDI as its encrypted store, over the client.

Simulates JIM-mini storing a user's sensitive emergency contact in PDI instead
of its own database, then reading it back — reaching PDI only through
PDIClient. No PDI internals are imported by the "AI system" here.
"""

from pdi.client import PDIClient
from pdi.tests.conftest import new_tenant


def test_ai_system_stores_and_reads_secret_via_client(client):
    token = new_tenant(client, "jim-mini")
    pdi = PDIClient(token=token, client=client)   # injected TestClient transport

    # JIM stores a user's emergency contact securely in PDI.
    pdi.put("user_usr_1/emergency_contact", "Pat +1-555-0199")
    assert pdi.get("user_usr_1/emergency_contact") == "Pat +1-555-0199"

    # Missing key -> None (not an error).
    assert pdi.get("user_usr_1/unknown") is None

    # And the access is on PDI's audit trail.
    log = client.get("/audit", headers={"Authorization": f"Bearer {token}"}).json()
    assert any(e["action"] == "put" for e in log)
    assert any(e["action"] == "get" for e in log)


def test_client_delete(client):
    token = new_tenant(client)
    pdi = PDIClient(token=token, client=client)
    pdi.put("k", "v")
    assert pdi.delete("k") is True
    assert pdi.get("k") is None
