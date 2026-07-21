# Private Data Infrastructure (PDI)

![PDI — Private Data Infrastructure](assets/cover.svg)

A standalone **secure private data platform** (the "Private Data Infrastructure"
proposal for Any Corporation): a private, encrypted data vault with a
tamper-evident audit log and a tenant registry. It is the infrastructure layer
that AI systems such as QRME and JIM-mini can *optionally* run on top of —
storing sensitive data in PDI's encrypted vault instead of their own databases,
reached only over PDI's HTTP API. Both integrations are live: JIM-mini
vaults its medical and context payloads here, and QRME seals its profile
source material — each as its own tenant with its own token. See
[docs/tandem.md](docs/tandem.md).

## What it provides

- **Private, encrypted data vault** — record values are sealed at rest with
  AES-256-GCM (`pdi/crypto.py`); only ciphertext touches disk. AAD binds each
  record to its tenant + key so ciphertext can't be relocated.
- **Tenant registry** — each integrating system gets a tenant + bearer token;
  data is strictly namespaced per tenant (no cross-tenant reads).
- **Tamper-evident audit log** — every access is recorded in an append-only,
  SHA-256 hash-chained log; `GET /audit/verify` detects any retroactive edit.
- **Disaster-recovery snapshot & restore** — `GET /snapshot` exports
  ciphertext only; `POST /restore` reinserts a snapshot after a loss, with
  AAD still binding every record to its tenant + key.
- **Cloud-model contribution intake** — `POST /contributions` seals
  anonymized model-improvement data from integrating systems under
  `contributions/{source}/…` keys, encrypted and audit-chained;
  `GET /contributions` lists the intake ([docs/cloud-model.md](docs/cloud-model.md)).
- **Role-based access control** — `POST /tenants/{id}/tokens` issues scoped
  `read`/`write` tokens; read tokens cannot write or delete, and
  `DELETE /tokens/{token}` revokes instantly.
- **Tokens hashed at rest** — only the SHA-256 hash of each tenant/scoped
  token is stored, so a leak of PDI's own database yields no usable
  credential; the plaintext is shown once at issuance. The admin token is
  compared in constant time.
- **Deployment record** — models the on-premises vs. colocation (Tier III+)
  options from the proposal.

## Your data promise

**No raw user data ever leaves your vault.** PDI is the vault.

- Everything stored is AES-256-GCM ciphertext, AAD-bound to its tenant and
  key — one integrating system can never read another's records, and the
  database on disk holds nothing readable.
- PDI's own credentials get the same care as your data: bearer tokens are
  stored only as SHA-256 hashes, shown once at issuance.
- Every access — store, read, erase — lands in a tamper-evident hash-chained
  audit log; `GET /audit/verify` proves nothing was retroactively edited, and
  integrating apps surface a per-user view of it.
- Deletion is real: the owning app purges its keys, tenant deletion offers a
  soft recovery window and then a permanent wipe, and no orphaned ciphertext
  remains.
- Deployed on-premises or in colocation — your hardware, your keys
  (`PDI_MASTER_KEY`), your walls.

## Run

```bash
pip install -e .[dev]
export PDI_MASTER_KEY=$(python -c "import base64,os;print(base64.b64encode(os.urandom(32)).decode())")
uvicorn pdi.api:app
```

`PDI_DB` sets the SQLite path (default `pdi.db`). `PDI_MASTER_KEY` is base64 of
32 bytes; in production it belongs in the corporation's own KMS/HSM inside the
private facility (an ephemeral key is generated if unset — dev only).

## Console screens

The PDI operator console, screen by screen — one per capability of the vault, in the product's design language (Deep Indigo · Vault Cyan · Soft Silver, SF-style type, liquid-glass cards). It shares the night-indigo universe of QRME and JIM-mini, with vault cyan as its accent — one world, three products. Each screen is a self-contained SVG (no fonts, images, or scripts) and maps to a real endpoint. Regenerate with `python3 docs/screens/build.py`.

### The vault

