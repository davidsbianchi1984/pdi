"""SQLite persistence for PDI (independent of QRME and JIM databases).

Record *values* are stored encrypted (see crypto.py); only opaque ciphertext
touches disk. The audit log is append-only and hash-chained for tamper
evidence.
"""

from __future__ import annotations

import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone

_SCHEMA = """
CREATE TABLE IF NOT EXISTS deployments (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    option      TEXT NOT NULL,   -- on_premises | colocation
    facility    TEXT,
    tier        TEXT,            -- e.g. "Tier III+"
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tenants (
    id             TEXT PRIMARY KEY,
    name           TEXT NOT NULL,   -- integrating system, e.g. "jim-mini"
    token          TEXT NOT NULL UNIQUE,   -- SHA-256 hash of the bearer token
    deleted_at     TEXT,            -- soft-delete tombstone (recovery window)
    retention_days INTEGER,         -- NULL = keep forever; N = auto-expire after N days
    terms_version  TEXT,            -- ToS version in force at provisioning (receipt)
    terms_accepted_at TEXT,
    created_at     TEXT NOT NULL
);

-- Envelope encryption: each version has a data-encryption key (DEK), stored
-- only wrapped (encrypted) by the KEK in the KMS/HSM. Rotation adds a version.
CREATE TABLE IF NOT EXISTS key_versions (
    version      INTEGER PRIMARY KEY,
    wrapped_dek  TEXT NOT NULL,   -- DEK encrypted by the key-encryption key
    active       INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT NOT NULL
);

-- BYOK: a tenant that brings its own key gets its own keyring, kept separate
-- from the deployment's above so an existing vault needs no migration and the
-- two custody models never share a version number.
CREATE TABLE IF NOT EXISTS tenant_key_versions (
    tenant_id    TEXT NOT NULL REFERENCES tenants(id),
    version      INTEGER NOT NULL,
    wrapped_dek  TEXT NOT NULL,   -- DEK wrapped by the *customer's* KEK
    active       INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT NOT NULL,
    PRIMARY KEY (tenant_id, version)
);

-- Which custody model a tenant is under. No row = the deployment's own key
-- (the operator can decrypt). A row means the KEK is the customer's, and this
-- table deliberately holds *no key material* — only where the key comes from.
CREATE TABLE IF NOT EXISTS tenant_keys (
    tenant_id   TEXT PRIMARY KEY REFERENCES tenants(id),
    provider    TEXT NOT NULL,          -- held | kms
    config      TEXT NOT NULL DEFAULT '{}',   -- provider settings, never a key
    check_value TEXT,                   -- proves a presented key is the right
                                        -- one, without storing the key
    adopted_at  TEXT NOT NULL
);

-- Additional scoped tokens per tenant (role-based access control):
-- 'read' tokens can only read; the tenant's primary token is 'write'.
CREATE TABLE IF NOT EXISTS tenant_tokens (
    token       TEXT PRIMARY KEY,   -- SHA-256 hash of the scoped bearer token
    tenant_id   TEXT NOT NULL REFERENCES tenants(id),
    role        TEXT NOT NULL,   -- read | write
    revoked     INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS language_prefs (
    tenant_id   TEXT PRIMARY KEY REFERENCES tenants(id),
    language    TEXT NOT NULL,          -- pdi.i18n.SUPPORTED code, e.g. "es"
    mode        TEXT NOT NULL DEFAULT 'pre',  -- pre | on_demand
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS records (
    id          TEXT PRIMARY KEY,
    tenant_id   TEXT NOT NULL REFERENCES tenants(id),
    key         TEXT NOT NULL,          -- caller-chosen logical key
    ciphertext  TEXT NOT NULL,          -- AES-256-GCM sealed value
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    UNIQUE (tenant_id, key)
);

-- Compliance-grade secure file transfers. A corporation (tenant) seals a file
-- for a recipient under named compliance programs (HIPAA, OSHA, CPNI, …). The
-- content lives in the vault (encrypted at rest); a hashed one-shot receive
-- token authorizes retrieval; retention is the strictest across its programs.
CREATE TABLE IF NOT EXISTS transfers (
    id                 TEXT PRIMARY KEY,
    tenant_id          TEXT NOT NULL REFERENCES tenants(id),
    recipient          TEXT NOT NULL,
    filename           TEXT NOT NULL,
    size               INTEGER NOT NULL DEFAULT 0,
    classification     TEXT,
    programs           TEXT NOT NULL DEFAULT '[]',
    party_type         TEXT,                    -- subscriber | organization | partner
    vault_key          TEXT NOT NULL,           -- where the sealed bytes live
    receive_token_hash TEXT NOT NULL,           -- only the SHA-256 is stored
    status             TEXT NOT NULL DEFAULT 'sealed',  -- sealed | received | revoked
    retention_days     INTEGER NOT NULL DEFAULT 0,
    expires_at         TEXT,                    -- record retained until here
    created_at         TEXT NOT NULL
);

-- Inbound intakes: a corporation requests a file FROM a broadband user or a
-- partner company; that party submits it in with a one-shot submit token, and
-- it is sealed in the vault under the same compliance controls.
CREATE TABLE IF NOT EXISTS intakes (
    id                TEXT PRIMARY KEY,
    tenant_id         TEXT NOT NULL REFERENCES tenants(id),
    from_party        TEXT NOT NULL,            -- who is asked to submit
    party_type        TEXT,                     -- subscriber | organization | partner
    purpose           TEXT,
    programs          TEXT NOT NULL DEFAULT '[]',
    submit_token_hash TEXT NOT NULL,            -- only the SHA-256 is stored
    status            TEXT NOT NULL DEFAULT 'open',  -- open | submitted | closed
    vault_key         TEXT,                     -- set once submitted
    filename          TEXT,
    classification    TEXT,
    retention_days    INTEGER NOT NULL DEFAULT 0,
    expires_at        TEXT,
    created_at        TEXT NOT NULL
);

-- Bequests (pdi/bequests.py): a named person may read named scopes of this
-- tenant's vault — but only after a condition the owner set has been
-- attested. The grant token does not exist until activation: a bequest at
-- rest is a promise, not a credential, so a database read before the
-- activation yields nothing a grantee could use. Only the hash survives
-- minting.
CREATE TABLE IF NOT EXISTS bequests (
    id             TEXT PRIMARY KEY,
    tenant_id      TEXT NOT NULL REFERENCES tenants(id),
    grantee_name   TEXT NOT NULL,
    key_prefixes   TEXT NOT NULL,   -- JSON list, e.g. ["jim/u1/medical/"]
    condition      TEXT NOT NULL,   -- executor | attestation
    note           TEXT,            -- the owner's words to the grantee
    created_at     TEXT NOT NULL,
    revoked_at     TEXT,
    activated_at   TEXT,
    activation_ref TEXT,            -- what attested it: a JIM vigil event id,
                                    -- a QRME succession verification_ref, a
                                    -- death-certificate reference
    grant_hash     TEXT             -- SHA-256 of the minted grant token
);

-- Chain of custody: every material event on a transfer, for the compliance
-- record (mirrored into the tamper-evident audit chain).
CREATE TABLE IF NOT EXISTS transfer_receipts (
    id          TEXT PRIMARY KEY,
    transfer_id TEXT NOT NULL REFERENCES transfers(id),
    event       TEXT NOT NULL,   -- created | received | revoked
    actor       TEXT,
    at          TEXT NOT NULL
);

-- Connected-app connectors. Each links a tenant to an AI-integrated app from
-- the catalog (Apple Photos, Google Calendar, Microsoft 365, Canva, …). The
-- tenant's agents collect context (sealed as vault records), act, or produce.
CREATE TABLE IF NOT EXISTS app_connectors (
    id           TEXT PRIMARY KEY,
    tenant_id    TEXT NOT NULL REFERENCES tenants(id),
    provider     TEXT NOT NULL,
    app          TEXT NOT NULL,
    label        TEXT NOT NULL,
    capabilities TEXT NOT NULL DEFAULT '[]',
    directions   TEXT NOT NULL DEFAULT '[]',
    status       TEXT NOT NULL DEFAULT 'active',
    collected    INTEGER NOT NULL DEFAULT 0,
    actions      INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT NOT NULL
);

-- Social-platform connectors. A tenant links a platform in one of two
-- directions: collect pulls the account's content in and seals each item as a
-- vault record (raw data other systems build profiles from); publish shares an
-- update on the platform, reachable by a QR beacon.
CREATE TABLE IF NOT EXISTS connectors (
    id          TEXT PRIMARY KEY,
    tenant_id   TEXT NOT NULL REFERENCES tenants(id),
    platform    TEXT NOT NULL,   -- instagram | x | tiktok | facebook | linkedin | youtube | reddit | threads
    direction   TEXT NOT NULL,   -- collect | publish
    handle      TEXT,
    scope       TEXT NOT NULL DEFAULT '[]',
    status      TEXT NOT NULL DEFAULT 'active',  -- active | revoked
    collected   INTEGER NOT NULL DEFAULT 0,
    published   INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL
);

-- Custody beacons (pdi/beacons.py): a printed code on a physical carrier — a
-- records box, a decommissioned drive, a courier bag — or on the facility door
-- itself. The card a stranger sees says that the thing is under custody and
-- what governs it, and never a word about what is inside. See docs/beacons.md.
CREATE TABLE IF NOT EXISTS custody_beacons (
    id          TEXT PRIMARY KEY,
    tenant_id   TEXT NOT NULL REFERENCES tenants(id),
    ref_kind    TEXT NOT NULL,   -- transfer | intake | object | facility
    ref_id      TEXT,            -- NULL for a bare object or a facility gate
    label       TEXT NOT NULL,
    disclose    TEXT NOT NULL DEFAULT 'blind',   -- blind | contact
    programs    TEXT NOT NULL DEFAULT '[]',
    state       TEXT NOT NULL DEFAULT 'sealed',  -- sealed | in_transit | opened | closed
    scans       INTEGER NOT NULL DEFAULT 0,
    active      INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT NOT NULL
);

-- Scans are cheap and frequent — a barcode gun sweeping a pallet sees the same
-- code hundreds of times — so they land here rather than on the audit chain.
-- Only a `found` report is chain-worthy; volume is how a chain stops being read.
CREATE TABLE IF NOT EXISTS beacon_scans (
    id          TEXT PRIMARY KEY,
    beacon_id   TEXT NOT NULL REFERENCES custody_beacons(id),
    at          TEXT NOT NULL
);

-- A ring at a facility gate, and the agent session that answered it. The
-- transcript is sealed in the vault; only its key and hash reach the audit
-- chain, so the chain proves what was said without becoming a copy of it.
CREATE TABLE IF NOT EXISTS beacon_rings (
    id                TEXT PRIMARY KEY,
    beacon_id         TEXT NOT NULL REFERENCES custody_beacons(id),
    tenant_id         TEXT NOT NULL REFERENCES tenants(id),
    kind              TEXT NOT NULL,   -- delivery | access | collection | other
    note              TEXT,
    state             TEXT NOT NULL DEFAULT 'open',  -- open | resolved | refused | handed_off | closed
    outcome           TEXT,            -- the policy outcome that was applied
    handed_to         TEXT,            -- the human it was routed to
    spoken_by         TEXT,            -- qrme | scripted — who wrote the words
    vault_key         TEXT,            -- sealed agent transcript
    transcript_sha256 TEXT,
    created_at        TEXT NOT NULL,
    closed_at         TEXT
);

-- Who answers this tenant's facility gate, and when (see pdi/roster.py).
-- Per tenant and in the database rather than one deployment-wide env var:
-- PDI is multi-tenant, so a global on-call name routed every customer's
-- courier to whoever set the variable.
CREATE TABLE IF NOT EXISTS gate_roster (
    id         TEXT PRIMARY KEY,
    tenant_id  TEXT NOT NULL REFERENCES tenants(id),
    name       TEXT NOT NULL,
    role       TEXT NOT NULL DEFAULT 'on-call',  -- a label, never a permission
    position   INTEGER NOT NULL DEFAULT 0,       -- order to try within a shift
    days       TEXT NOT NULL DEFAULT 'mon,tue,wed,thu,fri,sat,sun',
    from_time  TEXT NOT NULL DEFAULT '00:00:00',
    to_time    TEXT NOT NULL DEFAULT '23:59:59',  -- <= from_time ⇒ crosses midnight
    created_at TEXT NOT NULL
);

-- Facility-level settings the roster is read against. A separate table rather
-- than a column on `tenants`, which is the convention everywhere else here.
CREATE TABLE IF NOT EXISTS gate_settings (
    tenant_id  TEXT PRIMARY KEY REFERENCES tenants(id),
    timezone   TEXT NOT NULL DEFAULT 'UTC',   -- IANA; a rota read in the wrong
    updated_at TEXT NOT NULL                  -- zone pages the wrong person
);

-- An attempt to reach a human about a hand-off. Its own table rather than
-- columns on the ring: one ring can be paged more than once (a channel that
-- was down at 2am and back at 2:05), and the list somebody actually wants in
-- the morning is "which pages never landed" *across* rings.
CREATE TABLE IF NOT EXISTS gate_pages (
    id          TEXT PRIMARY KEY,
    ring_id     TEXT NOT NULL REFERENCES beacon_rings(id),
    tenant_id   TEXT NOT NULL REFERENCES tenants(id),
    urgency     TEXT NOT NULL,   -- now | soon
    reason      TEXT NOT NULL,   -- the decision outcome that raised it
    handed_to   TEXT,
    on_shift    INTEGER NOT NULL DEFAULT 1,  -- was the roster actually covering?
    state       TEXT NOT NULL,   -- queued (no channel) | sent | failed
    attempts    INTEGER NOT NULL DEFAULT 0,
    last_error  TEXT,
    created_at  TEXT NOT NULL,
    sent_at     TEXT
);

CREATE TABLE IF NOT EXISTS audit (
    seq         INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id   TEXT,
    action      TEXT NOT NULL,   -- put | get | delete | tenant.create | ...
    ref         TEXT,            -- record key or resource id
    at          TEXT NOT NULL,
    prev_hash   TEXT NOT NULL,
    hash        TEXT NOT NULL
);

-- Robots bound to a tenant as data sources (see pdi/robotics.py). What a
-- robot collects (maps, snapshots, sensor logs) is sealed into the vault
-- under robot/{model}/{id}/{kind}/… and audited like every vault write.
CREATE TABLE IF NOT EXISTS robots (
    id         TEXT PRIMARY KEY,
    tenant_id  TEXT NOT NULL REFERENCES tenants(id),
    model      TEXT NOT NULL,    -- robotics.BY_KEY key, e.g. saros_20
    name       TEXT NOT NULL,
    status     TEXT NOT NULL DEFAULT 'active',   -- active | revoked
    collected  INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

-- Per-customer BAA execution records (pdi/baa.py): metadata of the signed
-- Business Associate Agreement for each tenant. HIPAA-program transfers and
-- intakes are refused for tenants with no active record. The signed
-- instrument itself stays with counsel; document_sha256 keeps it verifiable.
CREATE TABLE IF NOT EXISTS baa_records (
    id                  TEXT PRIMARY KEY,
    tenant_id           TEXT NOT NULL REFERENCES tenants(id),
    customer_legal_name TEXT NOT NULL,
    operator_legal_name TEXT NOT NULL,
    effective_date      TEXT NOT NULL,
    customer_signatory  TEXT,
    operator_signatory  TEXT,
    document_sha256     TEXT,          -- hash of the executed document
    status              TEXT NOT NULL DEFAULT 'executed',  -- executed | superseded | terminated
    terminated_at       TEXT,
    created_at          TEXT NOT NULL
);

-- "Help us improve": product feedback anyone can send about the app itself.
-- Not tenant record data — this is meta feedback on PDI as a product, so it
-- sits outside the per-tenant namespace. Submitter is a tenant:id when a
-- tenant token is presented, else 'anonymous'; a submitter sees only their
-- own words, everyone the aggregate tally.
CREATE TABLE IF NOT EXISTS feedback (
    id         TEXT PRIMARY KEY,
    submitter  TEXT NOT NULL DEFAULT 'anonymous',
    category   TEXT NOT NULL,          -- idea | improvement | bug | praise | other
    message    TEXT NOT NULL,
    rating     INTEGER,                -- optional 1..5 satisfaction
    status     TEXT NOT NULL DEFAULT 'received',   -- received | reviewed | planned | shipped
    created_at TEXT NOT NULL
);

-- Where the console's helper dock sits and what it shows (see pdi/dock.py).
-- Preferences only. The pane shows counts and routes; it cannot read a record,
-- so there is nothing here to grant.
CREATE TABLE IF NOT EXISTS dock_prefs (
    tenant_id  TEXT PRIMARY KEY,
    corner     TEXT NOT NULL DEFAULT 'bottom_right',
    state      TEXT NOT NULL DEFAULT 'open',
    face       TEXT NOT NULL DEFAULT 'agents',
    faces      TEXT NOT NULL,                        -- JSON array
    updated_at TEXT NOT NULL
);

-- Where a tenant's vault physically lives (see pdi/hosting.py). A record of an
-- arrangement, not a switch: nothing in this product moves data because a row
-- changed.
--
-- One live row per tenant, ended rather than replaced, because "where has this
-- vault lived" is precisely the question an auditor asks afterwards.
CREATE TABLE IF NOT EXISTS tenant_hosting (
    id         TEXT PRIMARY KEY,
    tenant_id  TEXT NOT NULL,
    mode       TEXT NOT NULL,   -- colocation | leased_space | own_facility | own_device
    note       TEXT,
    started_at TEXT NOT NULL,
    ended_at   TEXT
);
CREATE INDEX IF NOT EXISTS tenant_hosting_live
    ON tenant_hosting (tenant_id, ended_at);

-- How far an operator has got through the console walkthrough (pdi/tutorial.py).
-- One row per step rather than a cursor, so somebody who jumped to the audit
-- chapter and came back is not told they have finished the vault.
--
-- Outside the per-tenant namespace on purpose: this is about a person learning
-- the console, not about anybody's records — and it is the only thing the
-- walkthrough writes anywhere.
CREATE TABLE IF NOT EXISTS console_tutorial (
    learner_id TEXT NOT NULL,
    lesson     TEXT NOT NULL,
    done_at    TEXT NOT NULL,
    PRIMARY KEY (learner_id, lesson)
);

-- Accessibility reports: what somebody was trying to do, what stood in the
-- way, and what would have helped — in their own words, in their own
-- language. Deliberately narrower than feedback: there is no submitter
-- column at all, because a report about ability must not require disclosing
-- anything about the body that wrote it. No pdi_key either — this IS the
-- vault product, so there is no second place to seal to.
-- Error reports, folded into counters the moment they arrive (pdi/problems.py).
-- No report is stored as a report: the key is what triage needs and nothing
-- narrower, because a row that identifies one install is what the whole
-- content-free design exists to avoid.
CREATE TABLE IF NOT EXISTS problem_reports (
    source      TEXT NOT NULL,
    app_version TEXT NOT NULL,
    platform    TEXT NOT NULL,
    op          TEXT NOT NULL,
    status      INTEGER NOT NULL,
    day         TEXT NOT NULL,
    count       INTEGER NOT NULL DEFAULT 0,
    last_seen   TEXT NOT NULL,
    PRIMARY KEY (source, app_version, platform, op, status)
);

-- The resident intelligence (pdi/resident.py): the coach/agent living in
-- this process, beside the data. A task is a plan of steps; each step names
-- a tool from the closed registry; structured results land in resident_rows
-- (the queryable tables) and embeddings in resident_vectors. Every row is
-- tenant-scoped, because the engine runs inside the same fence as the vault.
CREATE TABLE IF NOT EXISTS resident_tasks (
    id          TEXT PRIMARY KEY,
    tenant_id   TEXT NOT NULL REFERENCES tenants(id),
    goal        TEXT NOT NULL,
    planned_by  TEXT NOT NULL,   -- rules-v1 | caller
    status      TEXT NOT NULL,   -- planned | running | done | failed
    created_at  TEXT NOT NULL,
    finished_at TEXT,
    every_hours REAL,            -- standing tasks: repeat interval
    next_run_at TEXT             -- standing tasks: the next appointment
);

CREATE TABLE IF NOT EXISTS resident_steps (
    id          TEXT PRIMARY KEY,
    task_id     TEXT NOT NULL REFERENCES resident_tasks(id),
    tenant_id   TEXT NOT NULL REFERENCES tenants(id),
    position    INTEGER NOT NULL,
    title       TEXT NOT NULL,
    tool        TEXT NOT NULL,
    args        TEXT NOT NULL,   -- JSON
    status      TEXT NOT NULL,   -- planned | done | failed | skipped
    result_ref  TEXT,            -- a vault key, a dataset name, a vector key
    summary     TEXT,
    error       TEXT,
    finished_at TEXT
);

-- "Fetch data, put it in a table so the app can query it." One physical
-- table, many named datasets: this schema adds tables by CREATE IF NOT
-- EXISTS at boot and never migrates, so the datasets a tenant invents at
-- runtime are rows here rather than DDL.
CREATE TABLE IF NOT EXISTS resident_rows (
    id         TEXT PRIMARY KEY,
    tenant_id  TEXT NOT NULL REFERENCES tenants(id),
    dataset    TEXT NOT NULL,
    row        TEXT NOT NULL,    -- one flat JSON object
    source_ref TEXT,             -- where it came from (a vault key, a URL)
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS resident_rows_by_dataset
    ON resident_rows (tenant_id, dataset);

CREATE TABLE IF NOT EXISTS resident_vectors (
    id          TEXT PRIMARY KEY,
    tenant_id   TEXT NOT NULL REFERENCES tenants(id),
    key         TEXT NOT NULL,
    text_sha256 TEXT NOT NULL,   -- of what was embedded; the text itself is not kept here
    embedder    TEXT NOT NULL,   -- which algorithm made it; mixed spaces do not compare
    dim         INTEGER NOT NULL,
    vector      BLOB NOT NULL,   -- float32 little-endian, L2-normalised
    created_at  TEXT NOT NULL,
    UNIQUE (tenant_id, key)
);

CREATE TABLE IF NOT EXISTS access_reports (
    id         TEXT PRIMARY KEY,
    lang       TEXT NOT NULL DEFAULT 'en',
    doing      TEXT NOT NULL,           -- what the person was trying to do
    wall       TEXT NOT NULL,           -- what stood in the way
    help       TEXT,                    -- what would help, if they said
    status     TEXT NOT NULL DEFAULT 'received',  -- received | accepted | built
    created_at TEXT NOT NULL
);
"""

