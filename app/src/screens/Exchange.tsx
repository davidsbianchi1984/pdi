import { useEffect, useState } from "react";
import { api, CustodyChain, IntakeRow, TransferRow } from "../api";
import { useSession } from "../store";

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

  if (!token) {
    return <div className="screen"><p className="muted center">
      Select a tenant first.</p></div>;
  }

  return (
    <div className="screen">
      <header className="screen-head">
        <h2>Exchange</h2>
        <span className="muted small">
          what leaves sealed, and what is asked to come in
        </span>
      </header>

      {error && <div className="error">⚠ {error}</div>}

      <div className="card">
        <h3>Send something out</h3>
        <div className="row">
          <input value={recipient} placeholder="clinic-a"
                 onChange={(e) => setRecipient(e.target.value)} />
          <input value={filename} placeholder="report.pdf"
                 onChange={(e) => setFilename(e.target.value)} />
        </div>
        <textarea rows={3} value={text} placeholder="The contents"
                  onChange={(e) => setText(e.target.value)} />
        <button className="primary"
                disabled={busy || !recipient.trim() || !text.trim()}
                onClick={() => run(async () => {
                  const t = await api.sendTransfer({
                    recipient: recipient.trim(), filename: filename.trim(),
                    content: btoa(unescape(encodeURIComponent(text))) },
                    token!);
                  if (t.receive_token) {
                    setReceipts((m) => ({ ...m, [t.id]: t.receive_token! }));
                  }
                  setText(""); setRecipient("");
                })}>Seal and send</button>
        <p className="muted small">
          The receive token comes back once, here, and is never served again.
          Give it to the recipient by whatever channel you would have used for
          the file itself — it is the thing that opens this transfer and
          nothing else opens it.
        </p>
      </div>

      <div className="card">
        <h3>Out</h3>
        {transfers.length === 0 && (
          <div className="muted small">Nothing sent.</div>
        )}
        {transfers.map((t) => (
          <div key={t.id}
               style={{ padding: "10px 0", borderBottom: "1px solid var(--line)" }}>
            <div className="row">
              <strong style={{ flex: 1 }}>{t.filename}</strong>
              <span className="muted small">
                → {t.recipient} · {t.size} bytes · {t.status}
                {t.programs.length > 0 ? ` · ${t.programs.join(", ")}` : ""}
              </span>
            </div>
            <div className="row">
              <button disabled={busy}
                      onClick={() => run(async () => {
                        await api.transfer(t.id, token!);
                      })}>Refresh</button>
              <button disabled={busy}
                      onClick={() => run(async () => {
                        setCustody(await api.transferCustody(t.id, token!));
                      })}>Chain of custody</button>
              <button disabled={busy || !receipts[t.id]}
                      title={receipts[t.id]
                        ? "Fetch it the way the recipient would"
                        : "The receive token was shown once, in another session"}
                      onClick={() => run(async () => {
                        const out = await api.receiveTransfer(
                          t.id, receipts[t.id]);
                        setGot(decodeURIComponent(escape(atob(out.content))));
                      })}>Receive it as the recipient</button>
              <button disabled={busy}
                      onClick={() => run(() =>
                        api.withdrawTransfer(t.id, token!))}>Withdraw</button>
            </div>
            {receipts[t.id] && (
              <div className="muted small">
                receive token held for this session only
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="card">
        <h3>Ask for something in</h3>
        <div className="row">
          <input value={party} placeholder="Dr Osei's office"
                 onChange={(e) => setParty(e.target.value)} />
          <input value={purpose} placeholder="records request"
                 onChange={(e) => setPurpose(e.target.value)} />
          <button className="primary" disabled={busy || !party.trim()}
                  onClick={() => run(async () => {
                    const i = await api.requestIntake({
                      from_party: party.trim(),
                      purpose: purpose.trim() || undefined }, token!);
                    if (i.submit_token) {
                      setSubmits((m) => ({ ...m, [i.id]: i.submit_token! }));
                    }
                    setParty(""); setPurpose("");
                  })}>Open an intake</button>
        </div>
        <p className="muted small">
          An intake is a one-way door somebody else walks through. The submit
          token is theirs, not yours — the same shape as a receive token and
          for the same reason.
        </p>
      </div>

      <div className="card">
        <h3>In</h3>
        {intakes.length === 0 && (
          <div className="muted small">Nothing requested.</div>
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
                      })}>Refresh</button>
              <button disabled={busy}
                      onClick={() => run(async () => {
                        setCustody(await api.intakeCustody(i.id, token!));
                      })}>Chain of custody</button>
              <button disabled={busy || !submits[i.id]}
                      title={submits[i.id]
                        ? "Send a file in the way the other party would"
                        : "The submit token was shown once, in another session"}
                      onClick={() => run(() => api.submitToIntake(
                        i.id, submits[i.id],
                        { filename: "their-file.pdf",
                          content: btoa("a file from the other party") }))}>
                Submit as the other party
              </button>
              <button disabled={busy || i.status !== "submitted"}
                      onClick={() => run(async () => {
                        const f = await api.intakeFile(i.id, token!);
                        setGot(decodeURIComponent(escape(atob(f.content))));
                      })}>Open what came in</button>
              <button disabled={busy}
                      onClick={() => run(() =>
                        api.cancelIntake(i.id, token!))}>Cancel</button>
            </div>
          </div>
        ))}
      </div>

      {got !== null && (
        <div className="card">
          <h3>What came out of the seal</h3>
          <pre style={{ whiteSpace: "pre-wrap" }}>{got}</pre>
          <p className="muted small">
            That read is in the audit chain. Opening a sealed thing is an
            event, not a lookup.
          </p>
        </div>
      )}

      {custody && (
        <div className="card">
          <h3>Chain of custody</h3>
          <p className="muted small">
            Audit chain{" "}
            <strong>
              {custody.audit_chain_intact ? "verifies" : "DOES NOT VERIFY"}
            </strong>
            {custody.retained_until
              ? ` · retained until ${custody.retained_until}`
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
