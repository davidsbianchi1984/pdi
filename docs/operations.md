# PDI operations & internals

How the Private Data Infrastructure behaves in production. Sections marked
**[implemented]** are in the codebase and tested; **[planned]** documents the
intended design for v1+ that isn't code yet.

## Master key & key rotation

- **At rest** every record value is sealed with AES-256-GCM (`pdi/crypto.py`).
  The data-encryption key is derived from `PDI_MASTER_KEY` (base64, 32 bytes).
  **[implemented]**
- **AAD binding**: each record's ciphertext carries `tenant_id:key` as
  additional authenticated data, so a blob cannot be moved between tenants or
  keys without failing authentication. **[implemented]**
- **Production KMS/HSM** **[planned]**: `PDI_MASTER_KEY` is the dev seam. In
  production the master key lives in a KMS/HSM (AWS KMS, GCP KMS, or a
  PKCS#11 HSM); PDI calls `Decrypt`/`GenerateDataKey` at boot to obtain a
  short-lived data key held only in memory, never on disk. Envelope
  encryption: KMS holds the key-encrypting key; per-record data keys are
  wrapped.
- **Rotation** **[planned]**: `POST /rotate` (admin) re-seals every record
  under a new key. During rotation both `PDI_MASTER_KEY` (new) and
  `PDI_MASTER_KEY_PREV` (old) are present; each record is opened with the key
  that authenticates it and re-sealed under the new key, one tenant at a
  time, recorded in the audit chain (`rotate.begin` / `rotate.complete`).
  Rotation is idempotent and resumable — a `key_version` column on `records`
  tracks progress so a crash resumes where it stopped.

## Audit log

- **Structure** **[implemented]** (`pdi/audit.py`, `audit` table):
  `seq` (autoincrement), `tenant_id`, `action`, `ref`, `at`, `prev_hash`,
  `hash`. Each row's `hash = SHA-256(prev_hash + canonical-json(entry))`,
  forming a tamper-evident chain from a fixed genesis (`"0"*64`).
- **Events recorded** **[implemented]**: `put`, `get`, `delete`,
  `tenant.create`, `token.issue`, `token.revoke`, `snapshot.export`,
  `snapshot.restore`, `tenant.soft_delete`, `tenant.wipe`, `tenant.restore`,
  and the contribution intake. Every data-plane and admin mutation lands on
  the chain.
- **Verification** **[implemented]**: `GET /audit/verify` walks the whole
  chain and reports `{intact, entries}`; any retroactive edit breaks the hash
  link and is detected.
- **Retention** **[planned]**: the audit chain is append-only and never
  pruned (compliance requirement). For volume, closed chains are periodically
  sealed: a checkpoint row records the running hash, older rows are exported
  to cold storage (ciphertext), and `verify` accepts a checkpoint as its
  starting anchor. Retention default: indefinite; configurable per
  jurisdiction.

## Tenant deletion **[implemented]**

Two modes, both admin-guarded and audited:

- `DELETE /tenants/{id}` (default `mode=soft`) — sets a `deleted_at`
  tombstone. The tenant's tokens stop resolving immediately (access is cut),
  but records are retained for a recovery window and can be restored with
  `POST /tenants/{id}/restore`.
- `DELETE /tenants/{id}?mode=wipe` — permanently removes the tenant's
  records, scoped tokens, and the tenant row. Not restorable.

The soft window default is **30 days** **[planned: enforcement]**; a
scheduled sweep promotes soft-deleted tenants to `wipe` once the window
elapses.

## Snapshot, restore & disaster recovery

- **Snapshot** **[implemented]**: `GET /snapshot` exports ciphertext only —
  plaintext never leaves. **Restore** **[implemented]**: `POST /restore`
  reinserts a ciphertext snapshot; AAD still binds each record to its
  tenant+key, so a snapshot can only be restored where it belongs. Both are
  writer-token gated and audited.
- **DR procedure** **[planned]**: (1) continuous ciphertext replication of
  the `records` + `audit` tables to a warm standby; (2) the master key is
  recoverable independently via KMS multi-region / HSM backup — never bundled
  with the data; (3) recovery = restore ciphertext + point PDI at the KMS
  key; (4) post-recovery, `GET /audit/verify` must return `intact:true`
  before the vault is reopened for writes.

## Performance & scaling

- **v1 substrate** **[implemented]**: single-file SQLite with WAL mode
  (concurrent readers). Suitable for one node, thousands of tenants, and
  low-millions of records.
- **Scaling story** **[planned]**: the data model is already tenant-sharded
  (`tenant_id` on every row), so the growth path is (a) Postgres for a single
  large deployment, then (b) shard tenants across nodes by `tenant_id` hash.
  Because AAD binds ciphertext to `tenant_id:key`, records are relocatable
  across shards without re-encryption. Target envelope: 10k+ tenants, ~10 GB
  ciphertext per tenant, per-record reads O(1) by `(tenant_id, key)` index.

## Billing / usage metering **[planned]**

Structure only for v1: the audit chain already records every `put`/`get`/
`delete` with `tenant_id` and timestamp, so usage (operation counts, bytes
stored per tenant from `records`) is derivable without new instrumentation. A
`GET /usage` (admin) would aggregate: records, ciphertext bytes, ops/day per
tenant — the metering feed for a downstream billing system.

## Cloud-model contribution intake **[implemented]**

`POST /contributions` (writer token) seals anonymized model-improvement data
under `contributions/{source}/…` keys with AES-256-GCM and records it on the
audit chain. **Anonymization is the integrating system's responsibility and
happens before the payload reaches PDI** — QRME strips profile/interactor ids
and replaces display names; JIM-mini sends only condition/severity/rating,
never ids or notes (see each app's contribution code and `docs/cloud-model.md`).
PDI's role is encrypted, tenant-isolated, audited storage of what arrives.
