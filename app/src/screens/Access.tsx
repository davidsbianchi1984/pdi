import { useState } from "react";
import { api, AccessReports } from "../api";
import { deviceLanguage, t } from "../l10n";

/**
 * Ability is not a gate — the vault's accessibility statement and its door.
 *
 * The form asks three questions and none is a diagnosis: what were you
 * trying to do, what stood in the way, what would help. It sends no token —
 * reporting that the vault shut you out must not require the tenant token
 * it may have shut you out of — and the table it lands in has no submitter
 * column, so a report about ability cannot become a record about a body.
 *
 * The words stay on this deployment. This IS the vault product, so there is
 * no second place to seal to and nothing is ever relayed to the shared
 * problems collector. The deployment's admin token — the same one that
 * mints tenants — is what reads them, and an accepted report becomes a row
 * in the repo's only-shrinks accessibility backlog.
 */

const NEEDS = ["blind", "deaf", "mute", "motor",
               "cognitive", "dyslexia", "motion"] as const;

function message(e: unknown): string {
  return e instanceof Error ? e.message : String(e);
}

export function Access() {
  const lang = deviceLanguage();
  const L = (key: string) => t(key, lang);

  const [doing, setDoing] = useState("");
  const [wall, setWall] = useState("");
  const [help, setHelp] = useState("");
  const [sent, setSent] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [reviewer, setReviewer] = useState("");
  const [reports, setReports] = useState<AccessReports | null>(null);
  const [reviewError, setReviewError] = useState<string | null>(null);

  async function send() {
    setBusy(true); setError(null);
    try {
      const r = await api.sendAccessReport({
        doing: doing.trim(), wall: wall.trim(),
        help: help.trim() || undefined, lang,
      });
      setSent(r.note);
      setDoing(""); setWall(""); setHelp("");
    } catch (e) { setError(message(e)); }
    setBusy(false);
  }

  async function load() {
    setBusy(true); setReviewError(null);
    try { setReports(await api.accessReports(reviewer.trim())); }
    catch (e) { setReviewError(message(e)); }
    setBusy(false);
  }

  return (
    <>
      <div className="card">
        <h3>{L("acc.title")}</h3>
        <p className="small">{L("acc.lead")}</p>
        <h3>{L("acc.needs.title")}</h3>
        <ul className="refs">
          {NEEDS.map((need) => (
            <li key={need} className="small">{L(`acc.needs.${need}`)}</li>
          ))}
        </ul>
        <p className="small"><strong>{L("acc.needs.more")}</strong></p>
      </div>

      <div className="card">
        <h3>{L("acc.report.title")}</h3>
        <p className="muted small">{L("acc.report.lead")}</p>
        <label>
          {L("acc.report.doing")}
          <textarea value={doing} rows={2}
                    onChange={(e) => setDoing(e.target.value)} />
        </label>
        <label>
          {L("acc.report.wall")}
          <textarea value={wall} rows={3}
                    onChange={(e) => setWall(e.target.value)} />
        </label>
        <label>
          {L("acc.report.help")}
          <textarea value={help} rows={2}
                    onChange={(e) => setHelp(e.target.value)} />
        </label>
        <button disabled={busy || !doing.trim() || !wall.trim()}
                onClick={send}>
          {L("acc.report.send")}
        </button>
        {sent && (
          <p className="small">
            <strong>{L("acc.report.sent")}</strong>{" "}
            <span className="muted">{sent}</span>
          </p>
        )}
        {error && <p className="error small">{error}</p>}
      </div>

      <div className="card">
        <h3>{L("acc.review.title")}</h3>
        <p className="muted small">{L("acc.review.lead")}</p>
        <div className="row">
          <input type="password" value={reviewer}
                 onChange={(e) => setReviewer(e.target.value)}
                 placeholder={L("acc.review.token")} style={{ flex: 1 }} />
          <button disabled={busy} onClick={load}>{L("acc.review.load")}</button>
        </div>
        {reports && (reports.total === 0
          ? <p className="muted small">{L("acc.review.empty")}</p>
          : <ul className="refs">
              {reports.reports.map((r) => (
                <li key={r.id}>
                  <p className="small"><strong>{r.doing}</strong></p>
                  <p className="small">{r.wall}</p>
                  {r.help && <p className="small"><em>{r.help}</em></p>}
                  <p className="muted small">{r.lang}{" · "}{r.created_at}</p>
                </li>
              ))}
            </ul>)}
        {reviewError && <p className="error small">{reviewError}</p>}
      </div>
    </>
  );
}
