"""Pydantic schemas for the PDI API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


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
