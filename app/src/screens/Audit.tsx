import { useEffect, useState } from "react";
import { api, type AuditEntry } from "../api";
import { useSession } from "../store";

const CAT_COLOR: Record<string, string> = {
  data: "cyan", key: "amber", retention: "amber", tenant: "green",
  access: "green", dr: "cyan", contribution: "cyan", admin: "muted",
};

export function Audit() {
  const { session } = useSession();
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [chain, setChain] = useState<{ intact: boolean; entries: number } | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    if (!session.tenantToken) return;
    try {
      setChain(await api.verify(session.tenantToken));
      setEntries((await api.audit(session.tenantToken)).slice().reverse());
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
        <h2>Audit</h2>
        <span className="muted small">append-only · SHA-256 hash-chained</span>
      </header>

      {!session.tenantToken && <div className="card"><p className="muted">Select a tenant to view its audit entries.</p></div>}
      {error && <div className="error">⚠ {error}</div>}

      {chain && (
        <div className={"verify-banner " + (chain.intact ? "ok" : "bad")}>
          {chain.intact ? "✓ Chain intact" : "✗ Chain broken"} — {chain.entries} entries verified
          <button onClick={refresh}>Re-verify</button>
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
