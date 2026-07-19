"""Private Data Infrastructure HTTP API.

Admin endpoints manage deployments and tenants. Data endpoints require a tenant
bearer token (``Authorization: Bearer pdi_...``) and operate only within that
tenant's namespace — one integrating system cannot read another's records.
"""

from __future__ import annotations

import os
import secrets

from fastapi import Depends, FastAPI, Header, HTTPException

from . import audit, db, vault


def vault_module_new_id() -> str:
    return db.new_id("ctb")
from .models import (ContributionIn, DeploymentCreate, RecordPut,
                     SnapshotRestore, TenantCreate, TokenIssue)


def _tenant(authorization: str = Header(default="")) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "missing tenant bearer token")
    tenant = vault.tenant_by_token(authorization[len("Bearer "):])
    if tenant is None:
        raise HTTPException(401, "invalid tenant token")
    return tenant


def _admin(authorization: str = Header(default="")) -> None:
    """Admin endpoints (deployments, tenants, token issuance) are guarded by
    PDI_ADMIN_TOKEN. Unset = development mode (open, for local use only)."""
    required = os.environ.get("PDI_ADMIN_TOKEN")
    if not required:
        return
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "admin bearer token required")
    # Constant-time compare so a wrong token can't be recovered by timing.
    if not secrets.compare_digest(authorization[len("Bearer "):], required):
        raise HTTPException(403, "invalid admin token")


def _writer(tenant: dict = Depends(_tenant)) -> dict:
    if tenant.get("role") != "write":
        raise HTTPException(403, "this token is read-only")
    return tenant


def create_app() -> FastAPI:
    app = FastAPI(title="Private Data Infrastructure", version="0.1.0")

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    # -- admin: deployments & tenants ---------------------------------------

    @app.post("/deployments", status_code=201)
    def create_deployment(body: DeploymentCreate,
                          _: None = Depends(_admin)) -> dict:
        return vault.create_deployment(body.model_dump())

    @app.post("/tenants", status_code=201)
    def create_tenant(body: TenantCreate, _: None = Depends(_admin)) -> dict:
        # Returns the tenant token once — the integrating system stores it.
        return vault.create_tenant(body.name)

    @app.post("/tenants/{tenant_id}/tokens", status_code=201)
    def issue_token(tenant_id: str, body: TokenIssue,
                    _: None = Depends(_admin)) -> dict:
        # Role-based access control: scoped read or write tokens per tenant.
        return vault.issue_token(tenant_id, body.role)

    @app.delete("/tokens/{token}", status_code=204)
    def revoke_token(token: str, _: None = Depends(_admin)) -> None:
        if not vault.revoke_token(token):
            raise HTTPException(404, "token not found")

    @app.delete("/tenants/{tenant_id}")
    def delete_tenant(tenant_id: str, mode: str = "soft",
                      _: None = Depends(_admin)) -> dict:
        # mode=soft (default) tombstones with a recovery window; mode=wipe
        # permanently removes the tenant's data. Both are audited.
        if mode not in ("soft", "wipe"):
            raise HTTPException(422, "mode must be 'soft' or 'wipe'")
        result = vault.delete_tenant(tenant_id, mode)
        if result is None:
            raise HTTPException(404, "tenant not found")
        return result

    @app.post("/tenants/{tenant_id}/restore")
    def restore_tenant(tenant_id: str, _: None = Depends(_admin)) -> dict:
        result = vault.restore_tenant(tenant_id)
        if result is None:
            raise HTTPException(404, "tenant not found")
        return result

    # -- data plane (tenant-scoped, encrypted at rest) ----------------------

    @app.put("/records")
    def put_record(body: RecordPut, tenant: dict = Depends(_writer)) -> dict:
        return vault.put(tenant, body.key, body.value)

    @app.get("/records/{key:path}")
    def get_record(key: str, tenant: dict = Depends(_tenant)) -> dict:
        rec = vault.get(tenant, key)
        if rec is None:
            raise HTTPException(404, "record not found")
        return rec

    @app.delete("/records/{key:path}", status_code=204)
    def delete_record(key: str, tenant: dict = Depends(_writer)) -> None:
        if not vault.delete(tenant, key):
            raise HTTPException(404, "record not found")

    @app.get("/records")
    def list_records(tenant: dict = Depends(_tenant)) -> dict:
        return {"keys": vault.list_keys(tenant)}

    @app.get("/snapshot")
    def snapshot(tenant: dict = Depends(_tenant)) -> dict:
        return vault.export_snapshot(tenant)

    @app.post("/restore")
    def restore(body: SnapshotRestore, tenant: dict = Depends(_writer)) -> dict:
        # Disaster recovery: reinsert a ciphertext-only snapshot.
        return vault.restore_snapshot(
            tenant, [r.model_dump() for r in body.records])

    # -- cloud-model contribution intake ------------------------------------

    @app.post("/contributions", status_code=201)
    def add_contribution(body: ContributionIn,
                         tenant: dict = Depends(_writer)) -> dict:
        """Encrypted, audited intake for anonymized model-improvement data
        contributed by integrating systems (see docs/cloud-model.md)."""
        import json as _json
        contribution_id = vault_module_new_id()
        key = f"contributions/{body.source}/{contribution_id}"
        vault.put(tenant, key, _json.dumps(
            {"kind": body.kind, "payload": body.payload}))
        return {"id": contribution_id, "key": key, "sealed": True}

    @app.get("/contributions")
    def list_contributions(tenant: dict = Depends(_tenant)) -> dict:
        keys = [k for k in vault.list_keys(tenant)
                if k.startswith("contributions/")]
        return {"count": len(keys), "keys": keys}

    # -- compliance ---------------------------------------------------------

    @app.get("/audit")
    def audit_log(tenant: dict = Depends(_tenant)) -> list[dict]:
        return audit.entries(tenant["id"])

    @app.get("/audit/verify")
    def audit_verify(tenant: dict = Depends(_tenant)) -> dict:
        # Chain integrity is global; any tenant may verify the whole chain.
        return audit.verify()

    return app


app = create_app()
