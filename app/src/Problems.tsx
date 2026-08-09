import { useState } from "react";
import { CONSOLE_VERSION } from "./api";
import {
  clearProblems, collectorUrl, problemReport, problems, sendProblems,
  sendingEnabled, setSending, type Problem, type SendOutcome,
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

  const collector = collectorUrl();
  // Built once and used for both the preview and the count, so the number
  // beside the button and the text below it can never describe different
  // things.
  const payload = problemReport(CONSOLE_VERSION);
  const report = JSON.stringify(payload, null, 2);
  const unsent = (payload.problems as Problem[]).length;

  return (
    <div className="card">
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
        {collector
          ? <>{t("pr.sentto", lang)} <code>{collector}</code>{" "}
            {t("pr.sentto.rest", lang)}</>
          : <>{t("pr.nocollector", lang)}</>}
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
              const outcome = await sendProblems(CONSOLE_VERSION);
              setSaid(t(OUTCOME[outcome], lang));
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
    </div>
  );
}
