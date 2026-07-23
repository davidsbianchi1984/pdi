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

-- Additional scoped tokens per tenant (role-based access control):
-- 'read' tokens can only read; the tenant's primary token is 'write'.
CREATE TABLE IF NOT EXISTS tenant_tokens (
    token       TEXT PRIMARY KEY,   -- SHA-256 hash of the scoped bearer token
    tenant_id   TEXT NOT NULL REFERENCES tenants(id),
    role        TEXT NOT NULL,   -- read | write
    revoked     INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL
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

CREATE TABLE IF NOT EXISTS audit (
    seq         INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id   TEXT,
    action      TEXT NOT NULL,   -- put | get | delete | tenant.create | ...
    ref         TEXT,            -- record key or resource id
    at          TEXT NOT NULL,
    prev_hash   TEXT NOT NULL,
    hash        TEXT NOT NULL
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
