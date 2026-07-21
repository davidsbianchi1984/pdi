"""PDI Services — Position & Assistant Builder.

An industry-agnostic role-mapping intake (the "AI Integration & Role Mapping
Questionnaire"): a person describes their role and workflow, and the builder
returns a structured **assistant blueprint** plus a ready-to-use **assistant
spec** (a system-prompt for a personalized sub-model). The raw answers are
sensitive workforce data, so they're sealed in the tenant's vault; the blueprint
is derived and returned.

Responsible-by-design: this is *decision support*, not an automated staffing
decision. High-stakes calls (incident response, contracts, budgets, safety) are
always flagged **human-in-the-loop**; automation output is framed as
opportunities and assistant capabilities, and reskilling / repositioning paths
are surfaced alongside — never a verdict on a person.
"""

from __future__ import annotations

# ---- capability catalogue (maps questionnaire signals -> assistant skills) --
CAPABILITIES = {
    "task_tracking": "Real-time task tracking",
    "doc_drafting": "Document drafting & data entry",
    "report_generation": "Routine report generation",
    "compliance_logging": "Compliance logging & checklists",
    "scheduling": "Employee scheduling suggestions",
    "maintenance_alerts": "Maintenance & incident alerts",
    "log_summaries": "Daily activity-log summaries",
    "decision_support": "Decision suggestions in your style",
}

# Decisions that must keep a human in the loop, whatever the automation score.
HUMAN_IN_LOOP = {
    "incident_response": "Incident-response decisions",
    "contracts": "Contract approvals & vendor commitments",
    "budget": "Budget allocations",
    "staffing": "Staffing coverage & time-off approvals",
    "safety_compliance": "Safety / regulatory compliance sign-off",
}

TONES = {"directive", "neutral", "casual", "analytical"}
INTERACTIONS = {"voice", "text", "hybrid"}
OVERSIGHT = {"frontline", "administrative", "supervisory", "executive"}

RESKILL_PATHS = [
    "AI assistant management & prompt operations",
    "Data operations & analytics",
    "System analytics & workflow automation design",
]


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, round(x, 2)))


