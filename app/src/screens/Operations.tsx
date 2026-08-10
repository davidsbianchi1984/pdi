import { useEffect, useState } from "react";
import { api, OperationsEntry, ProvenanceOut } from "../api";
import { useSession } from "../store";
import { deviceLanguage, Lang, t } from "../l10n";

// The operations journal: coordination records QRME sealed into this
// tenant's vault, readable in place. A view, never a side door — every
// entry shown here was read through the ordinary audited path, so the
// audit chain carries these reads like any others.
export function Operations() {
  const { session } = useSession();
  const lang = (session.language as Lang) ?? deviceLanguage();
  const [entries, setEntries] = useState<OperationsEntry[]>([]);
  const [proof, setProof] = useState<Record<string, ProvenanceOut>>({});
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
      {t("op.pick", lang)}</p></div>;
  }

  return (
    <div className="screen">
      <header className="screen-head">
        <h2>{t("op.title", lang)}</h2>
        <span className="muted small">{t("op.sub", lang)}</span>
      </header>

      {entries.length === 0 && (
        <div className="card">
          <p className="muted center">
            {t("op.none", lang)}
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
          {!proof[e.key] && (
            <button onClick={() =>
              api.provenance(e.key, session.tenantToken!)
                .then((p) => setProof((x) => ({ ...x, [e.key]: p })))
                .catch((err) => setError((err as Error).message))
            }>{t("op.prove", lang)}</button>
          )}
          {proof[e.key] && (
            <p className="muted small">
              {proof[e.key].origin} · {proof[e.key].sealed.cipher.split(" (")[0]} ·{" "}
              {proof[e.key].audit.count} {t("op.events", lang)}{" "}
              {proof[e.key].chain.intact === false ? "BROKEN" : "intact"}
            </p>
          )}
        </div>
      ))}

      {note && <p className="muted small">{note}</p>}
      {error && <div className="error">⚠ {error}</div>}
    </div>
  );
}
