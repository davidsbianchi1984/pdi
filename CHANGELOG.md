# Changelog

All notable changes to PDI are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Security

- **Open admin now fails closed off-machine** — `PDI_ADMIN_TOKEN` unset is
  still development mode, but only for callers on the same machine. From a
  routable address the admin surface returns 503 instead of exposing tenant
  creation, token minting, tenant deletion, and snapshot restore to anyone
  who finds the URL.
- **A published deployment refuses an ephemeral key** — with `PDI_PUBLIC_URL`
  set and no `PDI_MASTER_KEY` (or KMS provider), sealing fails closed instead
  of encrypting under a process-local key that vanishes on restart, which
  would have made every sealed record silently unreadable. Laptop use without
  a key is unchanged.

### Added

- **`PDI_PUBLIC_URL` for published deployments** — `GET /pair` advertises
  the deployment's public address (QR included) instead of a LAN address,
  so the phone flow works hosted or local from one code path. Documented
  in docs/operations.md alongside the HTTPS and token guidance.

- **Deployable as one container** — a two-stage `Dockerfile` builds the vault
  console and installs the API into a single image, so a hosted instance
  serves UI and API from one origin exactly as the phone flow does. Runs as a
  non-root user, keeps the vault on a `/data` volume, honours `$PORT`, and
  reports health at `/health`. No key material is baked in: `PDI_MASTER_KEY`
  is supplied at runtime, so the image itself is safe to push to a registry.

### Documentation

- **docs/hosting.md** — hosting a collation facility, and the only line that
  matters when outsourcing it: *who holds the key-encryption key*.
  Self-hosted, colocation, and managed side by side, with what each one means
  for whether the host can read your records and what a subpoena to them
  yields. Plus the deploy commands, what the image cannot protect for you
  (the volume, and the key — lost means unrecoverable, by design), and what
  the deployment does not give you: no rate limiting, no backups, no key
  escrow, no attestation.
- docs/operations.md gains a **key-custody table** stating plainly what is
  implemented (AES-256-GCM, envelope encryption, AAD binding, rotation) and
  what is a seam (the KMS/HSM provider) or out of scope (TLS in transit).
- docs/operations.md's key-rotation section corrected: it still described a
  planned `POST /rotate` with a `PDI_MASTER_KEY_PREV` handoff, which is not
  what shipped. Rotation is implemented as versioned DEKs behind
  `POST /keys/rotate` / `reseal` / `retire`, and the section now documents
  that.

## [0.1.4] — 2026-07-24

### Added

- **`python -m pdi` launcher** — bare invocation prints the menu of
  every way to run the vault console, one command each, so users choose
  their device: `phone` (builds the console if missing — npm install
  included on first run — prints the pairing URL with a scannable QR
  drawn straight into the terminal, serves on the local network; flags
  `--port`, `--rebuild`, `--no-build`, `--print-only`), `desktop` (the
  Electron app on this PC, or a pointer to the packaged installers when
  npm is absent), and `serve` (the headless API alone, `--host`/`--port`).
  Same backend, data, and token checks in every form.

## [0.1.3] — 2026-07-24

### Added

- **Run it on your phone** — the API serves the built operator console at
  `/app`, so a phone on the same Wi-Fi opens the vault console with nothing
  to configure (one origin for UI and API, so no CORS and no "which host?"
  step). `GET /pair` resolves this machine's local-network address and
  returns the URL to open — with `GET /pair/qr.svg` as a scannable QR and a
  pairing card in Settings. Installable as a PWA (manifest, icon, standalone
  display, app-shell service worker that never caches API traffic), with a
  phone layout: the sidebar becomes a bottom tab bar, 16px inputs so iOS
  doesn't zoom, and safe-area insets for the notch and home indicator.

## [0.1.2] — 2026-07-24

### Added

- **Terms of Service** — docs/terms.md (v1.0: B2B service terms — the
  Customer owns its data, tenant-token safekeeping, acceptable use, PHI
  requires the recorded BAA, as-is warranty disclaimer, liability cap)
  served versioned at `GET /terms`; provisioning a tenant records the
  version in force (`terms_version`/`terms_accepted_at`) as the receipt.
- **BAA enforcement** (pdi/baa.py) — the operator records each customer's
  executed BAA (`POST /tenants/{id}/baa`, metadata + document hash only);
  HIPAA-program transfers and intakes are refused for tenants without an
  active record; `GET /baa` gives tenants their own standing;
  `baa.execute`/`baa.terminate` land in the audit chain. The template
  itself gains a mitigation clause and the unsuccessful-attempts
  security-incident carve-out.

- **BAA template** (docs/baa-template.md) — a production-ready Business
  Associate Agreement with the required § 164.504(e) provisions and an
  exhibit mapping each contractual promise to the PDI control that keeps
  it; linked from the enterprise guide.
- **macOS notarization wiring** — hardened runtime + entitlements +
  `notarize` in the electron-builder config; docs/releasing.md walks
  through obtaining the macOS and Windows certificates.

## [0.1.1] — 2026-07-24

### Added

- **First-run onboarding screens** — welcome, provider login (Apple / Google /
  email), key-provider setup (managed KMS/HSM vs local master key),
  scoped-token grant, connected systems, and an "all set" summary, in iOS and
  Android chrome.
- **Native iOS / Android / Windows apps at parity** — Overview (with language,
  in-app feedback, and **admin key management**: load / rotate / retire key
  versions with the deployment's admin token, kept in memory only), Vault,
  Audit, Robots (vault-backed data sources with sealed ingest), platform
  Connectors, compliance Transfers, and Secure Intake.
- **Enterprise compliance transfer** — HIPAA / OSHA / CPNI-grade secure file
  transfer for corporations (outbound) and **secure intake** (subscribers &
  partners send files in), sealed and audit-chained end to end.
- **Robots as vault-backed data sources** — catalog binding, sealed ingest of
  maps/snapshots/sensor logs, tenant-owned custody that survives unbinding.
- **Connected platforms** — all 16 suite connection platforms, the Apple /
  Google / Microsoft / Canva connected-apps catalog, and per-assistant
  screens (Apple Intelligence, Gemini, Copilot).
- **Language & provenance** — per-tenant language with hand-translated vault
  notes in all supported languages, sign-in gateway choice, dictionary
  translate, and sealed-record provenance (origin, seal, audit trail).
- **Positions / assistant builder** — the AI-integration & role-mapping
  questionnaire that blueprints an assistant for any industry role.
- **Starter vault seed** — a demo tenant with sealed records covering every
  provenance origin, a bound robot, and a full custody cycle in the audit
  trail.
- **Desktop-frame gallery** — all 36 capability screens rendered in a wide
  operator-console frame alongside the phone sets (108 SVGs total).
- In-app **"Help us improve" feedback** (`POST`/`GET /improve`) and **chrome
  localization** — the apps' own nav labels in all 10 languages — plus
  pull-to-refresh on the mobile Overviews.

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

[Unreleased]: https://github.com/davidsbianchi1984/pdi/compare/app-v0.1.4...HEAD
[0.1.4]: https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.1.4
[0.1.3]: https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.1.3
[0.1.2]: https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.1.2
[0.1.1]: https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.1.1
[0.1.0]: https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.1.0
