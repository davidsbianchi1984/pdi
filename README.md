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
- **Role-based access control** — `POST /tenants/{id}/tokens` issues scoped
  `read`/`write` tokens; read tokens cannot write or delete, and
  `DELETE /tokens/{token}` revokes instantly.
- **Deployment record** — models the on-premises vs. colocation (Tier III+)
  options from the proposal.

## Run

```bash
pip install -e .[dev]
export PDI_MASTER_KEY=$(python -c "import base64,os;print(base64.b64encode(os.urandom(32)).decode())")
uvicorn pdi.api:app
```

`PDI_DB` sets the SQLite path (default `pdi.db`). `PDI_MASTER_KEY` is base64 of
32 bytes; in production it belongs in the corporation's own KMS/HSM inside the
private facility (an ephemeral key is generated if unset — dev only).

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
