import { useEffect, useState } from "react";
import { api, ResidentPosture, ResidentTask } from "../api";
import { useSession } from "../store";
import { deviceLanguage, Lang, t } from "../l10n";

/**
 * The resident intelligence: the agent living in the vault process.
 *
 * The opposite approach to the tandem's HTTP calls — planner, closed tool
 * registry, queryable datasets, embeddings and local-only inference running
 * beside the data, with no separate orchestration service. This screen is
 * the same engine reached from outside, which is the whole symmetry: a
 * tenant in a colocation rack and a tenant on the standard service open the
 * identical doors and get the identical privacy.
 *
 * Two honesty rules the screen repeats rather than smooths over:
 *
 *   * The registry's `leaves_host` column renders beside every tool and
 *     every planned step — a person deciding whether to run a plan should
 *     not have to read Python to learn which steps go outside.
 *   * The posture names the embedder and whether a local model is present.
 *     A stub that answered under a model's name would be the lie the whole
 *     module exists not to tell.
 */
export function Resident() {
  const { session } = useSession();
  const [posture, setPosture] = useState<ResidentPosture | null>(null);
  const [tasks, setTasks] = useState<ResidentTask[]>([]);
  const [datasets, setDatasets] = useState<
    { dataset: string; row_count: number; last_write: string }[]>([]);
  const [rows, setRows] = useState<Record<string, unknown>[] | null>(null);
  const [rowsOf, setRowsOf] = useState("");
  const [goal, setGoal] = useState("");
  const [embedKey, setEmbedKey] = useState("");
  const [embedText, setEmbedText] = useState("");
  const [embedded, setEmbedded] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [matches, setMatches] = useState<
    { key: string; score: number }[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const token = session.tenantToken;
  const lang = (session.language as Lang) ?? deviceLanguage();
  const fail = (e: unknown) =>
    setError(e instanceof Error ? e.message : String(e));

  function load() {
    if (!token) return;
    api.residentPosture(token).then(setPosture).catch(fail);
    api.residentTasks(token).then(setTasks).catch(fail);
    api.residentDatasets(token).then(setDatasets).catch(fail);
  }
  useEffect(load, [token]);

  const act = (fn: () => Promise<unknown>) => async () => {
    setError(null);
    setBusy(true);
    try {
      await fn();
      load();
    } catch (e) {
      fail(e);
    } finally {
      setBusy(false);
    }
  };

  if (!token) {
    return (
      <div className="screen">
        <h2>{t("res.title", lang)}</h2>
        <p className="muted">{t("res.signin", lang)}</p>
      </div>
    );
  }

  return (
    <div className="screen">
      <h2>{t("res.title", lang)}</h2>
      <p className="muted">{t("res.pitch", lang)}</p>
      {error && <p className="error">{error}</p>}

      {posture && (
        <div className="card">
          <h3>{t("res.posture", lang)}</h3>
          <p className="muted small">{posture.means}</p>
          <p className="small">
            {t("res.hosting", lang)}: <code>{posture.hosting_mode}</code>
            {" · "}
            {t("res.model", lang)}:{" "}
            <code>{posture.local_model ?? t("res.nomodel", lang)}</code>
            {" · "}
            {t("res.embedder", lang)}: <code>{posture.embedder}</code>
          </p>
          <table className="small">
            <tbody>
              {posture.tools.map((tool) => (
                <tr key={tool.name}>
                  <td><code>{tool.name}</code></td>
                  <td>{tool.means}</td>
                  <td>{tool.leaves_host
                    ? t("res.leaves", lang) : t("res.stays", lang)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="muted small">{posture.privacy}</p>
        </div>
      )}

      <div className="card">
        <h3>{t("res.plan", lang)}</h3>
        <p className="muted small">{t("res.plan.how", lang)}</p>
        <label>
          {t("res.plan", lang)}
          <textarea value={goal} onChange={(e) => setGoal(e.target.value)}
                    rows={2} placeholder={t("res.plan.ph", lang)} />
        </label>
        <button disabled={busy || !goal.trim()} onClick={act(async () => {
          await api.residentPlan({ goal: goal.trim() }, token);
          setGoal("");
        })}>
          {t("res.plan.go", lang)}
        </button>
      </div>

      <div className="card">
        <h3>{t("res.tasks", lang)}</h3>
        {tasks.length === 0 && (
          <p className="muted small">{t("res.tasks.none", lang)}</p>
        )}
        {tasks.map((task) => (
          <div key={task.id} className="row-block">
            <p className="small">
              <b>{task.goal}</b> — {task.status}
              {" "}<span className="muted">({task.planned_by})</span>
            </p>
            <ol className="small">
              {task.plan_steps.map((s) => (
                <li key={s.position}>
                  <code>{s.tool}</code> — {s.status}
                  {s.leaves_host && <> · {t("res.leaves", lang)}</>}
                  {s.summary && <> · {s.summary}</>}
                  {s.error && <span className="error"> · {s.error}</span>}
                </li>
              ))}
            </ol>
            {(task.status === "planned" || task.status === "failed") && (
              <button disabled={busy} onClick={act(async () => {
                await api.residentRun(task.id, token);
              })}>
                {t("res.run", lang)}
              </button>
            )}
          </div>
        ))}
      </div>

      <div className="card">
        <h3>{t("res.datasets", lang)}</h3>
        {datasets.length === 0 && (
          <p className="muted small">{t("res.datasets.none", lang)}</p>
        )}
        {datasets.map((d) => (
          <p className="small" key={d.dataset}>
            <code>{d.dataset}</code> · {d.row_count}
            {" "}
            <button disabled={busy} onClick={act(async () => {
              const got = await api.residentRows(d.dataset, token);
              setRowsOf(d.dataset);
              setRows(got.dataset_rows);
            })}>
              {t("res.rows.open", lang)}
            </button>
          </p>
        ))}
        {rows && (
          <>
            <h4><code>{rowsOf}</code></h4>
            {rows.length === 0 && (
              <p className="muted small">{t("res.rows.none", lang)}</p>
            )}
            {rows.map((r, i) => (
              <p className="small mono" key={i}>{JSON.stringify(r)}</p>
            ))}
          </>
        )}
      </div>

      <div className="card">
        <h3>{t("res.embed", lang)}</h3>
        <input value={embedKey} onChange={(e) => setEmbedKey(e.target.value)}
               placeholder={t("res.embed.key", lang)} />
        <textarea value={embedText} rows={2}
                  onChange={(e) => setEmbedText(e.target.value)}
                  placeholder={t("res.embed.text", lang)} />
        <button disabled={busy || !embedKey.trim() || !embedText.trim()}
                onClick={act(async () => {
                  const out = await api.residentEmbed(
                    { key: embedKey.trim(), text: embedText },
                    token);
                  setEmbedded(out.embedder);
                  setEmbedText("");
                })}>
          {t("res.embed.go", lang)}
        </button>
        {embedded && (
          <p className="muted small">
            {t("res.embed.done", lang)} <code>{embedded}</code>
          </p>
        )}
        <div>
          <label>
            {t("res.search.ph", lang)}
            <input value={query} onChange={(e) => setQuery(e.target.value)}
                   placeholder={t("res.search.ph", lang)} />
          </label>
          <button disabled={busy || !query.trim()} onClick={act(async () => {
            const out = await api.residentSearch(
              { query: query.trim() }, token);
            setMatches(out.matches);
          })}>
            {t("res.search.go", lang)}
          </button>
        </div>
        {matches && (
          <>
            {matches.length === 0 && (
              <p className="muted small">{t("res.search.none", lang)}</p>
            )}
            {matches.map((m) => (
              <p className="small" key={m.key}>
                <code>{m.key}</code> · {m.score}
                {" "}
                <button disabled={busy} onClick={act(async () => {
                  await api.residentForget(m.key, token);
                  setMatches((was) => (was ?? []).filter(
                    (x) => x.key !== m.key));
                })}>
                  {t("res.forget", lang)}
                </button>
              </p>
            ))}
          </>
        )}
      </div>
    </div>
  );
}
