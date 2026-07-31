import { useEffect, useState } from "react";
import { api, BeaconRefKind, BeaconRow, CustodyChain, RingKind, Row,
         ScanCard } from "../api";
import { useSession } from "../store";

/**
 * A sealed carrier, and the code on the outside of it.
 *
 * Thirteen routes, none of which the desktop console could reach. The whole
 * point of the feature is a code somebody who is *not* a tenant can scan —
 * a courier holding a crate, a technician at a rack — and that side of it
 * (`/s/{bid}`) takes no credential at all, deliberately.
 *
 * What a scanner learns is capped by `disclose`, which the server enforces
 * and which is a single value rather than the list a first reading suggests:
 * `blind` proves the thing is under custody and says nothing else; `contact`
 * adds a way to reach whoever holds it. What a scanner can *do* is leave a
 * note in the chain of custody — timestamped, hash-chained, readable by the
 * holder, and not alterable by the person who left it.
 *
 * The card the server serves a stranger says the important part in its own
 * words: *this code proves custody, not contents*. `contents` is null on
 * every card and always will be. That sentence is printed here rather than
 * paraphrased.
 */

const KINDS: BeaconRefKind[] = ["transfer", "intake", "object", "facility"];
const RINGS: RingKind[] = ["delivery", "access", "collection", "other"];

