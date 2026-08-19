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


class AppConnect(BaseModel):
    provider: str
    app: str
    capabilities: list[str] = Field(default_factory=list)  # empty = grant all


class AppItem(BaseModel):
    content: str
    ref: str | None = None


class AppCollect(BaseModel):
    items: list[AppItem] = Field(default_factory=list)


class AppInvoke(BaseModel):
    capability: str
    input: str | None = None


class RobotBind(BaseModel):
    model: str                      # pdi.robotics catalog key, e.g. "saros_20"
    name: str | None = None         # household name; defaults to the label


class RobotIngest(BaseModel):
    kind: str                       # map | snapshot | sensor_log
    content: str                    # the payload to seal (JSON/base64/text)
    ref: str | None = None          # vendor-side reference, if any


PartyType = Literal["subscriber", "organization", "partner"]


class TransferCreate(BaseModel):
    recipient: str                     # who the file is for (id / email / handle)
    filename: str
    content: str                       # the file body (sealed at rest)
    programs: list[str] = Field(default_factory=list)  # hipaa | osha | cpni | ...
    classification: str | None = None  # e.g. PHI | PII | confidential
    party_type: PartyType | None = None  # subscriber (a broadband user) | organization | partner


class IntakeCreate(BaseModel):
    from_party: str                    # who is asked to send a file in
    party_type: PartyType | None = None
    purpose: str | None = None
    programs: list[str] = Field(default_factory=list)


class IntakeSubmit(BaseModel):
    filename: str
    content: str
    classification: str | None = None


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


class LanguageChoice(BaseModel):
    language: str                      # pdi.i18n.SUPPORTED code, e.g. "es"
    mode: str = "pre"                  # pre (notes swapped in) | on_demand


class TranslateRequest(BaseModel):
    text: str
    to: str | None = None


class RecordPut(BaseModel):
    key: str
    value: str    # plaintext from the caller; sealed at rest by PDI


class CustomerKeyAdopt(BaseModel):
    """Bring your own key (BYOK).

    ``held`` — you supply the key and present it on every request; PDI stores
    nothing derived from it, so the operator's disk and backups are unreadable
    without you. ``kms`` — the key stays in your own KMS and PDI calls out to
    unwrap; the operator can decrypt while your grant is live, and cannot once
    you revoke it.
    """
    provider: Literal["held", "kms"] = "held"
    key: str | None = None        # held: base64 of 32 bytes. Never stored.
    config: dict = {}             # kms: {"key_id": "..."} — never key material


class TokenIssue(BaseModel):
    role: Literal["read", "write"]


class BAARecordIn(BaseModel):
    """Metadata of an executed Business Associate Agreement (docs/baa-template.md)."""
    customer_legal_name: str
    operator_legal_name: str
    effective_date: str                # ISO date the agreement took effect
    customer_signatory: str | None = None
    operator_signatory: str | None = None
    document_sha256: str | None = None  # hash of the signed instrument


class FeedbackSubmit(BaseModel):
    """"Help us improve": product feedback on the app itself."""
    category: str = "idea"             # idea | improvement | bug | praise | other
    message: str
    rating: int | None = None          # optional 1..5 satisfaction


class AccessReportSubmit(BaseModel):
    """An accessibility report: three answers, none of them a diagnosis."""
    doing: str                         # what you were trying to do
    wall: str                          # what stood in the way
    help: str | None = None           # what would help, in your words
    lang: str = "en"                  # the language the report is written in


class DockConfig(BaseModel):
    """Where the console's helper pane sits and what it carries (pdi/dock.py)."""
    corner: str | None = None
    state: str | None = None
    face: str | None = None
    faces: list[str] | None = None


class HostingChoice(BaseModel):
    """Where a tenant's vault lives (pdi/hosting.py).

    A record of an arrangement rather than an instruction: nothing moves
    because this changes.
    """
    mode: str                           # colocation | leased_space | own_facility | own_device
    note: str | None = None


class GuideMark(BaseModel):
    """A step of the console walkthrough (pdi/tutorial.py).

    `learner_id` is whoever is being walked through, and carries no
    authority — the walkthrough describes the console rather than any data, so
    knowing which step somebody is on is not a secret worth a check that would
    stop an operator with no token yet from being shown around.
    """
    learner_id: str
    lesson: str = ""
    mode: str = "text"                  # text | voice


class ConsoleAsk(BaseModel):
    """A question for the console assistant (pdi/assistant.py)."""
    question: str
    mode: str = "text"                  # text | voice


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


class BeaconPlace(BaseModel):
    """Print a carrier — or a gate — onto something.

    ``programs`` is only read for ``object`` and ``facility``: a beacon on a
    transfer or an intake inherits that record's programs, because the record
    already knows what governs it and two sources for one fact is how they end
    up disagreeing on the card a stranger reads.
    """

    ref_kind: Literal["transfer", "intake", "object", "facility"]
    ref_id: str | None = None
    label: str
    disclose: Literal["blind", "contact"] = "blind"
    programs: list[str] = Field(default_factory=list)


class BeaconState(BaseModel):
    state: Literal["sealed", "in_transit", "opened", "closed"]


class BeaconFound(BaseModel):
    """A finder's report. Not a message — a custody receipt."""

    where: str | None = None
    contact: str | None = None


class GateRing(BaseModel):
    """Somebody at the door. ``note`` is their own words, and is treated as
    evidence of what was asked rather than as an instruction to anything."""

    kind: Literal["delivery", "access", "collection", "other"]
    note: str | None = None


class RosterAdd(BaseModel):
    """Somebody who answers this facility's gate, and when.

    ``days``/``from_time``/``to_time`` are optional and default to always on,
    which is what a roster of plain names meant before shifts existed. A shift
    whose ``to_time`` is at or before its ``from_time`` crosses midnight —
    ``18:00``–``06:00`` is the case a facility gate exists for.
    """

    name: str
    role: Literal["on-call", "supervisor", "reception", "security",
                  "site lead"] = "on-call"
    days: str | None = None          # "mon-fri" | "sat,sun" | "all"
    from_time: str | None = None     # "18:00"
    to_time: str | None = None       # "06:00"


class GateTimezone(BaseModel):
    """The facility's own IANA zone. Refused if unknown rather than silently
    read as UTC — the silent version looks correct for half the year."""

    timezone: str


class BequestCreate(BaseModel):
    """The owner's answer to "what about when you are gone?" — written now,
    while they are fine. Names the grantee, bounds the shelf."""

    grantee_name: str
    key_prefixes: list[str]
    condition: str = "executor"     # executor | attestation
    note: str | None = None


class BequestActivate(BaseModel):
    """The attestation is not optional: what confirmed the condition — a JIM
    vigil event id, a QRME succession verification, a certificate number."""

    activation_ref: str


class ResidentStep(BaseModel):
    """One step of a caller-authored plan. The tool must be on the resident
    registry — validated at plan time, so a bad plan refuses before it runs."""

    tool: str
    title: str | None = None
    args: dict = {}


class ResidentPlan(BaseModel):
    """A goal in words. Steps are optional: absent, the deterministic
    planner decomposes the goal; present, they are validated the same."""

    goal: str
    steps: list[ResidentStep] | None = None


class ResidentEmbed(BaseModel):
    key: str
    text: str


class ResidentSearch(BaseModel):
    query: str
    top_k: int = 5


class ResidentInfer(BaseModel):
    prompt: str
