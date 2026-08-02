import { useEffect, useState } from "react";
import { api, getBase, setBase, type PairInfo } from "../api";
import { Problems } from "../Problems";
import { useSession } from "../store";

export function Settings() {
  const { session, setSession, clear } = useSession();
  const [base, setBaseInput] = useState(getBase());
  const [admin, setAdmin] = useState(session.adminToken || "");
  const [saved, setSaved] = useState(false);
  const [pair, setPair] = useState<PairInfo | null>(null);

  useEffect(() => {
    api.pair().then(setPair).catch(() => setPair(null));
  }, []);

  function save() {
    setBase(base);
    setSession({ adminToken: admin || undefined });
    setSaved(true);
    setTimeout(() => setSaved(false), 1500);
  }

  return (
    <div className="screen">
      <header className="screen-head"><h2>Settings</h2></header>
      <div className="card">
        <h3>Connection</h3>
        <label>Backend base URL<input value={base} onChange={(e) => setBaseInput(e.target.value)} /></label>
        <label>
          Admin token <span className="muted small">(leave blank if the backend runs open, dev mode)</span>
          <input value={admin} onChange={(e) => setAdmin(e.target.value)} placeholder="PDI_ADMIN_TOKEN" />
        </label>
        <button className="primary" onClick={save}>{saved ? "Saved ✓" : "Save"}</button>
      </div>

      <OfflinePosture />
      {pair && (
        <div className="card">
          <h3>Open on your phone</h3>
          <p className="muted small">{pair.note}</p>
          <div className="pair">
            {/* The literal rather than `pair.qr_svg`, which holds this exact
                    string from the server. Same request, and the route audit
                    can see it: a path that only exists in a response body is a
                    door no static check can find, and the last one of those got
                    itself exempted as "not a client call" and then went years
                    without anybody noticing it rendered nowhere. */}
            <img className="pair-qr" src={getBase() + "/pair/qr.svg"} alt="QR code for the console URL on this network" />
            <div>
              <div className="mono pair-url">{pair.console_url}</div>
              <ol className="pair-steps">{pair.how.map((s) => <li key={s}>{s}</li>)}</ol>
            </div>
          </div>
        </div>
      )}
      <div className="card">
        <h3>Session</h3>
        <div className="muted small">Tenant: {session.tenantName || "none"}</div>
        <button className="danger" onClick={clear}>Sign out</button>
      </div>
      <Problems />
    </div>
  );
}


/** What this deployment can and cannot reach.
 *
 *  Offline mode was settable and unreadable: the flag existed, the guarantee
 *  was written in a docstring, and there was nowhere for the person running
 *  the deployment — or an auditor standing behind them — to see the answer.
 *
 *      asked     can the guarantee be turned on
 *      mattered  can it be checked
 *
 *  Read-only on purpose. This is a posture the deployment sets in its
 *  environment, not a switch in a console: a button here would imply somebody
 *  signed into the app can decide whether the host talks to the internet.
 */
function OfflinePosture() {
  const [posture, setPosture] = useState<Awaited<
    ReturnType<typeof api.offlineStatus>> | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    api.offlineStatus().then(setPosture).catch(() => setFailed(true));
  }, []);

  if (failed) return null;
  if (!posture) return <div className="card"><p className="small">…</p></div>;

  return (
    <div className="card">
      <h3>{posture.offline ? "Offline — nothing leaves this host"
                           : "Online"}</h3>
      <p className="small">
        {posture.external_transmission_possible
          ? "This deployment can reach other machines."
          : "Every path out of this host refuses any address that is not "
            + "this machine or its own network."}
      </p>
      <ul className="small muted">
        {posture.guarantees.map((g) => <li key={g}>{g}</li>)}
      </ul>
      <p className="muted small">{posture.local_destinations_allowed}</p>
    </div>
  );
}
