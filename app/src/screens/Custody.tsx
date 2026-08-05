import { useEffect, useState } from "react";
import { api, BaaStatus, CompliancePrograms, HostingMode, KeyVersion,
         Row, TenantKey } from "../api";
import { useSession } from "../store";

/**
 * Who holds the key, who holds the hardware, and what paperwork the law
 * wants before either matters.
 *
 * Twenty-two routes, and the one at the top of the screen is the only
 * question this product really answers: **can the operator decrypt this?**
 * The server returns that as a boolean with a sentence attached, and the
 * sentence is printed rather than paraphrased, because every other claim on
 * this page is downstream of it.
 *
 * The key provider is `held` or `kms`. It is *not* `customer`, which is what
 * the concept is called in the plan copy, in the hosting guarantees, and in
 * the field name `customer_managed` two lines away — so the obvious guess is
 * a 422 and driving it is what showed that.
 *
 * `DELETE /key` hands a tenant back to deployment custody and answers 409 if
 * it was never under its own. That refusal is shown rather than swallowed:
 * an operator pressing it wants to know whether the state changed.
 */
export function Custody() {
  const { session } = useSession();
  const [key, setKey] = useState<TenantKey | null>(null);
  const [versions, setVersions] = useState<KeyVersion[]>([]);
  const [snapshot, setSnapshot] = useState<Row[] | null>(null);
  const [programs, setPrograms] = useState<CompliancePrograms[]>([]);
  const [baa, setBaa] = useState<BaaStatus | null>(null);
  const [tenantBaaRow, setTenantBaaRow] = useState<BaaStatus | null>(null);
  const [modes, setModes] = useState<Record<string, HostingMode>>({});
  const [mine, setMine] = useState<(HostingMode & { tenant_id: string }) | null>(null);
  const [history, setHistory] = useState<Row[]>([]);
  const [minted, setMinted] = useState<string | null>(null);
  const [said, setSaid] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [customerKey, setCustomerKey] = useState("");
  const [legalName, setLegalName] = useState("");
  const [operatorName, setOperatorName] = useState("Vault Operations LLC");
  const [effective, setEffective] = useState("");
  const [recordKey, setRecordKey] = useState("");
  const [deleteMode, setDeleteMode] = useState("soft");

  const token = session.tenantToken;
  const admin = session.adminToken || undefined;
  const tenantId = session.tenantId;

  function load() {
    api.compliancePrograms().then((r) => setPrograms(r.programs)).catch(fail);
    api.hostingModes().then((r) => setModes(r.modes)).catch(fail);
    if (!token) return;
    api.tenantKey(token).then(setKey).catch(fail);
    api.baaStatus(token).then(setBaa).catch(fail);
    if (tenantId) {
      api.hosting(tenantId, token).then(setMine).catch(fail);
      api.hostingHistory(tenantId, token).then(setHistory).catch(fail);
      // 404 until one is on file, which is itself the answer.
      api.tenantBaa(tenantId, admin).then(setTenantBaaRow)
        .catch(() => setTenantBaaRow(null));
    }
  }
  function fail(e: unknown) { setError((e as Error).message); }
  useEffect(load, [token, tenantId]);

  async function run(work: () => Promise<unknown>) {
    setBusy(true); setError(null); setSaid(null);
    try { await work(); load(); } catch (e) { fail(e); }
    finally { setBusy(false); }
  }

  return (
    <div className="screen">
      <header className="screen-head">
        <h2>Custody</h2>
        <span className="muted small">the key, the hardware, the paperwork</span>
      </header>

      {error && <div className="error">⚠ {error}</div>}
      {said && <div className="muted small">{said}</div>}

      <div className="card">
        <h3>Can the operator decrypt this?</h3>
        <p style={{ fontSize: "1.4em" }}>
          <strong>{key ? (key.operator_can_decrypt ? "Yes" : "No") : "…"}</strong>
        </p>
        {key && <p className="muted small">{key.note}</p>}
        {key && (
          <p className="muted small">
            provider <code>{key.provider}</code> ·{" "}
            {key.customer_managed
              ? "customer-managed" : "under deployment custody"}
          </p>
        )}
        <div className="row">
          <input value={customerKey} placeholder="base64 32-byte key"
                 onChange={(e) => setCustomerKey(e.target.value)} />
          <button className="primary" disabled={busy || !customerKey.trim()}
                  onClick={() => run(() => api.setTenantKey(
                    { provider: "held", key: customerKey.trim() }, token!))}>
            Hold our own key
          </button>
          <button disabled={busy}
                  onClick={() => run(() => api.setTenantKey(
                    { provider: "kms" }, token!))}>Use a KMS</button>
          <button disabled={busy}
                  onClick={() => run(async () => {
                    try {
                      await api.surrenderTenantKey(token!);
                      setSaid("Handed back to deployment custody.");
                    } catch (e) {
                      // A 409 here means nothing changed, which the operator
                      // needs told rather than shown as a generic failure.
                      setSaid((e as Error).message);
                    }
                  })}>Hand it back</button>
        </div>
      </div>

      <div className="card">
        <h3>Key versions</h3>
        <div className="row">
          <button disabled={busy}
                  onClick={() => run(async () => {
                    const r = await api.resealUnderNewKey(admin);
                    setSaid(`Active version ${r.active_version} · `
                      + `${r.resealed} resealed · `
                      + `${r.customer_managed_skipped} skipped because the `
                      + `customer holds their key and we cannot open it`);
                  })}>Reseal under the active key</button>
          <button disabled={busy}
                  onClick={() => run(async () => {
                    const r = await api.retireOldKeys(admin);
                    setVersions(r.versions);
                    setSaid(`${r.retired} retired`);
                  })}>Retire the old ones</button>
        </div>
        {versions.map((v) => (
          <div key={v.version} className="row"
               style={{ padding: "4px 0" }}>
            <span style={{ flex: 1 }}>version {v.version}</span>
            <span className="muted small">
              {v.provider}{v.active ? " · active" : ""} ·{" "}
              {new Date(v.created_at).toLocaleString()}
            </span>
          </div>
        ))}
        <p className="muted small">
          A reseal skips every record the customer holds the key for, and
          reports how many. That number is the honest measure of bring-your-
          own-key: it is how much of the vault the operator could not touch
          even when asked to.
        </p>
      </div>

      <div className="card">
        <h3>Take it away, and put it back</h3>
        <div className="row">
          <button disabled={busy || !token}
                  onClick={() => run(async () => {
                    const s = await api.snapshot(token!);
                    setSnapshot(s.records);
                    setSaid(`${s.records.length} record(s) in hand`);
                  })}>Snapshot</button>
          <button disabled={busy || !snapshot}
                  onClick={() => run(() =>
                    api.restoreRecords(snapshot!, token!))}>
            Restore from the snapshot
          </button>
          <button disabled={busy || !tenantId}
                  onClick={() => run(() =>
                    api.restoreTenant(tenantId!, admin))}>
            Restore the whole tenant
          </button>
        </div>
        <div className="row">
          <input value={recordKey} placeholder="a record key"
                 onChange={(e) => setRecordKey(e.target.value)} />
          <button disabled={busy || !recordKey.trim()}
                  onClick={() => run(() =>
                    api.deleteRecord(recordKey.trim(), token!))}>
            Delete a record
          </button>
        </div>
        <div className="row">
          <select value={deleteMode}
                  onChange={(e) => setDeleteMode(e.target.value)}>
            <option value="soft">soft — recoverable</option>
            <option value="hard">hard — gone</option>
          </select>
          <button className="danger" disabled={busy || !tenantId}
                  onClick={() => run(() =>
                    api.deleteTenant(tenantId!, deleteMode, admin))}>
            Delete the tenant
          </button>
        </div>
        <p className="muted small">
          The audit trail survives every one of these. A deletion is an entry
          in the chain, not a gap in it — a vault that could erase the record
          of erasing something would not be evidence of anything.
        </p>
      </div>

      <div className="card">
        <h3>Tokens</h3>
        <div className="row">
          <button disabled={busy || !tenantId}
                  onClick={() => run(async () => {
                    const t = await api.mintToken(tenantId!, "read", admin);
                    setMinted(t.token);
                  })}>Mint a read token</button>
          <button disabled={busy || !tenantId}
                  onClick={() => run(async () => {
                    const t = await api.mintToken(tenantId!, "write", admin);
                    setMinted(t.token);
                  })}>Mint a write token</button>
          <button disabled={busy || !minted}
                  onClick={() => run(async () => {
                    await api.revokeToken(minted!, admin);
                    setMinted(null);
                    setSaid("Revoked.");
                  })}>Revoke it</button>
        </div>
        {minted && (
          <p className="muted small">
            <code>{minted}</code> — shown once. Only its SHA-256 is stored,
            so nothing here or anywhere else can show it to you again.
          </p>
        )}
      </div>

      <div className="card">
        <h3>The paperwork</h3>
        {baa && (
          <p className="muted small">
            {baa.executed
              ? `BAA executed, effective ${baa.effective_date}`
              : baa.note}
          </p>
        )}
        <div className="row">
          <label>Customer legal name
            <input value={legalName} placeholder="Customer legal name"
                   onChange={(e) => setLegalName(e.target.value)} />
          </label>
          <label>Operator legal name
            <input value={operatorName} placeholder="Operator legal name"
                   onChange={(e) => setOperatorName(e.target.value)} />
          </label>
          {/* The date box carried no name at all — the other two at least
              said theirs in grey until somebody typed over it. */}
          <label>Effective date
            <input value={effective} type="date"
                   onChange={(e) => setEffective(e.target.value)} />
          </label>
          <button className="primary"
                  disabled={busy || !tenantId || !legalName.trim() || !effective}
                  onClick={() => run(() => api.recordBaa(tenantId!, {
                    customer_legal_name: legalName.trim(),
                    operator_legal_name: operatorName.trim(),
                    effective_date: effective }, admin))}>Record it</button>
          <button disabled={busy || !tenantId}
                  onClick={() => run(() =>
                    api.rescindBaa(tenantId!, admin))}>Rescind</button>
        </div>
        {tenantBaaRow?.executed && (
          <p className="muted small">
            On file for this tenant: {tenantBaaRow.customer_legal_name} ↔{" "}
            {tenantBaaRow.operator_legal_name}
          </p>
        )}
        <h4>Programs</h4>
        {programs.map((p) => (
          <div key={p.key}
               style={{ padding: "8px 0", borderBottom: "1px solid var(--line)" }}>
            <div className="row">
              <strong style={{ flex: 1 }}>{p.label}</strong>
              <span className="muted small">
                {p.sector} · retention {p.retention_days} days
              </span>
            </div>
            <div className="muted small">{p.summary}</div>
            <div className="muted small">{p.controls.join(" · ")}</div>
          </div>
        ))}
      </div>

      <div className="card">
        <h3>Where it physically is</h3>
        {mine && (
          <p className="muted small">
            <strong>{mine.title}</strong> — {mine.means} · {mine.price}
          </p>
        )}
        {mine?.free_because && (
          <p className="muted small">Free because: {mine.free_because}</p>
        )}
        <div className="row">
          {Object.entries(modes).map(([id, m]) => (
            <button key={id} disabled={busy || !tenantId}
                    onClick={() => run(() => api.setHosting(
                      tenantId!, { mode: id }, token!))}>
              {m.title} · {m.price}
            </button>
          ))}
        </div>
        <div className="row">
          <button disabled={busy}
                  onClick={() => run(() => api.recordDeployment({
                    name: "new site", option: "colocation" }, token!))}>
            Record a deployment
          </button>
        </div>
        {mine && (
          <>
            <p className="muted small">
              We are responsible for: {mine.we_are_responsible_for.join(", ")}
            </p>
            <p className="muted small">
              You are responsible for: {mine.you_are_responsible_for.join(", ")}
            </p>
          </>
        )}
        {history.map((h, i) => (
          <div key={i} className="muted small" style={{ padding: "4px 0" }}>
            {String(h.mode ?? "")} · {String(h.at ?? h.created_at ?? "")}
            {h.note ? ` — ${String(h.note)}` : ""}
          </div>
        ))}
      </div>
    </div>
  );
}
