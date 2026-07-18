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
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,   -- integrating system, e.g. "jim-mini"
    token       TEXT NOT NULL UNIQUE,   -- bearer token presented on requests
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
        conn.executescript(_SCHEMA)
        _local.conn = conn
        _local.path = db_path()
    return conn


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
