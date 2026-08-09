import { useEffect, useState } from "react";
import { api, getBase, setBase, type PairInfo } from "../api";
import { Problems } from "../Problems";
import { useSession } from "../store";
import { deviceLanguage, Lang, t } from "../l10n";

export function Settings() {
  const { session, setSession, clear } = useSession();
  const lang = (session.language as Lang) ?? deviceLanguage();
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
      <header className="screen-head"><h2>{t("st.title", lang)}</h2></header>
      <div className="card">
        <h3>{t("st.connection", lang)}</h3>
        <label>{t("st.base", lang)}
          <input value={base} onChange={(e) => setBaseInput(e.target.value)} />
        </label>
        <label>
          {t("co.admin.ph", lang)}{" "}
          <span className="muted small">{t("st.admin.note", lang)}</span>
          <input value={admin} onChange={(e) => setAdmin(e.target.value)} placeholder="PDI_ADMIN_TOKEN" />
        </label>
        <button className="primary" onClick={save}>
          {saved ? t("st.saved", lang) : t("st.save", lang)}
        </button>
      </div>

      <OfflinePosture />
      {pair && (
        <div className="card">
          <h3>{t("st.phone", lang)}</h3>
          <p className="muted small">{pair.note}</p>
          <div className="pair">
            {/* The literal rather than `pair.qr_svg`, which holds this exact
                    string from the server. Same request, and the route audit
                    can see it: a path that only exists in a response body is a
                    door no static check can find, and the last one of those got
                    itself exempted as "not a client call" and then went years
                    without anybody noticing it rendered nowhere. */}
            <img className="pair-qr" src={getBase() + "/pair/qr.svg"}
                 alt={t("st.qr.alt", lang)} />
            <div>
              <div className="mono pair-url">{pair.console_url}</div>
              <ol className="pair-steps">{pair.how.map((s) => <li key={s}>{s}</li>)}</ol>
            </div>
          </div>
        </div>
      )}
      <div className="card">
        <h3>{t("st.session", lang)}</h3>
        <div className="muted small">
          {t("st.tenant", lang)} {session.tenantName || t("st.none", lang)}
        </div>
        <button className="danger" onClick={clear}>{t("st.signout", lang)}</button>
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
  const { session } = useSession();
  const lang = (session.language as Lang) ?? deviceLanguage();
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
      <h3>{posture.offline ? t("st.offline", lang) : t("st.online", lang)}</h3>
      <p className="small">
        {posture.external_transmission_possible
          ? t("st.canreach", lang)
          : t("st.noreach", lang)}
      </p>
      <ul className="small muted">
        {posture.guarantees.map((g) => <li key={g}>{g}</li>)}
      </ul>
      <p className="muted small">{posture.local_destinations_allowed}</p>
    </div>
  );
}
