import { useState } from "react";
import { useSession } from "./store";
import { Overview } from "./screens/Overview";
import { Tenants } from "./screens/Tenants";
import { Records } from "./screens/Records";
import { Keys } from "./screens/Keys";
import { Audit } from "./screens/Audit";
import { Settings } from "./screens/Settings";

type Tab = "overview" | "tenants" | "records" | "keys" | "audit" | "settings";
const NAV: { id: Tab; label: string; icon: string }[] = [
  { id: "overview", label: "Overview", icon: "▦" },
  { id: "tenants", label: "Tenants", icon: "👥" },
  { id: "records", label: "Vault", icon: "🔒" },
  { id: "keys", label: "Keys & Retention", icon: "🗝" },
  { id: "audit", label: "Audit", icon: "✓" },
  { id: "settings", label: "Settings", icon: "⚙" },
];

export function App() {
  const { session } = useSession();
  const [tab, setTab] = useState<Tab>("overview");
  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <span className="orb" />
          <div>
            <div className="brand-name">PDI</div>
            <div className="brand-sub">Private Data Infrastructure</div>
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
            <span className="muted small">no tenant selected</span>
          )}
        </div>
      </aside>
      <main className="content">
        {tab === "overview" && <Overview go={setTab} />}
        {tab === "tenants" && <Tenants />}
        {tab === "records" && <Records go={setTab} />}
        {tab === "keys" && <Keys />}
        {tab === "audit" && <Audit />}
        {tab === "settings" && <Settings />}
      </main>
    </div>
  );
}
