import { useEffect, useState } from "react";
import { api } from "../api";
import { useSession } from "../store";

export function Records({ go }: { go: (t: "tenants") => void }) {
  const { session } = useSession();
  const [keys, setKeys] = useState<string[]>([]);
  const [key, setKey] = useState("records/med/contact");
  const [value, setValue] = useState("Maria Bianchi · +1 415 555 0199");
  const [opened, setOpened] = useState<{ key: string; value: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    if (!session.tenantToken) return;
    try {
      setKeys((await api.listKeys(session.tenantToken)).keys);
    } catch (e) {
      setError((e as Error).message);
    }
  }
  useEffect(() => {
    refresh();
  }, [session.tenantToken]);

  if (!session.tenantToken) {
    return (
      <div className="screen">
        <header className="screen-head"><h2>Vault</h2></header>
        <div className="card">
          <p className="muted">No tenant selected — create or select one first.</p>
          <button className="primary" onClick={() => go("tenants")}>Go to Tenants</button>
        </div>
      </div>
    );
  }

  async function seal() {
    setError(null);
    try {
      await api.putRecord(key, value, session.tenantToken!);
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function open(k: string) {
    setError(null);
    try {
      const r = await api.getRecord(k, session.tenantToken!);
      setOpened({ key: r.key, value: r.value });
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="screen">
      <header className="screen-head">
        <h2>Vault</h2>
        <span className="muted small">records sealed at rest · AES-256-GCM · {session.tenantName}</span>
      </header>

      <div className="card">
        <h3>Seal a record</h3>
        <label>Key<input value={key} onChange={(e) => setKey(e.target.value)} /></label>
        <label>Value (plaintext — sealed by PDI)<input value={value} onChange={(e) => setValue(e.target.value)} /></label>
        <button className="primary" onClick={seal}>Seal record</button>
        {error && <div className="error">⚠ {error}</div>}
      </div>

      <div className="card">
        <h3>Records <span className="muted small">({keys.length})</span></h3>
        {keys.length === 0 && <div className="muted">No records yet.</div>}
        <ul className="keylist">
          {keys.map((k) => (
            <li key={k}>
              <span className="mono">🔒 {k}</span>
              <button onClick={() => open(k)}>Open</button>
            </li>
          ))}
        </ul>
      </div>

      {opened && (
        <div className="card">
          <h3>Decrypted</h3>
          <div className="muted small mono">{opened.key}</div>
          <pre className="mono cyan">{opened.value}</pre>
        </div>
      )}
    </div>
  );
}
