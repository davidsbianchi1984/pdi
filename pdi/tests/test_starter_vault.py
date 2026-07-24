"""The starter vault: a seeded demo tenant with sealed records covering
every provenance origin, a bound robot with sealed collection data, and an
audit trail that already shows a full custody cycle."""

from pdi.seed import ROBOT_MODEL, STARTER_RECORDS, TENANT_NAME
from pdi.tests.conftest import auth


def test_seed_creates_the_demo_tenant_with_sealed_records(client):
    r = client.post("/seed")
    assert r.status_code == 201, r.text
    out = r.json()
    assert out["created"] is True and out["name"] == TENANT_NAME
    assert out["token"].startswith("pdi_")

    keys = client.get("/records", headers=auth(out["token"])).json()["keys"]
    for key, _ in STARTER_RECORDS:
        assert key in keys
    # The demo robot's collection data is sealed under robot/ keys too.
    assert any(k.startswith(f"robot/{ROBOT_MODEL}/") for k in keys)

    rec = client.get("/records/welcome/readme",
                     headers=auth(out["token"])).json()
    assert "AES-256-GCM" in rec["value"]


def test_seed_is_idempotent_and_never_reissues_the_token(client):
    first = client.post("/seed").json()
    second = client.post("/seed").json()
    assert second["created"] is False
    assert second["tenant_id"] == first["tenant_id"]
    assert "token" not in second        # issued once, at creation, only
    keys = client.get("/records", headers=auth(first["token"])).json()["keys"]
    assert len(keys) == len(STARTER_RECORDS) + 2      # no duplicates


def test_starter_records_cover_every_provenance_origin(client):
    token = client.post("/seed").json()["token"]
    origins = {
        "jim/demo-user/medical/checkin-001": "JIM Guardian",
        "qrme/demo-profile/sources/note-001": "QRME",
        "finance/2025/summary": "direct API write",
    }
    for key, expected in origins.items():
        p = client.get(f"/provenance/{key}", headers=auth(token)).json()
        assert expected in p["origin"], (key, p["origin"])
        assert p["chain"]["intact"] is True


def test_demo_robot_is_bound_with_sealed_collection_data(client):
    token = client.post("/seed").json()["token"]
    robots = client.get("/robots", headers=auth(token)).json()
    assert len(robots) == 1 and robots[0]["model"] == ROBOT_MODEL
    assert robots[0]["collected"] == 2
    data = client.get(f"/robots/{robots[0]['id']}/data",
                      headers=auth(token)).json()
    assert len(data["keys"]) == 2


def test_seed_audit_trail_shows_a_full_custody_cycle(client):
    token = client.post("/seed").json()["token"]
    p = client.get("/provenance/welcome/readme", headers=auth(token)).json()
    actions = [e["action"] for e in p["audit"]["events"]]
    assert "put" in actions and "get" in actions      # seal -> access
