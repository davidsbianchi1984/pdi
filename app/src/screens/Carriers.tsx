import { useEffect, useState } from "react";
import { api, BeaconRefKind, BeaconRow, CustodyChain, RingKind, Row,
         ScanCard } from "../api";
import { useSession } from "../store";
import { deviceLanguage, fill, Lang, t } from "../l10n";

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

  const lang = (session.language as Lang) ?? deviceLanguage();

  if (!token) {
    return <div className="screen"><p className="muted center">
      {t("car.pick", lang)}</p></div>;
  }

  return (
    <div className="screen">
      <header className="screen-head">
        <h2>{t("car.title", lang)}</h2>
        <span className="muted small">{t("car.sub", lang)}</span>
      </header>

      {error && <div className="error">⚠ {error}</div>}

      <div className="card">
        <h3>{t("car.place", lang)}</h3>
        <div className="row">
          <label>{t("car.label", lang)}
            <input value={label} placeholder={t("car.label.ph", lang)}
                   onChange={(e) => setLabel(e.target.value)} />
          </label>
          <label>{t("car.standsfor", lang)}
            <select value={kind}
                    onChange={(e) => setKind(e.target.value as BeaconRefKind)}>
              {KINDS.map((k) => <option key={k} value={k}>{k}</option>)}
            </select>
          </label>
          <label>{t("car.disclose", lang)}
            <select value={disclose}
                    onChange={(e) =>
                      setDisclose(e.target.value as "blind" | "contact")}>
              <option value="blind">{t("car.disclose.blind", lang)}</option>
              <option value="contact">{t("car.disclose.contact", lang)}</option>
            </select>
          </label>
          <button className="primary" disabled={busy || !label.trim()}
                  onClick={() => run(async () => {
                    await api.placeBeacon({ ref_kind: kind,
                      label: label.trim(), disclose }, token!);
                    setLabel("");
                  })}>{t("car.place.go", lang)}</button>
        </div>
        <p className="muted small">{t("car.blindwhy", lang)}</p>
      </div>

      <div className="card">
        <h3>{t("car.placed", lang)}</h3>
        {beacons.length === 0 && (
          <div className="muted small">{t("car.none", lang)}</div>
        )}
        {beacons.map((b) => (
          <div key={b.id}
               style={{ padding: "10px 0", borderBottom: "1px solid var(--line)" }}>
            <div className="row">
              <strong style={{ flex: 1 }}>{b.label}</strong>
              <span className="muted small">
                {b.ref_kind} · {b.state} · {b.disclose} ·{" "}
                {b.scans === 1 ? t("car.scans.one", lang)
                              : fill("car.scans", lang, { n: b.scans })}
                {b.active ? "" : ` · ${t("car.lifted", lang)}`}
              </span>
            </div>
            <div className="row">
              <button disabled={busy}
                      onClick={() => run(async () => {
                        setCustody(await api.beaconCustody(b.id, token!));
                      })}>{t("car.chain", lang)}</button>
              <button disabled={busy}
                      onClick={() => run(async () => {
                        setCard(await api.scanCard(b.id));
                      })}>{t("car.sees", lang)}</button>
              <button disabled={busy}
                      onClick={() => run(async () => {
                        setPage(await api.scanPage(b.id));
                        setQr(await api.scanQr(b.id));
                      })}>{t("car.codeitself", lang)}</button>
              <button disabled={busy}
                      onClick={() => run(async () => {
                        setCustody(null);
                        await api.beacon(b.id, token!);
                      })}>{t("car.refresh", lang)}</button>
              <select value={b.state}
                      onChange={(e) => run(() => api.setBeaconState(
                        b.id, e.target.value, token!))}>
                {["sealed", "in_transit", "delivered", "opened"].map((st) => (
                  <option key={st} value={st}>{st}</option>
                ))}
              </select>
              <button disabled={busy}
                      onClick={() => run(() => api.liftBeacon(b.id, token!))}>
                {t("car.lift", lang)}
              </button>
            </div>
            <div className="row">
              <span className="muted small">{t("car.asscanner", lang)}</span>
              <label>{t("car.kind", lang)}
                <select value={ringKind}
                        onChange={(e) =>
                          setRingKind(e.target.value as RingKind)}>
                  {RINGS.map((r) => <option key={r} value={r}>{r}</option>)}
                </select>
              </label>
              <button disabled={busy}
                      onClick={() => run(() => api.ringHolder(b.id,
                        { kind: ringKind }))}>{t("car.ring", lang)}</button>
              <button disabled={busy}
                      onClick={() => run(() => api.reportFound(b.id,
                        { where: "loading dock" }))}>{t("car.found", lang)}</button>
            </div>
          </div>
        ))}
      </div>

      {card && (
        <div className="card">
          <h3>{t("car.strangercard", lang)}</h3>
          <p><strong>{card.badge}</strong></p>
          <p className="muted small">{card.note}</p>
          <p className="muted small">
            {card.reference} · {card.kind} · {card.state} ·{" "}
            {card.under_custody ? t("car.custody.yes", lang)
                               : t("car.custody.no", lang)}
            {card.held_by
              ? ` · ${fill("car.heldby", lang, { who: card.held_by })}` : ""}
          </p>
          <p className="muted small">
            {t("car.contents", lang)}{" "}
            <strong>{card.contents === null
                       ? t("car.contents.no", lang) : "?"}</strong>
            {" "}{t("car.contents.never", lang)}
          </p>
        </div>
      )}

      {(page || qr) && (
        <div className="card">
          <h3>{t("car.printed", lang)}</h3>
          {qr && (
            <img alt={t("car.scannable", lang)}
                 src={"data:image/svg+xml;utf8," + encodeURIComponent(qr)}
                 style={{ width: 180, height: 180 }} />
          )}
          {page && (
            <p className="muted small">
              {fill("car.landing", lang, { n: page.length })}
            </p>
          )}
        </div>
      )}

      {custody && (
        <div className="card">
          <h3>{t("car.chain", lang)}</h3>
          <p className="muted small">
            {t("car.auditchain", lang)}{" "}
            <strong>
              {custody.audit_chain_intact ? t("car.verifies", lang)
                                          : t("car.notverify", lang)}
            </strong>
            . {t("car.claims", lang)}
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
              {fill("car.controls", lang,
                    { list: custody.controls.required.join(", ") })}
            </p>
          )}
        </div>
      )}

      <div className="card">
        <h3>{t("car.rang", lang)}</h3>
        <label className="row">
          <input type="checkbox" checked={openOnly}
                 onChange={(e) => setOpenOnly(e.target.checked)} />
          {" "}{t("car.openonly", lang)}
        </label>
        {rings.length === 0 && (
          <div className="muted small">{t("car.norings", lang)}</div>
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
                    })}>{t("car.transcript", lang)}</button>
          </div>
        ))}
        {transcript && (
          <p className="muted small">{JSON.stringify(transcript)}</p>
        )}
      </div>
    </div>
  );
}
