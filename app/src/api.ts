// Thin typed client for the PDI vault API.
import { recordProblem } from "./errors";
//
// Default base: when the console is served *by* the API (the phone case —
// http://<machine>:8000/app/), the backend is the origin we came from, so
// the phone needs no configuration at all. Only the Electron desktop shell
// (file://) and the Vite dev server fall back to the local backend.
const LOOPBACK = "http://127.0.0.1:8000";
// The desktop shell starts its own backend and tells us where it is. That
// address wins over any stored loopback one — the sibling products' lesson:
// a saved 127.0.0.1:8000 from an earlier install points at a leftover
// backend of an older version.
function desktopBackendUrl(): string | null {
  if (typeof window === "undefined") return null;
  const bridge = (window as { pdiDesktop?: { backendUrl?: string | null } }).pdiDesktop;
  return bridge?.backendUrl || null;
}
function defaultBase(): string {
  if (typeof window === "undefined") return LOOPBACK;
  const { protocol, origin, pathname } = window.location;
  if (protocol !== "http:" && protocol !== "https:") return LOOPBACK;  // file://
  if (pathname.startsWith("/app")) return origin;   // served by the API itself
  return LOOPBACK;                                   // vite dev on :5173
}

export function getBase(): string {
  const stored = localStorage.getItem("pdi.base");
  const desktop = desktopBackendUrl();
  if (desktop) {
    // Only a remote address survives on the desktop; a loopback one must
    // match the backend this app actually started.
    if (stored && !/^https?:\/\/(127\.0\.0\.1|localhost|\[::1\])(:|\/|$)/.test(stored)) {
      return stored;
    }
    return desktop;
  }
  return stored || defaultBase();
}
export function setBase(url: string) {
  localStorage.setItem("pdi.base", url.replace(/\/+$/, ""));
}
export function clearBase() { localStorage.removeItem("pdi.base"); }

// -- the key the customer holds --------------------------------------------
//
// A tenant under customer custody presents its key on **every** request:
// `_tenant` reads `x-tenant-key`, and without it the vault answers 428 to
// every record read and every write. This console sent that header on two
// bequest calls and nowhere else, so pressing *hold my own key* on the
// Custody screen locked the console out of its own vault — including out of
// the hand-back button that is supposed to undo it.
//
// In memory and never on disk. `localStorage` is the operator's machine at
// rest, which is precisely what this product promises nobody but the
// customer holds; being asked for the key again after a reload is the
// guarantee working rather than an obstacle.
let heldKey: string | null = null;

/** Arm the customer key for this session, or forget it with `null`. */
export function holdKey(key: string | null) {
  heldKey = key && key.trim() ? key.trim() : null;
}
export function keyIsHeld(): boolean { return heldKey !== null; }

// The console's own version, injected at build time (vite.config.ts) and
// compared against /health's — see VersionGuard.tsx.
declare const __APP_VERSION__: string;
export const CONSOLE_VERSION: string =
  typeof __APP_VERSION__ !== "undefined" ? __APP_VERSION__ : "dev";

/** For the routes that answer **markup**, not JSON.
 *
 *  `req` parses every body with `JSON.parse` and does not guard it, so a
 *  route serving HTML or SVG does not come back wrong — it throws a
 *  `SyntaxError` from inside the client, which surfaces to the operator as
 *  "Unexpected token <" and names nothing.
 *
 *  Three routes do exactly that. `GET /s/{bid}` serves the page a phone
 *  camera lands on after scanning a sealed carrier's code, and two `qr.svg`
 *  routes serve the codes themselves. A route's content type is part of its
 *  shape and appears nowhere in its signature; calling them against a
 *  running vault is how this was found.
 */
async function reqText(
  path: string, opts: { token?: string } = {},
): Promise<string> {
  const headers: Record<string, string> = {};
  if (opts.token) headers["authorization"] = `Bearer ${opts.token}`;
  if (heldKey) headers["x-tenant-key"] = heldKey;
  const res = await fetch(getBase() + path, { headers });
  const text = await res.text();
  if (!res.ok) {
    recordProblem("GET", path, res.status);
    throw new Error(`That didn't work (${res.status}).`);
  }
  return text;
}

