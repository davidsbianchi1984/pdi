import { useEffect, useState } from "react";
import { api, ConnectorRow, RobotModel, Row } from "../api";
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
      Select a tenant first.</p></div>;
  }

  return (
    <div className="screen">
      <header className="screen-head">
        <h2>Bridges</h2>
        <span className="muted small">what reaches into this vault</span>
      </header>

      {error && <div className="error">⚠ {error}</div>}
      {said && <div className="muted small">{said}</div>}

      <div className="card">
        <h3>Connected accounts</h3>
        <div className="row">
          <label>Platform
            <input value={platform} placeholder="mastodon"
                   onChange={(e) => setPlatform(e.target.value)} />
          </label>
          <label>Handle
            <input value={handle} placeholder="@ops"
                   onChange={(e) => setHandle(e.target.value)} />
          </label>
          {/* Labelled because a refusal has to name the field the way the
              form does, and the field-label record declines to invent a
              word for a control nobody has labelled. */}
          <label>Direction
            <select value={direction}
                    onChange={(e) => setDirection(e.target.value)}>
              <option value="publish">publish — out</option>
              <option value="collect">collect — in</option>
            </select>
          </label>
          <button className="primary" disabled={busy || !platform.trim()}
                  onClick={() => run(async () => {
                    await api.addConnector({ platform: platform.trim(),
                      direction, handle: handle.trim() || undefined }, token!);
                    setHandle("");
                  })}>Connect</button>
        </div>
        <p className="muted small">
          {Object.keys((catalog?.providers ?? {}) as object).length ||
            ((catalog?.providers ?? []) as unknown[]).length}{" "}
          providers catalogued, each with the directions it can be asked for.
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
                      })}>Its code</button>
              {c.direction === "publish" ? (
                <>
                  <input value={post} placeholder="Say something"
                         onChange={(e) => setPost(e.target.value)} />
                  <button disabled={busy || !post.trim()}
                          onClick={() => run(async () => {
                            await api.publishFromConnector(c.id,
                              { content: post.trim() }, token!);
                            setPost("");
                          })}>Publish</button>
                </>
              ) : (
                <button disabled={busy}
                        onClick={() => run(() => api.ingestToConnector(
                          c.id, [{ content: "an item from elsewhere" }],
                          token!))}>Ingest</button>
              )}
              <button disabled={busy}
                      onClick={() => run(() =>
                        api.removeConnector(c.id, token!))}>Disconnect</button>
            </div>
          </div>
        ))}
        {beacon && <p className="muted small">{JSON.stringify(beacon)}</p>}
        {qr && (
          <img alt="the connector's code"
               src={"data:image/svg+xml;utf8," + encodeURIComponent(qr)}
               style={{ width: 150, height: 150 }} />
        )}
      </div>

      <div className="card">
        <h3>Robots</h3>
        <div className="row">
          <label>Model
            <select value={model} onChange={(e) => setModel(e.target.value)}>
              <option value="">Pick a model…</option>
              {models.map((m) => (
                <option key={m.model} value={m.model}>
                  {m.label}{m.maker ? ` — ${m.maker}` : ""}
                </option>
              ))}
            </select>
          </label>
          <input value={robotName} placeholder="Hall NEO"
                 onChange={(e) => setRobotName(e.target.value)} />
          <button className="primary" disabled={busy || !model}
                  onClick={() => run(async () => {
                    await api.bindRobot({ model,
                      name: robotName.trim() || undefined }, token!);
                    setRobotName("");
                  })}>Bind</button>
        </div>
        <p className="muted small">
          The model has to be one the catalogue knows — an unknown one is a
          404 rather than a row nobody can act on. Everything a bound robot
          sends in is sealed under this tenant's key like anything else.
        </p>
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
                    })}>What it has sent</button>
            <button disabled={busy}
                    onClick={() => run(() => api.robotIngest(String(r.id),
                      { kind: "observation",
                        content: btoa("a reading from the floor") }, token!))}>
              Send something in
            </button>
            <button disabled={busy}
                    onClick={() => run(() =>
                      api.unbindRobot(String(r.id), token!))}>Unbind</button>
          </div>
        ))}
        {data && <p className="muted small">{JSON.stringify(data)}</p>}
      </div>

      <div className="card">
        <h3>What the other products contributed</h3>
        <div className="row">
          <label>Source
            <input value={source} placeholder="jim-mini"
                   onChange={(e) => setSource(e.target.value)} />
          </label>
          <label>Reference
            <input value={ref} placeholder="a reference to withdraw by"
                   onChange={(e) => setRef(e.target.value)} />
          </label>
          <button className="primary" disabled={busy || !source.trim()}
                  onClick={() => run(async () => {
                    const c = await api.contribute({ source: source.trim(),
                      kind: "outcome", payload: { helped: true },
                      ref: ref.trim() || undefined }, token!);
                    setSaid(`Sealed as ${c.key}`);
                  })}>Contribute one</button>
          <button disabled={busy || !ref.trim()}
                  onClick={() => run(() =>
                    api.withdrawContribution(ref.trim(), token!))}>
            Withdraw by reference
          </button>
        </div>
        <p className="muted small">
          {contributions?.count ?? 0} held. The listing is a count and a set
          of keys — never contents. A vault holding a thing is not the same
          as a vault showing it to whoever asks for the list.
        </p>
        {(contributions?.keys ?? []).slice(0, 12).map((k) => (
          <div key={k} className="muted small" style={{ padding: "3px 0" }}>
            {k}
          </div>
        ))}
      </div>

      <div className="card">
        <h3>Something to look at</h3>
        <button disabled={busy}
                onClick={() => run(async () => {
                  const r = await api.seedDemo(admin);
                  setSaid(`Seeded ${String(r.name)} — `
                    + `${String(r.records)} records. `
                    + `${String(r.note ?? "")}`);
                })}>Seed a demo tenant</button>
        <p className="muted small">
          A tenant with records, a bound robot and something ingested, so the
          rest of this console has something true to draw.
        </p>
      </div>
    </div>
  );
}
