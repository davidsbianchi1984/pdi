"""Pydantic schemas for the PDI API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


SocialPlatform = Literal[
    "instagram", "x", "tiktok", "facebook", "linkedin", "youtube", "reddit",
    "threads", "whatsapp", "meta", "mastodon", "twitch", "snapchat", "roblox",
    "pinterest", "discord",
]


class ConnectorCreate(BaseModel):
    platform: SocialPlatform
    direction: Literal["collect", "publish"]
    handle: str | None = None
    scope: list[str] = Field(default_factory=list)


class ConnectorItem(BaseModel):
    content: str
    ref: str | None = None             # the item's id on the platform


class ConnectorIngest(BaseModel):
    items: list[ConnectorItem] = Field(default_factory=list)


class ConnectorPublish(BaseModel):
    content: str
    topic: str | None = None


class DeploymentCreate(BaseModel):
    name: str
    option: Literal["on_premises", "colocation"]
    facility: str | None = None
    tier: str | None = None


class TenantCreate(BaseModel):
    name: str
    # Record retention for this tenant: a window ("7d"/"30d"/"90d"/"180d"/
    # "1y"/"forever") or a positive day count. Omitted / "forever" = keep
    # forever (the default).
    retention: str | None = None


class RetentionSet(BaseModel):
    retention: str    # "7d" | "30d" | "90d" | "180d" | "1y" | "forever" | <days>


class RecordPut(BaseModel):
    key: str
    value: str    # plaintext from the caller; sealed at rest by PDI


class TokenIssue(BaseModel):
    role: Literal["read", "write"]


class SnapshotRecord(BaseModel):
    key: str
    ciphertext: str
    updated_at: str | None = None


class SnapshotRestore(BaseModel):
    records: list[SnapshotRecord]


class RoleOverview(BaseModel):
    """Section 1 — Personal & Role Overview."""
    job_title: str | None = None
    department: str | None = None
    # frontline | administrative | supervisory | executive
    role_type: str | None = None
    manages_staff: int = 0


class WorkflowAudit(BaseModel):
    """Section 2 — Daily Workflow Audit."""
    manages: list[str] = []            # scheduling | timekeeping | dispatch | inventory
    documents_incidents: bool = False
    recurring_meetings: bool = False
    manual_tasks: bool = False


class DecisionMaking(BaseModel):
    """Section 3 — Decision-Making & Oversight."""
    scope: list[str] = []              # routes | staffing | incident | contracts | budget
    automatable_decisions: list[str] = []


class Bottlenecks(BaseModel):
    """Section 4 — Workflow Bottlenecks & Obsolescence."""
    redundant_tasks: list[str] = []
    outdated_tasks: list[str] = []


class Preferences(BaseModel):
    """Section 5 — AI Adoption & Personalization."""
    wants: list[str] = []              # capability keys the person explicitly wants
    tone: str | None = None            # directive | neutral | casual | analytical
    interaction: str | None = None     # voice | text | hybrid
    summarize_logs: bool = False
    learn_decision_style: bool = False


class AdminExec(BaseModel):
    """Section 6 — Administrative & Executive Roles."""
    compliance_accountable: bool = False


class FutureEvolution(BaseModel):
    """Section 7 — Future AI & Workforce Evolution."""
    comfortable_automation: bool = False
    roles_obsolete_3_5yr: list[str] = []
    reskilling_interest: bool = False


class PositionIntake(BaseModel):
    """A completed AI Integration & Role-Mapping Questionnaire — industry
    agnostic. Every section is optional so a partial intake still yields a
    (partial) blueprint; the builder only ever *adds* capability suggestions,
    never fabricates a staffing verdict."""
    industry: str | None = None
    role: RoleOverview = RoleOverview()
    workflow: WorkflowAudit = WorkflowAudit()
    decisions: DecisionMaking = DecisionMaking()
    bottlenecks: Bottlenecks = Bottlenecks()
    preferences: Preferences = Preferences()
    admin: AdminExec = AdminExec()
    future: FutureEvolution = FutureEvolution()


class ContributionIn(BaseModel):
    """Anonymized model-improvement contribution from an integrating system.

    The intake is a normal vault write: sealed with AES-256-GCM under a
    ``contributions/`` key and recorded in the audit chain, so the cloud
    model's training data is encrypted at rest and every access is auditable.
    """

    source: str            # e.g. "qrme" | "jim-mini"
    kind: str              # e.g. "rated_exchange" | "guidance_outcome"
    payload: dict
    ref: str | None = None  # contributor's anonymous ref, for later revocation
