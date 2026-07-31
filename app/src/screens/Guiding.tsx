import { useEffect, useState } from "react";
import { api, ConsoleAnswer, DockCatalog, DockState, GuideBook,
         ImproveBoard, LanguageOption, Row, TranslateOut } from "../api";
import { useSession } from "../store";

/**
 * The console's own guide, the pane in its corner, and the words it uses.
 *
 * Eighteen routes, and the whole of it is the part of PDI whose job is
 * explaining the rest of PDI — which had no door of its own. An operator
 * could be walked through the vault by an assistant they could not open.
 *
 * Two things the server insists on and this screen repeats rather than
 * smooths over:
 *
 *   * The guide has **no name and no face**, and it says so in its own first
 *     sentence. PDI's subject is other people's sealed material; an assistant
 *     with a persona standing next to it would be the least trustworthy
 *     object in the product.
 *   * `POST /translate` performs **no machine translation**. It translates
 *     PDI's own note strings and returns `engine: "none"` with a note saying
 *     exactly that. A console that hid the note behind a spinner would be
 *     implying a capability the vault deliberately does not have.
 */
export function Guiding() {
  const { session } = useSession();
  const [book, setBook] = useState<GuideBook | null>(null);
  const [step, setStep] = useState<Row | null>(null);
  const [progress, setProgress] = useState<Row | null>(null);
  const [answer, setAnswer] = useState<ConsoleAnswer | null>(null);
  const [dock, setDock] = useState<DockState | null>(null);
  const [catalog, setCatalog] = useState<DockCatalog | null>(null);
  const [face, setFace] = useState<Row | null>(null);
  const [where, setWhere] = useState<Row | null>(null);
  const [languages, setLanguages] = useState<LanguageOption[]>([]);
  const [mine, setMine] = useState<Row | null>(null);
  const [translated, setTranslated] = useState<TranslateOut | null>(null);
  const [board, setBoard] = useState<ImproveBoard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [question, setQuestion] = useState("");
  const [language, setLanguage] = useState("en");
  const [text, setText] = useState("");
  const [idea, setIdea] = useState("");

  const token = session.tenantToken;
  const tenantId = session.tenantId;

  function load() {
    api.guide().then(setBook).catch(fail);
    api.dockFaces().then(setCatalog).catch(fail);
    api.languages().then((r) => setLanguages(r.languages)).catch(fail);
    if (!token) return;
    api.language(token).then(setMine).catch(fail);
    api.improvements(token).then(setBoard).catch(fail);
    if (tenantId) {
      api.dock(tenantId, token).then(setDock).catch(fail);
      api.guideProgress(tenantId).then(setProgress).catch(fail);
    }
  }
  function fail(e: unknown) { setError((e as Error).message); }
  useEffect(load, [token, tenantId]);

  async function run(work: () => Promise<unknown>) {
    setBusy(true); setError(null);
    try { await work(); load(); } catch (e) { fail(e); }
    finally { setBusy(false); }
  }

  return (
    <div className="screen">
      <header className="screen-head">
        <h2>Guiding</h2>
        <span className="muted small">
          the console's guide, its corner, and its words
        </span>
      </header>

      {error && <div className="error">⚠ {error}</div>}

      <div className="card">
        <h3>The guide</h3>
        <p className="muted small">{book?.guide ?? "…"}</p>
        {book?.ceiling && (
          <p className="muted small"><strong>{book.ceiling}</strong></p>
        )}
        <div className="row">
          <button disabled={busy || !tenantId}
                  onClick={() => run(() => api.startGuide(
                    { learner_id: tenantId! }))}>Start the walkthrough</button>
          <button disabled={busy}
                  onClick={() => run(async () => {
                    setStep(await api.guideStep("what_pdi_is"));
                  })}>Read a step</button>
          <button disabled={busy}
                  onClick={() => run(async () => {
                    setStep(await api.guideForScreen(1));
                  })}>What is this screen?</button>
          <button disabled={busy || !tenantId}
                  onClick={() => run(() => api.finishGuideStep(
                    { learner_id: tenantId!, lesson: "what_pdi_is" }))}>
            Mark it done
          </button>
        </div>
        {progress != null && (
          <p className="muted small">
            {String(progress.done ?? 0)} of {String(progress.total ?? 0)} done
          </p>
        )}
        {step && (
          <p className="muted small">
            <strong>{String(step.title ?? "")}</strong> —{" "}
            {String(step.what ?? "")} {String(step.click ?? "")}
          </p>
        )}
        {(book?.chapters ?? []).map((c) => (
          <div key={c.chapter} className="muted small"
               style={{ padding: "4px 0" }}>
            {c.chapter} · {c.steps.length} steps
          </div>
        ))}
      </div>

      <div className="card">
        <h3>Ask it</h3>
        <div className="row">
          <input value={question} placeholder="Where is the audit log?"
                 onChange={(e) => setQuestion(e.target.value)} />
          <button className="primary" disabled={busy || !question.trim()}
                  onClick={() => run(async () => {
                    setAnswer(await api.askConsole(
                      { question: question.trim() }, token!));
                  })}>Ask</button>
        </div>
        {answer && (
          <>
            <p>{answer.answer}</p>
            <p className="muted small">{answer.disclosure}</p>
            {answer.refused && (
              <p className="muted small">
                Refused — and that is the answer, not a failure. It was asked
                something about what is inside the vault, which it cannot
                read.
              </p>
            )}
            {answer.directions && (
              <p className="muted small">
                → {answer.directions.title} · screens{" "}
                {answer.directions.screens.join(", ")}
              </p>
            )}
            <p className="muted small">
              It knows about: {answer.topics.join(", ")}
            </p>
          </>
        )}
      </div>

      <div className="card">
        <h3>The corner</h3>
        {dock && (
          <p className="muted small">
            {dock.corner} · {dock.state} · showing {dock.face}
          </p>
        )}
        <div className="row">
          {(dock?.faces ?? []).map((f) => (
            <button key={f} disabled={busy || !tenantId}
                    onClick={() => run(async () => {
                      setFace(await api.dockFace(tenantId!, f, token!));
                      setWhere(await api.dockWhere(f));
                    })}>{f}</button>
          ))}
        </div>
        <div className="row">
          <button disabled={busy || !tenantId}
                  onClick={() => run(() => api.setDock(tenantId!,
                    { corner: dock?.corner === "bottom_right"
                        ? "bottom_left" : "bottom_right" }, token!))}>
            Other corner
          </button>
          <button disabled={busy || !tenantId}
                  onClick={() => run(() => api.setDock(tenantId!,
                    { state: dock?.state === "open" ? "handle" : "open" },
                    token!))}>
            {dock?.state === "open" ? "Tuck it away" : "Open it"}
          </button>
        </div>
        {face && where && (
          <p className="muted small">
            {String(catalog?.faces[String(face.face ?? "")] ?? "")}{" "}
            {String(where.title ?? where.screen ?? "")}
          </p>
        )}
        {catalog && (
          <p className="muted small">
            Never in the pane: {Object.values(catalog.never).join(" · ")}
          </p>
        )}
      </div>

      <div className="card">
        <h3>Words</h3>
        <div className="row">
          <select value={language}
                  onChange={(e) => setLanguage(e.target.value)}>
            {languages.map((l) => (
              <option key={l.code} value={l.code}>
                {l.label}
                {l.notes_translated ? "" : " (notes stay in English)"}
              </option>
            ))}
          </select>
          <button className="primary" disabled={busy || !token}
                  onClick={() => run(() => api.setLanguage(
                    { language }, token!))}>Use this</button>
          <span className="muted small">
            now: {String(mine?.label ?? "…")}
          </span>
        </div>
        <div className="row">
          <input value={text} placeholder="A note to translate"
                 onChange={(e) => setText(e.target.value)} />
          <button disabled={busy || !text.trim() || !token}
                  onClick={() => run(async () => {
                    setTranslated(await api.translate(
                      { text: text.trim(), to: language }, token!));
                  })}>Translate</button>
        </div>
        {translated && (
          <>
            <p>{translated.translation}</p>
            <p className="muted small">
              engine: <code>{translated.engine}</code> — {translated.note}
            </p>
          </>
        )}
      </div>

      <div className="card">
        <h3>Tell us about the console</h3>
        <div className="row">
          <input value={idea} placeholder="What would make this better?"
                 onChange={(e) => setIdea(e.target.value)} />
          <button className="primary" disabled={busy || !idea.trim() || !token}
                  onClick={() => run(async () => {
                    await api.suggestImprovement({ category: "improvement",
                      message: idea.trim() }, token!);
                    setIdea("");
                  })}>Send it</button>
        </div>
        {board && (
          <p className="muted small">
            {board.total} in all · {board.mine.length} of them yours ·{" "}
            {board.categories.join(", ")}
          </p>
        )}
      </div>
    </div>
  );
}
