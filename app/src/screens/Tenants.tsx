import { useState } from "react";
import { api } from "../api";
import { useSession } from "../store";

export function Tenants() {
  const { session, setSession } = useSession();
  const [name, setName] = useState("qrme");
  const [retention, setRetention] = useState("forever");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [created, setCreated] = useState<string | null>(null);

  async function create() {
    if (!name.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const t = await api.createTenant(name.trim(), retention, session.adminToken);
      setSession({ tenantId: t.id, tenantName: t.name, tenantToken: t.token });
      setCreated(t.token);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="screen">
      <header className="screen-head">
        <h2>Tenants</h2>
        <span className="muted small">one per integrating system</span>
      </header>

      <div className="card">
        <h3>Create a tenant</h3>
        <label>
          Name
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. qrme" />
        </label>
        <label>
          Record retention (up to forever)
          <select value={retention} onChange={(e) => setRetention(e.target.value)}>
            {["forever", "1y", "180d", "90d", "30d", "7d"].map((w) => <option key={w}>{w}</option>)}
          </select>
        </label>
        <button className="primary" onClick={create} disabled={busy}>
          {busy ? "Creating…" : "Create tenant"}
        </button>
        {error && <div className="error">⚠ {error}</div>}
      </div>

      {created && (
        <div className="card warn-card">
          <h3>Token — shown once</h3>
          <p className="muted small">Only its SHA-256 hash is stored. It's now this session's active tenant.</p>
          <pre className="mono token">{created}</pre>
        </div>
      )}

      {session.tenantName && (
        <div className="tile wide">
          <div className="tile-label">Active tenant</div>
          <div className="tile-value cyan">{session.tenantName}</div>
          <div className="tile-sub">{session.tenantId}</div>
        </div>
      )}
    </div>
  );
}
