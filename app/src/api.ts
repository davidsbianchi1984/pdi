// Thin typed client for the PDI vault API.
const DEFAULT_BASE = "http://127.0.0.1:8000";

export function getBase(): string {
  return localStorage.getItem("pdi.base") || DEFAULT_BASE;
}
export function setBase(url: string) {
  localStorage.setItem("pdi.base", url.replace(/\/+$/, ""));
}

async function req<T>(
  path: string,
  opts: { method?: string; body?: unknown; token?: string } = {},
): Promise<T> {
  const headers: Record<string, string> = { "content-type": "application/json" };
  if (opts.token) headers["authorization"] = `Bearer ${opts.token}`;
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

export const api = {
  health: () => req<{ status: string }>("/health"),

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

  // audit
  audit: (token: string) => req<AuditEntry[]>("/audit", { token }),
  verify: (token: string) =>
    req<{ intact: boolean; entries: number }>("/audit/verify", { token }),
  auditSchema: () =>
    req<{ actions: { action: string; category: string; description: string }[]; retention: string }>(
      "/audit/schema"),
};
