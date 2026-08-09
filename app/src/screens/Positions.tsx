import { useEffect, useState } from "react";
import { api, Blueprint, PositionIntake } from "../api";
import { deviceLanguage, fill, Lang, t } from "../l10n";
import { useSession } from "../store";

// The AI Integration & Role-Mapping Questionnaire, condensed to the signals the
// builder acts on. Industry-agnostic — the operator types their own industry.
// The keys are what the builder acts on; the words are what the operator
// reads. Keeping them apart is why a Spanish console can send `staffing`.
const CAP_OPTIONS = ["task_tracking", "doc_drafting", "report_generation",
  "compliance_logging", "scheduling", "maintenance_alerts", "log_summaries",
  "decision_support"] as const;

const DECISION_SCOPE = ["routes", "staffing", "incident", "contracts", "budget"];
const MANAGES = ["scheduling", "timekeeping", "dispatch", "inventory"];
const OVERSIGHT = ["frontline", "administrative", "supervisory", "executive"];
const TONES = ["directive", "neutral", "casual", "analytical"];
const INTERACTIONS = ["voice", "text", "hybrid"];

function Chips({ options, value, onChange, label }: {
  options: readonly string[]; value: string[]; onChange: (v: string[]) => void;
  label: (o: string) => string;
}) {
  const toggle = (o: string) =>
    onChange(value.includes(o) ? value.filter((x) => x !== o) : [...value, o]);
  return (
    <div className="chips">
      {options.map((o) => (
        <button key={o} type="button"
          className={"chip" + (value.includes(o) ? " on" : "")}
          onClick={() => toggle(o)}>{label(o)}</button>
      ))}
    </div>
  );
}

