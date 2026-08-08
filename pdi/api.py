"""Private Data Infrastructure HTTP API.

Admin endpoints manage deployments and tenants. Data endpoints require a tenant
bearer token (``Authorization: Bearer pdi_...``) and operate only within that
tenant's namespace — one integrating system cannot read another's records.
"""

from __future__ import annotations

import io
import json
import logging
import os
import secrets

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse

from . import (app_connectors, assistant, audit, baa, beacons, bequests,
               catalog,
               compliance, connectors, crypto, db, dock as dock_mod, gate,
               hosting, i18n,
               intakes,
               landing, mobile, notify, offline, positions, retention,
               robotics, roster,
               terms as terms_mod, transfers, tutorial, vault)
from .models import (AppCollect, AppConnect, AppInvoke, BAARecordIn,
                     BeaconFound, BeaconPlace, BeaconState,
                     BequestActivate, BequestCreate,
                     ConnectorCreate, ConnectorIngest, ConnectorPublish,
                     ConsoleAsk, ContributionIn, CustomerKeyAdopt, GuideMark,
                     DockConfig, HostingChoice,
                     DeploymentCreate, FeedbackSubmit, GateRing, IntakeCreate,
                     IntakeSubmit, LanguageChoice, PositionIntake,
                     TranslateRequest, RecordPut, RetentionSet, RobotBind,
                     RobotIngest, RosterAdd, SnapshotRestore, TenantCreate,
                     TokenIssue, TransferCreate, GateTimezone)


#: The unhandled-error path logs here and nowhere else: the traceback
#: stays on this machine, and what leaves is a status and a sentence.
_log = logging.getLogger(__name__)

def _public_base() -> str:
    return os.environ.get("PDI_PUBLIC_URL", "https://pdi.app").rstrip("/")


def _tenant(authorization: str = Header(default=""),
            x_tenant_key: str = Header(default="")) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "missing tenant bearer token")
    tenant = vault.tenant_by_token(authorization[len("Bearer "):])
    if tenant is None:
        raise HTTPException(401, "invalid tenant token")
    # BYOK: a customer-managed key travels per request and is never stored.
    # Carried on the tenant dict so it reaches the seal/open calls without
    # every layer in between having to know about it.
    tenant = dict(tenant)
    try:
        tenant["customer_key"] = crypto.parse_key(x_tenant_key)
    except crypto.CustomerKeyMismatch as exc:
        raise HTTPException(400, str(exc)) from exc
    return tenant


# Addresses that can only be a caller on this machine. "testclient" is
# Starlette's in-process sentinel — it names no socket, so no network peer
# can ever present it.
_LOCAL_CALLERS = {"127.0.0.1", "::1", "localhost", "testclient"}


def _admin(request: Request, authorization: str = Header(default="")) -> None:
    """Admin endpoints (deployments, tenants, token issuance, deletion,
    snapshot restore) are guarded by PDI_ADMIN_TOKEN.

    Unset is development mode — open, but **only to callers on this
    machine**. A deployment reachable from anywhere else fails closed
    instead: an open admin surface on a routable address would let any
    caller who finds it create tenants, mint tokens, wipe a vault, or
    restore a snapshot over it. Refusing is the safe failure; the operator
    sets a token and restarts.
    """
    required = os.environ.get("PDI_ADMIN_TOKEN")
    if not required:
        caller = request.client.host if request.client else ""
        if caller in _LOCAL_CALLERS:
            return
        raise HTTPException(
            503, "this deployment is reachable beyond localhost but has no "
                 "PDI_ADMIN_TOKEN set — admin endpoints stay closed until "
                 "one is configured (see docs/operations.md)")
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "admin bearer token required")
    # Constant-time compare so a wrong token can't be recovered by timing.
    if not secrets.compare_digest(authorization[len("Bearer "):], required):
        raise HTTPException(403, "invalid admin token")


def _writer(tenant: dict = Depends(_tenant)) -> dict:
    if tenant.get("role") != "write":
        raise HTTPException(403, "this token is read-only")
    return tenant



#: What a recipient is told when their token opens nothing.
#:
#: One sentence for two situations — no such transfer, and a real one with the
#: wrong token — because telling them apart is what made this public route an
#: oracle for transfer ids. It is true either way and reveals neither.
RECEIVE_NO = "that token does not open anything here"

#: Reachable only with the correct token, so it discloses nothing to anybody
#: who is not the intended recipient — and it is the one thing that recipient
#: most needs said plainly rather than left to guess at.
RECEIVE_REVOKED = "this transfer has been revoked"

