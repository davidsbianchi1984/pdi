# Changelog

All notable changes to PDI are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **First-run onboarding screens** — welcome, provider login (Continue with
  Apple / Google / email), key-provider setup (managed KMS/HSM vs local master
  key), scoped-token grant, connected systems, and an "all set" summary — a
  guided first-run before the operator console, rendered in both iOS and Android
  chrome.

## [0.1.0] — 2026-07-21

First public release. PDI (Private Data Infrastructure) is the encrypted-vault
product of the three-product suite — the storage layer that
[qrme](https://github.com/davidsbianchi1984/qrme) and
[jim-mini](https://github.com/davidsbianchi1984/jim-mini) can run on top of.

### Added

- **Encrypted vault** — per-tenant records sealed with AES-256-GCM, AAD-bound
  to tenant + key so a record can't be moved or read across tenants.
- **Envelope encryption & key management** — versioned data-encryption keys
  wrapped by a KEK (env or KMS provider); `POST /keys/rotate` rotates and
  re-seals, `/keys/reseal` and `/keys/retire` complete the rotation.
- **Tamper-evident audit** — append-only, SHA-256 hash-chained log;
  `GET /audit/verify` detects any retroactive edit and `GET /audit/schema`
  documents the event schema and action catalogue.
- **Tenant registry & RBAC** — bearer tokens hashed at rest; scoped read/write
  tokens (`/tenants/{id}/tokens`) with instant revocation.
- **Retention up to forever** — per-tenant windows (`7d`…`1y`, `forever`, or a
  day count); `POST /retention/sweep` enforces them (`forever` expires nothing).
- **Tenant deletion** — soft-delete with a recovery window vs. permanent wipe,
  both audited; `restore` undoes a soft-delete.
- **Disaster recovery** — ciphertext-only snapshot export and restore, AAD
  still binding every record to its tenant + key.
- **Cloud-model contribution intake** — sealed, tenant-scoped, individually
  revocable anonymized training contributions.
- **Position & assistant builder** — the industry-agnostic AI Integration &
  Role-Mapping questionnaire: seals raw answers in the vault and returns an
  assistant blueprint (capabilities, automation opportunities, human-in-the-loop
  guardrails, reskilling paths, and a ready-to-use system-prompt). Decision
  support, never an automated staffing decision.
- **Apps** — a runnable React + Vite + Electron operator console and mobile
  screen designs; CI that smoke-builds the console and a per-OS installer
  release workflow.

[Unreleased]: https://github.com/davidsbianchi1984/pdi/compare/app-v0.1.0...HEAD
[0.1.0]: https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.1.0