def build_blueprint(intake: dict) -> dict:
    """Turn a completed questionnaire (any industry) into an assistant
    blueprint. Everything is explainable: each recommendation lists why."""
    s1 = intake.get("role", {})
    s2 = intake.get("workflow", {})
    s3 = intake.get("decisions", {})
    s4 = intake.get("bottlenecks", {})
    s5 = intake.get("preferences", {})
    s6 = intake.get("admin", {})
    s7 = intake.get("future", {})

    oversight = s1.get("role_type") if s1.get("role_type") in OVERSIGHT else "frontline"
    industry = intake.get("industry") or "general"

    # -- recommended capabilities: explicit prefs + inferred from workflow ----
    wants = set(s5.get("wants") or [])
    caps: dict[str, str] = {}
    reasons: dict[str, str] = {}
    for c in wants:
        if c in CAPABILITIES:
            caps[c] = CAPABILITIES[c]
            reasons[c] = "requested"
    # infer from the workflow audit
    manages = set(s2.get("manages") or [])           # scheduling/timekeeping/dispatch/inventory
    if manages & {"scheduling", "timekeeping", "dispatch"} and "scheduling" not in caps:
        caps["scheduling"] = CAPABILITIES["scheduling"]; reasons["scheduling"] = "manages scheduling/dispatch"
    if s2.get("documents_incidents") and "maintenance_alerts" not in caps:
        caps["maintenance_alerts"] = CAPABILITIES["maintenance_alerts"]; reasons["maintenance_alerts"] = "documents incidents/maintenance"
    if (s6.get("compliance_accountable") or s2.get("recurring_meetings")) and "compliance_logging" not in caps:
        caps["compliance_logging"] = CAPABILITIES["compliance_logging"]; reasons["compliance_logging"] = "compliance / recurring logs"
    if (s2.get("manual_tasks")) and "report_generation" not in caps:
        caps["report_generation"] = CAPABILITIES["report_generation"]; reasons["report_generation"] = "manual report/data work"
    if s5.get("summarize_logs"):
        caps["log_summaries"] = CAPABILITIES["log_summaries"]; reasons["log_summaries"] = "requested log summaries"
    if s5.get("learn_decision_style"):
        caps["decision_support"] = CAPABILITIES["decision_support"]; reasons["decision_support"] = "opted into decision suggestions"

    # -- automation opportunity score (0..1), explainable ---------------------
    signals = 0.0
    if s2.get("manual_tasks"): signals += 1
    if s4.get("redundant_tasks"): signals += 1
    if s4.get("outdated_tasks"): signals += 1
    if s3.get("automatable_decisions"): signals += 1
    signals += 0.5 * len(caps)
    if s7.get("comfortable_automation"): signals += 1
    signals += 0.5 * len(s7.get("roles_obsolete_3_5yr") or [])
    automation_score = _clamp(signals / 8.0)

    # -- human-in-the-loop: which decisions must stay human -------------------
    dec = set(s3.get("scope") or [])                 # routes/staffing/incident/contracts/budget
    keep_human = []
    mapping = {"incident": "incident_response", "contracts": "contracts",
               "budget": "budget", "staffing": "staffing"}
    for d in dec:
        if d in mapping:
            keep_human.append(HUMAN_IN_LOOP[mapping[d]])
    if s6.get("compliance_accountable"):
        keep_human.append(HUMAN_IN_LOOP["safety_compliance"])
    keep_human = sorted(set(keep_human))

    # -- obsolescence: framed as automation opportunities, not verdicts -------
    opportunities = sorted(set(
        (s4.get("redundant_tasks") or []) + (s4.get("outdated_tasks") or [])
        + (s3.get("automatable_decisions") or [])))
    watch_3_5yr = list(s7.get("roles_obsolete_3_5yr") or [])

    reskilling = {
        "interested": bool(s7.get("reskilling_interest")),
        "suggested_paths": RESKILL_PATHS if s7.get("reskilling_interest") else [],
    }

    tone = s5.get("tone") if s5.get("tone") in TONES else "neutral"
    interaction = s5.get("interaction") if s5.get("interaction") in INTERACTIONS else "hybrid"

    spec = _assistant_spec(s1, industry, oversight, list(caps.values()),
                           tone, interaction, keep_human, s5)

    return {
        "industry": industry,
        "role": {"job_title": s1.get("job_title"), "department": s1.get("department"),
                 "oversight_level": oversight, "manages_staff": s1.get("manages_staff", 0)},
        "assistant": {
            "tone": tone, "interaction": interaction,
            "capabilities": [{"key": k, "label": v, "why": reasons.get(k, "requested")}
                             for k, v in caps.items()],
        },
        "automation": {
            "opportunity_score": automation_score,
            "opportunities": opportunities,          # tasks to automate, not people
            "watch_3_5yr": watch_3_5yr,
            "note": "Advisory automation opportunities. Not a staffing decision.",
        },
        "human_in_loop": {
            "required": keep_human,
            "note": "These decisions keep a human accountable regardless of automation.",
        },
        "reskilling": reskilling,
        "assistant_spec": spec,
    }


def _assistant_spec(s1: dict, industry: str, oversight: str, capabilities: list[str],
                    tone: str, interaction: str, keep_human: list[str], s5: dict) -> str:
    """A ready-to-use system-prompt for the personalized sub-model."""
    name = s1.get("job_title") or "Role"
    caps = "; ".join(capabilities) or "general assistance"
    guard = ("; ".join(keep_human) or "none flagged")
    style = s5.get("learn_decision_style") and " Learn the operator's decision-making style and suggest — never take — actions." or ""
    summ = s5.get("summarize_logs") and " Proactively summarise the daily activity log." or ""
    return (
        f"You are the AI assistant for a {name} in the {industry} sector "
        f"({oversight} role). Communicate in a {tone} tone over {interaction}. "
        f"Your capabilities: {caps}.{summ}{style} "
        f"Human-in-the-loop — never auto-approve or finalise: {guard}. Always "
        f"escalate safety and incident matters to a person. You are decision "
        f"support: surface options and evidence, and defer final judgement to "
        f"the human you assist."
    )