def create_app() -> FastAPI:
    app = FastAPI(title="Private Data Infrastructure", version="0.59.2")

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

    @app.get("/terms")
    def get_terms() -> dict:
        """Current Terms of Service — version, key points, and the full
        document's path. Public: an integrating system can always show
        the terms in force. Each tenant records the version in force at
        provisioning (its receipt)."""
        return {
            "version": terms_mod.TERMS_VERSION,
            "key_points": terms_mod.KEY_POINTS,
            "document": terms_mod.DOCUMENT,
        }

    # BYOK failures are a normal, expected answer — "you have to bring the
    # key" and "that is the wrong key" — not server errors. Handled centrally
    # so every path that touches a sealed record reports them the same way,
    # rather than each route remembering to.

    # Every refusal in this vault, in the language of whoever is reading it.
    #
    # `i18n.refuse` is the one place a refusal becomes a response. Before it
    # there were three handlers building responses three different ways — two
    # hand-rolled `Response`s with `json.dumps`, one `JSONResponse` — which is
    # how a fourth would have arrived with a fourth shape and no translation.
    # `pdi/i18n.py` carries the argument about whose language it is.
    #
    # test_the_vault_refuses_in_one_language.py fails the next handler added
    # that does not return through here.
    @app.exception_handler(HTTPException)
    async def _refusal_in_the_readers_language(request: Request,
                                               exc: HTTPException):
        return i18n.refuse(request, exc.status_code,
                           {"detail": exc.detail}, exc.headers)

    # The refusal FastAPI renders itself, which is the one a person meets most
    # often: a mistyped form is a 422. `RequestValidationError` is neither an
    # `HTTPException` nor a domain error, so it went out past all three
    # handlers here — in English, and carrying pydantic's `input` key, which
    # on a missing field is the entire submitted body handed straight back. In
    # a vault that means a record value in plaintext, on the one path that
    # never touches the encryption layer. See `pdi/i18n.py`.
    #
    # Routed through `i18n.refuse` like everything else, so the structural
    # guard covers it. The rows are already translated by `validation_detail`;
    # `localize_detail` leaves a list alone, so nothing is done twice.
    @app.exception_handler(RequestValidationError)
    async def _rejected_input_stays_with_its_sender(
            request: Request, invalid: RequestValidationError):
        # `message` rides alongside because `detail` is a list, and a list is
        # not something any of this product's clients could show a person: the
        # console printed it as JSON, Android did the same by coercion, and
        # iOS and Windows asked for a string, got an array, and fell back to
        # "HTTP 422".
        #
        #     asked     is the refusal translated
        #     mattered  is the refusal a sentence
        #
        # `detail` keeps its shape — it is the FastAPI contract and what the
        # driven tests read. The sentence carries nothing the rows do not.
        language = i18n.refusal_language(request)
        rows = i18n.validation_detail(invalid.errors(), language)
        return i18n.refuse(request, 422, {
            "detail": rows, "message": i18n.validation_message(rows, language)})

    @app.exception_handler(crypto.CustomerKeyRequired)
    async def _key_required(request: Request, exc: crypto.CustomerKeyRequired):
        # 428 Precondition Required: the request is fine, it is missing a
        # precondition the caller can supply and retry with.
        return i18n.refuse(request, 428, {"detail": str(exc)})

    @app.exception_handler(crypto.CustomerKeyMismatch)
    async def _key_mismatch(request: Request, exc: crypto.CustomerKeyMismatch):
        return i18n.refuse(request, 403, {"detail": str(exc)})

    @app.get("/offline/status")
    def offline_status() -> dict:
        """What this deployment can and cannot reach.

        A vault whose whole promise is that data stays where it is put should
        be able to say so out loud. The flag exists now; this is where an
        operator, or an auditor standing behind them, reads the answer.

        Open, like `/health`: the posture has to be confirmable before there
        is a tenant token to confirm it with, and the answer names no tenant,
        no record and no key.
        """
        return offline.status()

    @app.get("/health")
    def health() -> dict:
        # The version is here so a desktop shell can tell whether the
        # backend answering the port is its own — the sibling products
        # learned this the hard way (a stale backend from an older install
        # answers /health perfectly well and then serves an older API).
        return {"status": "ok", "version": app.version,
                "console": mobile.console_dir() is not None}

    # -- run it from your phone ---------------------------------------------

    @app.get("/pair")
    def pair(request: Request) -> dict:
        """How to open the operator console on a phone: the console's URL on
        this local network, ready to type or scan. Same Wi-Fi, no app
        store."""
        return mobile.pairing(port=request.url.port or 8000)

    @app.get("/pair/qr.svg")
    def pair_qr(request: Request) -> Response:
        """The console URL as a QR code — point the phone's camera at it."""
        import segno
        buf = io.BytesIO()
        url = mobile.pairing(port=request.url.port or 8000)["console_url"]
        segno.make(url, error="q").save(
            buf, kind="svg", scale=8, border=2,
            dark="#0c0920", light="#ffffff")
        return Response(content=buf.getvalue(), media_type="image/svg+xml")

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
                422, i18n.fill(i18n.MUST_BE_ONE_OF, field="language",
                              choices=", ".join(i18n.SUPPORTED)))
        if body.mode not in i18n.MODES:
            raise HTTPException(
                422, i18n.fill(i18n.MUST_BE_ONE_OF, field="mode",
                              choices=", ".join(i18n.MODES)))
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

    @app.get("/operations")
    def operations_journal(tenant: dict = Depends(_tenant)) -> dict:
        """The operations journal: coordination records QRME sealed into
        this tenant's vault (``qrme/coordination/*``), decrypted with the
        tenant's own token and read through the ordinary audited path. The
        journal is a view, not a side door — every entry read here lands
        on the audit chain like any other read."""
        entries = []
        for key in vault.list_keys(tenant):
            if not key.startswith("qrme/coordination/"):
                continue
            rec = vault.get(tenant, key)
            try:
                body = json.loads(rec["value"])
            except (ValueError, TypeError):
                body = {}
            entries.append({
                "key": key, "updated_at": rec["updated_at"],
                "org": body.get("org"), "goal": body.get("goal"),
                "plan": body.get("plan"),
                "departments": [c.get("department")
                                for c in body.get("contributions", [])],
            })
        return {"entries": entries,
                "note": "coordination output QRME sealed here; every read "
                        "of this journal is on the audit chain"}

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
                422, i18n.fill(i18n.MUST_BE_ONE_OF, field="kind",
                              choices=", ".join(robotics.DATA_KINDS)))
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
        # No production PHI before the BAA: HIPAA-program transfers require
        # an executed Business Associate Agreement on file for this tenant.
        if (refusal := baa.blocks(tenant["id"], body.programs)):
            raise HTTPException(403, refusal)
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

    # -- bequests (pdi/bequests.py) -----------------------------------------
    # Vault access that begins only when a condition is attested: the grant
    # token does not exist until activation, and it only ever reads.

    @app.exception_handler(bequests.BequestError)
    def _bequest_refusal(request: Request, exc: bequests.BequestError):
        return i18n.refuse(request, exc.status, {"detail": exc.message})

    @app.post("/bequests", status_code=201)
    def create_bequest(body: BequestCreate,
                       tenant: dict = Depends(_writer)) -> dict:
        return bequests.create(tenant, body.grantee_name, body.key_prefixes,
                               condition=body.condition, note=body.note)

    @app.get("/bequests")
    def list_bequests(tenant: dict = Depends(_tenant)) -> list[dict]:
        return bequests.for_tenant(tenant)

    @app.delete("/bequests/{bid}")
    def revoke_bequest(bid: str, tenant: dict = Depends(_writer)) -> dict:
        return bequests.revoke(tenant, bid)

    @app.post("/bequests/{bid}/activate",
              dependencies=[Depends(_admin)])
    def activate_bequest(bid: str, body: BequestActivate) -> dict:
        """The executor's act: attests the condition (the ref is recorded in
        the audit chain) and mints the grant token — shown once."""
        return bequests.activate(bid, body.activation_ref)

    @app.delete("/bequests/{bid}/grant", dependencies=[Depends(_admin)])
    def admin_revoke_bequest(bid: str) -> dict:
        return bequests.admin_revoke(bid)

    @app.get("/bequests/grant/keys")
    def bequest_keys(x_grant_token: str = Header(default=""),
                     x_tenant_key: str = Header(default="")) -> dict:
        """What the grantee may see. No tenant credential — the grant token
        is the (auditable) authorization, like a transfer receive token."""
        return bequests.grant_keys(
            x_grant_token, customer_key=crypto.parse_key(x_tenant_key))

    @app.get("/bequests/grant/read")
    def bequest_read(key: str, x_grant_token: str = Header(default=""),
                     x_tenant_key: str = Header(default="")) -> dict:
        return bequests.grant_read(
            x_grant_token, key, customer_key=crypto.parse_key(x_tenant_key))

    @app.post("/transfers/{tid}/receive")
    def receive_transfer(
        tid: str,
        x_receive_token: str = Header(default=""),
        accept_language: str = Header(default=""),
    ) -> dict:
        """The recipient retrieves the file with their receive token — no tenant
        credential; the token itself is the (auditable) authorization.

        **An unknown id and a wrong token answer identically.** They did not
        until this round: a missing transfer was a 404 and a real one with a
        bad token was a 403, so anybody — with no credential of any kind, this
        route takes none — could walk ids and learn which sealed transfers
        exist. For compliance-grade material that is a disclosure on its own,
        before anything is opened.

        `/r/{tid}` was written carefully not to be that oracle, and there is a
        test named for it. The test reads the *page*. The page is not where an
        id gets probed; this is, because this is the one anybody can call
        directly with a shell.

        Revoked stays distinguishable, because reaching it requires the real
        token: `transfers.receive` matches the hash before it looks at status,
        so only the intended recipient learns access was cut — which is the
        one thing they most need to be told rather than left guessing about.

        The reader here is not a tenant, so the response middleware — which
        keys on the calling tenant's language — will never translate anything
        for them. The details are therefore translated on the way out, from
        the same header the page they are standing on was rendered from.
        """
        language = i18n.negotiate(accept_language)
        row = transfers.get(tid)
        result = None if row is None else transfers.receive(row,
                                                            x_receive_token)
        if result is None:
            raise HTTPException(
                403, i18n.tr_page(RECEIVE_NO, language))
        if result == "revoked":
            raise HTTPException(
                410, i18n.tr_page(RECEIVE_REVOKED, language))
        result["custody"] = i18n.tr_page(result["custody"], language)
        return result

    # -- inbound intake: a subscriber or partner sends a file IN ------------

    def _intake_or_404(iid: str, tenant: dict) -> dict:
        row = intakes.get(iid)
        if row is None or row["tenant_id"] != tenant["id"]:
            raise HTTPException(404, "intake not found")
        return row

    @app.post("/intakes", status_code=201)
    def create_intake(body: IntakeCreate, tenant: dict = Depends(_writer)) -> dict:
        if (refusal := baa.blocks(tenant["id"], body.programs)):
            raise HTTPException(403, refusal)
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

    # -- BYOK: customer-managed keys ----------------------------------------
    # The tenant's own decision, so these are authenticated by the tenant's
    # write token, not the operator's admin token. An operator who could put a
    # tenant under a key of the operator's choosing would defeat the point.

    @app.get("/key")
    def key_custody(tenant: dict = Depends(_tenant)) -> dict:
        """Who holds the key for this tenant's records, and what that
        guarantees. Deliberately explicit about the limits."""
        return crypto.custody(tenant["id"])

    @app.put("/key", status_code=201)
    def adopt_key(body: CustomerKeyAdopt,
                  tenant: dict = Depends(_writer)) -> dict:
        """Bring your own key. Every existing record is re-sealed under it in
        one transaction — a half-migrated tenant would be the worst state to
        be in, with no way to tell from outside which records the operator can
        still read."""
        try:
            key = crypto.parse_key(body.key)
            return crypto.adopt_customer_key(
                tenant["id"], body.provider, key, body.config)
        except crypto.CustomerKeyMismatch as exc:
            raise HTTPException(400, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.delete("/key")
    def release_key(tenant: dict = Depends(_writer)) -> dict:
        """Hand custody back to the deployment. Requires the customer key in
        ``x-tenant-key``: the records must be opened to be re-sealed, which is
        the guarantee working, not an obstacle."""
        try:
            return crypto.release_customer_key(
                tenant["id"], tenant.get("customer_key"))
        except crypto.CustomerKeyRequired as exc:
            raise HTTPException(428, str(exc)) from exc
        except crypto.CustomerKeyMismatch as exc:
            raise HTTPException(403, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc

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

    # -- custody beacons: a printed code on a physical thing ----------------
    # The seal card says a carrier is under custody and what governs it, and
    # never what is in it. See docs/beacons.md.

    def _beacon_or_404(bid: str, tenant: dict) -> dict:
        row = beacons.get(bid)
        if row is None or row["tenant_id"] != tenant["id"]:
            raise HTTPException(404, "beacon not found")
        return row

    @app.post("/beacons", status_code=201)
    def place_beacon(body: BeaconPlace, tenant: dict = Depends(_writer)) -> dict:
        try:
            return beacons.place(tenant, body.ref_kind, body.ref_id,
                                 body.label, body.disclose, body.programs)
        except beacons.BeaconError as exc:
            raise HTTPException(
                404 if str(exc).startswith("no such") else 422, str(exc))

    @app.get("/beacons")
    def list_beacons(tenant: dict = Depends(_tenant)) -> list[dict]:
        return beacons.for_tenant(tenant["id"])

    @app.get("/beacons/{bid}")
    def get_beacon(bid: str, tenant: dict = Depends(_tenant)) -> dict:
        return beacons._out(_beacon_or_404(bid, tenant))

    @app.get("/beacons/{bid}/custody")
    def beacon_custody(bid: str, tenant: dict = Depends(_tenant)) -> dict:
        return beacons.custody(_beacon_or_404(bid, tenant))

    @app.put("/beacons/{bid}/state")
    def set_beacon_state(bid: str, body: BeaconState,
                         tenant: dict = Depends(_writer)) -> dict:
        try:
            return beacons.set_state(_beacon_or_404(bid, tenant), body.state)
        except beacons.BeaconError as exc:
            raise HTTPException(422, str(exc))

    @app.delete("/beacons/{bid}")
    def retire_beacon(bid: str, tenant: dict = Depends(_writer)) -> dict:
        return beacons.retire(_beacon_or_404(bid, tenant))

    # The public surface. No token — a stranger holding a phone at a sticker is
    # exactly the caller this exists for.

    @app.get("/s/{bid}", response_class=HTMLResponse)
    def seal_card_page(
        bid: str,
        accept_language: str = Header(default=""),
    ) -> HTMLResponse:
        """What a phone's camera app opens when somebody scans the sticker.

        HTML, because a QR is pointed at by a human holding a phone — this
        used to answer JSON and show a courier a wall of braces. The JSON is
        still served at ``/s/{id}/card`` for anything reading it
        programmatically.

        The language comes from the header rather than from a tenant: the
        person scanning is a courier or a clerk who has never had an account
        here, so there is no stored preference to look up and their browser
        has been saying which language they read all along.
        """
        language = i18n.negotiate(accept_language)
        card = beacons.seal_card(bid)
        if card is None:
            return HTMLResponse(landing.gone(language), status_code=404)
        return HTMLResponse(landing.page_for(card, language))

    @app.get("/r/{tid}", response_class=HTMLResponse)
    def receive_page(
        tid: str,
        accept_language: str = Header(default=""),
    ) -> HTMLResponse:
        """Where the recipient of a sealed transfer collects it.

        `receive_transfer` states its caller: "no tenant credential; the token
        itself is the (auditable) authorization." That caller had nowhere to
        go. The only thing in the product calling that route was the console's
        "Receive it as the recipient" button — the *sender* rehearsing, and
        disabled unless their own session still held the receipt.

        The link carries the token in its **fragment** (`/r/{id}#<token>`),
        which browsers never send to a server. A query string would put a
        one-shot authorization for compliance-grade material into every access
        log and Referer header between here and the recipient.

        The page renders for any id. Whether the transfer exists is the
        token's business to answer, not the URL's — a 404 here would turn this
        route into a way of asking whether a given transfer id is real.
        """
        return HTMLResponse(
            landing.receive_page(tid, i18n.negotiate(accept_language)))

    @app.get("/s/{bid}/card")
    def seal_card(bid: str) -> dict:
        """The same scan, as JSON — for an app rather than a phone browser.
        Never the contents, on either surface."""
        card = beacons.seal_card(bid)
        if card is None:
            raise HTTPException(404, "this code does not resolve to anything")
        return card

    @app.get("/s/{bid}/qr.svg")
    def beacon_qr(bid: str) -> Response:
        """The printable code. Public: the sticker has to be made before
        anybody scans it, and the card behind it discloses nothing anyway."""
        row = beacons.get(bid)
        if row is None or not row["active"]:
            raise HTTPException(404, "this code does not resolve to anything")
        import segno

        buf = io.BytesIO()
        segno.make(f"{_public_base()}/s/{bid}", error="q").save(
            buf, kind="svg", scale=8, border=2, dark="#181240", light="#ffffff")
        return Response(content=buf.getvalue(), media_type="image/svg+xml")

    @app.post("/s/{bid}/found", status_code=201)
    def report_found(bid: str, body: BeaconFound,
                     accept_language: str = Header(default="")) -> dict:
        """A finder's custody receipt — the one thing a stranger can do with a
        carrier, and it is an instrument rather than a message.

        **In the finder's language.** A comment two rounds ago said the reply
        here "comes back through the response middleware, which is the
        tenant's language rather than the reader's", and used that to justify
        preferring it over the page's own strings. That was wrong in a way
        worth writing down: the middleware keys on the *calling* tenant, and
        this call has none. So `note` was never localized into anything, by
        anyone, in any deployment — not the tenant's language and not the
        reader's. It was English permanently, and the comment made that read
        like a considered trade-off.
        """
        language = i18n.negotiate(accept_language)
        try:
            out = beacons.found(bid, body.where, body.contact)
        except beacons.BeaconError as exc:
            raise HTTPException(409, i18n.tr_page(str(exc), language))
        if out is None:
            raise HTTPException(404, i18n.tr_page(
                "this code does not resolve to anything", language))
        if isinstance(out.get("note"), str):
            out["note"] = i18n.tr_page(out["note"], language)
        return out

    @app.post("/s/{bid}/ring", status_code=201)
    def ring_gate(bid: str, body: GateRing,
                  accept_language: str = Header(default="")) -> dict:
        """Ring a facility gate. The agent answers within its ceiling and hands
        off everything else — it can never grant entry, whatever it says.

        `unreached_note` is the reason this route is in this round. When
        nobody answered the page, it is the sentence telling somebody standing
        at a door not to wait for anyone to come out and to call the number on
        the door instead. It was English for every caller in every country,
        and it is the one sentence here whose being understood decides whether
        a person stands outside in the dark.

        The agent's own `words` are left alone: they are what the facility
        chose to say, generated in the voice its operator configured, and
        putting them through a lookup table would either miss entirely or
        replace a facility's answer with ours.
        """
        language = i18n.negotiate(accept_language)
        row = beacons.get(bid)
        if row is None or not row["active"]:
            raise HTTPException(404, i18n.tr_page(
                "this code does not resolve to anything", language))
        try:
            opened = beacons.ring(row, body.kind, body.note)
        except beacons.BeaconError as exc:
            raise HTTPException(409, i18n.tr_page(str(exc), language))
        tenant = vault.tenant_by_id(row["tenant_id"])
        if tenant is None:                       # tenant deleted under a live code
            raise HTTPException(404, i18n.tr_page(
                "this code does not resolve to anything", language))
        answered = gate.answer(beacons.ring_row(opened["id"]), tenant)
        reply = {**opened, **answered}
        if isinstance(reply.get("unreached_note"), str):
            reply["unreached_note"] = i18n.tr_page(
                reply["unreached_note"], language)
        return reply

    @app.get("/gate/ceiling")
    def gate_ceiling() -> dict:
        """What the agent may and may not do, and where the boundary comes
        from — published so a tenant can read the limits without the source."""
        return gate.ceiling()

    @app.get("/gate/roster")
    def get_roster(tenant: dict = Depends(_tenant)) -> dict:
        """This facility's roster, and **who it would reach right now** — so
        "who answers the gate at 3am?" has an answer in the afternoon."""
        return roster.describe(tenant["id"])

    @app.post("/gate/roster", status_code=201)
    def add_to_roster(body: RosterAdd,
                      tenant: dict = Depends(_writer)) -> dict:
        """Add somebody to the rota. Validated here, on the way in, so a
        malformed shift is a 422 an operator reads in daylight rather than a
        surprise at the door."""
        try:
            return roster.add(tenant, body.name, body.role, body.days,
                              body.from_time, body.to_time)
        except roster.RosterError as exc:
            raise HTTPException(422, str(exc))

    @app.delete("/gate/roster/{rid}")
    def remove_from_roster(rid: str, tenant: dict = Depends(_writer)) -> dict:
        if not roster.remove(tenant, rid):
            raise HTTPException(404, "roster entry not found")
        return {"id": rid, "removed": True}

    @app.put("/gate/timezone")
    def set_gate_timezone(body: GateTimezone,
                          tenant: dict = Depends(_writer)) -> dict:
        """The facility's own timezone. A rota written in local time and read
        in UTC is wrong by the offset — and by a *different* offset in summer,
        so it looks right for half the year."""
        try:
            return roster.set_timezone(tenant, body.timezone)
        except roster.RosterError as exc:
            raise HTTPException(422, str(exc))

    @app.get("/gate/channel")
    def gate_channel() -> dict:
        """Whether a hand-off can actually reach anybody. Public, and free of
        the URL itself: an operator should be able to confirm the gate can page
        a human *before* the night it matters, rather than learning it from a
        queued page the next morning."""
        return notify.channel()

    @app.get("/gate/pages")
    def list_pages(undelivered_only: bool = False,
                   tenant: dict = Depends(_tenant)) -> list[dict]:
        """Hand-offs, and whether each one reached anyone.
        `undelivered_only=true` is the list to read in the morning."""
        return notify.for_tenant(tenant["id"], undelivered_only)

    @app.post("/gate/pages/{pid}/retry")
    def retry_page(pid: str, tenant: dict = Depends(_writer)) -> dict:
        """Send a queued or failed page again — the channel may have been down
        for a minute, or configured five minutes after the ring."""
        row = notify.row(pid)
        if row is None or row["tenant_id"] != tenant["id"]:
            raise HTTPException(404, "page not found")
        try:
            return notify.retry(row)
        except notify.NotifyError as exc:
            raise HTTPException(409, str(exc))

    @app.get("/rings")
    def list_rings(open_only: bool = False,
                   tenant: dict = Depends(_tenant)) -> list[dict]:
        return beacons.rings_for(tenant["id"], open_only)

    @app.get("/rings/{rid}/transcript")
    def ring_transcript(rid: str, tenant: dict = Depends(_tenant)) -> dict:
        row = beacons.ring_row(rid)
        if row is None or row["tenant_id"] != tenant["id"]:
            raise HTTPException(404, "ring not found")
        out = gate.transcript(row, tenant)
        if out is None:
            raise HTTPException(404, "no transcript for this ring")
        return out

    # -- compliance ---------------------------------------------------------

    # -- BAA: executed per customer before production PHI (pdi/baa.py) -----

    def _tenant_or_404(tenant_id: str) -> dict:
        row = db.connect().execute("SELECT * FROM tenants WHERE id=?",
                                   (tenant_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "tenant not found")
        return dict(row)

    @app.post("/tenants/{tenant_id}/baa", status_code=201)
    def record_baa(tenant_id: str, body: BAARecordIn,
                   _: None = Depends(_admin)) -> dict:
        """The operator records an executed BAA for a tenant (customer).
        Metadata only — parties, signatories, effective date, and the hash of
        the signed document; the instrument itself stays with counsel. From
        this moment HIPAA-program transfers/intakes are unblocked."""
        _tenant_or_404(tenant_id)
        return baa.record(tenant_id, body.model_dump())

    @app.get("/tenants/{tenant_id}/baa")
    def get_baa(tenant_id: str, _: None = Depends(_admin)) -> dict:
        _tenant_or_404(tenant_id)
        row = baa.active(tenant_id)
        if row is None:
            raise HTTPException(404, "no executed BAA on file for this tenant")
        return row

    @app.delete("/tenants/{tenant_id}/baa")
    def terminate_baa(tenant_id: str, _: None = Depends(_admin)) -> dict:
        """Terminate the tenant's active BAA — HIPAA-program flows are
        refused again from this moment. History is kept (status=terminated)."""
        _tenant_or_404(tenant_id)
        if not baa.terminate(tenant_id):
            raise HTTPException(404, "no executed BAA on file for this tenant")
        return {"tenant_id": tenant_id, "status": "terminated"}

    @app.get("/baa")
    def my_baa(tenant: dict = Depends(_tenant)) -> dict:
        """The tenant's own BAA standing — the integrating application's
        pre-production checklist can verify it programmatically."""
        row = baa.active(tenant["id"])
        return {"executed": row is not None,
                "effective_date": row["effective_date"] if row else None,
                "note": None if row else
                    "no executed BAA on file — HIPAA-program transfers and "
                    "intakes are refused until the operator records one "
                    "(docs/baa-template.md)"}

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

    # -- "help us improve": product feedback on the app itself --------------
    # Meta feedback about PDI as a product — not tenant record data, so it
    # sits outside the per-tenant namespace and needs no token. When a tenant
    # token is presented the submitter is recorded so they can find their own
    # submissions again; otherwise it's anonymous.

    _IMPROVE_CATEGORIES = ("idea", "improvement", "bug", "praise", "other")

    def _improve_submitter(authorization: str) -> str:
        if authorization.startswith("Bearer "):
            tenant = vault.tenant_by_token(authorization[len("Bearer "):])
            if tenant is not None:
                return f"tenant:{tenant['id']}"
        return "anonymous"

    @app.post("/improve", status_code=201)
    def submit_improvement(body: FeedbackSubmit,
                           authorization: str = Header(default="")) -> dict:
        """Tell us how to make PDI better — an idea, an improvement, a bug,
        or praise, with an optional 1–5 rating. Open to anyone."""
        if body.category not in _IMPROVE_CATEGORIES:
            raise HTTPException(
                422, i18n.fill(i18n.MUST_BE_ONE_OF, field="category",
                              choices=", ".join(_IMPROVE_CATEGORIES)))
        message = body.message.strip()
        if not message:
            raise HTTPException(422, "a message is required")
        if body.rating is not None and not (1 <= body.rating <= 5):
            raise HTTPException(422, "rating must be 1–5")
        conn = db.connect()
        fid = db.new_id("fbk")
        conn.execute(
            "INSERT INTO feedback (id, submitter, category, message, rating,"
            " status, created_at) VALUES (?,?,?,?,?,'received',?)",
            (fid, _improve_submitter(authorization), body.category, message,
             body.rating, db.utcnow()))
        conn.commit()
        return {"id": fid, "category": body.category, "status": "received",
                "note": "thank you — this goes straight to the team"}

    @app.get("/improve")
    def list_improvements(authorization: str = Header(default="")) -> dict:
        """The caller's own submissions (newest first) plus the public tally
        by category — never anyone else's words."""
        conn = db.connect()
        submitter = _improve_submitter(authorization)
        mine = []
        if submitter != "anonymous":
            mine = [dict(r) for r in conn.execute(
                "SELECT id, category, message, rating, status, created_at"
                " FROM feedback WHERE submitter=?"
                " ORDER BY created_at DESC, rowid DESC", (submitter,)).fetchall()]
        tally = {c: 0 for c in _IMPROVE_CATEGORIES}
        for row in conn.execute(
                "SELECT category, COUNT(*) AS n FROM feedback"
                " GROUP BY category").fetchall():
            if row["category"] in tally:
                tally[row["category"]] = row["n"]
        return {"mine": mine, "tally": tally, "total": sum(tally.values()),
                "categories": list(_IMPROVE_CATEGORIES)}

    # -- the pane in the corner ---------------------------------------------

    @app.get("/dock/faces")
    def dock_vocabulary() -> dict:
        """Everything needed to draw the pane. Public — the console's shape,
        not anybody's data."""
        return dock_mod.vocabulary()

    @app.get("/dock/where/{face}")
    def dock_where(face: str) -> dict:
        try:
            return dock_mod.route(face)
        except dock_mod.DockError as exc:
            raise HTTPException(404, str(exc)) from None

    @app.get("/dock/{tenant_id}")
    def dock_settings(tenant_id: str, tenant: dict = Depends(_tenant)) -> dict:
        if tenant["id"] != tenant_id:
            raise HTTPException(403, "not your tenant")
        return dock_mod.settings(tenant_id)

    @app.put("/dock/{tenant_id}")
    def dock_configure(tenant_id: str, body: DockConfig,
                       tenant: dict = Depends(_tenant)) -> dict:
        if tenant["id"] != tenant_id:
            raise HTTPException(403, "not your tenant")
        try:
            return dock_mod.configure(tenant_id, body.corner, body.state,
                                      body.face, body.faces)
        except dock_mod.DockError as exc:
            raise HTTPException(422, str(exc)) from None

    @app.get("/dock/{tenant_id}/face/{name}")
    def dock_face(tenant_id: str, name: str,
                  tenant: dict = Depends(_tenant)) -> dict:
        if tenant["id"] != tenant_id:
            raise HTTPException(403, "not your tenant")
        try:
            return dock_mod.face(tenant_id, name)
        except dock_mod.DockError as exc:
            raise HTTPException(422, str(exc)) from None

    # -- where the vault lives ----------------------------------------------

    @app.get("/hosting")
    def hosting_modes() -> dict:
        """The four places a vault can live, what each costs, and who holds
        what up. Public — somebody choosing where to put sensitive data has
        to be able to read the options before they have a tenant."""
        return hosting.modes()

    @app.get("/hosting/{tenant_id}")
    def hosting_for(tenant_id: str, tenant: dict = Depends(_tenant)) -> dict:
        """This tenant's arrangement."""
        if tenant["id"] != tenant_id:
            raise HTTPException(403, "not your tenant")
        return hosting.arrangement(tenant_id)

    @app.put("/hosting/{tenant_id}")
    def choose_hosting(tenant_id: str, body: HostingChoice,
                       tenant: dict = Depends(_tenant)) -> dict:
        """Record where this tenant's vault lives.

        A record, not a switch. Nothing here moves data: choosing a mode
        describes an arrangement people make, and an endpoint that silently
        migrated somebody's vault because a field changed would be the most
        alarming one in this product.
        """
        if tenant["id"] != tenant_id:
            raise HTTPException(403, "not your tenant")
        try:
            return hosting.choose(tenant_id, body.mode, body.note)
        except hosting.HostingError as exc:
            raise HTTPException(422, str(exc)) from None

    @app.get("/hosting/{tenant_id}/history")
    def hosting_history(tenant_id: str,
                        tenant: dict = Depends(_tenant)) -> dict:
        """Where this vault has lived — the question an auditor asks
        afterwards."""
        if tenant["id"] != tenant_id:
            raise HTTPException(403, "not your tenant")
        return {"tenant_id": tenant_id, "history": hosting.history(tenant_id)}

    # -- the console guide ---------------------------------------------------
    #
    # Public, deliberately: it describes the console rather than anybody's
    # data, and the person who most needs it is the operator standing a vault
    # up who has no token yet. Nothing here reads a record — see pdi/tutorial.py
    # for why that is structural rather than a promise.

    @app.get("/console/guide")
    def console_guide(mode: str = "text") -> dict:
        """The whole walkthrough, chaptered."""
        try:
            return tutorial.outline(mode)
        except tutorial.TutorialError as exc:
            raise HTTPException(422, str(exc)) from None

    @app.get("/console/guide/steps/{key}")
    def console_guide_step(key: str, mode: str = "text") -> dict:
        """One named step, for a screen that wants to explain itself."""
        try:
            return tutorial.step(key, mode)
        except tutorial.TutorialError as exc:
            raise HTTPException(404, str(exc)) from None

    @app.get("/console/guide/for-screen/{number}")
    def console_guide_for_screen(number: int, mode: str = "text") -> dict:
        """The lesson covering a given console screen, so a screen's help
        button opens at the right place rather than at the beginning."""
        found = tutorial.for_screen(number, mode)
        if found is None:
            raise HTTPException(404, "no lesson covers that screen")
        return found

    @app.post("/console/guide/start")
    def console_guide_start(body: GuideMark) -> dict:
        """Begin, or begin again from the top."""
        try:
            return tutorial.start(body.learner_id, body.mode)
        except tutorial.TutorialError as exc:
            raise HTTPException(422, str(exc)) from None

    @app.get("/console/guide/progress/{learner_id}")
    def console_guide_progress(learner_id: str, mode: str = "text") -> dict:
        """Where this operator is, and what is next."""
        try:
            return tutorial.where(learner_id, mode)
        except tutorial.TutorialError as exc:
            raise HTTPException(422, str(exc)) from None

    @app.post("/console/guide/done")
    def console_guide_done(body: GuideMark) -> dict:
        """Mark one step done and hand back the next."""
        try:
            return tutorial.mark(body.learner_id, body.lesson, body.mode)
        except tutorial.TutorialError as exc:
            raise HTTPException(404, str(exc)) from None

    @app.post("/console/ask")
    def console_ask(body: ConsoleAsk) -> dict:
        """Ask about operating PDI. Reads no record, changes nothing.

        `mode="voice"` renders the walkthrough for listening rather than
        reading — one lesson rendered twice, not a second script.
        """
        try:
            return assistant.ask(body.question, body.mode)
        except tutorial.TutorialError as exc:
            raise HTTPException(422, str(exc)) from None

    # The console itself, served from this API so a phone loads the UI and
    # calls the API on one origin (no CORS, nothing to configure). Mounted
    # last so it can never shadow an API route; absent until app/ is built.
    _console = mobile.console_dir()
    if _console is not None:
        from fastapi.staticfiles import StaticFiles
        app.mount("/app", StaticFiles(directory=str(_console), html=True),
                  name="console")

    # A failure the console can read.
    #
    # An unhandled exception is rendered by Starlette's `ServerErrorMiddleware`,
    # which sits *outside* every middleware this factory adds — including CORS.
    # So a 500 went back to a browser with no `access-control-allow-origin`, the
    # browser dropped the whole response, and the console reported a network
    # error. Measured over HTTP at 0.59.2, in all three products:
    #
    #     GET /health   200   access-control-allow-origin: *
    #     a 500         500   access-control-allow-origin: None
    #
    # No in-process test could see it: a `TestClient` never sends an `Origin`
    # and never runs the browser's rule. And the consequence is worse here than
    # the missing header suggests — this estate's consoles distinguish "the
    # backend is unreachable" from "the backend refused", and a 500 the browser
    # discards is indistinguishable from the first. The version-mismatch guard
    # and the problem reporter both read a failure that never arrives.
    #
    # Registering `@app.exception_handler(Exception)` does not fix it: Starlette
    # hands that handler to `ServerErrorMiddleware`, which is still outside the
    # CORS layer. It has to be a middleware, and it has to sit *inside* CORS —
    # which is why the CORS block below is the last one added.
    #
    #     asked     does the server answer when a route fails
    #     mattered  does the answer reach the reader
    #
    # The body says nothing about what broke. The traceback is logged here and
    # stays here; what leaves is a status and a sentence, which is the same
    # posture every other refusal in this product takes.
    @app.middleware("http")
    async def _a_failure_the_console_can_read(request: Request, call_next):
        try:
            return await call_next(request)
        except Exception:
            _log.exception("unhandled error on %s %s",
                           request.method, request.url.path)
            return JSONResponse(
                status_code=500,
                content={"detail": "server_error",
                         "message": "Something went wrong on our side. "
                                    "Nothing you sent was recorded."})

    # Last on purpose, and this is load-bearing. `add_middleware` inserts at
    # the front, so the middleware registered last is the outermost — and CORS
    # has to be outside the catch-all above, or the 500 it builds goes back
    # without the header again. The three products used to disagree about this
    # ordering: two added CORS before their request-scoped middleware and one
    # after, which nothing was comparing.
    _origins = os.environ.get("PDI_CORS_ORIGINS")
    if _origins:
        from fastapi.middleware.cors import CORSMiddleware
        _allow = ["*"] if _origins.strip() == "*" else [
            o.strip() for o in _origins.split(",") if o.strip()]
        app.add_middleware(
            CORSMiddleware, allow_origins=_allow, allow_credentials=False,
            allow_methods=["*"], allow_headers=["*"])

    return app


app = create_app()
