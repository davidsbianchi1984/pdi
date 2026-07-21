import { useEffect, useState } from "react";
import { api, type KeyVersion, type RetentionPolicy } from "../api";
import { useSession } from "../store";

export function Keys() {
  const { session } = useSession();
  const [keys, setKeys] = useState<KeyVersion[]>([]);
  const [ret, setRet] = useState<RetentionPolicy | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    try {
      setKeys((await api.keys(session.adminToken)).versions);
      setRet(await api.retention(session.adminToken));
    } catch (e) {
      setError((e as Error).message);
    }
  }
  useEffect(() => {
    refresh();
  }, [session.adminToken]);

  async function rotate() {
    setBusy(true);
    setError(null);
    try {
      const r = await api.rotateKey(session.adminToken);
      setMsg(`Rotated to v${r.active_version}; re-sealed ${r.reseal?.resealed ?? 0} records.`);
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function setRetention(tenantId: string, w: string) {
    try {
      await api.setRetention(tenantId, w, session.adminToken);
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function sweep() {
    try {
      const s = await api.sweep(session.adminToken);
      setMsg(`Swept: purged ${s.purged_tenants} tenants, expired ${s.expired_records} records (window ${s.recovery_window}).`);
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="screen">
      <header className="screen-head">
        <h2>Keys &amp; Retention</h2>
        <span className="muted small">envelope encryption · retention up to forever</span>
      </header>
      {error && <div className="error">⚠ {error}</div>}
      {msg && <div className="ok-note">{msg}</div>}

      <div className="card">
        <h3>Key versions <span className="muted small">({keys[0]?.provider || "envelope"})</span></h3>
        <table className="tbl">
          <thead><tr><th>version</th><th>state</th><th>created</th></tr></thead>
          <tbody>
            {keys.map((k) => (
              <tr key={k.version}>
                <td className="mono">v{k.version}</td>
                <td>{k.active ? <span className="cyan">active</span> : <span className="muted">retired-able</span>}</td>
                <td className="muted small">{k.created_at.slice(0, 19).replace("T", " ")}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <button className="primary" onClick={rotate} disabled={busy}>
          {busy ? "Rotating…" : "Rotate key (re-seal records)"}
        </button>
      </div>

      <div className="card">
        <h3>Retention</h3>
        <div className="muted small">Recovery window: <span className="cyan">{ret?.recovery_window}</span></div>
        {ret?.record_retention.map((r) => (
          <div className="row-inline" key={r.tenant_id}>
            <span>{r.name}</span>
            <select value={r.retention} onChange={(e) => setRetention(r.tenant_id, e.target.value)}>
              {(ret.windows || ["7d", "30d", "90d", "180d", "1y", "forever"]).map((w) => (
                <option key={w}>{w}</option>
              ))}
            </select>
          </div>
        ))}
        <button onClick={sweep}>Run retention sweep</button>
      </div>
    </div>
  );
}
