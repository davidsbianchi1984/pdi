import { useEffect, useState } from "react";
import { api, Blueprint, PositionIntake } from "../api";
import { useSession } from "../store";

// The AI Integration & Role-Mapping Questionnaire, condensed to the signals the
// builder acts on. Industry-agnostic — the operator types their own industry.
const CAP_OPTIONS = [
  ["task_tracking", "Real-time task tracking"],
  ["doc_drafting", "Document drafting & data entry"],
  ["report_generation", "Routine report generation"],
  ["compliance_logging", "Compliance logging & checklists"],
  ["scheduling", "Employee scheduling suggestions"],
  ["maintenance_alerts", "Maintenance & incident alerts"],
  ["log_summaries", "Daily activity-log summaries"],
  ["decision_support", "Decision suggestions in your style"],
] as const;

const DECISION_SCOPE = ["routes", "staffing", "incident", "contracts", "budget"];
const MANAGES = ["scheduling", "timekeeping", "dispatch", "inventory"];

function Chips({ options, value, onChange }: {
  options: readonly string[]; value: string[]; onChange: (v: string[]) => void;
}) {
  const toggle = (o: string) =>
    onChange(value.includes(o) ? value.filter((x) => x !== o) : [...value, o]);
  return (
    <div className="chips">
      {options.map((o) => (
        <button key={o} type="button"
          className={"chip" + (value.includes(o) ? " on" : "")}
          onClick={() => toggle(o)}>{o}</button>
      ))}
    </div>
  );
}

