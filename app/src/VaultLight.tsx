import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import { deviceLanguage, Lang, t } from "./l10n";
import { useSession } from "./store";

/**
 * The vault's light, always on screen — the sibling of QRME's agent
 * lights and JIM's Guardian lights, sized down to what this product
 * honestly has to glance at: one process, answering or not. Green is the
 * vault answering (with its version, so a stale backend is visible at a
 * glance next to the console's own); unreachable is a state the light
 * shows, not one it hides in — the lesson QRME's widget paid for: a
 * failed first fetch renders an unlit dot that retries on press.
 */

const POLL_MS = 15000;
const MIN_KEY = "pdi.lights.min";

export function VaultLight() {
  const { session } = useSession();
  const lang = (session.language as Lang) ?? deviceLanguage();
  const [health, setHealth] = useState<{ status: string;
    version?: string } | null>(null);
  const [unreachable, setUnreachable] = useState(false);
  const [min, setMin] = useState(() => localStorage.getItem(MIN_KEY) === "1");

  const load = useCallback(() => {
    api.health()
      .then((h) => { setHealth(h); setUnreachable(false); })
      .catch(() => setUnreachable(true)); // keep any last answer
  }, []);

  useEffect(() => {
    load();
    const timer = setInterval(load, POLL_MS);
    return () => clearInterval(timer);
  }, [load]);

  if (!health) {
    if (!unreachable) return null;
    return (
      <button className="vl-dot vl-dot-off"
              onClick={load}
              aria-label={t("vl.unreachable", lang)}
              title={t("vl.unreachable", lang)}>
        <span className="vl-dot-face" />
      </button>
    );
  }

  const ok = health.status === "ok";
  const color = ok ? "#43e08a" : "#e0687a";

  const setMinimized = (v: boolean) => {
    setMin(v);
    if (v) localStorage.setItem(MIN_KEY, "1");
    else localStorage.removeItem(MIN_KEY);
  };

  if (min) {
    return (
      <button className="vl-dot"
              onClick={() => setMinimized(false)}
              aria-label={t("vl.show", lang)} title={t("vl.title", lang)}>
        <span className="vl-dot-face" style={{ background: color }} />
      </button>
    );
  }

  return (
    <div className="vault-light" role="status" aria-label={t("vl.title", lang)}
         style={{ borderColor: color }}>
      <span className="vl-lamp" style={{ background: color }} />
      <span className="vl-text">
        {ok ? t("vl.answering", lang) : t("vl.degraded", lang)}
        {health.version ? ` · v${health.version}` : ""}
      </span>
      <button className="vl-min" onClick={() => setMinimized(true)}
              aria-label={t("vl.min", lang)}>–</button>
    </div>
  );
}