export function Carriers() {
  const { session } = useSession();
  const [beacons, setBeacons] = useState<BeaconRow[]>([]);
  const [rings, setRings] = useState<Row[]>([]);
  const [custody, setCustody] = useState<CustodyChain | null>(null);
  const [card, setCard] = useState<ScanCard | null>(null);
  const [page, setPage] = useState<string | null>(null);
  const [qr, setQr] = useState<string | null>(null);
  const [transcript, setTranscript] = useState<Row | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [label, setLabel] = useState("");
  const [kind, setKind] = useState<BeaconRefKind>("object");
  const [disclose, setDisclose] = useState<"blind" | "contact">("blind");
  const [ringKind, setRingKind] = useState<RingKind>("delivery");
  const [openOnly, setOpenOnly] = useState(false);

  const token = session.tenantToken;

  function load() {
    if (!token) return;
    api.beacons(token).then(setBeacons).catch(fail);
    api.rings(token, openOnly).then(setRings).catch(fail);
  }
  function fail(e: unknown) { setError((e as Error).message); }
  useEffect(load, [token, openOnly]);

  async function run(work: () => Promise<unknown>) {
    if (!token) return;
    setBusy(true); setError(null);
    try { await work(); load(); } catch (e) { fail(e); }
    finally { setBusy(false); }
  }

  if (!token) {
    return <div className="screen"><p className="muted center">
      Select a tenant first — carriers are placed with the tenant's own
      token.</p></div>;
  }

  return (
    <div className="screen">
      <header className="screen-head">
        <h2>Carriers</h2>
        <span className="muted small">
          a sealed thing, and the code on the outside of it
        </span>
      </header>

      {error && <div className="error">⚠ {error}</div>}

      <div className="card">
        <h3>Place a code</h3>
        <div className="row">
          <input value={label} placeholder="Server rack A"
                 onChange={(e) => setLabel(e.target.value)} />
          <select value={kind}
                  onChange={(e) => setKind(e.target.value as BeaconRefKind)}>
            {KINDS.map((k) => <option key={k} value={k}>{k}</option>)}
          </select>
          <select value={disclose}
                  onChange={(e) =>
                    setDisclose(e.target.value as "blind" | "contact")}>
            <option value="blind">blind — custody only</option>
            <option value="contact">contact — and a way to reach us</option>
          </select>
          <button className="primary" disabled={busy || !label.trim()}
                  onClick={() => run(async () => {
                    await api.placeBeacon({ ref_kind: kind,
                      label: label.trim(), disclose }, token!);
                    setLabel("");
                  })}>Place</button>
        </div>
        <p className="muted small">
          A code on a crate is for whoever is holding the crate, so scanning
          it needs no account. Blind is the default because the safe answer
          to <em>what is in here</em> is that the code cannot tell you.
        </p>
      </div>

      <div className="card">
        <h3>Placed</h3>
        {beacons.length === 0 && (
          <div className="muted small">None placed.</div>
        )}
        {beacons.map((b) => (
          <div key={b.id}
               style={{ padding: "10px 0", borderBottom: "1px solid var(--line)" }}>
            <div className="row">
              <strong style={{ flex: 1 }}>{b.label}</strong>
              <span className="muted small">
                {b.ref_kind} · {b.state} · {b.disclose} · {b.scans} scan
                {b.scans === 1 ? "" : "s"}
                {b.active ? "" : " · lifted"}
              </span>
            </div>
            <div className="row">
              <button disabled={busy}
                      onClick={() => run(async () => {
                        setCustody(await api.beaconCustody(b.id, token!));
                      })}>Chain of custody</button>
              <button disabled={busy}
                      onClick={() => run(async () => {
                        setCard(await api.scanCard(b.id));
                      })}>What a scanner sees</button>
              <button disabled={busy}
                      onClick={() => run(async () => {
                        setPage(await api.scanPage(b.id));
                        setQr(await api.scanQr(b.id));
                      })}>The code itself</button>
              <button disabled={busy}
                      onClick={() => run(async () => {
                        setCustody(null);
                        await api.beacon(b.id, token!);
                      })}>Refresh</button>
              <select value={b.state}
                      onChange={(e) => run(() => api.setBeaconState(
                        b.id, e.target.value, token!))}>
                {["sealed", "in_transit", "delivered", "opened"].map((st) => (
                  <option key={st} value={st}>{st}</option>
                ))}
              </select>
              <button disabled={busy}
                      onClick={() => run(() => api.liftBeacon(b.id, token!))}>
                Lift it
              </button>
            </div>
            <div className="row">
              <span className="muted small">Act as a scanner:</span>
              <select value={ringKind}
                      onChange={(e) =>
                        setRingKind(e.target.value as RingKind)}>
                {RINGS.map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
              <button disabled={busy}
                      onClick={() => run(() => api.ringHolder(b.id,
                        { kind: ringKind }))}>Ring the holder</button>
              <button disabled={busy}
                      onClick={() => run(() => api.reportFound(b.id,
                        { where: "loading dock" }))}>Report it found</button>
            </div>
          </div>
        ))}
      </div>

      {card && (
        <div className="card">
          <h3>The card a stranger gets</h3>
          <p><strong>{card.badge}</strong></p>
          <p className="muted small">{card.note}</p>
          <p className="muted small">
            {card.reference} · {card.kind} · {card.state} ·{" "}
            {card.under_custody ? "under custody" : "not under custody"}
            {card.held_by ? ` · held by ${card.held_by}` : ""}
          </p>
          <p className="muted small">
            Contents: <strong>{card.contents === null ? "not disclosed" : "?"}</strong>
            {" "}— and there is no value of `disclose` that changes that.
          </p>
        </div>
      )}

      {(page || qr) && (
        <div className="card">
          <h3>The printed code</h3>
          {qr && (
            <img alt="the scannable code"
                 src={"data:image/svg+xml;utf8," + encodeURIComponent(qr)}
                 style={{ width: 180, height: 180 }} />
          )}
          {page && (
            <p className="muted small">
              The landing page is {page.length} characters of HTML — a page
              for a courier's phone, not a document for this console.
            </p>
          )}
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
            . A custody list nobody can check is a list of claims, so the
            verification is shown above the list rather than under it.
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
          {(custody.controls?.required ?? []).length > 0 && (
            <p className="muted small">
              Controls required: {custody.controls.required.join(", ")}
            </p>
          )}
        </div>
      )}

      <div className="card">
        <h3>Somebody rang</h3>
        <label className="row">
          <input type="checkbox" checked={openOnly}
                 onChange={(e) => setOpenOnly(e.target.checked)} />
          {" "}open only
        </label>
        {rings.length === 0 && (
          <div className="muted small">Nobody has scanned and rung.</div>
        )}
        {rings.map((r) => (
          <div key={String(r.id)} className="row"
               style={{ padding: "6px 0", borderBottom: "1px solid var(--line)" }}>
            <span style={{ flex: 1 }}>
              {String(r.kind)} · {String(r.beacon ?? "")}
            </span>
            <span className="muted small">{String(r.status ?? "")}</span>
            <button disabled={busy}
                    onClick={() => run(async () => {
                      setTranscript(
                        await api.ringTranscript(String(r.id), token!));
                    })}>Transcript</button>
          </div>
        ))}
        {transcript && (
          <p className="muted small">{JSON.stringify(transcript)}</p>
        )}
      </div>
    </div>
  );
}
