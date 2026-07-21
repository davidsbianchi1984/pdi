"""Private Data Infrastructure HTTP API.

Admin endpoints manage deployments and tenants. Data endpoints require a tenant
bearer token (``Authorization: Bearer pdi_...``) and operate only within that
tenant's namespace — one integrating system cannot read another's records.
"""

from __future__ import annotations

import os
import secrets

from fastapi import Depends, FastAPI, Header, HTTPException

from . import audit, crypto, db, positions, retention, vault
from .models import (ContributionIn, DeploymentCreate, PositionIntake, RecordPut,
                     RetentionSet, SnapshotRestore, TenantCreate, TokenIssue)


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

    # Optional CORS for a packaged operator-console front-end (app/) calling the
    # API from another origin. Off by default; set PDI_CORS_ORIGINS to a
    # comma-separated allowlist, or "*" for any.
    _origins = os.environ.get("PDI_CORS_ORIGINS")
    if _origins:
        from fastapi.middleware.cors import CORSMiddleware
        _allow = ["*"] if _origins.strip() == "*" else [
            o.strip() for o in _origins.split(",") if o.strip()]
        app.add_middleware(
            CORSMiddleware, allow_origins=_allow, allow_credentials=False,
            allow_methods=["*"], allow_headers=["*"])

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
        try:
            days = retention.parse_window(body.retention)
        except ValueError as e:
            raise HTTPException(422, str(e))
        return vault.create_tenant(body.name, retention_days=days)

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
        contributed by integrating systems (see docs/cloud-model.md). The
        payload is sealed under a ``contributions/`` key and the intake is
        recorded in the audit chain, so the cloud model's training data is
        encrypted at rest and every contribution is individually auditable and
        revocable (delete its key)."""
        import json as _json
        contribution_id = db.new_id("ctb")
        key = f"contributions/{body.source}/{contribution_id}"
        vault.put(tenant, key, _json.dumps({
            "kind": body.kind, "payload": body.payload, "ref": body.ref,
            "at": db.utcnow()}))
        audit.record("contribution.add", tenant_id=tenant["id"], ref=body.ref or key)
        return {"id": contribution_id, "key": key, "ref": body.ref, "sealed": True}

    @app.get("/contributions")
    def list_contributions(tenant: dict = Depends(_tenant)) -> dict:
        keys = [k for k in vault.list_keys(tenant)
                if k.startswith("contributions/")]
        return {"count": len(keys), "keys": keys}

    @app.delete("/contributions/{ref}", status_code=200)
    def revoke_contribution(ref: str, tenant: dict = Depends(_writer)) -> dict:
        """Revoke a contribution by its anonymous ref — deletes the sealed
        item (and audits it), so a contributor can withdraw a specific
        exchange without exposing who it belonged to."""
        import json as _json
        removed = 0
        for key in list(vault.list_keys(tenant)):
            if not key.startswith("contributions/"):
                continue
            rec = vault.get(tenant, key)
            if rec and _json.loads(rec["value"]).get("ref") == ref:
                vault.delete(tenant, key)
                removed += 1
        if not removed:
            raise HTTPException(404, "no contribution with that ref")
        audit.record("delete", tenant_id=tenant["id"], ref=f"contribution:{ref}")
        return {"ref": ref, "revoked": removed}

    # -- position & assistant builder (AI Integration & Role Mapping) --------

    @app.post("/positions", status_code=201)
    def create_position(body: PositionIntake, tenant: dict = Depends(_writer)) -> dict:
        """Turn a completed role-mapping questionnaire into an assistant
        blueprint. The raw answers are sensitive workforce data, so they are
        sealed in the tenant's vault under ``positions/{id}``; only the derived
        blueprint (capabilities, automation opportunities, human-in-the-loop
        guardrails, reskilling paths, assistant system-prompt) is returned. This
        is decision support — never an automated staffing decision."""
        import json as _json
        intake = body.model_dump()
        blueprint = positions.build_blueprint(intake)
        position_id = db.new_id("pos")
        key = f"positions/{position_id}"
        # Seal the raw intake *and* the derived blueprint together, so the
        # sensitive answers never leave the vault but the blueprint is
        # reproducible without re-decrypting only to re-derive.
        vault.put(tenant, key, _json.dumps({"intake": intake, "blueprint": blueprint,
                                            "at": db.utcnow()}))
        audit.record("position.create", tenant_id=tenant["id"], ref=position_id)
        return {"id": position_id, "key": key, **blueprint}

    @app.get("/positions")
    def list_positions(tenant: dict = Depends(_tenant)) -> dict:
        keys = [k for k in vault.list_keys(tenant) if k.startswith("positions/")]
        return {"count": len(keys),
                "ids": [k.split("/", 1)[1] for k in keys]}

    @app.get("/positions/{position_id}")
    def get_position(position_id: str, tenant: dict = Depends(_tenant)) -> dict:
        import json as _json
        rec = vault.get(tenant, f"positions/{position_id}")
        if rec is None:
            raise HTTPException(404, "position not found")
        data = _json.loads(rec["value"])
        return {"id": position_id, **data["blueprint"]}

    # -- key management (production: envelope encryption + rotation) ---------

    @app.get("/keys")
    def list_keys(_: None = Depends(_admin)) -> dict:
        return {"provider": os.environ.get("PDI_KEY_PROVIDER", "env"),
                "versions": crypto.key_versions()}

    @app.post("/keys/rotate", status_code=201)
    def rotate_key(reseal: bool = True, _: None = Depends(_admin)) -> dict:
        """Rotate to a new key version. By default immediately re-seals every
        record under it (``?reseal=false`` to defer). Old versions stay until
        retired, so nothing becomes unreadable mid-rotation."""
        result = crypto.rotate()
        audit.record("key.rotate", ref=str(result["active_version"]))
        if reseal:
            result["reseal"] = vault.reseal_all()
        return result

    @app.post("/keys/reseal")
    def reseal_keys(_: None = Depends(_admin)) -> dict:
        return vault.reseal_all()

    @app.post("/keys/retire")
    def retire_keys(_: None = Depends(_admin)) -> dict:
        """Retire non-active key versions (only safe after a reseal)."""
        n = crypto.retire_old_versions()
        audit.record("key.retire", ref=str(n))
        return {"retired": n, "versions": crypto.key_versions()}

    # -- retention (up to forever) ------------------------------------------

    @app.get("/retention")
    def retention_policy(_: None = Depends(_admin)) -> dict:
        return retention.policy()

    @app.put("/tenants/{tenant_id}/retention")
    def set_retention(tenant_id: str, body: RetentionSet,
                      _: None = Depends(_admin)) -> dict:
        try:
            result = retention.set_tenant_retention(tenant_id, body.retention)
        except ValueError as e:
            raise HTTPException(422, str(e))
        if result is None:
            raise HTTPException(404, "tenant not found")
        return result

    @app.post("/retention/sweep")
    def retention_sweep(_: None = Depends(_admin)) -> dict:
        """Enforce retention now — purge soft-deleted tenants past the recovery
        window and expire records past their tenant's retention. ``forever``
        windows purge/expire nothing."""
        return retention.sweep()

    # -- compliance ---------------------------------------------------------

    @app.get("/audit")
    def audit_log(tenant: dict = Depends(_tenant)) -> list[dict]:
        return audit.entries(tenant["id"])

    @app.get("/audit/verify")
    def audit_verify(tenant: dict = Depends(_tenant)) -> dict:
        # Chain integrity is global; any tenant may verify the whole chain.
        return audit.verify()

    @app.get("/audit/schema")
    def audit_schema() -> dict:
        # The event schema: fields, the action catalogue, and retention stance.
        return audit.schema()

    return app


app = create_app()
