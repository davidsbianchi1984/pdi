"""Private Data Infrastructure HTTP API.

Admin endpoints manage deployments and tenants. Data endpoints require a tenant
bearer token (``Authorization: Bearer pdi_...``) and operate only within that
tenant's namespace — one integrating system cannot read another's records.
"""

from __future__ import annotations

from fastapi import Depends, FastAPI, Header, HTTPException

from . import audit, vault
from .models import DeploymentCreate, RecordPut, TenantCreate


def _tenant(authorization: str = Header(default="")) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "missing tenant bearer token")
    tenant = vault.tenant_by_token(authorization[len("Bearer "):])
    if tenant is None:
        raise HTTPException(401, "invalid tenant token")
    return tenant


def create_app() -> FastAPI:
    app = FastAPI(title="Private Data Infrastructure", version="0.1.0")

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    # -- admin: deployments & tenants ---------------------------------------

    @app.post("/deployments", status_code=201)
    def create_deployment(body: DeploymentCreate) -> dict:
        return vault.create_deployment(body.model_dump())

    @app.post("/tenants", status_code=201)
    def create_tenant(body: TenantCreate) -> dict:
        # Returns the tenant token once — the integrating system stores it.
        return vault.create_tenant(body.name)

    # -- data plane (tenant-scoped, encrypted at rest) ----------------------

    @app.put("/records")
    def put_record(body: RecordPut, tenant: dict = Depends(_tenant)) -> dict:
        return vault.put(tenant, body.key, body.value)

    @app.get("/records/{key:path}")
    def get_record(key: str, tenant: dict = Depends(_tenant)) -> dict:
        rec = vault.get(tenant, key)
        if rec is None:
            raise HTTPException(404, "record not found")
        return rec

    @app.delete("/records/{key:path}", status_code=204)
    def delete_record(key: str, tenant: dict = Depends(_tenant)) -> None:
        if not vault.delete(tenant, key):
            raise HTTPException(404, "record not found")

    @app.get("/records")
    def list_records(tenant: dict = Depends(_tenant)) -> dict:
        return {"keys": vault.list_keys(tenant)}

    @app.get("/snapshot")
    def snapshot(tenant: dict = Depends(_tenant)) -> dict:
        return vault.export_snapshot(tenant)

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
