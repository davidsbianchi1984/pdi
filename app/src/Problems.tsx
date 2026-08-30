import { useState } from "react";
import { api, CONSOLE_VERSION, getBase } from "./api";
import {
  clearProblems, collectorUrl, markReported, problemReport, problems,
  sendProblems, sendingEnabled, setSending, type Problem, type SendOutcome,
} from "./errors";
import { deviceLanguage, Lang, t } from "./l10n";
import { useSession } from "./store";

/**
 * What went wrong, and exactly what leaves this device.
 *
 * The preview is not a description of the report — it *is* the report, from the
 * same function that produces the copied text and the posted body. A screen
 * that summarised the payload in prose would be making a promise the code could
 * quietly break; this one can only be wrong in the way the payload is wrong.
 *
 * Two lists on purpose. The rows are the whole history, which is the user's;
 * the preview is the unreported remainder, which is the message. After a send
 * the history is unchanged and the preview is empty, and that difference is the
 * honest picture rather than a bug in the screen.
 */
/** Keys rather than sentences: this map is module-level and cannot ask for a
 *  language, so the screen resolves what it names. */
const OUTCOME: Record<SendOutcome, string> = {
  "sent": "pr.out.sent",
  "nothing-to-send": "pr.out.nothing",
  "turned-off": "pr.out.off",
  "no-collector": "pr.out.nocollector",
  "awaiting-notice": "pr.out.awaiting",
  "failed": "pr.out.failed",
};

export function Problems() {
  const { session } = useSession();
  const lang = (session.language as Lang) ?? deviceLanguage();
  const [rows, setRows] = useState<Problem[]>(problems);
  const [showing, setShowing] = useState(false);
  const [copied, setCopied] = useState(false);
  const [sending, setSendingNow] = useState(false);
  const [said, setSaid] = useState("");
  const [on, setOn] = useState(sendingEnabled);

  // The operator's half: what has reached the server, from every client of
  // this deployment. Reading needs PDI_PROBLEMS_KEY (or a caller on the
  // backend's own machine); the refusal is rendered verbatim when it does.
  const [readerKey, setReaderKey] = useState("");
  const [serverRows, setServerRows] = useState<Awaited<
    ReturnType<typeof api.problemRows>>["rows"] | null>(null);
  const [readError, setReadError] = useState("");

  // An external collector wins where a release stamps one in; the fallback
  // is this deployment's own backend, which serves the same intake.
  const collector = collectorUrl() || getBase();
  // Built once and used for both the preview and the count, so the number
  // beside the button and the text below it can never describe different
  // things.
  const payload = problemReport(CONSOLE_VERSION);
  const report = JSON.stringify(payload, null, 2);
  const unsent = (payload.problems as Problem[]).length;

  return (
    <div className="card" data-screen="8">
      <h3>{t("pr.title", lang)}</h3>
      <p className="muted small">{t("pr.note", lang)}</p>

      {rows.length === 0 && <p className="muted small">{t("pr.none", lang)}</p>}
      {rows.map((r) => (
        <div key={r.fingerprint} className="row">
          <code>{r.op}</code>
          <span className="muted">
            {r.status === 0 ? t("pr.noanswer", lang) : r.status}
          </span>
          {r.count > 1 && <span className="muted">×{r.count}</span>}
          <span className="muted">{r.day}</span>
        </div>
      ))}

      <p className="muted small">
        {t("pr.sentto", lang)} <code>{collector}</code>{" "}
        {t("pr.sentto.rest", lang)}
      </p>

      {collector && (
        <div className="row">
          <label>
            <input
              type="checkbox"
              checked={on}
              onChange={(e) => { setSending(e.target.checked); setOn(e.target.checked); }}
            />{" "}
            {t("pr.auto", lang)}
          </label>
          <button
            disabled={sending || !unsent}
            onClick={async () => {
              setSendingNow(true);
              // An external collector goes through the auto-sender's own
              // gate; the backend goes through the app's ordinary wire, so
              // this button is itself the console's door to POST
              // /v1/problems — audit-readable where a raw fetch against a
              // variable address cannot be.
              if (collectorUrl()) {
                setSaid(t(OUTCOME[await sendProblems(CONSOLE_VERSION)], lang));
              } else {
                try {
                  await api.reportProblems(payload);
                  markReported(payload);
                  setSaid(t(OUTCOME["sent"], lang));
                } catch {
                  setSaid(t(OUTCOME["failed"], lang));
                }
              }
              setRows(problems());
              setSendingNow(false);
            }}>
            {sending ? t("pr.sending", lang) : t("pr.sendnow", lang)}
          </button>
          {said && <span className="muted small">{said}</span>}
        </div>
      )}

      {rows.length > 0 && (
        <>
          <div className="row">
            <button onClick={() => setShowing(!showing)}>
              {showing ? t("pr.hide", lang) : t("pr.show", lang)}
            </button>
            <button
              onClick={async () => {
                try {
                  await navigator.clipboard.writeText(report);
                  setCopied(true);
                } catch {
                  // Clipboard permission is not guaranteed. Falling back to
                  // showing the text is more useful than an error, because the
                  // text is the deliverable either way.
                  setShowing(true);
                }
              }}>
              {copied ? t("pr.copied", lang) : t("pr.copy", lang)}
            </button>
            <button
              onClick={() => {
                clearProblems();
                setRows([]);
                setCopied(false);
              }}>
              {t("pr.clear", lang)}
            </button>
          </div>
          {showing && (
            <>
              {unsent === 0 && (
                <p className="muted small">{t("pr.allsent", lang)}</p>
              )}
              <pre className="small">{report}</pre>
            </>
          )}
        </>
      )}

      {/* The other end of the wire — the retrieval half, for whoever
          operates the server. Ported from the siblings, where a field
          report asked whether these results "get funneled back here to
          where we can make corrections". */}
      <h4>{t("prob.server", lang)}</h4>
      <p className="muted small">{t("prob.server.pitch", lang)}</p>
      <div className="row">
        <input type="password" value={readerKey}
               onChange={(e) => setReaderKey(e.target.value)}
               placeholder={t("prob.key.ph", lang)} style={{ flex: 1 }} />
        <button onClick={async () => {
          setReadError("");
          try {
            setServerRows((await api.problemRows(
              readerKey.trim() || undefined)).rows);
          } catch (e) {
            setServerRows(null);
            setReadError(e instanceof Error ? e.message : String(e));
          }
        }}>{t("prob.fetch", lang)}</button>
      </div>
      {readError && <p className="small">⚠ {readError}</p>}
      {serverRows && serverRows.length === 0 && (
        <p className="muted small">{t("prob.none", lang)}</p>
      )}
      {serverRows && serverRows.map((r, i) => (
        <div className="row" key={i}>
          <code>{r.op}</code>
          <span className="muted">{r.status_code}</span>
          <span className="muted">×{r.count}</span>
          <span className="muted">
            {r.source} {r.app_version} · {r.platform} · {r.day}
          </span>
        </div>
      ))}
    </div>
  );
}
