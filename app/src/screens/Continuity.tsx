import { useCallback, useEffect, useState } from "react";
import {
  api, type Bequest, type GateCeiling, type GateChannel,
  type GatePage, type GateRoster,
} from "../api";
import { useSession } from "../store";
import { deviceLanguage, fill, Lang, t } from "../l10n";

/**
 * Continuity, and the gateway that stands in when nobody is on shift.
 *
 * Both had complete backends and no caller anywhere. Bequests are the whole
 * continuity path — what may be read, by whom, if a condition is ever
 * attested — and for a vault that is the part that matters at the moment it
 * is needed, which is a moment the person who set it up is not present for.
 *
 * Three actors touch this screen and they are kept visibly apart, because
 * conflating them is how a continuity feature becomes a back door:
 *
 * - the **tenant**, who records a bequest and may revoke it while alive;
 * - the **operator**, holding an admin token, who activates one against an
 *   attested reference — that reference goes into the audit chain;
 * - the **heir**, who holds a grant token and, separately, the customer key.
 *
 * A bequest grants nothing when created. It is a standing instruction that
 * stays dormant until somebody with a different credential attests the
 * condition, and the screen says so rather than leaving "created" to imply
 * "in force".
 */
export function Continuity() {
  const { session } = useSession();
  const token = session.tenantToken;
  const lang = (session.language as Lang) ?? deviceLanguage();

  const [bequests, setBequests] = useState<Bequest[]>([]);
  const [ceiling, setCeiling] = useState<GateCeiling | null>(null);
  const [roster, setRoster] = useState<GateRoster | null>(null);
  const [pages, setPages] = useState<GatePage[]>([]);
  const [channel, setChannel] = useState<GateChannel | null>(null);

  const [grantee, setGrantee] = useState("");
  const [prefixes, setPrefixes] = useState("");
  const [note, setNote] = useState("");
  // The session already holds an admin token when the operator signed in
  // with one. Asking again would be theatre; the field is here only for
  // the case where it does not.
  const [adminToken, setAdminToken] = useState(session.adminToken ?? "");
  const [ref, setRef] = useState("");
  const [minted, setMinted] = useState<{ id: string; token: string } | null>(null);
  const [heirGrant, setHeirGrant] = useState("");
  const [heirKey, setHeirKey] = useState("");
  const [heirKeys, setHeirKeys] = useState<string[] | null>(null);
  const [heirValue, setHeirValue] = useState<string | null>(null);
  const [rosterName, setRosterName] = useState("");
  const [rosterRole, setRosterRole] = useState("on-call");
  const [tz, setTz] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [said, setSaid] = useState<string | null>(null);

  const load = useCallback(() => {
    if (!token) return;
    api.bequests(token).then(setBequests).catch(() => setBequests([]));
    api.gateCeiling(token).then(setCeiling).catch(() => setCeiling(null));
    api.gateRoster(token).then(setRoster).catch(() => setRoster(null));
    api.gatePages(token).then(setPages).catch(() => setPages([]));
    // Whether a page can be delivered at all. The screen listed pages and
    // whether each one arrived, and never said whether a channel was
    // configured — so a deployment with none showed "nothing paged", which
    // reads as *nothing needed paging* and means *nothing could have been*.
    api.gateChannel(token).then(setChannel).catch(() => setChannel(null));
  }, [token]);
  useEffect(load, [load]);

  async function run(action: () => Promise<unknown>, ok?: string) {
    setBusy(true); setError(null); setSaid(null);
    try { await action(); if (ok) setSaid(ok); load(); }
    catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  }

  if (!token) return <p>{t("co.signin", lang)}</p>;

  return (
    <section className="screen">
      <h2>{t("co.title", lang)}</h2>
      {error && <p className="error">{error}</p>}
      {said && <p className="muted">{said}</p>}

      <h3>{t("co.bequests", lang)}</h3>
      <p className="muted">{t("co.bequests.note", lang)}</p>
      {bequests.length === 0 && <p className="muted">{t("co.nothing", lang)}</p>}
      {bequests.map((b) => (
        <div key={b.id} className="card">
          <div className="row">
            <strong>{b.grantee_name}</strong>
            <span className="muted">{b.condition}</span>
            {b.revoked
              ? <span className="pill">revoked</span>
              : b.activated
                ? <span className="pill">{t("co.inforce", lang)}</span>
                : <span className="muted">{t("co.dormant", lang)}</span>}
          </div>
          <p className="muted">{t("co.wouldopen", lang)} {b.key_prefixes.join(", ")}</p>
          {b.note && <p>{b.note}</p>}
          {b.activated && b.activation_ref && (
            <p className="muted">
              {b.activated_at
                ? fill("co.attested.dated", lang, {
                    ref: b.activation_ref,
                    date: b.activated_at.slice(0, 10) })
                : fill("co.attested", lang, { ref: b.activation_ref })}
            </p>
          )}
          {!b.revoked && (
            <button disabled={busy}
              onClick={() => {
                if (confirm(`Revoke ${b.grantee_name}'s bequest? It stops being able to open anything.`))
                  run(() => api.revokeBequest(b.id, token), "Revoked.");
              }}>
              {t("co.revoke", lang)}
            </button>
          )}
        </div>
      ))}
      <div className="row">
        <input value={grantee} placeholder={t("co.grantee.ph", lang)}
          onChange={(e) => setGrantee(e.target.value)} />
        <input value={prefixes} placeholder={t("co.prefixes.ph", lang)}
          onChange={(e) => setPrefixes(e.target.value)} />
        <input value={note} placeholder={t("co.note.ph", lang)}
          onChange={(e) => setNote(e.target.value)} />
        <button disabled={busy || !grantee.trim() || !prefixes.trim()}
          onClick={() => run(async () => {
            await api.createBequest({
              grantee_name: grantee.trim(),
              key_prefixes: prefixes.split(",").map((s) => s.trim()).filter(Boolean),
              note: note.trim() || undefined,
            }, token);
            setGrantee(""); setPrefixes(""); setNote("");
          }, "Recorded. It opens nothing until it is activated.")}>
          {t("co.record", lang)}
        </button>
      </div>

      <h3>{t("co.activation", lang)}</h3>
      <p className="muted">{t("co.activation.note", lang)}</p>
      <div className="row">
        <input type="password" value={adminToken}
          placeholder={session.adminToken
            ? t("co.admin.session.ph", lang) : t("co.admin.ph", lang)}
          onChange={(e) => setAdminToken(e.target.value)} />
        <input value={ref} placeholder={t("co.ref.ph", lang)}
          onChange={(e) => setRef(e.target.value)} />
      </div>
      {bequests.filter((b) => !b.activated && !b.revoked).map((b) => (
        <div key={b.id} className="row">
          <span>{b.grantee_name}</span>
          <button disabled={busy || !adminToken.trim() || !ref.trim()}
            onClick={() => run(async () => {
              const out = await api.activateBequest(b.id, ref.trim(), adminToken.trim());
              if (out.grant_token) setMinted({ id: b.id, token: out.grant_token });
              setRef("");
            }, t("co.activated", lang))}>
            {t("co.activate", lang)}
          </button>
        </div>
      ))}
      {minted && (
        <div className="card">
          <p><strong>{t("co.minted", lang)}</strong>{" "}
            {t("co.minted.note", lang)}</p>
          <code>{minted.token}</code>
          <button onClick={() => setMinted(null)}>{t("co.copied", lang)}</button>
        </div>
      )}

      {bequests.filter((b) => b.activated && !b.revoked).length > 0 && (
        <>
          <h3>{t("co.takeback", lang)}</h3>
          <p className="muted">{t("co.takeback.note", lang)}</p>
          {bequests.filter((b) => b.activated && !b.revoked).map((b) => (
            <div key={b.id} className="row">
              <span>{b.grantee_name}</span>
              <button className="danger"
                      disabled={busy || !adminToken.trim()}
                      onClick={() => run(
                        () => api.revokeBequestGrant(b.id, adminToken.trim()),
                        t("co.revoked.grant", lang))}>
                {t("co.revoke.grant", lang)}
              </button>
            </div>
          ))}
        </>
      )}

      <h3>{t("co.redeem", lang)}</h3>
      <p className="muted">{t("co.redeem.note", lang)}</p>
      <div className="row">
        <input type="password" value={heirGrant} placeholder={t("co.grant.ph", lang)}
          onChange={(e) => setHeirGrant(e.target.value)} />
        <input type="password" value={heirKey} placeholder={t("co.custkey.ph", lang)}
          onChange={(e) => setHeirKey(e.target.value)} />
        <button disabled={busy || !heirGrant.trim() || !heirKey.trim()}
          onClick={() => run(async () => {
            const out = await api.bequestKeys(heirGrant.trim(), heirKey.trim());
            setHeirKeys(out.keys ?? []);
            setHeirValue(null);
          })}>
          {t("co.whatopen", lang)}
        </button>
      </div>
      {heirKeys && heirKeys.length === 0
        && <p className="muted">{t("co.nothing.readable", lang)}</p>}
      {(heirKeys ?? []).map((k) => (
        <div key={k} className="row">
          <span>{k}</span>
          <button disabled={busy}
            onClick={() => run(async () => {
              const out = await api.bequestRead(k, heirGrant.trim(), heirKey.trim());
              setHeirValue(typeof out.value === "string"
                ? out.value : JSON.stringify(out.value, null, 1));
            })}>
            {t("co.read", lang)}
          </button>
        </div>
      ))}
      {heirValue && <pre>{heirValue}</pre>}

      <h3>{t("co.ceiling", lang)}</h3>
      {/* Rendered from the server, key by key. This is the statement of what
          the agent may and may not do; paraphrasing it in the client would
          make the console the authority on a boundary it does not own. */}
      {ceiling && (
        <div className="card">
          <p><strong>{ceiling.rule}</strong></p>
          <p className="muted">{t("co.may", lang)}</p>
          <ul>
            {Object.entries(ceiling.may).map(([k, v]) => (
              <li key={k}><strong>{k}</strong> — {v}</li>
            ))}
          </ul>
          <p className="muted">{t("co.maynever", lang)}</p>
          <ul>
            {Object.entries(ceiling.may_never).map(([k, v]) => (
              <li key={k}><strong>{k}</strong> — {v}</li>
            ))}
          </ul>
        </div>
      )}

      <h3>{t("co.shift", lang)}</h3>
      {roster && (
        <p className="muted">
          {roster.anybody_on_shift
            ? `${roster.on_now.map((r) => r.name).join(", ")} on now.`
            : t("co.nobody", lang)}
          {roster.timezone ? ` Times in ${roster.timezone}.` : ""}
          {!roster.configured && t("co.noroster", lang)}
        </p>
      )}
      {(roster?.roster ?? []).map((r) => (
        <div key={r.id} className="card">
          <div className="row">
            <strong>{r.name}</strong>
            <span className="muted">{r.role}</span>
            {r.days && <span className="muted">{r.days}</span>}
            {r.from && <span className="muted">{r.from}–{r.to}</span>}
            {r.crosses_midnight && <span className="muted">{t("co.overmidnight", lang)}</span>}
          </div>
          <button disabled={busy}
            onClick={() => run(() => api.removeFromRoster(r.id, token), t("co.removed", lang))}>
            {t("co.remove", lang)}
          </button>
        </div>
      ))}
      <div className="row">
        <label>{t("co.name.ph", lang)}
          <input value={rosterName} placeholder={t("co.name.ph", lang)}
            onChange={(e) => setRosterName(e.target.value)} />
        </label>
        <label>{t("co.role.ph", lang)}
          <select value={rosterRole} onChange={(e) => setRosterRole(e.target.value)}>
            {["on-call", "supervisor", "reception", "security", "site lead"]
              .map((r) => <option key={r} value={r}>{r}</option>)}
          </select>
        </label>
        <button disabled={busy || !rosterName.trim()}
          onClick={() => run(async () => {
            await api.addToRoster({ name: rosterName.trim(), role: rosterRole }, token);
            setRosterName("");
          }, "Added.")}>
          {t("co.addroster", lang)}
        </button>
      </div>
      <div className="row">
        <input value={tz} placeholder={t("co.tz.ph", lang)}
          onChange={(e) => setTz(e.target.value)} />
        <button disabled={busy || !tz.trim()}
          onClick={() => run(async () => {
            await api.setGateTimezone(tz.trim(), token);
            setTz("");
          }, "Timezone set.")}>
          {t("co.set", lang)}
        </button>
      </div>

      <h3>{t("co.sent", lang)}</h3>
      <p className="muted">{t("co.sent.note", lang)}</p>
      {channel && (
        <p className="muted">
          {t("co.channel", lang)}{" "}
          <strong>
            {channel.configured
              ? t("co.configured", lang) : t("co.notconfigured", lang)}
          </strong>
          {channel.signed ? t("co.signed", lang) : ""}
          {channel.note ? ` — ${channel.note}` : ""}
        </p>
      )}
      {pages.length === 0 && (
        <p className="muted">
          {channel && !channel.configured
            ? t("co.nothingcould", lang)
            : t("co.nothingpaged", lang)}
        </p>
      )}
      {pages.map((p, i) => (
        <div key={String(p.id ?? i)} className="card">
          <div className="row">
            <span className="muted">
              {p.delivered ? "delivered" : "not delivered"}
            </span>
            {!p.delivered && p.id && (
              <button disabled={busy}
                onClick={() => run(() => api.retryPage(String(p.id), token),
                  "Retried.")}>
                {t("co.retry", lang)}
              </button>
            )}
          </div>
        </div>
      ))}
    </section>
  );
}
