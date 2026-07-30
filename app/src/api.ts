// Thin typed client for the PDI vault API.
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

// The console's own version, injected at build time (vite.config.ts) and
// compared against /health's — see VersionGuard.tsx.
declare const __APP_VERSION__: string;
export const CONSOLE_VERSION: string =
  typeof __APP_VERSION__ !== "undefined" ? __APP_VERSION__ : "dev";

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
  Object.assign(headers, opts.extra ?? {});
  const res = await fetch(getBase() + path, {
    method: opts.method || "GET",
    headers,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  const text = await res.text();
  const data = text ? JSON.parse(text) : null;
  if (!res.ok) {
    const d = (data && (data.detail || data.message)) || res.statusText;
    throw new Error(typeof d === "string" ? d : JSON.stringify(d));
  }
  return data as T;
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
};
