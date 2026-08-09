import { useEffect, useState } from "react";
import { api, BaaStatus, CompliancePrograms, holdKey, HostingMode, KeyVersion,
         keyIsHeld, Row, TenantKey } from "../api";
import { useSession } from "../store";
import { deviceLanguage, fill, Lang, t } from "../l10n";

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
  // Mirrors the module-level key in api.ts so the screen re-renders when it
  // is armed or forgotten. The key itself stays there and out of React's
  // state tree, which devtools would happily print.
  const [armed, setArmed] = useState(keyIsHeld());
  const [legalName, setLegalName] = useState("");
  const [operatorName, setOperatorName] = useState("Vault Operations LLC");
  const [effective, setEffective] = useState("");
  const [recordKey, setRecordKey] = useState("");
  const [deleteMode, setDeleteMode] = useState("soft");

  const token = session.tenantToken;
  const admin = session.adminToken || undefined;
  const tenantId = session.tenantId;
  const lang = (session.language as Lang) ?? deviceLanguage();

  function load() {
    api.compliancePrograms().then((r) => setPrograms(r.programs)).catch(fail);
    api.hostingModes().then((r) => setModes(r.modes)).catch(fail);
    if (!token) return;
    api.tenantKey(token).then(setKey).catch(fail);
    api.baaStatus(token).then(setBaa).catch(fail);
    if (tenantId) {
      api.hosting(tenantId, token).then(setMine).catch(fail);
      api.hostingHistory(tenantId, token)
        .then((r) => setHistory(r.history)).catch(fail);
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
        <h2>{t("cu.title", lang)}</h2>
        <span className="muted small">{t("cu.sub", lang)}</span>
      </header>

      {error && <div className="error">⚠ {error}</div>}
      {said && <div className="muted small">{said}</div>}

      <div className="card">
        <h3>{t("cu.decrypt", lang)}</h3>
        <p style={{ fontSize: "1.4em" }}>
          <strong>{key
            ? (key.operator_can_decrypt ? t("cu.yes", lang) : t("cu.no", lang))
            : "…"}</strong>
        </p>
        {key && <p className="muted small">{key.note}</p>}
        {key && (
          <p className="muted small">
            {t("cu.provider", lang)} <code>{key.provider}</code> ·{" "}
            {key.customer_managed
              ? t("cu.customer_managed", lang) : t("cu.deployment", lang)}
          </p>
        )}
        {/* Whether this session is *carrying* the key, which is a different
            question from whether the tenant is under customer custody: the
            first is about this browser tab, the second about the vault. A
            reload answers yes to the second and no to the first, and every
            request in between comes back 428. */}
        <p className="muted small">
          {armed ? t("cu.key.armed", lang) : t("cu.key.absent", lang)}
        </p>
        <div className="row">
          <input value={customerKey} placeholder={t("cu.key.ph", lang)}
                 type="password" autoComplete="off"
                 onChange={(e) => setCustomerKey(e.target.value)} />
          <button className="primary" disabled={busy || !customerKey.trim()}
                  onClick={() => run(async () => {
                    // Armed *before* the adopt call, not after: the reload
                    // this button triggers reads /key, which is behind the
                    // same dependency the adoption puts a key in front of.
                    holdKey(customerKey.trim());
                    setArmed(true);
                    await api.setTenantKey(
                      { provider: "held", key: customerKey.trim() }, token!);
                  })}>
            {t("cu.hold", lang)}
          </button>
          <button disabled={busy || !customerKey.trim()}
                  onClick={() => { holdKey(customerKey.trim());
                                   setArmed(true);
                                   setSaid(t("cu.key.armed", lang));
                                   load(); }}>
            {t("cu.key.use", lang)}
          </button>
          <button disabled={busy || !armed}
                  onClick={() => { holdKey(null); setArmed(false);
                                   setCustomerKey("");
                                   setSaid(t("cu.key.absent", lang)); }}>
            {t("cu.key.forget", lang)}
          </button>
          <button disabled={busy}
                  onClick={() => run(() => api.setTenantKey(
                    { provider: "kms" }, token!))}>
            {t("cu.kms", lang)}
          </button>
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
                  })}>{t("cu.handback", lang)}</button>
        </div>
      </div>

      <div className="card">
        <h3>{t("cu.versions", lang)}</h3>
        <div className="row">
          <button disabled={busy}
                  onClick={() => run(async () => {
                    const r = await api.resealUnderNewKey(admin);
                    setSaid(`Active version ${r.active_version} · `
                      + `${r.resealed} resealed · `
                      + `${r.customer_managed_skipped} skipped because the `
                      + `customer holds their key and we cannot open it`);
                  })}>{t("cu.reseal", lang)}</button>
          <button disabled={busy}
                  onClick={() => run(async () => {
                    const r = await api.retireOldKeys(admin);
                    setVersions(r.versions);
                    setSaid(`${r.retired} retired`);
                  })}>{t("cu.retire", lang)}</button>
        </div>
        {versions.map((v) => (
          <div key={v.version} className="row"
               style={{ padding: "4px 0" }}>
            <span style={{ flex: 1 }}>version {v.version}</span>
            <span className="muted small">
              {v.provider}{v.active ? ` · ${t("cu.active", lang)}` : ""} ·{" "}
              {new Date(v.created_at).toLocaleString()}
            </span>
          </div>
        ))}
        <p className="muted small">{t("cu.reseal.note", lang)}</p>
      </div>

      <div className="card">
        <h3>{t("cu.away", lang)}</h3>
        <div className="row">
          <button disabled={busy || !token}
                  onClick={() => run(async () => {
                    const s = await api.snapshot(token!);
                    setSnapshot(s.records);
                    setSaid(`${s.records.length} record(s) in hand`);
                  })}>{t("cu.snapshot", lang)}</button>
          <button disabled={busy || !token}
                  onClick={() => run(async () => {
                    // Everything this deployment holds about this tenant, as
                    // a file. The snapshot beside it is ciphertext for
                    // restoring; this is the answer to *what do you have*.
                    const all = await api.exportEverything(token!);
                    const blob = new Blob([JSON.stringify(all, null, 2)],
                                          { type: "application/json" });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = `pdi-export-${tenantId ?? "tenant"}.json`;
                    a.click();
                    URL.revokeObjectURL(url);
                    setSaid(`${Object.keys(all.tables).length} table(s) in hand`);
                  })}>{t("cu.export", lang)}</button>
          <button disabled={busy || !snapshot}
                  onClick={() => run(() =>
                    api.restoreRecords(snapshot!, token!))}>
            {t("cu.restore", lang)}
          </button>
          <button disabled={busy || !tenantId}
                  onClick={() => run(() =>
                    api.restoreTenant(tenantId!, admin))}>
            {t("cu.restore.all", lang)}
          </button>
        </div>
        <div className="row">
          <input value={recordKey} placeholder={t("cu.delrec.ph", lang)}
                 onChange={(e) => setRecordKey(e.target.value)} />
          <button disabled={busy || !recordKey.trim()}
                  onClick={() => run(() =>
                    api.deleteRecord(recordKey.trim(), token!))}>
            {t("cu.delrec", lang)}
          </button>
        </div>
        <div className="row">
          <select value={deleteMode}
                  onChange={(e) => setDeleteMode(e.target.value)}>
            <option value="soft">{t("cu.del.soft", lang)}</option>
            <option value="hard">{t("cu.del.hard", lang)}</option>
          </select>
          <button className="danger" disabled={busy || !tenantId}
                  onClick={() => run(() =>
                    api.deleteTenant(tenantId!, deleteMode, admin))}>
            {t("cu.deltenant", lang)}
          </button>
        </div>
        <p className="muted small">{t("cu.audit.note", lang)}</p>
      </div>

      <div className="card">
        <h3>{t("cu.tokens", lang)}</h3>
        <div className="row">
          <button disabled={busy || !tenantId}
                  onClick={() => run(async () => {
                    const t = await api.mintToken(tenantId!, "read", admin);
                    setMinted(t.token);
                  })}>{t("cu.mint.read", lang)}</button>
          <button disabled={busy || !tenantId}
                  onClick={() => run(async () => {
                    const t = await api.mintToken(tenantId!, "write", admin);
                    setMinted(t.token);
                  })}>{t("cu.mint.write", lang)}</button>
          <button disabled={busy || !minted}
                  onClick={() => run(async () => {
                    await api.revokeToken(minted!, admin);
                    setMinted(null);
                    setSaid(t("cu.revoked", lang));
                  })}>{t("cu.revoke", lang)}</button>
        </div>
        {minted && (
          <p className="muted small">
            <code>{minted}</code> {t("cu.minted.note", lang)}
          </p>
        )}
      </div>

      <div className="card">
        <h3>{t("cu.paperwork", lang)}</h3>
        {baa && (
          <p className="muted small">
            {baa.executed
              ? `BAA executed, effective ${baa.effective_date}`
              : baa.note}
          </p>
        )}
        <div className="row">
          <label>{t("cu.cust.name", lang)}
            <input value={legalName} placeholder={t("cu.cust.name", lang)}
                   onChange={(e) => setLegalName(e.target.value)} />
          </label>
          <label>{t("cu.op.name", lang)}
            <input value={operatorName} placeholder={t("cu.op.name", lang)}
                   onChange={(e) => setOperatorName(e.target.value)} />
          </label>
          {/* The date box carried no name at all — the other two at least
              said theirs in grey until somebody typed over it. */}
          <label>{t("cu.eff", lang)}
            <input value={effective} type="date"
                   onChange={(e) => setEffective(e.target.value)} />
          </label>
          <button className="primary"
                  disabled={busy || !tenantId || !legalName.trim() || !effective}
                  onClick={() => run(() => api.recordBaa(tenantId!, {
                    customer_legal_name: legalName.trim(),
                    operator_legal_name: operatorName.trim(),
                    effective_date: effective }, admin))}>
            {t("cu.record", lang)}
          </button>
          <button disabled={busy || !tenantId}
                  onClick={() => run(() =>
                    api.rescindBaa(tenantId!, admin))}>
            {t("cu.rescind", lang)}
          </button>
        </div>
        {tenantBaaRow?.executed && (
          <p className="muted small">
            {t("cu.onfile", lang)} {tenantBaaRow.customer_legal_name} ↔{" "}
            {tenantBaaRow.operator_legal_name}
          </p>
        )}
        <h4>{t("cu.programs", lang)}</h4>
        {programs.map((p) => (
          <div key={p.key}
               style={{ padding: "8px 0", borderBottom: "1px solid var(--line)" }}>
            <div className="row">
              <strong style={{ flex: 1 }}>{p.label}</strong>
              <span className="muted small">
                {p.sector} ·{" "}
                {fill("cu.retention", lang, { n: p.retention_days })}
              </span>
            </div>
            <div className="muted small">{p.summary}</div>
            <div className="muted small">{p.controls.join(" · ")}</div>
          </div>
        ))}
      </div>

      <div className="card">
        <h3>{t("cu.where", lang)}</h3>
        {mine && (
          <p className="muted small">
            <strong>{mine.title}</strong> — {mine.means} · {mine.price}
          </p>
        )}
        {mine?.free_because && (
          <p className="muted small">
            {t("cu.free", lang)} {mine.free_because}
          </p>
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
            {t("cu.deploy", lang)}
          </button>
        </div>
        {mine && (
          <>
            <p className="muted small">
              {t("cu.we", lang)} {mine.we_are_responsible_for.join(", ")}
            </p>
            <p className="muted small">
              {t("cu.you", lang)} {mine.you_are_responsible_for.join(", ")}
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
