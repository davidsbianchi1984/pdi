import { useEffect, useState } from "react";
import { api, ConsoleAnswer, DockCatalog, DockState, GuideBook,
         ImproveBoard, LanguageOption, Row, TranslateOut } from "../api";
import { useSession } from "../store";
import { deviceLanguage, fill, Lang, t } from "../l10n";

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
  const { session, setSession } = useSession();
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
  // The console's own words follow the tenant's choice; before there is one,
  // they follow the browser rather than defaulting to English. The shells have
  // read the device this way since the accountless-screen round.
  const lang = (session.language as Lang) ?? deviceLanguage();

  function load() {
    api.guide().then(setBook).catch(fail);
    api.dockFaces().then(setCatalog).catch(fail);
    api.languages().then((r) => setLanguages(r.languages)).catch(fail);
    if (!token) return;
    api.language(token).then((r) => {
      setMine(r);
      const chosen = String(r.language ?? "");
      if (chosen) { setLanguage(chosen); setSession({ language: chosen }); }
    }).catch(fail);
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
        <h2>{t("gd.title", lang)}</h2>
        <span className="muted small">
          {t("gd.sub", lang)}
        </span>
      </header>

      {error && <div className="error">⚠ {error}</div>}

      <div className="card">
        <h3>{t("gd.guide", lang)}</h3>
        <p className="muted small">{book?.guide ?? "…"}</p>
        {book?.ceiling && (
          <p className="muted small"><strong>{book.ceiling}</strong></p>
        )}
        <div className="row">
          <button disabled={busy || !tenantId}
                  onClick={() => run(() => api.startGuide(
                    { learner_id: tenantId! }))}>{t("gd.start", lang)}</button>
          <button disabled={busy}
                  onClick={() => run(async () => {
                    setStep(await api.guideStep("what_pdi_is"));
                  })}>{t("gd.step", lang)}</button>
          <button disabled={busy}
                  onClick={() => run(async () => {
                    setStep(await api.guideForScreen(1));
                  })}>{t("gd.thisscreen", lang)}</button>
          <button disabled={busy || !tenantId}
                  onClick={() => run(() => api.finishGuideStep(
                    { learner_id: tenantId!, lesson: "what_pdi_is" }))}>
            {t("gd.done", lang)}
          </button>
        </div>
        {progress != null && (
          <p className="muted small">
            {fill("gd.progress", lang,
                  { done: String(progress.done ?? 0),
                    total: String(progress.total ?? 0) })}
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
            {c.chapter} · {c.steps.length} {t("gd.steps", lang)}
          </div>
        ))}
      </div>

      <div className="card">
        <h3>{t("gd.ask.head", lang)}</h3>
        <div className="row">
          <label>{t("gd.q", lang)}
            <input value={question} placeholder={t("gd.q.ph", lang)}
                   onChange={(e) => setQuestion(e.target.value)} />
          </label>
          <button className="primary" disabled={busy || !question.trim()}
                  onClick={() => run(async () => {
                    setAnswer(await api.askConsole(
                      { question: question.trim() }, token!));
                  })}>{t("gd.ask.go", lang)}</button>
        </div>
        {answer && (
          <>
            <p>{answer.answer}</p>
            <p className="muted small">{answer.disclosure}</p>
            {answer.refused && (
              <p className="muted small">
                {t("gd.refused", lang)}
              </p>
            )}
            {answer.directions && (
              <p className="muted small">
                → {answer.directions.title} · {t("gd.screens", lang)}{" "}
                {answer.directions.screens.join(", ")}
              </p>
            )}
            <p className="muted small">
              {t("gd.knows", lang)} {answer.topics.join(", ")}
            </p>
          </>
        )}
      </div>

      <div className="card">
        <h3>{t("gd.corner", lang)}</h3>
        {dock && (
          <p className="muted small">
            {dock.corner} · {dock.state} · {t("gd.showing", lang)} {dock.face}
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
            {t("gd.othercorner", lang)}
          </button>
          <button disabled={busy || !tenantId}
                  onClick={() => run(() => api.setDock(tenantId!,
                    { state: dock?.state === "open" ? "handle" : "open" },
                    token!))}>
            {dock?.state === "open"
              ? t("gd.tuck", lang) : t("gd.open", lang)}
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
            {t("gd.never", lang)} {Object.values(catalog.never).join(" · ")}
          </p>
        )}
      </div>

      <div className="card">
        <h3>{t("gd.words", lang)}</h3>
        <div className="row">
          <label>{t("gd.lang", lang)}
            <select value={language}
                    onChange={(e) => setLanguage(e.target.value)}>
              {languages.map((l) => (
                <option key={l.code} value={l.code}>
                  {l.label}
                  {l.notes_translated ? "" : t("gd.notes.en", lang)}
                </option>
              ))}
            </select>
          </label>
          <button className="primary" disabled={busy || !token}
                  onClick={() => run(async () => {
                    await api.setLanguage({ language }, token!);
                    setSession({ language });
                  })}>{t("gd.use", lang)}</button>
          <span className="muted small">
            {t("gd.now", lang)} {String(mine?.label ?? "…")}
          </span>
        </div>
        <div className="row">
          <label>{t("gd.text", lang)}
            <input value={text} placeholder={t("gd.text.ph", lang)}
                   onChange={(e) => setText(e.target.value)} />
          </label>
          <button disabled={busy || !text.trim() || !token}
                  onClick={() => run(async () => {
                    setTranslated(await api.translate(
                      { text: text.trim(), to: language }, token!));
                  })}>{t("gd.translate", lang)}</button>
        </div>
        {translated && (
          <>
            <p>{translated.translation}</p>
            <p className="muted small">
              {t("gd.engine", lang)} <code>{translated.engine}</code> — {translated.note}
            </p>
          </>
        )}
      </div>

      <div className="card">
        <h3>{t("gd.tell", lang)}</h3>
        <div className="row">
          <input value={idea} placeholder={t("gd.idea.ph", lang)}
                 onChange={(e) => setIdea(e.target.value)} />
          <button className="primary" disabled={busy || !idea.trim() || !token}
                  onClick={() => run(async () => {
                    await api.suggestImprovement({ category: "improvement",
                      message: idea.trim() }, token!);
                    setIdea("");
                  })}>{t("gd.send", lang)}</button>
        </div>
        {board && (
          <p className="muted small">
            {board.total} {t("gd.total", lang)} · {board.mine.length}{" "}
            {t("gd.yours", lang)} ·{" "}
            {board.categories.join(", ")}
          </p>
        )}
      </div>
    </div>
  );
}
