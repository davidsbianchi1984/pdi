import { useEffect, useState } from "react";
import { api, getBase, CustodyChain, IntakeRow, TransferRow } from "../api";
import { useSession } from "../store";
import { deviceLanguage, fill, Lang, t } from "../l10n";

/**
 * What leaves the vault, and what is asked to come into it.
 *
 * Thirteen routes. The pair worth reading closely is `receive` and `submit`,
 * because both were bound wrong the first time and for the same reason.
 *
 * Neither takes the tenant's token. `POST /transfers/{id}/receive` takes an
 * `x-receive-token` header and `POST /intakes/{id}/submit` takes
 * `x-submit-token`. That is not a quirk — it is the whole design. The party
 * receiving a transfer is a clinic, and the party submitting to an intake is
 * a records office; neither is the tenant, neither has a tenant credential,
 * and neither should. Passing the tenant's token is a 403 every time, which
 * is what driving them showed and what the route table did not.
 *
 * Both tokens are shown exactly once, in the response that creates the thing,
 * and never again — so this screen keeps them in memory and says so. A
 * console that pretended it could fetch one later would be lying about a
 * secret.
 */
export function Exchange() {
  const { session } = useSession();
  const [transfers, setTransfers] = useState<TransferRow[]>([]);
  const [intakes, setIntakes] = useState<IntakeRow[]>([]);
  const [custody, setCustody] = useState<CustodyChain | null>(null);
  const [got, setGot] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // Shown once by the server, held here for this session only.
  const [receipts, setReceipts] = useState<Record<string, string>>({});
  const [submits, setSubmits] = useState<Record<string, string>>({});

  const [recipient, setRecipient] = useState("");
  const [filename, setFilename] = useState("report.pdf");
  const [text, setText] = useState("");
  const [party, setParty] = useState("");
  const [purpose, setPurpose] = useState("");

  const token = session.tenantToken;

  function load() {
    if (!token) return;
    api.transfers(token).then(setTransfers).catch(fail);
    api.intakes(token).then(setIntakes).catch(fail);
  }
  function fail(e: unknown) { setError((e as Error).message); }
  useEffect(load, [token]);

  async function run(work: () => Promise<unknown>) {
    if (!token) return;
    setBusy(true); setError(null);
    try { await work(); load(); } catch (e) { fail(e); }
    finally { setBusy(false); }
  }

  const lang = (session.language as Lang) ?? deviceLanguage();

  if (!token) {
    return <div className="screen"><p className="muted center">
      {t("exc.pick", lang)}</p></div>;
  }

  return (
    <div className="screen">
      <header className="screen-head">
        <h2>{t("exc.title", lang)}</h2>
        <span className="muted small">{t("exc.sub", lang)}</span>
      </header>

      {error && <div className="error">⚠ {error}</div>}

      <div className="card">
        <h3>{t("exc.send", lang)}</h3>
        <div className="row">
          {/* The placeholders stay what they were — an example, not a name.
              A 422 that says `filename` can now say Filename instead. */}
          <label>{t("exc.recipient", lang)}
            <input value={recipient} placeholder="clinic-a"
                   onChange={(e) => setRecipient(e.target.value)} />
          </label>
          <label>{t("exc.filename", lang)}
            <input value={filename} placeholder="report.pdf"
                   onChange={(e) => setFilename(e.target.value)} />
          </label>
        </div>
        {/* `content` on the wire, and the table has said Content in ten
            languages since the first round of this work. */}
        <label>{t("exc.content", lang)}
          <textarea rows={3} value={text}
                    placeholder={t("exc.content.ph", lang)}
                    onChange={(e) => setText(e.target.value)} />
        </label>
        <button className="primary"
                disabled={busy || !recipient.trim() || !text.trim()}
                onClick={() => run(async () => {
                  const sent = await api.sendTransfer({
                    recipient: recipient.trim(), filename: filename.trim(),
                    content: btoa(unescape(encodeURIComponent(text))) },
                    token!);
                  if (sent.receive_token) {
                    setReceipts((m) => ({ ...m,
                                          [sent.id]: sent.receive_token! }));
                  }
                  setText(""); setRecipient("");
                })}>{t("exc.seal", lang)}</button>
        <p className="muted small">{t("exc.once", lang)}</p>
      </div>

      <div className="card">
        <h3>{t("exc.out", lang)}</h3>
        {transfers.length === 0 && (
          <div className="muted small">{t("exc.nothingsent", lang)}</div>
        )}
        {transfers.map((tr) => (
          <div key={tr.id}
               style={{ padding: "10px 0", borderBottom: "1px solid var(--line)" }}>
            <div className="row">
              <strong style={{ flex: 1 }}>{tr.filename}</strong>
              <span className="muted small">
                → {tr.recipient} ·{" "}
                {fill("exc.bytes", lang, { n: tr.size })} · {tr.status}
                {tr.programs.length > 0 ? ` · ${tr.programs.join(", ")}` : ""}
              </span>
            </div>
            <div className="row">
              <button disabled={busy}
                      onClick={() => run(async () => {
                        await api.transfer(tr.id, token!);
                      })}>{t("exc.refresh", lang)}</button>
              <button disabled={busy}
                      onClick={() => run(async () => {
                        setCustody(await api.transferCustody(tr.id, token!));
                      })}>{t("exc.chain", lang)}</button>
              {/* The recipient's actual door. Until this existed, `/r/{id}`
                  was a page nobody could link to and the receive token was
                  something the sender was told to hand over with nowhere for
                  it to be used — the same defect one step earlier. */}
              <button disabled={busy || !receipts[tr.id]}
                      title={receipts[tr.id]
                        ? t("exc.copylink.t", lang)
                        : t("exc.tokengone", lang)}
                      onClick={() => run(async () => {
                        // Resolve it before handing it over: a misconfigured
                        // public base would otherwise be discovered by the
                        // recipient, who has nobody to ask.
                        await api.recipientPage(tr.id);
                        const link = `${getBase()}/r/${tr.id}`
                          + `#${encodeURIComponent(receipts[tr.id])}`;
                        navigator.clipboard?.writeText(link);
                        setGot(link);
                      })}>{t("exc.copylink", lang)}</button>
              <button disabled={busy || !receipts[tr.id]}
                      title={receipts[tr.id]
                        ? t("exc.asrecipient.t", lang)
                        : t("exc.tokengone", lang)}
                      onClick={() => run(async () => {
                        const out = await api.receiveTransfer(
                          tr.id, receipts[tr.id]);
                        setGot(decodeURIComponent(escape(atob(out.content))));
                      })}>{t("exc.asrecipient", lang)}</button>
              <button disabled={busy}
                      onClick={() => run(() =>
                        api.withdrawTransfer(tr.id, token!))}>{t("exc.withdraw", lang)}</button>
            </div>
            {receipts[tr.id] && (
              <div className="muted small">{t("exc.sessiononly", lang)}</div>
            )}
          </div>
        ))}
      </div>

      <div className="card">
        <h3>{t("exc.ask", lang)}</h3>
        <div className="row">
          <label>{t("exc.party", lang)}
            <input value={party} placeholder={t("exc.party.ph", lang)}
                   onChange={(e) => setParty(e.target.value)} />
          </label>
          <label>{t("exc.purpose", lang)}
            <input value={purpose} placeholder={t("exc.purpose.ph", lang)}
                   onChange={(e) => setPurpose(e.target.value)} />
          </label>
          <button className="primary" disabled={busy || !party.trim()}
                  onClick={() => run(async () => {
                    const i = await api.requestIntake({
                      from_party: party.trim(),
                      purpose: purpose.trim() || undefined }, token!);
                    if (i.submit_token) {
                      setSubmits((m) => ({ ...m, [i.id]: i.submit_token! }));
                    }
                    setParty(""); setPurpose("");
                  })}>{t("exc.openintake", lang)}</button>
        </div>
        <p className="muted small">{t("exc.onewaydoor", lang)}</p>
      </div>

      <div className="card">
        <h3>{t("exc.in", lang)}</h3>
        {intakes.length === 0 && (
          <div className="muted small">{t("exc.nothingasked", lang)}</div>
        )}
        {intakes.map((i) => (
          <div key={i.id}
               style={{ padding: "10px 0", borderBottom: "1px solid var(--line)" }}>
            <div className="row">
              <strong style={{ flex: 1 }}>{i.from_party}</strong>
              <span className="muted small">
                {i.purpose ?? ""} · {i.status}
                {i.filename ? ` · ${i.filename}` : ""}
              </span>
            </div>
            <div className="row">
              <button disabled={busy}
                      onClick={() => run(async () => {
                        await api.intake(i.id, token!);
                      })}>{t("exc.refresh", lang)}</button>
              <button disabled={busy}
                      onClick={() => run(async () => {
                        setCustody(await api.intakeCustody(i.id, token!));
                      })}>{t("exc.chain", lang)}</button>
              <button disabled={busy || !submits[i.id]}
                      title={submits[i.id]
                        ? t("exc.assubmitter.t", lang)
                        : t("exc.tokengone.submit", lang)}
                      onClick={() => run(() => api.submitToIntake(
                        i.id, submits[i.id],
                        { filename: "their-file.pdf",
                          content: btoa("a file from the other party") }))}>
                {t("exc.assubmitter", lang)}
              </button>
              <button disabled={busy || i.status !== "submitted"}
                      onClick={() => run(async () => {
                        const f = await api.intakeFile(i.id, token!);
                        setGot(decodeURIComponent(escape(atob(f.content))));
                      })}>{t("exc.openwhat", lang)}</button>
              <button disabled={busy}
                      onClick={() => run(() =>
                        api.cancelIntake(i.id, token!))}>{t("exc.cancel", lang)}</button>
            </div>
          </div>
        ))}
      </div>

      {got !== null && (
        <div className="card">
          <h3>{t("exc.outofseal", lang)}</h3>
          <pre style={{ whiteSpace: "pre-wrap" }}>{got}</pre>
          <p className="muted small">{t("exc.readisevent", lang)}</p>
        </div>
      )}

      {custody && (
        <div className="card">
          <h3>{t("exc.chain", lang)}</h3>
          <p className="muted small">
            {t("exc.auditchain", lang)}{" "}
            <strong>
              {custody.audit_chain_intact ? t("exc.verifies", lang)
                                          : t("exc.notverify", lang)}
            </strong>
            {custody.retained_until
              ? ` · ${fill("exc.retained", lang,
                           { when: custody.retained_until })}`
              : ""}
          </p>
          {custody.chain_of_custody.map((e, i) => (
            <div key={i} className="row"
                 style={{ padding: "6px 0", borderBottom: "1px solid var(--line)" }}>
              <span style={{ flex: 1 }}>{e.event}</span>
              <span className="muted small">
                {e.actor} · {new Date(e.at).toLocaleString()}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