export function Positions({ go }: { go: (t: "tenants") => void }) {
  const { session } = useSession();
  const [ids, setIds] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [bp, setBp] = useState<Blueprint | null>(null);

  // intake state
  const [industry, setIndustry] = useState("public transit");
  const [jobTitle, setJobTitle] = useState("Station Supervisor");
  const [department, setDepartment] = useState("Operations");
  const [roleType, setRoleType] = useState("supervisory");
  const [managesStaff, setManagesStaff] = useState(12);
  const [manages, setManages] = useState<string[]>(["scheduling", "dispatch"]);
  const [documentsIncidents, setDocumentsIncidents] = useState(true);
  const [manualTasks, setManualTasks] = useState(true);
  const [scope, setScope] = useState<string[]>(["staffing", "incident", "budget"]);
  const [redundant, setRedundant] = useState("manual headcount entry");
  const [outdated, setOutdated] = useState("paper incident forms");
  const [wants, setWants] = useState<string[]>(["task_tracking"]);
  const [tone, setTone] = useState("directive");
  const [interaction, setInteraction] = useState("voice");
  const [summarizeLogs, setSummarizeLogs] = useState(true);
  const [learnStyle, setLearnStyle] = useState(true);
  const [complianceAccountable, setComplianceAccountable] = useState(true);
  const [comfortable, setComfortable] = useState(true);
  const [reskilling, setReskilling] = useState(true);

  async function refresh() {
    if (!session.tenantToken) return;
    try { setIds((await api.listPositions(session.tenantToken)).ids); }
    catch (e) { setError((e as Error).message); }
  }
  useEffect(() => { refresh(); }, [session.tenantToken]);

  if (!session.tenantToken) {
    return (
      <div className="screen">
        <header className="screen-head"><h2>Positions</h2></header>
        <div className="card">
          <p className="muted">No tenant selected — create or select one first.</p>
          <button className="primary" onClick={() => go("tenants")}>Go to Tenants</button>
        </div>
      </div>
    );
  }

  const split = (s: string) => s.split(",").map((x) => x.trim()).filter(Boolean);

  async function build() {
    setError(null);
    const intake: PositionIntake = {
      industry,
      role: { job_title: jobTitle, department, role_type: roleType, manages_staff: managesStaff },
      workflow: { manages, documents_incidents: documentsIncidents, manual_tasks: manualTasks },
      decisions: { scope },
      bottlenecks: { redundant_tasks: split(redundant), outdated_tasks: split(outdated) },
      preferences: { wants, tone, interaction, summarize_logs: summarizeLogs, learn_decision_style: learnStyle },
      admin: { compliance_accountable: complianceAccountable },
      future: { comfortable_automation: comfortable, reskilling_interest: reskilling },
    };
    try {
      const b = await api.buildPosition(intake, session.tenantToken!);
      setBp(b);
      await refresh();
    } catch (e) { setError((e as Error).message); }
  }

  async function load(id: string) {
    setError(null);
    try { setBp(await api.getPosition(id, session.tenantToken!)); }
    catch (e) { setError((e as Error).message); }
  }

  return (
    <div className="screen">
      <header className="screen-head">
        <h2>Positions</h2>
        <span className="muted small">
          AI Integration &amp; Role-Mapping · answers sealed in the vault · {session.tenantName}
        </span>
      </header>

      <div className="card">
        <h3>Role &amp; industry</h3>
        <div className="grid2">
          <label>Industry<input value={industry} onChange={(e) => setIndustry(e.target.value)} /></label>
          <label>Job title<input value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} /></label>
          <label>Department<input value={department} onChange={(e) => setDepartment(e.target.value)} /></label>
          <label>Oversight level
            <select value={roleType} onChange={(e) => setRoleType(e.target.value)}>
              {["frontline", "administrative", "supervisory", "executive"].map((o) =>
                <option key={o} value={o}>{o}</option>)}
            </select>
          </label>
          <label>Staff managed
            <input type="number" value={managesStaff}
              onChange={(e) => setManagesStaff(Number(e.target.value) || 0)} />
          </label>
        </div>
      </div>

      <div className="card">
        <h3>Daily workflow</h3>
        <span className="muted small">What this role manages day-to-day</span>
        <Chips options={MANAGES} value={manages} onChange={setManages} />
        <label className="check">
          <input type="checkbox" checked={documentsIncidents}
            onChange={(e) => setDocumentsIncidents(e.target.checked)} />
          Documents incidents / maintenance
        </label>
        <label className="check">
          <input type="checkbox" checked={manualTasks}
            onChange={(e) => setManualTasks(e.target.checked)} />
          Has manual report / data-entry tasks
        </label>
      </div>

      <div className="card">
        <h3>Decision-making &amp; oversight</h3>
        <span className="muted small">Decisions this role owns (high-stakes ones stay human-in-the-loop)</span>
        <Chips options={DECISION_SCOPE} value={scope} onChange={setScope} />
        <label className="check">
          <input type="checkbox" checked={complianceAccountable}
            onChange={(e) => setComplianceAccountable(e.target.checked)} />
          Accountable for safety / regulatory compliance
        </label>
      </div>

      <div className="card">
        <h3>Bottlenecks &amp; obsolescence</h3>
        <span className="muted small">Framed as tasks to automate — never people</span>
        <label>Redundant tasks (comma-separated)
          <input value={redundant} onChange={(e) => setRedundant(e.target.value)} /></label>
        <label>Outdated tasks (comma-separated)
          <input value={outdated} onChange={(e) => setOutdated(e.target.value)} /></label>
      </div>

      <div className="card">
        <h3>AI adoption &amp; personalization</h3>
        <span className="muted small">Assistant capabilities the operator wants</span>
        <div className="chips">
          {CAP_OPTIONS.map(([k, label]) => (
            <button key={k} type="button"
              className={"chip" + (wants.includes(k) ? " on" : "")}
              onClick={() => setWants(wants.includes(k) ? wants.filter((x) => x !== k) : [...wants, k])}
              title={label}>{label}</button>
          ))}
        </div>
        <div className="grid2">
          <label>Tone
            <select value={tone} onChange={(e) => setTone(e.target.value)}>
              {["directive", "neutral", "casual", "analytical"].map((o) =>
                <option key={o} value={o}>{o}</option>)}
            </select>
          </label>
          <label>Interaction
            <select value={interaction} onChange={(e) => setInteraction(e.target.value)}>
              {["voice", "text", "hybrid"].map((o) => <option key={o} value={o}>{o}</option>)}
            </select>
          </label>
        </div>
        <label className="check">
          <input type="checkbox" checked={summarizeLogs}
            onChange={(e) => setSummarizeLogs(e.target.checked)} />
          Summarize the daily activity log
        </label>
        <label className="check">
          <input type="checkbox" checked={learnStyle}
            onChange={(e) => setLearnStyle(e.target.checked)} />
          Learn my decision-making style (suggest, never take, actions)
        </label>
        <label className="check">
          <input type="checkbox" checked={comfortable}
            onChange={(e) => setComfortable(e.target.checked)} />
          Comfortable with phased automation
        </label>
        <label className="check">
          <input type="checkbox" checked={reskilling}
            onChange={(e) => setReskilling(e.target.checked)} />
          Interested in reskilling / repositioning
        </label>
        <button className="primary" onClick={build}>Build assistant blueprint</button>
        {error && <div className="error">⚠ {error}</div>}
      </div>

      {bp && <BlueprintCard bp={bp} />}

      <div className="card">
        <h3>Saved positions <span className="muted small">({ids.length})</span></h3>
        {ids.length === 0 && <div className="muted">None yet.</div>}
        <ul className="keylist">
          {ids.map((id) => (
            <li key={id}>
              <span className="mono">🧭 {id}</span>
              <button onClick={() => load(id)}>Open</button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function BlueprintCard({ bp }: { bp: Blueprint }) {
  const pct = Math.round(bp.automation.opportunity_score * 100);
  return (
    <div className="card">
      <h3>Assistant blueprint</h3>
      <div className="muted small">
        {bp.role.job_title} · {bp.industry} · {bp.role.oversight_level} ·
        {" "}{bp.assistant.tone} / {bp.assistant.interaction}
      </div>

      <h4>Capabilities</h4>
      <ul className="keylist">
        {bp.assistant.capabilities.map((c) => (
          <li key={c.key}>
            <span>✓ {c.label}</span>
            <span className="muted small">{c.why}</span>
          </li>
        ))}
      </ul>

      <h4>Automation opportunity <span className="muted small">({pct}%)</span></h4>
      <div className="meter"><span style={{ width: `${pct}%` }} /></div>
      {bp.automation.opportunities.length > 0 && (
        <p className="muted small">Tasks: {bp.automation.opportunities.join(", ")}</p>
      )}
      <p className="muted small">{bp.automation.note}</p>

      <h4>Human-in-the-loop</h4>
      {bp.human_in_loop.required.length === 0
        ? <p className="muted small">None flagged.</p>
        : <ul className="keylist">
            {bp.human_in_loop.required.map((r) => <li key={r}><span>🔒 {r}</span></li>)}
          </ul>}
      <p className="muted small">{bp.human_in_loop.note}</p>

      {bp.reskilling.interested && bp.reskilling.suggested_paths.length > 0 && (
        <>
          <h4>Reskilling paths</h4>
          <ul className="keylist">
            {bp.reskilling.suggested_paths.map((p) => <li key={p}><span>↗ {p}</span></li>)}
          </ul>
        </>
      )}

      <h4>Assistant system-prompt</h4>
      <pre className="mono cyan">{bp.assistant_spec}</pre>
    </div>
  );
}
