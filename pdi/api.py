"""Private Data Infrastructure HTTP API.

Admin endpoints manage deployments and tenants. Data endpoints require a tenant
bearer token (``Authorization: Bearer pdi_...``) and operate only within that
tenant's namespace — one integrating system cannot read another's records.
"""

from __future__ import annotations

import io
import json
import os
import secrets

from fastapi import Depends, FastAPI, Header, HTTPException, Response

from . import (app_connectors, audit, catalog, compliance, connectors, crypto,
               db, i18n, intakes, positions, retention, robotics, transfers,
               vault)
from .models import (AppCollect, AppConnect, AppInvoke, ConnectorCreate,
                     ConnectorIngest, ConnectorPublish, ContributionIn,
                     DeploymentCreate, IntakeCreate, IntakeSubmit,
                     LanguageChoice, PositionIntake, TranslateRequest,
                     RecordPut, RetentionSet, RobotBind, RobotIngest,
                     SnapshotRestore, TenantCreate, TokenIssue, TransferCreate)


def _public_base() -> str:
    return os.environ.get("PDI_PUBLIC_URL", "https://pdi.app").rstrip("/")


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

    @app.middleware("http")
    async def localize_response_notes(request, call_next):
        """When the calling tenant has set a language, swap PDI's fixed
        explanatory note strings for their hand translations anywhere they
        appear in a JSON response. Only exact known strings are touched —
        structured data passes through byte-identical."""
        response = await call_next(request)
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return response
        tenant = vault.tenant_by_token(auth_header[7:])
        if tenant is None:
            return response
        language = i18n.effective_language(tenant["id"])
        content_type = response.headers.get("content-type", "")
        if language == i18n.DEFAULT or not content_type.startswith(
                "application/json"):
            return response
        body = b"".join([chunk async for chunk in response.body_iterator])
        try:
            localized = json.dumps(
                i18n.localize(json.loads(body), language)).encode()
        except (ValueError, TypeError):
            localized = body
        headers = {k: v for k, v in response.headers.items()
                   if k.lower() != "content-length"}
        return Response(content=localized, status_code=response.status_code,
                        headers=headers, media_type="application/json")

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

    @app.post("/seed", status_code=201)
    def seed_starter_vault(_: None = Depends(_admin)) -> dict:
        """Seed the starter demo vault: a "starter-demo" tenant with sealed
        sample records (every provenance origin), a bound robot with sealed
        collection data, and an audit trail to explore. Idempotent; the
        tenant token is returned only by the run that creates it."""
        from . import seed
        return seed.seed()

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

    # -- language (per-tenant; known note strings localize in responses) ----

    @app.get("/languages")
    def list_languages() -> dict:
        """Supported tenant languages. PDI's fixed explanatory notes are
        hand-translated for the marked subset; other languages read English
        notes — structured data is language-neutral either way."""
        return {"languages": [{"code": code, "label": label,
                               "notes_translated": code == i18n.DEFAULT
                                   or code in i18n.HAND_TRANSLATED}
                              for code, label in i18n.SUPPORTED.items()],
                "default": i18n.DEFAULT}

    @app.get("/language")
    def get_language(tenant: dict = Depends(_tenant)) -> dict:
        code, mode = i18n.get_pref(tenant["id"])
        return {"tenant_id": tenant["id"], "language": code,
                "label": i18n.SUPPORTED[code], "mode": mode}

    @app.put("/language")
    def set_language(body: LanguageChoice,
                     tenant: dict = Depends(_tenant)) -> dict:
        """mode "pre" (default) swaps translated notes into every response;
        "on_demand" keeps English and POST /translate serves lookups."""
        if body.language not in i18n.SUPPORTED:
            raise HTTPException(
                422, f"language must be one of {', '.join(i18n.SUPPORTED)}")
        if body.mode not in i18n.MODES:
            raise HTTPException(
                422, f"mode must be one of {', '.join(i18n.MODES)}")
        i18n.set_language(tenant["id"], body.language, body.mode)
        audit.record("language.set", tenant_id=tenant["id"], ref=body.language)
        return {"tenant_id": tenant["id"], "language": body.language,
                "label": i18n.SUPPORTED[body.language], "mode": body.mode}

    @app.post("/translate")
    def translate_text(body: TranslateRequest,
                       tenant: dict = Depends(_tenant)) -> dict:
        """Dictionary-only: PDI runs no model, so it translates exactly its
        own note strings and says so for anything else."""
        try:
            return i18n.translate(tenant["id"], body.text, body.to)
        except ValueError as exc:
            raise HTTPException(422, str(exc))

    # -- data plane (tenant-scoped, encrypted at rest) ----------------------

    @app.get("/provenance/{key:path}")
    def record_provenance(key: str, tenant: dict = Depends(_tenant)) -> dict:
        """The verifiable derivation trail of a sealed record: where it came
        from, how it is sealed, and its tamper-evident audit history — proof,
        not trust."""
        row = db.connect().execute(
            "SELECT * FROM records WHERE tenant_id=? AND key=?",
            (tenant["id"], key)).fetchone()
        if row is None:
            raise HTTPException(404, "record not found")
        if key.startswith("jim/"):
            origin = "JIM Guardian (sealed via the JIM tandem client)"
        elif key.startswith("qrme/"):
            origin = "QRME (sealed via the QRME tandem client)"
        else:
            origin = "direct API write by this tenant"
        trail = [{"action": e["action"], "at": e["at"],
                  "category": e["category"]}
                 for e in audit.entries(tenant["id"]) if e["ref"] == key]
        chain = audit.verify()
        audit.record("provenance.view", tenant_id=tenant["id"], ref=key)
        return {
            "key": key,
            "origin": origin,
            "sealed": {
                "cipher": "AES-256-GCM (envelope encryption: per-deployment "
                          "DEK, stored only wrapped)",
                "bound_to": "this tenant + key via AAD — the ciphertext "
                            "cannot be moved or re-attributed",
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "ciphertext_bytes": len(row["ciphertext"]),
            },
            "audit": {"events": trail, "count": len(trail)},
            "chain": chain,
            "note": "the audit chain is hash-linked; 'intact' means no entry "
                    "has been altered or removed since it was written",
        }

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

    # -- social connectors (tenant-scoped) ----------------------------------
    # collect seals the account's content as vault records; publish shares an
    # update on the platform, reachable by a QR beacon.

    def _connector_or_404(cid: str, tenant: dict) -> dict:
        row = connectors.get(cid)
        if row is None or row["tenant_id"] != tenant["id"]:
            raise HTTPException(404, "connector not found")
        return row

    @app.post("/connectors", status_code=201)
    def create_connector(body: ConnectorCreate,
                         tenant: dict = Depends(_writer)) -> dict:
        return connectors.create(tenant["id"], body.platform, body.direction,
                                body.handle, body.scope)

    @app.get("/connectors")
    def list_connectors(tenant: dict = Depends(_tenant)) -> list[dict]:
        return connectors.for_tenant(tenant["id"])

    @app.get("/connectors/catalog")
    def connector_catalog() -> dict:
        """The connected-apps catalog: the AI-integrated apps (Apple, Google,
        Microsoft, Canva) a tenant's agents can connect to."""
        return catalog.catalog()

    @app.delete("/connectors/{cid}")
    def revoke_connector(cid: str, tenant: dict = Depends(_writer)) -> dict:
        _connector_or_404(cid, tenant)
        return connectors.revoke(cid)

    @app.post("/connectors/{cid}/ingest", status_code=201)
    def ingest_connector(cid: str, body: ConnectorIngest,
                        tenant: dict = Depends(_writer)) -> dict:
        row = _connector_or_404(cid, tenant)
        if row["direction"] != "collect":
            raise HTTPException(409, "this connector is for publishing, not collecting")
        if row["status"] != "active":
            raise HTTPException(409, "connector has been revoked")
        return connectors.ingest(tenant, row, [i.model_dump() for i in body.items])

    @app.post("/connectors/{cid}/publish", status_code=201)
    def publish_connector(cid: str, body: ConnectorPublish,
                         tenant: dict = Depends(_writer)) -> dict:
        row = _connector_or_404(cid, tenant)
        if row["direction"] != "publish":
            raise HTTPException(409, "this connector is for collecting, not publishing")
        if row["status"] != "active":
            raise HTTPException(409, "connector has been revoked")
        return connectors.publish(row, body.content, body.topic)

    @app.get("/connectors/{cid}/beacon")
    def connector_beacon(cid: str, tenant: dict = Depends(_tenant)) -> dict:
        row = _connector_or_404(cid, tenant)
        if row["direction"] != "publish":
            raise HTTPException(409, "beacons are for publish connectors")
        return {"connector": cid, "platform": row["platform"],
                "handle": f"@{row['handle']}" if row["handle"] else None,
                "presence_url": connectors.presence_url(row, _public_base()),
                "qr_svg": f"/connectors/{cid}/qr.svg"}

    @app.get("/connectors/{cid}/qr.svg")
    def connector_qr(cid: str, tenant: dict = Depends(_tenant)) -> Response:
        row = _connector_or_404(cid, tenant)
        if row["direction"] != "publish":
            raise HTTPException(409, "beacons are for publish connectors")
        import segno

        buf = io.BytesIO()
        segno.make(connectors.presence_url(row, _public_base()), error="q").save(
            buf, kind="svg", scale=8, border=2, dark="#181240", light="#ffffff")
        return Response(content=buf.getvalue(), media_type="image/svg+xml")

    # -- connected-app connectors (tenant-scoped) ---------------------------
    # connect a catalog app; agents collect (sealed to the vault), act, produce.

    def _app_or_404(cid: str, tenant: dict) -> dict:
        row = app_connectors.get(cid)
        if row is None or row["tenant_id"] != tenant["id"]:
            raise HTTPException(404, "app connector not found")
        return row

    @app.post("/apps", status_code=201)
    def connect_app(body: AppConnect, tenant: dict = Depends(_writer)) -> dict:
        e = app_connectors.entry(body.provider, body.app)
        if e is None:
            raise HTTPException(404, f"unknown connector: {body.provider}/{body.app}")
        unknown = set(body.capabilities) - set(e["capabilities"])
        if unknown:
            raise HTTPException(422, f"{body.app} does not offer: {sorted(unknown)}")
        return app_connectors.create(tenant["id"], e, body.capabilities)

    @app.get("/apps")
    def list_apps(tenant: dict = Depends(_tenant)) -> list[dict]:
        return app_connectors.for_tenant(tenant["id"])

    @app.delete("/apps/{cid}")
    def revoke_app(cid: str, tenant: dict = Depends(_writer)) -> dict:
        _app_or_404(cid, tenant)
        return app_connectors.revoke(cid)

    @app.post("/apps/{cid}/ingest", status_code=201)
    def ingest_app(cid: str, body: AppCollect, tenant: dict = Depends(_writer)) -> dict:
        row = _app_or_404(cid, tenant)
        if "collect" not in json.loads(row["directions"]):
            raise HTTPException(409, f"{row['app']} does not support collecting context")
        if row["status"] != "active":
            raise HTTPException(409, "connector has been revoked")
        return app_connectors.ingest(tenant, row, [i.model_dump() for i in body.items])

    @app.post("/apps/{cid}/invoke", status_code=201)
    def invoke_app(cid: str, body: AppInvoke, tenant: dict = Depends(_writer)) -> dict:
        row = _app_or_404(cid, tenant)
        if row["status"] != "active":
            raise HTTPException(409, "connector has been revoked")
        if body.capability not in json.loads(row["capabilities"]):
            raise HTTPException(422, f"this {row['app']} connector was not granted "
                                     f"'{body.capability}'")
        return app_connectors.invoke(row, body.capability, body.input)

    # -- robots as vault-backed data sources --------------------------------
    # A home's robots (humanoids, home robots, vacuums) collect maps, camera
    # snapshots, and sensor logs; PDI seals each item into the tenant's vault
    # and hash-chains the intake so custody of what a robot saw is provable.

    def _robot_or_404(rid: str, tenant: dict) -> dict:
        row = robotics.by_id(rid, tenant["id"])
        if row is None:
            raise HTTPException(404, "robot not found")
        return row

    @app.get("/robotics/catalog")
    def robotics_catalog() -> dict:
        """Every supported robot platform, and the data kinds PDI accepts from
        one. Public — it is a static registry."""
        return robotics.robot_catalog()

    @app.post("/robots", status_code=201)
    def bind_robot(body: RobotBind, tenant: dict = Depends(_writer)) -> dict:
        spec = robotics.get(body.model)
        if spec is None:
            raise HTTPException(404, f"unknown robot model '{body.model}'")
        return robotics.create(tenant["id"], spec, body.name)

    @app.get("/robots")
    def list_robots(tenant: dict = Depends(_tenant)) -> list[dict]:
        return robotics.for_tenant(tenant["id"])

    @app.post("/robots/{rid}/ingest", status_code=201)
    def robot_ingest(rid: str, body: RobotIngest,
                     tenant: dict = Depends(_writer)) -> dict:
        row = _robot_or_404(rid, tenant)
        if row["status"] != "active":
            raise HTTPException(409, "robot has been unbound")
        if body.kind not in robotics.DATA_KINDS:
            raise HTTPException(
                422, f"kind must be one of {', '.join(robotics.DATA_KINDS)}")
        return robotics.ingest(tenant, row, body.kind, body.content, body.ref)

    @app.get("/robots/{rid}/data")
    def robot_data(rid: str, tenant: dict = Depends(_tenant)) -> dict:
        """The vault keys this robot has deposited. Values stay sealed — read
        one through GET /records/{key}, which is itself audited."""
        row = _robot_or_404(rid, tenant)
        return {"robot": rid, "keys": robotics.data_keys(tenant, row)}

    @app.delete("/robots/{rid}")
    def unbind_robot(rid: str, tenant: dict = Depends(_writer)) -> dict:
        _robot_or_404(rid, tenant)
        return robotics.unbind(tenant["id"], rid)

    # -- compliance-grade secure file transfers -----------------------------
    # A corporation seals a file for a recipient under HIPAA / OSHA / CPNI / …;
    # the recipient retrieves it with a one-shot receive token, every access
    # audited, retention enforced by the strictest program.

    @app.get("/compliance/programs")
    def compliance_programs() -> dict:
        """The compliance regimes PDI transfers can carry, and the controls PDI
        satisfies natively."""
        return compliance.catalog()

    def _transfer_or_404(tid: str, tenant: dict) -> dict:
        row = transfers.get(tid)
        if row is None or row["tenant_id"] != tenant["id"]:
            raise HTTPException(404, "transfer not found")
        return row

    @app.post("/transfers", status_code=201)
    def create_transfer(body: TransferCreate, tenant: dict = Depends(_writer)) -> dict:
        try:
            return transfers.create(tenant, body.recipient, body.filename,
                                    body.content, body.programs, body.classification,
                                    body.party_type)
        except transfers.UnknownProgram as exc:
            raise HTTPException(422, str(exc))

    @app.get("/transfers")
    def list_transfers(tenant: dict = Depends(_tenant)) -> list[dict]:
        return transfers.for_tenant(tenant["id"])

    @app.get("/transfers/{tid}")
    def get_transfer(tid: str, tenant: dict = Depends(_tenant)) -> dict:
        return transfers._out(_transfer_or_404(tid, tenant))

    @app.get("/transfers/{tid}/custody")
    def transfer_custody(tid: str, tenant: dict = Depends(_tenant)) -> dict:
        return transfers.custody(_transfer_or_404(tid, tenant))

    @app.delete("/transfers/{tid}")
    def revoke_transfer(tid: str, tenant: dict = Depends(_writer)) -> dict:
        return transfers.revoke(_transfer_or_404(tid, tenant))

    @app.post("/transfers/{tid}/receive")
    def receive_transfer(tid: str, x_receive_token: str = Header(default="")) -> dict:
        """The recipient retrieves the file with their receive token — no tenant
        credential; the token itself is the (auditable) authorization."""
        row = transfers.get(tid)
        if row is None:
            raise HTTPException(404, "transfer not found")
        result = transfers.receive(row, x_receive_token)
        if result is None:
            raise HTTPException(403, "invalid receive token")
        if result == "revoked":
            raise HTTPException(410, "this transfer has been revoked")
        return result

    # -- inbound intake: a subscriber or partner sends a file IN ------------

    def _intake_or_404(iid: str, tenant: dict) -> dict:
        row = intakes.get(iid)
        if row is None or row["tenant_id"] != tenant["id"]:
            raise HTTPException(404, "intake not found")
        return row

    @app.post("/intakes", status_code=201)
    def create_intake(body: IntakeCreate, tenant: dict = Depends(_writer)) -> dict:
        try:
            return intakes.create(tenant, body.from_party, body.party_type,
                                 body.purpose, body.programs)
        except intakes.UnknownProgram as exc:
            raise HTTPException(422, str(exc))

    @app.get("/intakes")
    def list_intakes(tenant: dict = Depends(_tenant)) -> list[dict]:
        return intakes.for_tenant(tenant["id"])

    @app.get("/intakes/{iid}")
    def get_intake(iid: str, tenant: dict = Depends(_tenant)) -> dict:
        return intakes._out(_intake_or_404(iid, tenant))

    @app.get("/intakes/{iid}/custody")
    def intake_custody(iid: str, tenant: dict = Depends(_tenant)) -> dict:
        return intakes.custody(_intake_or_404(iid, tenant))

    @app.get("/intakes/{iid}/file")
    def read_intake(iid: str, tenant: dict = Depends(_writer)) -> dict:
        row = _intake_or_404(iid, tenant)
        result = intakes.read(tenant, row)
        if result is None:
            raise HTTPException(409, "nothing has been submitted to this intake yet")
        return result

    @app.delete("/intakes/{iid}")
    def close_intake(iid: str, tenant: dict = Depends(_writer)) -> dict:
        return intakes.close(_intake_or_404(iid, tenant))

    @app.post("/intakes/{iid}/submit", status_code=201)
    def submit_intake(iid: str, body: IntakeSubmit,
                      x_submit_token: str = Header(default="")) -> dict:
        """The subscriber / partner sends their file in with the submit token —
        no tenant credential; the token is the (auditable) authorization."""
        row = intakes.get(iid)
        if row is None:
            raise HTTPException(404, "intake not found")
        result = intakes.submit(row, x_submit_token, body.filename, body.content,
                               body.classification)
        if result is None:
            raise HTTPException(403, "invalid submit token")
        if result == "closed":
            raise HTTPException(409, "this intake is no longer open")
        return result

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