<table>
  <tr>
    <td align="center" width="33%"><a href="docs/screens/01-overview.svg"><img src="docs/screens/01-overview.svg" width="210" alt="Overview — Your encrypted vault, live"></a><br><sub><b>01</b> · Overview</sub></td>
    <td align="center" width="33%"><a href="docs/screens/02-vault.svg"><img src="docs/screens/02-vault.svg" width="210" alt="Vault — Records, sealed at rest"></a><br><sub><b>02</b> · Vault</sub></td>
    <td align="center" width="33%"><a href="docs/screens/03-store-a-record.svg"><img src="docs/screens/03-store-a-record.svg" width="210" alt="Store a Record — Sealed the moment it lands"></a><br><sub><b>03</b> · Store a Record</sub></td>
  </tr>
  <tr>
    <td align="center" width="33%"><a href="docs/screens/04-encryption.svg"><img src="docs/screens/04-encryption.svg" width="210" alt="Encryption — AES-256-GCM, AAD-bound"></a><br><sub><b>04</b> · Encryption</sub></td>
  </tr>
</table>

### Tenants, access & intake

<table>
  <tr>
    <td align="center" width="33%"><a href="docs/screens/05-tenants.svg"><img src="docs/screens/05-tenants.svg" width="210" alt="Tenants — One per integrating system"></a><br><sub><b>05</b> · Tenants</sub></td>
    <td align="center" width="33%"><a href="docs/screens/06-create-tenant.svg"><img src="docs/screens/06-create-tenant.svg" width="210" alt="Create Tenant — Token shown once"></a><br><sub><b>06</b> · Create Tenant</sub></td>
    <td align="center" width="33%"><a href="docs/screens/07-access-control.svg"><img src="docs/screens/07-access-control.svg" width="210" alt="Access Control — Scoped read / write"></a><br><sub><b>07</b> · Access Control</sub></td>
  </tr>
  <tr>
    <td align="center" width="33%"><a href="docs/screens/10-contributions.svg"><img src="docs/screens/10-contributions.svg" width="210" alt="Contributions — Anonymized intake, sealed"></a><br><sub><b>10</b> · Contributions</sub></td>
  </tr>
</table>

### Audit & integrity

<table>
  <tr>
    <td align="center" width="33%"><a href="docs/screens/08-audit-log.svg"><img src="docs/screens/08-audit-log.svg" width="210" alt="Audit Log — Append-only, hash-chained"></a><br><sub><b>08</b> · Audit Log</sub></td>
    <td align="center" width="33%"><a href="docs/screens/09-verify-chain.svg"><img src="docs/screens/09-verify-chain.svg" width="210" alt="Verify Chain — Prove nothing was edited"></a><br><sub><b>09</b> · Verify Chain</sub></td>
  </tr>
</table>

### Operations & deployment

<table>
  <tr>
    <td align="center" width="33%"><a href="docs/screens/11-snapshot-restore.svg"><img src="docs/screens/11-snapshot-restore.svg" width="210" alt="Snapshot & Restore — Disaster recovery"></a><br><sub><b>11</b> · Snapshot & Restore</sub></td>
    <td align="center" width="33%"><a href="docs/screens/12-deployment.svg"><img src="docs/screens/12-deployment.svg" width="210" alt="Deployment — On-prem or colocation"></a><br><sub><b>12</b> · Deployment</sub></td>
    <td align="center" width="33%"><a href="docs/screens/13-key-management.svg"><img src="docs/screens/13-key-management.svg" width="210" alt="Key Management — Your keys, your walls"></a><br><sub><b>13</b> · Key Management</sub></td>
  </tr>
  <tr>
    <td align="center" width="33%"><a href="docs/screens/17-system-health.svg"><img src="docs/screens/17-system-health.svg" width="210" alt="System Health — Liveness & integrity"></a><br><sub><b>17</b> · System Health</sub></td>
  </tr>
</table>

### Isolation, the promise & the tandem

