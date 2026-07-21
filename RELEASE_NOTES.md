# PDI v0.1.0 — release notes

*Ready-to-paste body for the GitHub Release created when you push the
`app-v0.1.0` tag. Kept in sync with [CHANGELOG.md](CHANGELOG.md).*

---

**PDI (Private Data Infrastructure) v0.1.0** — the first public release of the
encrypted-vault product, one of three interoperating products (with
[qrme](https://github.com/davidsbianchi1984/qrme) and
[jim-mini](https://github.com/davidsbianchi1984/jim-mini)). PDI is the storage
layer both AI systems can run on top of.

### Highlights

- **Encrypted vault** — per-tenant records sealed with AES-256-GCM, AAD-bound to
  tenant + key so records can't be moved or read across tenants.
- **Key management** — envelope encryption with versioned DEKs wrapped by a KEK
  (env or KMS provider); rotate + re-seal + retire.
- **Tamper-evident audit** — append-only, SHA-256 hash-chained log with a
  documented event schema; `GET /audit/verify` detects any retroactive edit.
- **Tenant registry & RBAC** — bearer tokens hashed at rest; scoped read/write
  tokens with instant revocation.
- **Retention up to forever** — per-tenant windows enforced by a sweep;
  `forever` expires nothing.
- **Tenant deletion** — soft-delete with a recovery window vs. permanent wipe,
  both audited; restore undoes a soft-delete.
- **Disaster recovery** — ciphertext-only snapshot export and restore.
- **Contribution intake** — sealed, tenant-scoped, individually revocable
  anonymized training contributions.
- **Position & assistant builder** — the industry-agnostic AI Integration &
  Role-Mapping questionnaire → assistant blueprint; decision support, never an
  automated staffing decision.
- **Apps** — a runnable operator console; this release attaches per-OS installers
  built and (optionally) signed in CI.

### Install

Download the installer for your OS below (`.dmg` / `.exe` / `.AppImage`), or run
the backend from source — see the [README](README.md). Installers are signed
only if signing secrets are configured; otherwise they are unsigned (see
[docs/releasing.md](docs/releasing.md)).

**Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
