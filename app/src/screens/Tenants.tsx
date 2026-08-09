import { useState } from "react";
import { api } from "../api";
import { useSession } from "../store";
import { deviceLanguage, Lang, t } from "../l10n";

export function Tenants() {
  const { session, setSession } = useSession();
  const lang = (session.language as Lang) ?? deviceLanguage();
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
      // Not `t` — that is the translator, and this binding would shadow it.
      const made = await api.createTenant(name.trim(), retention, session.adminToken);
      setSession({ tenantId: made.id, tenantName: made.name, tenantToken: made.token });
      setCreated(made.token);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="screen">
      <header className="screen-head">
        <h2>{t("tn.title", lang)}</h2>
        <span className="muted small">{t("tn.sub", lang)}</span>
      </header>

      <div className="card">
        <h3>{t("tn.create", lang)}</h3>
        <label>
          {t("co.name.ph", lang)}
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. qrme" />
        </label>
        <label>
          {t("tn.retention", lang)}
          <select value={retention} onChange={(e) => setRetention(e.target.value)}>
            {["forever", "1y", "180d", "90d", "30d", "7d"].map((w) => <option key={w}>{w}</option>)}
          </select>
        </label>
        <button className="primary" onClick={create} disabled={busy}>
          {busy ? t("tn.creating", lang) : t("tn.createbtn", lang)}
        </button>
        {error && <div className="error">⚠ {error}</div>}
      </div>

      {created && (
        <div className="card warn-card">
          <h3>{t("tn.token", lang)}</h3>
          <p className="muted small">{t("tn.token.note", lang)}</p>
          <pre className="mono token">{created}</pre>
        </div>
      )}

      {session.tenantName && (
        <div className="tile wide">
          <div className="tile-label">{t("tn.active", lang)}</div>
          <div className="tile-value cyan">{session.tenantName}</div>
          <div className="tile-sub">{session.tenantId}</div>
        </div>
      )}
    </div>
  );
}
