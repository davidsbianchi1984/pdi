import { useEffect, useState } from "react";
import { api, type AuditEntry } from "../api";
import { useSession } from "../store";
import { deviceLanguage, Lang, t } from "../l10n";

const CAT_COLOR: Record<string, string> = {
  data: "cyan", key: "amber", retention: "amber", tenant: "green",
  access: "green", dr: "cyan", contribution: "cyan", admin: "muted",
};

export function Audit() {
  const { session } = useSession();
  const lang = (session.language as Lang) ?? deviceLanguage();
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [chain, setChain] = useState<{ intact: boolean; entries: number } | null>(null);
  // What each `action` string means, and how long entries are kept. The
  // backend has published this since the audit log existed; the console
  // listed raw action names beside it and never said what any of them was.
  // A log whose vocabulary is undocumented in the one place it is read is
  // a log somebody has to guess at during an incident.
  const [schema, setSchema] = useState<
    { actions: { action: string; category: string; description: string }[];
      retention: string } | null>(null);
  const [glossary, setGlossary] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    if (!session.tenantToken) return;
    try {
      setChain(await api.verify(session.tenantToken));
      setEntries((await api.audit(session.tenantToken)).slice().reverse());
      setSchema(await api.auditSchema());
    } catch (e) {
      setError((e as Error).message);
    }
  }
  useEffect(() => {
    refresh();
  }, [session.tenantToken]);

  return (
    <div className="screen">
      <header className="screen-head">
        <h2>{t("au.title", lang)}</h2>
        <span className="muted small">{t("au.sub", lang)}</span>
      </header>

      {!session.tenantToken && <div className="card"><p className="muted">{t("au.pick", lang)}</p></div>}
      {error && <div className="error">⚠ {error}</div>}

      {schema && (
        <div className="card">
          <div className="row">
            <span className="muted small" style={{ flex: 1 }}>
              {schema.actions.length} {t("au.actions", lang)}{" "}
              {schema.retention}
            </span>
            <button onClick={() => setGlossary((g) => !g)}>
              {glossary ? t("au.glossary.hide", lang) : t("au.glossary.show", lang)}
            </button>
          </div>
          {glossary && schema.actions.map((a) => (
            <div key={a.action} className="row"
                 style={{ padding: "4px 0" }}>
              <code style={{ width: 220 }}>{a.action}</code>
              <span className="muted small" style={{ width: 100 }}>
                {a.category}
              </span>
              <span className="muted small" style={{ flex: 1 }}>
                {a.description}
              </span>
            </div>
          ))}
        </div>
      )}

      {chain && (
        <div className={"verify-banner " + (chain.intact ? "ok" : "bad")}>
          {chain.intact ? t("au.chain.intact", lang) : t("au.chain.broken", lang)} — {chain.entries} {t("au.verified", lang)}
          <button onClick={refresh}>{t("au.reverify", lang)}</button>
        </div>
      )}

      {entries.length > 0 && (
        <div className="card">
          <table className="tbl">
            <thead><tr><th>#</th><th>action</th><th>category</th><th>ref</th><th>at</th></tr></thead>
            <tbody>
              {entries.map((e) => (
                <tr key={e.seq}>
                  <td className="mono muted">#{e.seq}</td>
                  <td className="mono">{e.action}</td>
                  <td className={CAT_COLOR[e.category] || "muted"}>{e.category}</td>
                  <td className="mono small">{e.ref || "—"}</td>
                  <td className="muted small">{(e.at || "").slice(11, 19)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