_local = threading.local()


def db_path() -> str:
    return os.environ.get("PDI_DB", "pdi.db")


def connect() -> sqlite3.Connection:
    conn = getattr(_local, "conn", None)
    if conn is None or getattr(_local, "path", None) != db_path():
        conn = sqlite3.connect(db_path())
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")  # concurrent readers
        conn.executescript(_SCHEMA)
        _migrate(conn)
        _local.conn = conn
        _local.path = db_path()
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    """Additive migrations for databases created before a column existed."""
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(tenants)")}
    if "retention_days" not in cols:
        conn.execute("ALTER TABLE tenants ADD COLUMN retention_days INTEGER")
        conn.commit()

    # `gate_pages` shipped in 0.1.9 without `on_shift`; CREATE TABLE IF NOT
    # EXISTS will not add it to a vault that already has the table. Defaulting
    # to 1 is right for the rows already there: they predate the roster, so
    # there was exactly one name and it was always the one on duty.
    # `resident_tasks` shipped in 0.86.0 without the standing-task columns.
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(resident_tasks)")}
    if cols and "every_hours" not in cols:
        conn.execute("ALTER TABLE resident_tasks ADD COLUMN every_hours REAL")
        conn.execute("ALTER TABLE resident_tasks ADD COLUMN next_run_at TEXT")
        conn.commit()

    cols = {r["name"] for r in conn.execute("PRAGMA table_info(gate_pages)")}
    if cols and "on_shift" not in cols:
        conn.execute("ALTER TABLE gate_pages ADD COLUMN on_shift INTEGER"
                     " NOT NULL DEFAULT 1")
        conn.commit()


def reset() -> None:
    conn = getattr(_local, "conn", None)
    if conn is not None:
        conn.close()
        _local.conn = None
        _local.path = None


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()