export function Positions({ go }: { go: (t: "tenants") => void }) {
  const { session } = useSession();
  const lang = (session.language as Lang) ?? deviceLanguage();
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
        <header className="screen-head"><h2>{t("pos.title", lang)}</h2></header>
        <div className="card">
          <p className="muted">{t("pos.notenant", lang)}</p>
          <button className="primary" onClick={() => go("tenants")}>
            {t("pos.gotenants", lang)}</button>
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
        <h2>{t("pos.title", lang)}</h2>
        <span className="muted small">
          {fill("pos.sub", lang, { name: session.tenantName ?? "" })}
        </span>
      </header>

      <div className="card">
        <h3>{t("pos.role", lang)}</h3>
        <div className="grid2">
          <label>{t("pos.industry", lang)}<input value={industry} onChange={(e) => setIndustry(e.target.value)} /></label>
          <label>{t("pos.jobtitle", lang)}<input value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} /></label>
          <label>{t("pos.department", lang)}<input value={department} onChange={(e) => setDepartment(e.target.value)} /></label>
          <label>{t("pos.oversight", lang)}
            <select value={roleType} onChange={(e) => setRoleType(e.target.value)}>
              {OVERSIGHT.map((o) =>
                <option key={o} value={o}>{t("pos.oversight." + o, lang)}</option>)}
            </select>
          </label>
          <label>{t("pos.staff", lang)}
            <input type="number" value={managesStaff}
              onChange={(e) => setManagesStaff(Number(e.target.value) || 0)} />
          </label>
        </div>
      </div>

      <div className="card">
        <h3>{t("pos.workflow", lang)}</h3>
        <span className="muted small">{t("pos.workflow.sub", lang)}</span>
        <Chips options={MANAGES} value={manages} onChange={setManages}
               label={(o) => t("pos.manages." + o, lang)} />
        <label className="check">
          <input type="checkbox" checked={documentsIncidents}
            onChange={(e) => setDocumentsIncidents(e.target.checked)} />
          {t("pos.incidents", lang)}
        </label>
        <label className="check">
          <input type="checkbox" checked={manualTasks}
            onChange={(e) => setManualTasks(e.target.checked)} />
          {t("pos.manual", lang)}
        </label>
      </div>

      <div className="card">
        <h3>{t("pos.decisions", lang)}</h3>
        <span className="muted small">{t("pos.decisions.sub", lang)}</span>
        <Chips options={DECISION_SCOPE} value={scope} onChange={setScope}
               label={(o) => t("pos.scope." + o, lang)} />
        <label className="check">
          <input type="checkbox" checked={complianceAccountable}
            onChange={(e) => setComplianceAccountable(e.target.checked)} />
          {t("pos.compliance", lang)}
        </label>
      </div>

      <div className="card">
        <h3>{t("pos.bottlenecks", lang)}</h3>
        <span className="muted small">{t("pos.bottlenecks.sub", lang)}</span>
        <label>{t("pos.redundant", lang)}
          <input value={redundant} onChange={(e) => setRedundant(e.target.value)} /></label>
        <label>{t("pos.outdated", lang)}
          <input value={outdated} onChange={(e) => setOutdated(e.target.value)} /></label>
      </div>

      <div className="card">
        <h3>{t("pos.adoption", lang)}</h3>
        <span className="muted small">{t("pos.adoption.sub", lang)}</span>
        <div className="chips">
          {CAP_OPTIONS.map((k) => (
            <button key={k} type="button"
              className={"chip" + (wants.includes(k) ? " on" : "")}
              onClick={() => setWants(wants.includes(k) ? wants.filter((x) => x !== k) : [...wants, k])}
              title={t("pos.cap." + k, lang)}>{t("pos.cap." + k, lang)}</button>
          ))}
        </div>
        <div className="grid2">
          <label>{t("pos.tone", lang)}
            <select value={tone} onChange={(e) => setTone(e.target.value)}>
              {TONES.map((o) =>
                <option key={o} value={o}>{t("pos.tone." + o, lang)}</option>)}
            </select>
          </label>
          <label>{t("pos.interaction", lang)}
            <select value={interaction} onChange={(e) => setInteraction(e.target.value)}>
              {INTERACTIONS.map((o) =>
                <option key={o} value={o}>{t("pos.interaction." + o, lang)}</option>)}
            </select>
          </label>
        </div>
        <label className="check">
          <input type="checkbox" checked={summarizeLogs}
            onChange={(e) => setSummarizeLogs(e.target.checked)} />
          {t("pos.summarize", lang)}
        </label>
        <label className="check">
          <input type="checkbox" checked={learnStyle}
            onChange={(e) => setLearnStyle(e.target.checked)} />
          {t("pos.learnstyle", lang)}
        </label>
        <label className="check">
          <input type="checkbox" checked={comfortable}
            onChange={(e) => setComfortable(e.target.checked)} />
          {t("pos.comfortable", lang)}
        </label>
        <label className="check">
          <input type="checkbox" checked={reskilling}
            onChange={(e) => setReskilling(e.target.checked)} />
          {t("pos.reskilling", lang)}
        </label>
        <button className="primary" onClick={build}>{t("pos.build", lang)}</button>
        {error && <div className="error">⚠ {error}</div>}
      </div>

      {bp && <BlueprintCard bp={bp} lang={lang} />}

      <div className="card">
        <h3>{t("pos.saved", lang)} <span className="muted small">({ids.length})</span></h3>
        {ids.length === 0 && <div className="muted">{t("pos.none", lang)}</div>}
        <ul className="keylist">
          {ids.map((id) => (
            <li key={id}>
              <span className="mono">🧭 {id}</span>
              <button onClick={() => load(id)}>{t("pos.open", lang)}</button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function BlueprintCard({ bp, lang }: { bp: Blueprint; lang: Lang }) {
  const pct = Math.round(bp.automation.opportunity_score * 100);
  return (
    <div className="card">
      <h3>{t("pos.blueprint", lang)}</h3>
      <div className="muted small">
        {bp.role.job_title} · {bp.industry} · {bp.role.oversight_level} ·
        {" "}{bp.assistant.tone} / {bp.assistant.interaction}
      </div>

      <h4>{t("pos.capabilities", lang)}</h4>
      <ul className="keylist">
        {bp.assistant.capabilities.map((c) => (
          <li key={c.key}>
            <span>✓ {c.label}</span>
            <span className="muted small">{c.why}</span>
          </li>
        ))}
      </ul>

      <h4>{t("pos.opportunity", lang)} <span className="muted small">({pct}%)</span></h4>
      <div className="meter"><span style={{ width: `${pct}%` }} /></div>
      {bp.automation.opportunities.length > 0 && (
        <p className="muted small">
          {fill("pos.tasks", lang,
                { list: bp.automation.opportunities.join(", ") })}</p>
      )}
      <p className="muted small">{bp.automation.note}</p>

      <h4>{t("pos.hil", lang)}</h4>
      {bp.human_in_loop.required.length === 0
        ? <p className="muted small">{t("pos.hil.none", lang)}</p>
        : <ul className="keylist">
            {bp.human_in_loop.required.map((r) => <li key={r}><span>🔒 {r}</span></li>)}
          </ul>}
      <p className="muted small">{bp.human_in_loop.note}</p>

      {bp.reskilling.interested && bp.reskilling.suggested_paths.length > 0 && (
        <>
          <h4>{t("pos.paths", lang)}</h4>
          <ul className="keylist">
            {bp.reskilling.suggested_paths.map((p) => <li key={p}><span>↗ {p}</span></li>)}
          </ul>
        </>
      )}

      <h4>{t("pos.spec", lang)}</h4>
      <pre className="mono cyan">{bp.assistant_spec}</pre>
    </div>
  );
}
