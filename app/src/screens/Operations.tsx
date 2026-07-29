import { useEffect, useState } from "react";
import { api, OperationsEntry } from "../api";
import { useSession } from "../store";

// The operations journal: coordination records QRME sealed into this
// tenant's vault, readable in place. A view, never a side door — every
// entry shown here was read through the ordinary audited path, so the
// audit chain carries these reads like any others.
export function Operations() {
  const { session } = useSession();
  const [entries, setEntries] = useState<OperationsEntry[]>([]);
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!session.tenantToken) return;
    api.operations(session.tenantToken)
      .then((r) => { setEntries(r.entries); setNote(r.note); })
      .catch((e) => setError((e as Error).message));
  }, [session.tenantToken]);

  if (!session.tenantToken) {
    return <div className="screen"><p className="muted center">
      Select a tenant first — the journal opens with the tenant's own token.</p></div>;
  }

  return (
    <div className="screen">
      <header className="screen-head">
        <h2>Operations</h2>
        <span className="muted small">coordination plans QRME sealed here — every read audited</span>
      </header>

      {entries.length === 0 && (
        <div className="card">
          <p className="muted center">
            Nothing yet. When QRME's departments coordinate with the tandem
            configured, each joint plan seals into this vault and appears
            here.
          </p>
        </div>
      )}

      {entries.slice().reverse().map((e) => (
        <div key={e.key} className="card">
          <h3>{e.goal || e.key}</h3>
          {e.org && <p className="muted small">{e.org}
            {e.departments.length > 0 && <> · {e.departments.join(" · ")}</>}</p>}
          {e.plan && <p style={{ whiteSpace: "pre-wrap" }}>{e.plan}</p>}
          <p className="muted small">{e.key} · {new Date(e.updated_at).toLocaleString()}</p>
        </div>
      ))}

      {note && <p className="muted small">{note}</p>}
      {error && <div className="error">⚠ {error}</div>}
    </div>
  );
}
