import { useEffect, useState } from "react";
import { api, CONSOLE_VERSION, clearBase, getBase } from "./api";
import { useSession } from "./store";
import { deviceLanguage, fill, Lang, t } from "./l10n";

/**
 * The version handshake, made visible.
 *
 * A stale backend from an older install answers /health perfectly well and
 * then serves an older API — so the app looks alive while every newer
 * screen (the operations journal, positions) answers "Not Found" with
 * no explanation. The Electron shell already refuses to adopt a
 * version-mismatched backend on its own port, but a *stored* base URL (for
 * example the machine's LAN address saved for the phone bridge) can still
 * route the console to whatever old process holds that address.
 *
 * This banner closes the loop from the console side: compare the console's
 * build version against what /health reports, and on mismatch say so in a
 * sentence, with the one-click fix when there is one.
 */
export function VersionGuard() {
  const { session } = useSession();
  const [backend, setBackend] = useState<string | null>(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    let alive = true;
    api.health()
      // A backend so old it predates the version field is exactly the case.
      .then((h) => { if (alive) setBackend(h.version || "(older than 0.5)"); })
      .catch(() => { /* unreachable is the connection panel's story */ });
    return () => { alive = false; };
  }, []);

  if (dismissed || backend === null || backend === CONSOLE_VERSION) return null;

  const lang = (session.language as Lang) ?? deviceLanguage();

  const desktop = (window as {
    pdiDesktop?: { backendUrl?: string | null } }).pdiDesktop?.backendUrl;
  const stored = typeof localStorage !== "undefined"
    ? localStorage.getItem("pdi.base") : null;
  // The one-click cure: when this app started its own backend but a stored
  // address is steering the console elsewhere, drop the address and reload.
  const canRepoint = Boolean(desktop && stored);

  return (
    <div className="version-guard" role="alert">
      <span>
        <b>{t("vg.two", lang)}</b>{" "}
        {fill("vg.mismatch", lang, { console: CONSOLE_VERSION,
                                     base: getBase(), backend })}
      </span>
      {canRepoint ? (
        <button className="vg-fix"
                onClick={() => { clearBase(); location.reload(); }}>
          {t("vg.useown", lang)}
        </button>
      ) : (
        <span className="vg-hint">{t("vg.quit", lang)}</span>
      )}
      <button className="vg-close" onClick={() => setDismissed(true)}
              aria-label={t("vg.dismiss", lang)}>×</button>
    </div>
  );
}
