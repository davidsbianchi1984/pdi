import { useEffect, useState } from "react";
import { useSession } from "./store";
import { deviceLanguage, Lang, t } from "./l10n";
import { ProblemNotice } from "./ProblemNotice";
import { Footsteps } from "./Footsteps";
import { VersionGuard } from "./VersionGuard";
import { VaultLight } from "./VaultLight";
import { Overview } from "./screens/Overview";
import { Resident } from "./screens/Resident";
import { Tenants } from "./screens/Tenants";
import { Records } from "./screens/Records";
import { Continuity } from "./screens/Continuity";
import { Operations } from "./screens/Operations";
import { Positions } from "./screens/Positions";
import { Keys } from "./screens/Keys";
import { Audit } from "./screens/Audit";
import { Settings } from "./screens/Settings";
import { Carriers } from "./screens/Carriers";
import { Exchange } from "./screens/Exchange";
import { Custody } from "./screens/Custody";
import { Bridges } from "./screens/Bridges";
import { Guiding } from "./screens/Guiding";
import { Access } from "./screens/Access";

type Tab = "overview" | "resident" | "tenants" | "records" | "exchange" | "carriers" | "bridges" | "operations" | "continuity" | "positions" | "keys" | "custody" | "audit" | "guiding" | "access" | "settings";
// Labels live in l10n.ts as `nav.{id}` — the sidebar reads in the visitor's
// language like everything it leads to, so a screen reader pronounces the
// tab names in the language the page declares.
const NAV: { id: Tab; icon: string }[] = [
  { id: "overview", icon: "▦" },
  { id: "tenants", icon: "👥" },
  { id: "records", icon: "🔒" },
  { id: "exchange", icon: "📦" },
  { id: "carriers", icon: "🏷" },
  { id: "bridges", icon: "🔌" },
  { id: "operations", icon: "📓" },
  { id: "continuity", icon: "🕯" },
  { id: "positions", icon: "🧭" },
  { id: "keys", icon: "🗝" },
  { id: "custody", icon: "⚖" },
  { id: "audit", icon: "✓" },
  { id: "guiding", icon: "🧑‍🏫" },
  { id: "resident", icon: "🧠" },
  { id: "access", icon: "♿" },
  { id: "settings", icon: "⚙" },
];

export function App() {
  const { session } = useSession();
  const lang = (session.language as Lang) ?? deviceLanguage();
  const [tab, setTab] = useState<Tab>("overview");
  // The document's own language attribute, so a screen reader pronounces
  // the page in the language it is actually written in — index.html ships
  // lang="en" and the app renders ten languages under it.
  useEffect(() => { document.documentElement.lang = lang; }, [lang]);
  return (
    <div className="app">
      <VersionGuard />
      <Footsteps />
      <aside className="sidebar">
        <div className="brand">
          <span className="orb" />
          <div>
            <div className="brand-name">PDI</div>
            <div className="brand-sub">{t("app.sub", lang)}</div>
          </div>
        </div>
        <nav>
          {NAV.map((n) => (
            <button
              key={n.id}
              className={"nav-item" + (tab === n.id ? " active" : "")}
              onClick={() => setTab(n.id)}
            >
              <span className="nav-icon">{n.icon}</span>
              {t(`nav.${n.id}`, lang)}
            </button>
          ))}
        </nav>
        <div className="tenant-chip">
          {session.tenantName ? (
            <>
              <span className="dot-online">●</span> {session.tenantName}
            </>
          ) : (
            <span className="muted small">{t("app.notenant", lang)}</span>
          )}
        </div>
      </aside>
      <main className="content">
        <ProblemNotice />
        {tab === "overview" && <Overview go={setTab} />}
        {tab === "tenants" && <Tenants />}
        {tab === "records" && <Records go={setTab} />}
        {tab === "operations" && <Operations />}
        {tab === "continuity" && <Continuity />}
        {tab === "positions" && <Positions go={setTab} />}
        {tab === "keys" && <Keys />}
        {tab === "audit" && <Audit />}
        {tab === "carriers" && <Carriers />}
        {tab === "exchange" && <Exchange />}
        {tab === "custody" && <Custody />}
        {tab === "bridges" && <Bridges />}
        {tab === "guiding" && <Guiding />}
        {tab === "resident" && <Resident />}
        {tab === "access" && <Access />}
        {tab === "settings" && <Settings />}
      </main>
      {/* Part of the shell, on every screen — the vault's one light,
          minimizable, and never silently absent. */}
      <VaultLight />
    </div>
  );
}
