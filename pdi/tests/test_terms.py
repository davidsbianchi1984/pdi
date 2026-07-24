"""Terms of Service: served versioned, receipt recorded at provisioning."""

from pdi import db, terms


def test_terms_served_versioned_with_key_points(client):
    r = client.get("/terms")
    assert r.status_code == 200
    body = r.json()
    assert body["version"] == terms.TERMS_VERSION
    assert body["document"] == "docs/terms.md"
    joined = " ".join(body["key_points"]).lower()
    assert "business associate agreement" in joined
    assert "as-is" in joined


def test_tenant_provisioning_records_terms_receipt(client):
    r = client.post("/tenants", json={"name": "acme-health"})
    assert r.status_code == 201
    tenant_id = r.json()["id"]
    row = db.connect().execute(
        "SELECT terms_version, terms_accepted_at FROM tenants WHERE id=?",
        (tenant_id,)).fetchone()
    assert row["terms_version"] == terms.TERMS_VERSION
    assert row["terms_accepted_at"]
