import { useEffect, useState } from "react";
import { api, ConnectorRow, RobotModel, Row } from "../api";
import { deviceLanguage, fill, Lang, t } from "../l10n";
import { useSession } from "../store";

/**
 * The other systems that reach into this vault — a connected account, a
 * robot in a building, another product contributing what it learned.
 *
 * Seventeen routes. What they have in common is that each one is a way for
 * something outside PDI to put material inside it, so each is shown with
 * what it seals and under whose key.
 *
 * A contribution is the interesting case. `POST /contributions` is how JIM
 * and QRME hand anonymised outcomes to the vault, and it answers with the
 * key it sealed them under — which means the contributor can withdraw them
 * by reference later, and `GET /contributions` is a count and a key list and
 * never the contents. That is right: the vault holding a thing is not the
 * vault being able to show it to whoever asks.
 */
export function Bridges() {
  const { session } = useSession();
  const lang = (session.language as Lang) ?? deviceLanguage();
  const [connectors, setConnectors] = useState<ConnectorRow[]>([]);
  const [catalog, setCatalog] = useState<Row | null>(null);
  const [models, setModels] = useState<RobotModel[]>([]);
  const [robots, setRobots] = useState<Row[]>([]);
  const [contributions, setContributions] =
    useState<{ count: number; keys: string[] } | null>(null);
  const [beacon, setBeacon] = useState<Row | null>(null);
  const [qr, setQr] = useState<string | null>(null);
  const [data, setData] = useState<Row | null>(null);
  const [said, setSaid] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [platform, setPlatform] = useState("mastodon");
  const [handle, setHandle] = useState("");
  const [direction, setDirection] = useState("publish");
  const [post, setPost] = useState("");
  const [model, setModel] = useState("");
  const [robotName, setRobotName] = useState("");
  const [source, setSource] = useState("jim-mini");
  const [ref, setRef] = useState("");

  const token = session.tenantToken;
  const admin = session.adminToken || undefined;

  function load() {
    api.connectorCatalog().then(setCatalog).catch(fail);
    api.roboticsCatalog().then((r) => setModels(r.robots)).catch(fail);
    if (!token) return;
    api.connectors(token).then(setConnectors).catch(fail);
    api.robots(token).then(setRobots).catch(fail);
    api.contributions(token).then(setContributions).catch(fail);
  }
  function fail(e: unknown) { setError((e as Error).message); }
  useEffect(load, [token]);

  async function run(work: () => Promise<unknown>) {
    setBusy(true); setError(null); setSaid(null);
    try { await work(); load(); } catch (e) { fail(e); }
    finally { setBusy(false); }
  }

  if (!token) {
    return <div className="screen"><p className="muted center">
      {t("bri.pick", lang)}</p></div>;
  }

  return (
    <div className="screen">
      <header className="screen-head">
        <h2>{t("bri.title", lang)}</h2>
        <span className="muted small">{t("bri.sub", lang)}</span>
      </header>

      {error && <div className="error">⚠ {error}</div>}
      {said && <div className="muted small">{said}</div>}

      <div className="card">
        <h3>{t("bri.accounts", lang)}</h3>
        <div className="row">
          <label>{t("bri.platform", lang)}
            <input value={platform} placeholder="mastodon"
                   onChange={(e) => setPlatform(e.target.value)} />
          </label>
          <label>{t("bri.handle", lang)}
            <input value={handle} placeholder="@ops"
                   onChange={(e) => setHandle(e.target.value)} />
          </label>
          {/* Labelled because a refusal has to name the field the way the
              form does, and the field-label record declines to invent a
              word for a control nobody has labelled. */}
          <label>{t("bri.direction", lang)}
            <select value={direction}
                    onChange={(e) => setDirection(e.target.value)}>
              <option value="publish">{t("bri.dir.publish", lang)}</option>
              <option value="collect">{t("bri.dir.collect", lang)}</option>
            </select>
          </label>
          <button className="primary" disabled={busy || !platform.trim()}
                  onClick={() => run(async () => {
                    await api.addConnector({ platform: platform.trim(),
                      direction, handle: handle.trim() || undefined }, token!);
                    setHandle("");
                  })}>{t("bri.connect", lang)}</button>
        </div>
        <p className="muted small">
          {fill("bri.providers", lang, {
            n: Object.keys((catalog?.providers ?? {}) as object).length ||
               ((catalog?.providers ?? []) as unknown[]).length,
          })}
        </p>
        {connectors.map((c) => (
          <div key={c.id}
               style={{ padding: "10px 0", borderBottom: "1px solid var(--line)" }}>
            <div className="row">
              <strong style={{ flex: 1 }}>
                {c.platform} {c.handle ?? ""}
              </strong>
              <span className="muted small">
                {c.direction} · {c.collected} in · {c.published} out
              </span>
            </div>
            <div className="row">
              <button disabled={busy}
                      onClick={() => run(async () => {
                        setBeacon(await api.connectorBeacon(c.id, token!));
                        setQr(await api.connectorQr(c.id, token!));
                      })}>{t("bri.itscode", lang)}</button>
              {c.direction === "publish" ? (
                <>
                  <input value={post} placeholder={t("bri.say.ph", lang)}
                         onChange={(e) => setPost(e.target.value)} />
                  <button disabled={busy || !post.trim()}
                          onClick={() => run(async () => {
                            await api.publishFromConnector(c.id,
                              { content: post.trim() }, token!);
                            setPost("");
                          })}>{t("bri.publish", lang)}</button>
                </>
              ) : (
                <>
                  <button disabled={busy}
                          onClick={() => run(() => api.ingestToConnector(
                            c.id, [{ content: "an item from elsewhere" }],
                            token!))}>{t("bri.ingest", lang)}</button>
                  {c.handle ? (
                    <button disabled={busy}
                            onClick={() => run(() => api.scrapeConnector(
                              c.id, token!))}>{t("bri.scrape", lang)}</button>
                  ) : null}
                </>
              )}
              <button disabled={busy}
                      onClick={() => run(() =>
                        api.removeConnector(c.id, token!))}>
                {t("bri.disconnect", lang)}</button>
            </div>
          </div>
        ))}
        {beacon && <p className="muted small">{JSON.stringify(beacon)}</p>}
        {qr && (
          <img alt={t("bri.code.alt", lang)}
               src={"data:image/svg+xml;utf8," + encodeURIComponent(qr)}
               style={{ width: 150, height: 150 }} />
        )}
      </div>

      <div className="card">
        <h3>{t("bri.robots", lang)}</h3>
        <div className="row">
          <label>{t("bri.model", lang)}
            <select value={model} onChange={(e) => setModel(e.target.value)}>
              <option value="">{t("bri.model.pick", lang)}</option>
              {models.map((m) => (
                <option key={m.model} value={m.model}>
                  {m.label}{m.maker ? ` — ${m.maker}` : ""}
                </option>
              ))}
            </select>
          </label>
          <input value={robotName} placeholder={t("bri.robot.ph", lang)}
                 onChange={(e) => setRobotName(e.target.value)} />
          <button className="primary" disabled={busy || !model}
                  onClick={() => run(async () => {
                    await api.bindRobot({ model,
                      name: robotName.trim() || undefined }, token!);
                    setRobotName("");
                  })}>{t("bri.bind", lang)}</button>
        </div>
        <p className="muted small">{t("bri.robots.note", lang)}</p>
        {robots.map((r) => (
          <div key={String(r.id)} className="row"
               style={{ padding: "8px 0", borderBottom: "1px solid var(--line)" }}>
            <span style={{ flex: 1 }}>
              {String(r.name ?? r.model)}{" "}
              <span className="muted small">{String(r.model)}</span>
            </span>
            <button disabled={busy}
                    onClick={() => run(async () => {
                      setData(await api.robotData(String(r.id), token!));
                    })}>{t("bri.sent", lang)}</button>
            <button disabled={busy}
                    onClick={() => run(() => api.robotIngest(String(r.id),
                      { kind: "observation",
                        content: btoa("a reading from the floor") }, token!))}>
              {t("bri.sendin", lang)}
            </button>
            <button disabled={busy}
                    onClick={() => run(() =>
                      api.unbindRobot(String(r.id), token!))}>
              {t("bri.unbind", lang)}</button>
          </div>
        ))}
        {data && <p className="muted small">{JSON.stringify(data)}</p>}
      </div>

      <div className="card">
        <h3>{t("bri.contributed", lang)}</h3>
        <div className="row">
          <label>{t("bri.source", lang)}
            <input value={source} placeholder={t("bri.source.ph", lang)}
                   onChange={(e) => setSource(e.target.value)} />
          </label>
          <label>{t("bri.ref", lang)}
            <input value={ref} placeholder={t("bri.ref.ph", lang)}
                   onChange={(e) => setRef(e.target.value)} />
          </label>
          <button className="primary" disabled={busy || !source.trim()}
                  onClick={() => run(async () => {
                    const c = await api.contribute({ source: source.trim(),
                      kind: "outcome", payload: { helped: true },
                      ref: ref.trim() || undefined }, token!);
                    setSaid(fill("bri.sealed", lang, { key: c.key }));
                  })}>{t("bri.contribute", lang)}</button>
          <button disabled={busy || !ref.trim()}
                  onClick={() => run(() =>
                    api.withdrawContribution(ref.trim(), token!))}>
            {t("bri.withdraw", lang)}
          </button>
        </div>
        <p className="muted small">
          {fill("bri.held", lang, { n: contributions?.count ?? 0 })}
        </p>
        {(contributions?.keys ?? []).slice(0, 12).map((k) => (
          <div key={k} className="muted small" style={{ padding: "3px 0" }}>
            {k}
          </div>
        ))}
      </div>

      <div className="card">
        <h3>{t("bri.look", lang)}</h3>
        <button disabled={busy}
                onClick={() => run(async () => {
                  const r = await api.seedDemo(admin);
                  setSaid(fill("bri.seeded", lang, {
                    name: String(r.name), n: String(r.records),
                    note: String(r.note ?? ""),
                  }));
                })}>{t("bri.seed", lang)}</button>
        <p className="muted small">{t("bri.seed.note", lang)}</p>
      </div>
    </div>
  );
}