async function req<T>(
  path: string,
  // `extra` carries the headers that are not a bearer token. The bequest
  // grant endpoints are the reason: an heir authenticates with a grant token
  // *and* a separately-held customer key, neither of which is a session.
  opts: { method?: string; body?: unknown; token?: string;
          extra?: Record<string, string> } = {},
): Promise<T> {
  const headers: Record<string, string> = { "content-type": "application/json" };
  if (opts.token) headers["authorization"] = `Bearer ${opts.token}`;
  if (heldKey) headers["x-tenant-key"] = heldKey;
  // After the session key, so an heir's separately-held customer key still
  // wins on the two grant calls that pass one explicitly.
  Object.assign(headers, opts.extra ?? {});
  const res = await fetch(getBase() + path, {
    method: opts.method || "GET",
    headers,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  const text = await res.text();
  const data = text ? JSON.parse(text) : null;
  if (!res.ok) {
    // The status and the operation, never the detail below: that string
    // carries whatever the user typed.
    recordProblem(opts.method || "GET", path, res.status);
    const body = data as { detail?: unknown; message?: unknown } | null;
    // The sentence first. A 422's `detail` is pydantic's list of rows, and
    // `JSON.stringify` on a list is exactly what the person used to read:
    // `[{"type":"missing","loc":["body","display_name"],...}]`. Every other
    // refusal carries a string `detail` and still comes through below.
    const said = body && typeof body.message === "string" && body.message
      ? body.message : null;
    const d = said ?? ((data && (data.detail || data.message)) || res.statusText);
    throw new Error(typeof d === "string" ? d : JSON.stringify(d));
  }
  return data as T;
}

/** A response with more in it than the screen reads. Used only where the
 *  server returns a large catalogue document — never as a stand-in for a
 *  shape that was too much trouble to drive. */
export type Row = Record<string, unknown>;

// --- shapes read off a running vault ---------------------------------------
// Driven, not inferred. Where the server names a closed set of values in its
// own 422 body, that set is a union here: a wrong literal fails the build,
// where a wrong string fails an operator mid-transfer.

/** What a sealed carrier's code is attached to. Four, and no others. */
export type BeaconRefKind = "transfer" | "intake" | "object" | "facility";

/** Why somebody scanned and rang. Also closed, also enforced. */
export type RingKind = "delivery" | "access" | "collection" | "other";

export interface BeaconRow {
  id: string; tenant_id: string; ref_kind: BeaconRefKind;
  ref_id?: string | null; label: string;
  /** A single value, not a list. `blind` proves custody and says nothing
   *  else; `contact` adds a way to reach whoever holds it. */
  disclose: "blind" | "contact";
  programs: string[]; state: string; scans: number; active: boolean;
  created_at: string; scan_url: string; qr_svg: string;
}

/** What a scanner sees. `contents` is always null and that is the feature:
 *  the code proves custody, it does not open the thing. */
export interface ScanCard {
  reference: string; kind: string; state: string; under_custody: boolean;
  programs: string[]; controls: ControlSet; badge: string;
  contents: null; note: string; found_url: string;
  held_by?: string | null; label?: string | null;
}

export interface ControlSet {
  required: string[]; satisfied_by_pdi: string[]; operational: string[];
}

/** One chain of custody, and whether the hash chain under it still verifies.
 *  `audit_chain_intact` is the load-bearing field — a custody list nobody
 *  can check is a list of claims. */
export interface CustodyChain {
  controls: ControlSet;
  chain_of_custody: { event: string; actor: string; at: string }[];
  audit_chain_intact: boolean;
  status?: string; state?: string; programs?: string[];
  retention_days?: number; retained_until?: string | null;
  [field: string]: unknown;
}

export interface TransferRow {
  id: string; tenant_id: string; recipient: string; filename: string;
  size: number; classification?: string | null; programs: string[];
  party_type?: string | null; status: string; retention_days: number;
  expires_at?: string | null; created_at: string;
  /** Shown once, on creation only — the listing does not carry it. */
  receive_token?: string; controls?: ControlSet;
}

export interface IntakeRow {
  id: string; tenant_id: string; from_party: string;
  party_type?: string | null; purpose?: string | null; programs: string[];
  status: string; filename?: string | null;
  classification?: string | null; retention_days: number;
  expires_at?: string | null; created_at: string;
  /** Shown once, as above. */
  submit_token?: string; controls?: ControlSet;
}

export interface TenantKey {
  provider: string; customer_managed: boolean;
  operator_can_decrypt: boolean; note: string;
}

export interface CompliancePrograms {
  key: string; label: string; sector: string; summary: string;
  controls: string[]; retention_days: number;
}

export interface BaaStatus {
  executed: boolean; effective_date?: string | null; note?: string;
  customer_legal_name?: string; operator_legal_name?: string;
}

export interface HostingMode {
  title: string; price: string; means: string;
  availability?: string; free_because?: string;
  we_are_responsible_for: string[]; you_are_responsible_for: string[];
  guarantees: string[]; note?: string; mode?: string;
}

export interface ConnectorRow {
  id: string; tenant_id: string; platform: string; direction: string;
  handle?: string | null; scope: string[]; status: string;
  collected: number; published: number; beacon: string;
}

export interface RobotModel {
  model: string; label: string; maker?: string; kind?: string;
  capabilities?: string[];
}

export interface GuideBook {
  guide: string; ceiling: string;
  chapters: { chapter: string; steps: Row[] }[];
}

/** The console assistant. `refused` is not an error path — it is the answer
 *  when somebody asks it something about the vault's contents, which it
 *  cannot read and says so. */
export interface ConsoleAnswer {
  answer: string; source: string; refused: boolean; disclosure: string;
  topics: string[];
  directions?: { lesson: string; title: string; screens: number[];
                 say: string; walkthrough_step: string } | null;
}

export interface DockState {
  tenant_id: string; corner: string; state: string; face: string;
  faces: string[]; set: boolean;
}

export interface DockCatalog {
  faces: Record<string, string>; corners: Record<string, string>;
  states: Record<string, string>; box: Record<string, number>;
  never: Record<string, string>;
}

export interface LanguageOption {
  code: string; label: string; notes_translated: boolean;
}

/** PDI does no machine translation. The `note` says so and is printed. */
export interface TranslateOut {
  text: string; translation: string; language: string;
  engine: string; note: string;
}

export interface ImproveBoard {
  mine: Row[]; tally: Record<string, number>; total: number;
  categories: string[];
}

export interface KeyVersion { version: number; active: boolean; created_at: string; provider: string }
export interface AuditEntry { seq: number; action: string; category: string; tenant_id?: string; ref?: string; at: string }
export interface RetentionPolicy {
  recovery_window: string;
  windows: string[];
  record_retention: { tenant_id: string; name: string; retention: string }[];
}

export interface Blueprint {
  id: string;
  industry: string;
  role: { job_title?: string; department?: string; oversight_level: string; manages_staff: number };
  assistant: {
    tone: string;
    interaction: string;
    capabilities: { key: string; label: string; why: string }[];
  };
  automation: { opportunity_score: number; opportunities: string[]; watch_3_5yr: string[]; note: string };
  human_in_loop: { required: string[]; note: string };
  reskilling: { interested: boolean; suggested_paths: string[] };
  assistant_spec: string;
}

// The AI Integration & Role-Mapping Questionnaire (all fields optional).
export interface PositionIntake {
  industry?: string;
  role?: { job_title?: string; department?: string; role_type?: string; manages_staff?: number };
  workflow?: { manages?: string[]; documents_incidents?: boolean; recurring_meetings?: boolean; manual_tasks?: boolean };
  decisions?: { scope?: string[]; automatable_decisions?: string[] };
  bottlenecks?: { redundant_tasks?: string[]; outdated_tasks?: string[] };
  preferences?: { wants?: string[]; tone?: string; interaction?: string; summarize_logs?: boolean; learn_decision_style?: boolean };
  admin?: { compliance_accountable?: boolean };
  future?: { comfortable_automation?: boolean; roles_obsolete_3_5yr?: string[]; reskilling_interest?: boolean };
}

export interface PairInfo {
  console_url: string; api_url: string; console_built: boolean;
  reachable: boolean; qr_svg: string; how: string[]; note: string;
}

export interface ProvenanceOut {
  key: string;
  origin: string;
  sealed: { cipher: string; bound_to: string; created_at: string;
            updated_at: string; ciphertext_bytes: number };
  audit: { events: { action: string; at: string; category: string }[];
           count: number };
  chain: { intact?: boolean; entries?: number } & Record<string, unknown>;
  note: string;
}

export interface OperationsEntry {
  key: string;
  updated_at: string;
  org?: string | null;
  goal?: string | null;
  plan?: string | null;
  departments: string[];
}

/** A standing instruction: if the condition is attested, this person may read
 *  these key prefixes. Dormant until an executor activates it. */
export type Bequest = {
  id: string;
  tenant_id: string;
  grantee_name: string;
  key_prefixes: string[];
  condition: string;
  note?: string | null;
  activated: boolean;
  activated_at?: string | null;
  activation_ref?: string | null;
  revoked: boolean;
  created_at: string;
  /** Returned by activation only, and only once. */
  grant_token?: string;
};

/** What the gateway agent may and may not do. Rendered rather than
 *  paraphrased: this is the statement of the ceiling, not a summary of it. */
export type GateCeiling = {
  rule: string;
  may: Record<string, string>;
  may_never: Record<string, string>;
  always_human?: unknown;
  human_in_loop?: unknown;
  enforcement?: unknown;
};

export type RosterEntry = {
  id: string;
  name: string;
  role: string;
  days?: string | null;
  from?: string | null;
  to?: string | null;
  position?: number;
  crosses_midnight?: boolean;
};

export type GateRoster = {
  configured: boolean;
  roster: RosterEntry[];
  on_now: RosterEntry[];
  anybody_on_shift: boolean;
  escalation_order?: string[];
  timezone?: string | null;
  evaluated_at?: string;
  note?: string;
};

export type GateChannel = {
  configured: boolean;
  signed?: boolean;
  envelope?: unknown;
  note?: string;
};

export type GatePage = {
  id?: string;
  delivered?: boolean;
  [key: string]: unknown;
};

export const api = {
  /** What this deployment can and cannot reach.
   *
   *  Offline mode was settable before this and had nowhere to be read. A
   *  guarantee nobody can see is a guarantee nobody can check. */
  offlineStatus: () => req<{
    offline: boolean; external_transmission_possible: boolean;
    local_destinations_allowed: string; guarantees: string[];
    cloud_attached?: boolean;
  }>("/offline/status"),
  health: () => req<{ status: string; version?: string }>("/health"),

  // How to open this console on a phone: its URL on the local network.
  pair: () => req<PairInfo>("/pair"),

  // admin
  createTenant: (name: string, retention: string | undefined, adminToken?: string) =>
    req<{ id: string; name: string; token: string }>("/tenants", {
      method: "POST", body: { name, retention }, token: adminToken,
    }),
  keys: (adminToken?: string) =>
    req<{ provider: string; versions: KeyVersion[] }>("/keys", { token: adminToken }),
  rotateKey: (adminToken?: string) =>
    req<{ active_version: number; reseal?: { resealed: number } }>("/keys/rotate", {
      method: "POST", token: adminToken,
    }),
  retention: (adminToken?: string) =>
    req<RetentionPolicy>("/retention", { token: adminToken }),
  setRetention: (tenantId: string, retention: string, adminToken?: string) =>
    req<{ retention: string }>(`/tenants/${tenantId}/retention`, {
      method: "PUT", body: { retention }, token: adminToken,
    }),
  sweep: (adminToken?: string) =>
    req<{ purged_tenants: number; expired_records: number; recovery_window: string }>(
      "/retention/sweep", { method: "POST", token: adminToken }),

  // tenant-scoped
  putRecord: (key: string, value: string, token: string) =>
    req<{ id: string; key: string; stored: boolean }>("/records", {
      method: "PUT", body: { key, value }, token,
    }),
  getRecord: (key: string, token: string) =>
    req<{ key: string; value: string; updated_at: string }>(
      `/records/${key}`, { token }),
  listKeys: (token: string) => req<{ keys: string[] }>("/records", { token }),
  // The operations journal: QRME-sealed coordination records, in place.
  operations: (token: string) =>
    req<{ entries: OperationsEntry[]; note: string }>("/operations", { token }),
  // The derivation trail of one sealed record: origin, seal, audit, chain.
  provenance: (key: string, token: string) =>
    req<ProvenanceOut>(`/provenance/${key}`, { token }),

  // positions — assistant builder
  buildPosition: (intake: PositionIntake, token: string) =>
    req<Blueprint>("/positions", { method: "POST", body: intake, token }),
  listPositions: (token: string) =>
    req<{ count: number; ids: string[] }>("/positions", { token }),
  getPosition: (id: string, token: string) =>
    req<Blueprint>(`/positions/${id}`, { token }),

  // audit
  audit: (token: string) => req<AuditEntry[]>("/audit", { token }),
  verify: (token: string) =>
    req<{ intact: boolean; entries: number }>("/audit/verify", { token }),
  auditSchema: () =>
    req<{ actions: { action: string; category: string; description: string }[]; retention: string }>(
      "/audit/schema"),
  // ---------------------------------------------------------------------
  // Continuity, and the gateway. Both had complete backends and no caller.
  // ---------------------------------------------------------------------

  // A bequest is dormant by design. Creating one grants nothing; it records
  // what *would* be readable, by whom, if the condition were ever attested.
  bequests: (token: string) => req<Bequest[]>("/bequests", { token }),
  createBequest: (body: { grantee_name: string; key_prefixes: string[];
    condition?: string; note?: string }, token: string) =>
    req<Bequest>("/bequests", { method: "POST", body, token }),
  revokeBequest: (bid: string, token: string) =>
    req<Bequest>(`/bequests/${bid}`, { method: "DELETE", token }),

  // The executor's act, and the operator's. Activation attests the condition
  // — the reference goes into the audit chain — and mints the grant token,
  // which is shown once and never again.
  activateBequest: (bid: string, activation_ref: string, adminToken: string) =>
    req<Bequest>(`/bequests/${bid}/activate`,
      { method: "POST", body: { activation_ref }, token: adminToken }),
  revokeBequestGrant: (bid: string, adminToken: string) =>
    req<{ revoked: boolean }>(`/bequests/${bid}/grant`,
      { method: "DELETE", token: adminToken }),

  // The heir's side. Two separate secrets on purpose: the grant token says
  // the condition was attested, the customer key decrypts. Holding one
  // without the other opens nothing.
  bequestKeys: (grantToken: string, customerKey: string) =>
    req<{ keys: string[] }>("/bequests/grant/keys",
      { extra: { "x-grant-token": grantToken, "x-tenant-key": customerKey } }),
  bequestRead: (key: string, grantToken: string, customerKey: string) =>
    req<{ key: string; value: unknown }>(
      `/bequests/grant/read?key=${encodeURIComponent(key)}`,
      { extra: { "x-grant-token": grantToken, "x-tenant-key": customerKey } }),

  // The suite gateway: what the agent may do, who is on shift, and what it
  // sent when nobody was.
  gateCeiling: (token: string) => req<GateCeiling>("/gate/ceiling", { token }),
  gateChannel: (token: string) => req<GateChannel>("/gate/channel", { token }),
  gateRoster: (token: string) => req<GateRoster>("/gate/roster", { token }),
  addToRoster: (body: { name: string; role?: string; days?: string;
    from_time?: string; to_time?: string }, token: string) =>
    req<RosterEntry>("/gate/roster", { method: "POST", body, token }),
  removeFromRoster: (rid: string, token: string) =>
    req<{ removed: boolean }>(`/gate/roster/${rid}`,
      { method: "DELETE", token }),
  setGateTimezone: (timezone: string, token: string) =>
    req<{ tenant_id: string; timezone: string }>("/gate/timezone",
      { method: "PUT", body: { timezone }, token }),
  gatePages: (token: string, undeliveredOnly = false) =>
    req<GatePage[]>("/gate/pages"
      + (undeliveredOnly ? "?undelivered_only=true" : ""), { token }),
  retryPage: (pid: string, token: string) =>
    req<GatePage>(`/gate/pages/${pid}/retry`, { method: "POST", token }),

  // =====================================================================
  // The rest of the vault's API.
  //
  // Eighty-four routes the desktop console could not reach on its own. Every
  // one was present on a phone shell, which is what let the union guard
  // report a healthy number for as long as it did: it was answering *some
  // client can reach this*, and a phone could.
  //
  // Shapes below were read off a running vault on 8792, not off the route
  // table. That is the house rule and it earned its keep again — see the
  // notes on the individual bindings for the six places the two disagreed.
  // =====================================================================

  // -- sealed carriers, and the code on the outside of one ----------------
  // `disclose` is a single value, not a list: `blind` shows a scanner that
  // the thing is under custody and nothing else; `contact` adds a way to
  // reach the holder. `ref_kind` is one of four and the server names them.
  beacons: (token: string) => req<BeaconRow[]>("/beacons", { token }),
  beacon: (bid: string, token: string) =>
    req<BeaconRow>(`/beacons/${bid}`, { token }),
  placeBeacon: (body: { ref_kind: BeaconRefKind; ref_id?: string;
                        label: string; disclose?: "blind" | "contact";
                        programs?: string[] }, token: string) =>
    req<BeaconRow>("/beacons", { method: "POST", body, token }),
  setBeaconState: (bid: string, state: string, token: string) =>
    req<BeaconRow>(`/beacons/${bid}/state`,
      { method: "PUT", body: { state }, token }),
  liftBeacon: (bid: string, token: string) =>
    req<{ id: string; active: boolean }>(`/beacons/${bid}`,
      { method: "DELETE", token }),
  beaconCustody: (bid: string, token: string) =>
    req<CustodyChain>(`/beacons/${bid}/custody`, { token }),
  // The scan side. No credential anywhere here, deliberately: a code on a
  // sealed crate is *for* whoever is holding the crate. What they can learn
  // is capped by `disclose`, and what they can do is leave a note in the
  // chain — which the holder reads and they cannot alter.
  scanPage: (bid: string) => reqText(`/s/${bid}`),
  // The recipient's page. The console fetches it for one reason: the sender
  // is about to put this URL in an email, and a deployment whose public base
  // is misconfigured would send a dead link to somebody who cannot ask why.
  // Checking costs one request and happens before the copy, not after.
  recipientPage: (tid: string) => reqText(`/r/${tid}`),
  scanCard: (bid: string) => req<ScanCard>(`/s/${bid}/card`),
  scanQr: (bid: string) => reqText(`/s/${bid}/qr.svg`),
  reportFound: (bid: string, body: { where?: string; contact?: string }) =>
    req<{ beacon: string; recorded: boolean; note: string }>(
      `/s/${bid}/found`, { method: "POST", body }),
  ringHolder: (bid: string, body: { kind: RingKind; note?: string }) =>
    req<Row>(`/s/${bid}/ring`, { method: "POST", body }),
  rings: (token: string, openOnly = false) =>
    req<Row[]>("/rings" + (openOnly ? "?open_only=true" : ""), { token }),
  ringTranscript: (rid: string, token: string) =>
    req<Row>(`/rings/${rid}/transcript`, { token }),

  // -- what comes in and what goes out ------------------------------------
  transfers: (token: string) => req<TransferRow[]>("/transfers", { token }),
  transfer: (tid: string, token: string) =>
    req<TransferRow>(`/transfers/${tid}`, { token }),
  sendTransfer: (body: { recipient: string; filename: string;
                         content: string; programs?: string[];
                         classification?: string; party_type?: string },
                 token: string) =>
    req<TransferRow>("/transfers", { method: "POST", body, token }),
  transferCustody: (tid: string, token: string) =>
    req<CustodyChain>(`/transfers/${tid}/custody`, { token }),
  withdrawTransfer: (tid: string, token: string) =>
    req<Row>(`/transfers/${tid}`, { method: "DELETE", token }),
  // The recipient is not the tenant, so this does not take the tenant's
  // token — it takes the one-time receive token, in a header of its own.
  // Binding it as a bearer credential is a 403 every time.
  receiveTransfer: (tid: string, receiveToken: string) =>
    req<{ id: string; filename: string; content: string;
          programs: string[]; custody: string }>(
      `/transfers/${tid}/receive`,
      { method: "POST", extra: { "x-receive-token": receiveToken } }),

  intakes: (token: string) => req<IntakeRow[]>("/intakes", { token }),
  intake: (iid: string, token: string) =>
    req<IntakeRow>(`/intakes/${iid}`, { token }),
  requestIntake: (body: { from_party: string; party_type?: string;
                          purpose?: string; programs?: string[] },
                  token: string) =>
    req<IntakeRow>("/intakes", { method: "POST", body, token }),
  intakeCustody: (iid: string, token: string) =>
    req<CustodyChain>(`/intakes/${iid}/custody`, { token }),
  intakeFile: (iid: string, token: string) =>
    req<{ id: string; filename: string; content: string;
          programs: string[] }>(`/intakes/${iid}/file`, { token }),
  cancelIntake: (iid: string, token: string) =>
    req<Row>(`/intakes/${iid}`, { method: "DELETE", token }),
  // Same shape as receive, and for the same reason: the party sending the
  // file in is not the tenant asking for it.
  submitToIntake: (iid: string, submitToken: string,
                   body: { filename: string; content: string;
                           classification?: string }) =>
    req<{ id: string; status: string; sealed: boolean; filename: string;
          note: string }>(`/intakes/${iid}/submit`,
      { method: "POST", body, extra: { "x-submit-token": submitToken } }),

  // -- custody of the key, and of the tenant ------------------------------
  // `provider` is `held` or `kms`. Not `customer` — which is what the
  // concept is called everywhere else in this product, and is a 422 here.
  tenantKey: (token: string) => req<TenantKey>("/key", { token }),
  setTenantKey: (body: { provider?: "held" | "kms"; key?: string;
                         config?: Row }, token: string) =>
    req<TenantKey>("/key", { method: "PUT", body, token }),
  // Hands the tenant back to deployment custody. A 409 if it never left.
  surrenderTenantKey: (token: string) =>
    req<TenantKey>("/key", { method: "DELETE", token }),
  resealUnderNewKey: (adminToken?: string) =>
    req<{ active_version: number; resealed: number;
          customer_managed_skipped: number }>("/keys/reseal",
      { method: "POST", token: adminToken }),
  retireOldKeys: (adminToken?: string) =>
    req<{ retired: number; versions: KeyVersion[] }>("/keys/retire",
      { method: "POST", token: adminToken }),

  // Portability, distinct from the disaster-recovery snapshot below: every
  // table in the deployment that names this tenant, credentials and sealed
  // bytes dropped per column.
  exportEverything: (token: string) =>
    req<{ tenant: Row | null; tables: Record<string, Row[]>; note: string }>(
      "/export", { token }),
  snapshot: (token: string) =>
    req<{ tenant_id: string; records: Row[] }>("/snapshot", { token }),
  restoreRecords: (records: Row[], token: string) =>
    req<Row>("/restore", { method: "POST", body: { records }, token }),
  restoreTenant: (tenantId: string, adminToken?: string) =>
    req<Row>(`/tenants/${tenantId}/restore`,
      { method: "POST", token: adminToken }),
  deleteRecord: (key: string, token: string) =>
    req<Row>(`/records/${key}`, { method: "DELETE", token }),
  // `mode` decides whether the tenant can come back. The audit trail
  // survives either way — that is the point of a hash chain.
  deleteTenant: (tenantId: string, mode: string, adminToken?: string) =>
    req<Row>(`/tenants/${tenantId}?mode=${encodeURIComponent(mode)}`,
      { method: "DELETE", token: adminToken }),
  mintToken: (tenantId: string, role: "read" | "write", adminToken?: string) =>
    req<{ token: string }>(`/tenants/${tenantId}/tokens`,
      { method: "POST", body: { role }, token: adminToken }),
  revokeToken: (token: string, adminToken?: string) =>
    req<Row>(`/tokens/${token}`, { method: "DELETE", token: adminToken }),

  // -- the paperwork a regulated transfer needs ---------------------------
  compliancePrograms: () =>
    req<{ programs: CompliancePrograms[] }>("/compliance/programs"),
  baaStatus: (token: string) => req<BaaStatus>("/baa", { token }),
  tenantBaa: (tenantId: string, adminToken?: string) =>
    req<BaaStatus>(`/tenants/${tenantId}/baa`, { token: adminToken }),
  recordBaa: (tenantId: string, body: { customer_legal_name: string;
                operator_legal_name: string; effective_date: string;
                customer_signatory?: string; operator_signatory?: string;
                document_sha256?: string }, adminToken?: string) =>
    req<BaaStatus>(`/tenants/${tenantId}/baa`,
      { method: "POST", body, token: adminToken }),
  rescindBaa: (tenantId: string, adminToken?: string) =>
    req<Row>(`/tenants/${tenantId}/baa`,
      { method: "DELETE", token: adminToken }),

  // -- where the vault physically is --------------------------------------
  hostingModes: () => req<{ modes: Record<string, HostingMode> }>("/hosting"),
  hosting: (tenantId: string, token: string) =>
    req<HostingMode & { tenant_id: string }>(`/hosting/${tenantId}`, { token }),
  // An **object** with a `history` key, not the array the name suggests.
  // Typed `Row[]` here, the Custody screen called `.map` on an object and
  // threw `history.map is not a function` the moment a vault had ever been
  // moved — a screen that worked on every fresh vault and on no vault with
  // a past.
  hostingHistory: (tenantId: string, token: string) =>
    req<{ tenant_id: string; history: Row[] }>(
      `/hosting/${tenantId}/history`, { token }),
  setHosting: (tenantId: string, body: { mode: string; note?: string },
               token: string) =>
    req<Row>(`/hosting/${tenantId}`, { method: "PUT", body, token }),
  recordDeployment: (body: { name: string; option: string;
                             facility?: string; tier?: string },
                     token: string) =>
    req<Row>("/deployments", { method: "POST", body, token }),

  // -- other systems reaching in ------------------------------------------
  connectorCatalog: () => req<Row>("/connectors/catalog"),
  connectors: (token: string) => req<ConnectorRow[]>("/connectors", { token }),
  addConnector: (body: { platform: string; direction: string;
                         handle?: string; scope?: string[] }, token: string) =>
    req<ConnectorRow>("/connectors", { method: "POST", body, token }),
  removeConnector: (cid: string, token: string) =>
    req<Row>(`/connectors/${cid}`, { method: "DELETE", token }),
  connectorBeacon: (cid: string, token: string) =>
    req<Row>(`/connectors/${cid}/beacon`, { token }),
  connectorQr: (cid: string, token: string) =>
    reqText(`/connectors/${cid}/qr.svg`, { token }),
  ingestToConnector: (cid: string, items: Row[], token: string) =>
    req<Row>(`/connectors/${cid}/ingest`,
      { method: "POST", body: { items }, token }),
  scrapeConnector: (cid: string, token: string) =>
    req<Row>(`/connectors/${cid}/scrape`, { method: "POST", token }),
  publishFromConnector: (cid: string, body: { content: string;
                                              topic?: string },
                         token: string) =>
    req<Row>(`/connectors/${cid}/publish`, { method: "POST", body, token }),

  roboticsCatalog: () => req<{ robots: RobotModel[] }>("/robotics/catalog"),
  robots: (token: string) => req<Row[]>("/robots", { token }),
  bindRobot: (body: { model: string; name?: string }, token: string) =>
    req<Row>("/robots", { method: "POST", body, token }),
  unbindRobot: (rid: string, token: string) =>
    req<Row>(`/robots/${rid}`, { method: "DELETE", token }),
  robotData: (rid: string, token: string) =>
    req<Row>(`/robots/${rid}/data`, { token }),
  robotIngest: (rid: string, body: { kind: string; content: string;
                                     ref?: string }, token: string) =>
    req<Row>(`/robots/${rid}/ingest`, { method: "POST", body, token }),

  contributions: (token: string) =>
    req<{ count: number; keys: string[] }>("/contributions", { token }),
  contribute: (body: { source: string; kind: string; payload: Row;
                       ref?: string }, token: string) =>
    req<{ id: string; key: string; ref?: string | null; sealed: boolean }>(
      "/contributions", { method: "POST", body, token }),
  withdrawContribution: (ref: string, token: string) =>
    req<Row>(`/contributions/${ref}`, { method: "DELETE", token }),
  seedDemo: (adminToken?: string) =>
    req<Row>("/seed", { method: "POST", token: adminToken }),

  // -- the guide, the dock, and the words it uses -------------------------
  guide: () => req<GuideBook>("/console/guide"),
  guideStep: (key: string) => req<Row>(`/console/guide/steps/${key}`),
  guideForScreen: (n: number) => req<Row>(`/console/guide/for-screen/${n}`),
  guideProgress: (learnerId: string) =>
    req<Row>(`/console/guide/progress/${learnerId}`),
  startGuide: (body: { learner_id: string; lesson?: string }) =>
    req<Row>("/console/guide/start", { method: "POST", body }),
  finishGuideStep: (body: { learner_id: string; lesson?: string }) =>
    req<Row>("/console/guide/done", { method: "POST", body }),
  askConsole: (body: { question: string; mode?: string }, token: string) =>
    req<ConsoleAnswer>("/console/ask", { method: "POST", body, token }),

  dockFaces: () => req<DockCatalog>("/dock/faces"),
  dockWhere: (face: string) => req<Row>(`/dock/where/${face}`),
  dock: (tenantId: string, token: string) =>
    req<DockState>(`/dock/${tenantId}`, { token }),
  dockFace: (tenantId: string, name: string, token: string) =>
    req<Row>(`/dock/${tenantId}/face/${name}`, { token }),
  setDock: (tenantId: string, body: { corner?: string; state?: string;
                                      face?: string; faces?: string[] },
            token: string) =>
    req<DockState>(`/dock/${tenantId}`, { method: "PUT", body, token }),

  languages: () => req<{ languages: LanguageOption[] }>("/languages"),
  language: (token: string) => req<Row>("/language", { token }),
  setLanguage: (body: { language: string; mode?: string }, token: string) =>
    req<Row>("/language", { method: "PUT", body, token }),
  // PDI performs no machine translation. This translates its **own** note
  // strings and says so in the response, which is why the screen prints the
  // note rather than hiding it behind a spinner.
  translate: (body: { text: string; to?: string }, token: string) =>
    req<TranslateOut>("/translate", { method: "POST", body, token }),

  improvements: (token: string) => req<ImproveBoard>("/improve", { token }),
  suggestImprovement: (body: { category?: string; message: string;
                               rating?: string }, token: string) =>
    req<Row>("/improve", { method: "POST", body, token }),

  // The accessibility door. The POST is deliberately tokenless — reporting
  // that the vault shut you out must not require a tenant token — and the
  // GET takes the deployment's admin token: reports are read by whoever
  // stands for the deployment.
  sendAccessReport: (body: { doing: string; wall: string; help?: string;
                             lang?: string }) =>
    req<{ id: string; status: string; note: string }>(
      "/access/reports", { method: "POST", body }),
  accessReports: (adminToken: string) =>
    req<AccessReports>("/access/reports", { token: adminToken }),
};

/** Accessibility reports, for the deployment's operator. Three answers in
 *  the writer's own words and language — never a name, never a diagnosis:
 *  the table they come from has no submitter column to select. */
export type AccessReports = {
  reports: { id: string; lang: string; doing: string; wall: string;
             help: string | null; status: string; created_at: string }[];
  total: number;
};
