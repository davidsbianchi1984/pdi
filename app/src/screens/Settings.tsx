import { useState } from "react";
import { getBase, setBase } from "../api";
import { useSession } from "../store";

export function Settings() {
  const { session, setSession, clear } = useSession();
  const [base, setBaseInput] = useState(getBase());
  const [admin, setAdmin] = useState(session.adminToken || "");
  const [saved, setSaved] = useState(false);

  function save() {
    setBase(base);
    setSession({ adminToken: admin || undefined });
    setSaved(true);
    setTimeout(() => setSaved(false), 1500);
  }

  return (
    <div className="screen">
      <header className="screen-head"><h2>Settings</h2></header>
      <div className="card">
        <h3>Connection</h3>
        <label>Backend base URL<input value={base} onChange={(e) => setBaseInput(e.target.value)} /></label>
        <label>
          Admin token <span className="muted small">(leave blank if the backend runs open, dev mode)</span>
          <input value={admin} onChange={(e) => setAdmin(e.target.value)} placeholder="PDI_ADMIN_TOKEN" />
        </label>
        <button className="primary" onClick={save}>{saved ? "Saved ✓" : "Save"}</button>
      </div>
      <div className="card">
        <h3>Session</h3>
        <div className="muted small">Tenant: {session.tenantName || "none"}</div>
        <button className="danger" onClick={clear}>Sign out</button>
      </div>
    </div>
  );
}
