import { useCallback, useEffect, useState } from "react";
import {
  api, type Bequest, type GateCeiling, type GatePage, type GateRoster,
} from "../api";
import { useSession } from "../store";

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

  const [bequests, setBequests] = useState<Bequest[]>([]);
  const [ceiling, setCeiling] = useState<GateCeiling | null>(null);
  const [roster, setRoster] = useState<GateRoster | null>(null);
  const [pages, setPages] = useState<GatePage[]>([]);

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
  }, [token]);
  useEffect(load, [load]);

  async function run(action: () => Promise<unknown>, ok?: string) {
    setBusy(true); setError(null); setSaid(null);
    try { await action(); if (ok) setSaid(ok); load(); }
    catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  }

  if (!token) return <p>Paste a tenant token to sign in.</p>;

  return (
    <section className="screen">
      <h2>Continuity &amp; gateway</h2>
      {error && <p className="error">{error}</p>}
      {said && <p className="muted">{said}</p>}

      <h3>Bequests</h3>
      <p className="muted">
        A standing instruction, dormant when written. Creating one grants
        nothing — it records what <em>would</em> become readable, by whom, if
        the condition were ever attested by an operator holding a different
        credential.
      </p>
      {bequests.length === 0 && <p className="muted">Nothing bequeathed.</p>}
      {bequests.map((b) => (
        <div key={b.id} className="card">
          <div className="row">
            <strong>{b.grantee_name}</strong>
            <span className="muted">{b.condition}</span>
            {b.revoked
              ? <span className="pill">revoked</span>
              : b.activated
                ? <span className="pill">in force</span>
                : <span className="muted">dormant</span>}
          </div>
          <p className="muted">Would open: {b.key_prefixes.join(", ")}</p>
          {b.note && <p>{b.note}</p>}
          {b.activated && b.activation_ref && (
            <p className="muted">
              Attested as “{b.activation_ref}”
              {b.activated_at ? ` on ${b.activated_at.slice(0, 10)}` : ""} —
              recorded in the audit chain.
            </p>
          )}
          {!b.revoked && (
            <button disabled={busy}
              onClick={() => {
                if (confirm(`Revoke ${b.grantee_name}'s bequest? It stops being able to open anything.`))
                  run(() => api.revokeBequest(b.id, token), "Revoked.");
              }}>
              Revoke
            </button>
          )}
        </div>
      ))}
      <div className="row">
        <input value={grantee} placeholder="Who inherits the read"
          onChange={(e) => setGrantee(e.target.value)} />
        <input value={prefixes} placeholder="Key prefixes, comma separated"
          onChange={(e) => setPrefixes(e.target.value)} />
        <input value={note} placeholder="Note (optional)"
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
          Record a bequest
        </button>
      </div>

      <h3>Activation — the operator's act</h3>
      <p className="muted">
        Activation needs an admin token, not this tenant's. That separation is
        the point: the person who wrote the bequest cannot also be the one who
        declares its condition met. The reference given here goes into the
        audit chain, and the grant token is shown <strong>once</strong>.
      </p>
      <div className="row">
        <input type="password" value={adminToken}
          placeholder={session.adminToken ? "Admin token (from your session)" : "Admin token"}
          onChange={(e) => setAdminToken(e.target.value)} />
        <input value={ref} placeholder="What attests the condition"
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
            }, "Activated.")}>
            Activate
          </button>
        </div>
      ))}
      {minted && (
        <div className="card">
          <p><strong>Grant token — copy it now.</strong> It is not stored and
            will not be shown again.</p>
          <code>{minted.token}</code>
          <button onClick={() => setMinted(null)}>I have copied it</button>
        </div>
      )}

      <h3>Redeeming — the heir's side</h3>
      <p className="muted">
        Two separate secrets, and neither works alone: the grant token says
        the condition was attested, the customer key decrypts. An executor who
        holds only the token opens nothing.
      </p>
      <div className="row">
        <input type="password" value={heirGrant} placeholder="Grant token"
          onChange={(e) => setHeirGrant(e.target.value)} />
        <input type="password" value={heirKey} placeholder="Customer key (base64)"
          onChange={(e) => setHeirKey(e.target.value)} />
        <button disabled={busy || !heirGrant.trim() || !heirKey.trim()}
          onClick={() => run(async () => {
            const out = await api.bequestKeys(heirGrant.trim(), heirKey.trim());
            setHeirKeys(out.keys ?? []);
            setHeirValue(null);
          })}>
          What can I open?
        </button>
      </div>
      {heirKeys && heirKeys.length === 0
        && <p className="muted">Nothing is readable under that grant.</p>}
      {(heirKeys ?? []).map((k) => (
        <div key={k} className="row">
          <span>{k}</span>
          <button disabled={busy}
            onClick={() => run(async () => {
              const out = await api.bequestRead(k, heirGrant.trim(), heirKey.trim());
              setHeirValue(typeof out.value === "string"
                ? out.value : JSON.stringify(out.value, null, 1));
            })}>
            Read
          </button>
        </div>
      ))}
      {heirValue && <pre>{heirValue}</pre>}

      <h3>The gateway's ceiling</h3>
      {/* Rendered from the server, key by key. This is the statement of what
          the agent may and may not do; paraphrasing it in the client would
          make the console the authority on a boundary it does not own. */}
      {ceiling && (
        <div className="card">
          <p><strong>{ceiling.rule}</strong></p>
          <p className="muted">It may:</p>
          <ul>
            {Object.entries(ceiling.may).map(([k, v]) => (
              <li key={k}><strong>{k}</strong> — {v}</li>
            ))}
          </ul>
          <p className="muted">It may never:</p>
          <ul>
            {Object.entries(ceiling.may_never).map(([k, v]) => (
              <li key={k}><strong>{k}</strong> — {v}</li>
            ))}
          </ul>
        </div>
      )}

      <h3>Who is on shift</h3>
      {roster && (
        <p className="muted">
          {roster.anybody_on_shift
            ? `${roster.on_now.map((r) => r.name).join(", ")} on now.`
            : "Nobody on shift."}
          {roster.timezone ? ` Times in ${roster.timezone}.` : ""}
          {!roster.configured && " No roster configured yet."}
        </p>
      )}
      {(roster?.roster ?? []).map((r) => (
        <div key={r.id} className="card">
          <div className="row">
            <strong>{r.name}</strong>
            <span className="muted">{r.role}</span>
            {r.days && <span className="muted">{r.days}</span>}
            {r.from && <span className="muted">{r.from}–{r.to}</span>}
            {r.crosses_midnight && <span className="muted">over midnight</span>}
          </div>
          <button disabled={busy}
            onClick={() => run(() => api.removeFromRoster(r.id, token), "Removed.")}>
            Remove
          </button>
        </div>
      ))}
      <div className="row">
        <input value={rosterName} placeholder="Name"
          onChange={(e) => setRosterName(e.target.value)} />
        <select value={rosterRole} onChange={(e) => setRosterRole(e.target.value)}>
          {["on-call", "supervisor", "reception", "security", "site lead"]
            .map((r) => <option key={r} value={r}>{r}</option>)}
        </select>
        <button disabled={busy || !rosterName.trim()}
          onClick={() => run(async () => {
            await api.addToRoster({ name: rosterName.trim(), role: rosterRole }, token);
            setRosterName("");
          }, "Added.")}>
          Add to roster
        </button>
      </div>
      <div className="row">
        <input value={tz} placeholder="Timezone (Europe/London)"
          onChange={(e) => setTz(e.target.value)} />
        <button disabled={busy || !tz.trim()}
          onClick={() => run(async () => {
            await api.setGateTimezone(tz.trim(), token);
            setTz("");
          }, "Timezone set.")}>
          Set
        </button>
      </div>

      <h3>What it sent</h3>
      <p className="muted">
        Pages the gateway raised when nobody was reachable, and whether they
        arrived. A page that failed to deliver is the one worth seeing.
      </p>
      {pages.length === 0 && <p className="muted">Nothing paged.</p>}
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
                Retry
              </button>
            )}
          </div>
        </div>
      ))}
    </section>
  );
}
