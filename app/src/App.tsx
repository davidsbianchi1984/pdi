import { useState } from "react";
import { useSession } from "./store";
import { deviceLanguage, Lang, t } from "./l10n";
import { ProblemNotice } from "./ProblemNotice";
import { VersionGuard } from "./VersionGuard";
import { VaultLight } from "./VaultLight";
import { Overview } from "./screens/Overview";
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

type Tab = "overview" | "tenants" | "records" | "exchange" | "carriers" | "bridges" | "operations" | "continuity" | "positions" | "keys" | "custody" | "audit" | "guiding" | "settings";
const NAV: { id: Tab; label: string; icon: string }[] = [
  { id: "overview", label: "Overview", icon: "▦" },
  { id: "tenants", label: "Tenants", icon: "👥" },
  { id: "records", label: "Vault", icon: "🔒" },
  { id: "exchange", label: "Exchange", icon: "📦" },
  { id: "carriers", label: "Carriers", icon: "🏷" },
  { id: "bridges", label: "Bridges", icon: "🔌" },
  { id: "operations", label: "Operations", icon: "📓" },
  { id: "continuity", label: "Continuity", icon: "🕯" },
  { id: "positions", label: "Positions", icon: "🧭" },
  { id: "keys", label: "Keys & Retention", icon: "🗝" },
  { id: "custody", label: "Custody", icon: "⚖" },
  { id: "audit", label: "Audit", icon: "✓" },
  { id: "guiding", label: "Guiding", icon: "🧑‍🏫" },
  { id: "settings", label: "Settings", icon: "⚙" },
];

export function App() {
  const { session } = useSession();
  const lang = (session.language as Lang) ?? deviceLanguage();
  const [tab, setTab] = useState<Tab>("overview");
  return (
    <div className="app">
      <VersionGuard />
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
              {n.label}
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
        {tab === "settings" && <Settings />}
      </main>
      {/* Part of the shell, on every screen — the vault's one light,
          minimizable, and never silently absent. */}
      <VaultLight />
    </div>
  );
}