<table>
  <tr>
    <td align="center" width="33%"><a href="docs/screens/14-tenant-isolation.svg"><img src="docs/screens/14-tenant-isolation.svg" width="210" alt="Tenant Isolation — Walls between systems"></a><br><sub><b>14</b> · Tenant Isolation</sub></td>
    <td align="center" width="33%"><a href="docs/screens/15-data-promise.svg"><img src="docs/screens/15-data-promise.svg" width="210" alt="Data Promise — Deletion is real"></a><br><sub><b>15</b> · Data Promise</sub></td>
    <td align="center" width="33%"><a href="docs/screens/16-your-data.svg"><img src="docs/screens/16-your-data.svg" width="210" alt="Your Data — The per-user audit view"></a><br><sub><b>16</b> · Your Data</sub></td>
  </tr>
  <tr>
    <td align="center" width="33%"><a href="docs/screens/18-tandem.svg"><img src="docs/screens/18-tandem.svg" width="210" alt="Tandem — Both AI systems, one vault"></a><br><sub><b>18</b> · Tandem</sub></td>
    <td align="center" width="33%"><a href="docs/screens/19-design-system.svg"><img src="docs/screens/19-design-system.svg" width="210" alt="Design System — One world, vault cyan"></a><br><sub><b>19</b> · Design System</sub></td>
  </tr>
</table>


## API

| Endpoint | Auth | Purpose |
|---|---|---|
| `GET /health` | — | Liveness |
| `POST /deployments` | admin | Record a deployment (on-premises / colocation) |
| `POST /tenants` | admin | Create an integrating tenant; returns its bearer token once |
| `PUT /records` | tenant | Store `{key, value}` — value sealed at rest |
| `GET /records/{key}` | tenant | Retrieve and decrypt a value (keys may be path-namespaced) |
| `DELETE /records/{key}` | tenant | Delete a record |
| `GET /records` | tenant | List this tenant's keys |
| `GET /snapshot` | tenant | DR export (ciphertext only) |
| `GET /audit` | tenant | This tenant's audit entries |
| `GET /audit/verify` | tenant | Verify the hash-chain is intact |

Tenant endpoints require `Authorization: Bearer pdi_...`.

## Tandem client

`pdi/client.py` (`PDIClient`) is the small library an AI system uses to store
secrets in PDI over HTTP — e.g. JIM-mini keeping a user's emergency contact in
the encrypted vault instead of its own database. The AI systems never import
PDI internals.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `PDI_DB` | `pdi.db` | SQLite database path (ciphertext only) |
| `PDI_MASTER_KEY` | — | Required: base64-encoded 32-byte AES-256 key (use a KMS/HSM in production) |

## Test

```bash
pytest pdi/tests
```

Covers encryption round-trip, encryption-at-rest (plaintext never on disk),
tenant isolation, the hash-chained audit log (including tamper detection), and
a tandem run where a simulated AI system uses `PDIClient`.

## Out of scope for v1

Real facility provisioning, HSM/KMS integration, replication/redundancy across
sites, and billing — represented structurally (deployment record, snapshot
export), not as live infrastructure.

## Architecture

![PDI architecture — tenants, encrypted vault, tamper-evident audit](assets/architecture.svg)

![PDI encryption flow — seal, store, audit](assets/encryption-flow.svg)

## Related projects

Three separate products, each standalone, interoperating only over HTTP —
see [docs/tandem.md](docs/tandem.md) for the full architecture:

- [**qrme**](https://github.com/davidsbianchi1984/qrme) — AI synthetic
  profiles: relationship-aware, remembered, moderated.
- [**jim-mini**](https://github.com/davidsbianchi1984/jim-mini) — Guardian
  personal guidance: monitor, predict, guide, escalate; can delegate
  specialist guidance to QRME.
- [**pdi**](https://github.com/davidsbianchi1984/pdi) — Private Data
  Infrastructure: the encrypted vault both AI systems can run on top of.

## License

MIT © 2026 David Bianchi — see [LICENSE](LICENSE).
