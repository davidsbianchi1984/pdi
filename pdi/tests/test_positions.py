"""Position & Assistant Builder — the AI Integration & Role-Mapping
Questionnaire. Sealed raw answers, derived blueprint, responsible framing."""

import sqlite3

from pdi import db as pdi_db
from pdi.positions import build_blueprint
from pdi.tests.conftest import new_tenant


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


# A fully-answered questionnaire for a supervisory transit role (any industry).
INTAKE = {
    "industry": "public transit",
    "role": {"job_title": "Station Supervisor", "department": "Operations",
             "role_type": "supervisory", "manages_staff": 12},
    "workflow": {"manages": ["scheduling", "dispatch"], "documents_incidents": True,
                 "recurring_meetings": True, "manual_tasks": True},
    "decisions": {"scope": ["routes", "staffing", "incident", "budget"],
                  "automatable_decisions": ["shift swaps", "routine route padding"]},
    "bottlenecks": {"redundant_tasks": ["manual headcount entry"],
                    "outdated_tasks": ["paper incident forms"]},
    "preferences": {"wants": ["task_tracking"], "tone": "directive",
                    "interaction": "voice", "summarize_logs": True,
                    "learn_decision_style": True},
    "admin": {"compliance_accountable": True},
    "future": {"comfortable_automation": True,
               "roles_obsolete_3_5yr": ["manual fare auditor"],
               "reskilling_interest": True},
}


def test_blueprint_is_decision_support_not_a_verdict():
    bp = build_blueprint(INTAKE)
    assert bp["industry"] == "public transit"
    assert bp["role"]["oversight_level"] == "supervisory"
    # Explicit + inferred capabilities, each with a reason.
    caps = {c["key"] for c in bp["assistant"]["capabilities"]}
    assert {"task_tracking", "scheduling", "maintenance_alerts",
            "compliance_logging", "report_generation", "log_summaries",
            "decision_support"} <= caps
    assert all(c["why"] for c in bp["assistant"]["capabilities"])
    # High-stakes decisions are kept human — regardless of automation score.
    req = bp["human_in_loop"]["required"]
    assert "Incident-response decisions" in req
    assert "Budget allocations" in req
    assert "Staffing coverage & time-off approvals" in req
    assert "Safety / regulatory compliance sign-off" in req
    # Obsolescence is framed as *task* opportunities, never people.
    assert "manual headcount entry" in bp["automation"]["opportunities"]
    assert "Not a staffing decision" in bp["automation"]["note"]
    # Reskilling paths are surfaced when the person is interested.
    assert bp["reskilling"]["interested"] is True
    assert bp["reskilling"]["suggested_paths"]
    # The assistant spec is a guardrailed system-prompt.
    spec = bp["assistant_spec"]
    assert "directive tone over voice" in spec
    assert "decision support" in spec
    assert "never auto-approve" in spec


def test_industry_agnostic_and_partial_intake():
    # A near-empty intake still yields a safe, defaulted blueprint.
    bp = build_blueprint({"role": {"job_title": "Analyst"}})
    assert bp["industry"] == "general"
    assert bp["role"]["oversight_level"] == "frontline"
    assert bp["assistant"]["tone"] == "neutral"
    assert bp["assistant"]["interaction"] == "hybrid"
    assert bp["automation"]["opportunity_score"] == 0.0
    assert bp["human_in_loop"]["required"] == []
    assert bp["reskilling"]["suggested_paths"] == []


def test_position_sealed_and_blueprint_returned(client):
    token = new_tenant(client, name="metro-ops")
    r = client.post("/positions", headers=_auth(token), json=INTAKE)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["id"].startswith("pos_")
    assert body["assistant_spec"]
    assert "Incident-response decisions" in body["human_in_loop"]["required"]

    # Listed by id.
    listing = client.get("/positions", headers=_auth(token)).json()
    assert listing["count"] == 1 and body["id"] in listing["ids"]

    # Fetchable — returns the derived blueprint again.
    got = client.get(f"/positions/{body['id']}", headers=_auth(token)).json()
    assert got["id"] == body["id"]
    assert got["assistant"]["tone"] == "directive"

    # Sealed at rest: the raw workforce answers never appear in the DB file.
    raw = sqlite3.connect(pdi_db.db_path()).execute(
        "SELECT ciphertext FROM records").fetchall()
    blob = " ".join(r[0] for r in raw)
    assert "Station Supervisor" not in blob
    assert "manual fare auditor" not in blob

    # The intake is on the audit chain.
    assert client.get("/audit/verify", headers=_auth(token)).json()["intact"] is True
    actions = [e["action"] for e in client.get("/audit", headers=_auth(token)).json()]
    assert "position.create" in actions


def test_read_only_token_cannot_create_position(client):
    token = new_tenant(client)
    tenant = client.get("/audit", headers=_auth(token)).json()[0]["tenant_id"]
    read = client.post(f"/tenants/{tenant}/tokens", json={"role": "read"}).json()
    r = client.post("/positions", headers=_auth(read["token"]), json=INTAKE)
    assert r.status_code == 403


def test_missing_position_is_404(client):
    token = new_tenant(client)
    assert client.get("/positions/pos_nope", headers=_auth(token)).status_code == 404
