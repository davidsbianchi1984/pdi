import { useEffect, useState } from "react";
import { api } from "../api";
import { useSession } from "../store";
import { deviceLanguage, Lang, t } from "../l10n";

export function Records({ go }: { go: (tab: "tenants") => void }) {
  const { session } = useSession();
  const lang = (session.language as Lang) ?? deviceLanguage();
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
        <header className="screen-head"><h2>{t("rec.vault", lang)}</h2></header>
        <div className="card">
          <p className="muted">{t("pos.notenant", lang)}</p>
          <button className="primary" onClick={() => go("tenants")}>
            {t("pos.gotenants", lang)}
          </button>
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
        <h2>{t("rec.vault", lang)}</h2>
        <span className="muted small">
          {t("rec.atrest", lang)} {session.tenantName}
        </span>
      </header>

      <div className="card">
        <h3>{t("rec.seal.head", lang)}</h3>
        <label>{t("rec.key", lang)}
          <input value={key} onChange={(e) => setKey(e.target.value)} />
        </label>
        <label>{t("rec.value.ph", lang)}
          <input value={value} onChange={(e) => setValue(e.target.value)} />
        </label>
        <button className="primary" onClick={seal}>{t("rec.seal", lang)}</button>
        {error && <div className="error">⚠ {error}</div>}
      </div>

      <div className="card">
        <h3>{t("rec.title", lang)} <span className="muted small">({keys.length})</span></h3>
        {keys.length === 0 && <div className="muted">{t("rec.none", lang)}</div>}
        <ul className="keylist">
          {keys.map((k) => (
            <li key={k}>
              <span className="mono">🔒 {k}</span>
              <button onClick={() => open(k)}>{t("pos.open", lang)}</button>
            </li>
          ))}
        </ul>
      </div>

      {opened && (
        <div className="card">
          <h3>{t("rec.decrypted", lang)}</h3>
          <div className="muted small mono">{opened.key}</div>
          <pre className="mono cyan">{opened.value}</pre>
        </div>
      )}
    </div>
  );
}
