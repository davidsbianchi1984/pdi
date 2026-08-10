import { useEffect, useState } from "react";
import { api, type KeyVersion, type RetentionPolicy } from "../api";
import { useSession } from "../store";
import { deviceLanguage, Lang, t } from "../l10n";

export function Overview({ go }: { go: (t: "tenants" | "keys" | "audit") => void }) {
  const { session } = useSession();
  const lang = (session.language as Lang) ?? deviceLanguage();
  const [health, setHealth] = useState<string>("…");
  const [keys, setKeys] = useState<KeyVersion[]>([]);
  const [ret, setRet] = useState<RetentionPolicy | null>(null);
  const [chain, setChain] = useState<{ intact: boolean; entries: number } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.health().then((h) => setHealth(h.status)).catch(() => setHealth("unreachable"));
    api.keys(session.adminToken).then((k) => setKeys(k.versions)).catch(() => {});
    api.retention(session.adminToken).then(setRet).catch(() => {});
    if (session.tenantToken)
      api.verify(session.tenantToken).then(setChain).catch((e) => setError((e as Error).message));
  }, [session.adminToken, session.tenantToken]);

  const active = keys.find((k) => k.active);
  const tiles = [
    { label: "Health", value: health === "ok" ? "OK" : health, sub: "GET /health" },
    { label: "Key version", value: active ? `v${active.version}` : "—", sub: active?.provider || "envelope" },
    { label: "Audit chain", value: chain ? (chain.intact ? "OK" : "BROKEN") : "—", sub: chain ? `${chain.entries} entries` : "select a tenant" },
    { label: "Recovery window", value: ret?.recovery_window || "—", sub: "soft-delete purge" },
  ];

  return (
    <div className="screen">
      <header className="screen-head">
        <h2>{t("ov.title", lang)}</h2>
        <span className={"dot-online" + (health === "ok" ? "" : " off")}>● {health === "ok" ? "Vault online" : health}</span>
      </header>
      {error && <div className="error">⚠ {error}</div>}
      <div className="tiles">
        {tiles.map((t) => (
          <div className="tile" key={t.label}>
            <div className="tile-label">{t.label}</div>
            <div className="tile-value">{t.value}</div>
            <div className="tile-sub">{t.sub}</div>
          </div>
        ))}
      </div>

      <div className="card">
        <h3>{t("ov.retention", lang)}</h3>
        {ret ? (
          ret.record_retention.length ? (
            <table className="tbl">
              <thead><tr><th>tenant</th><th>{t("ov.recordret", lang)}</th></tr></thead>
              <tbody>
                {ret.record_retention.map((r) => (
                  <tr key={r.tenant_id}><td>{r.name}</td><td className="cyan">{r.retention}</td></tr>
                ))}
              </tbody>
            </table>
          ) : <div className="muted">{t("ov.none", lang)}</div>
        ) : <div className="muted">Loading…</div>}
      </div>

      <div className="actions">
        <button onClick={() => go("tenants")}>{t("tn.title", lang)}</button>
        <button onClick={() => go("keys")}>{t("ky.title", lang)}</button>
        <button onClick={() => go("audit")}>{t("au.title", lang)}</button>
      </div>
    </div>
  );
}
