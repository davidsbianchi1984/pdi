# Changelog

All notable changes to PDI are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Custody beacons, designed** — [docs/beacons.md](docs/beacons.md). QRME
  ships desk beacons: a printed QR on a shop door that reveals a person. The
  gesture ports here; what it resolves to inverts. PDI's subject is custody of
  data, and custody keeps escaping into the physical world where PDI cannot see
  it — a records box in a van, a decommissioned drive on a pallet, a robot out
  for service. Design only; no code yet.

  The load-bearing decisions: a seal card reveals **that** a thing is sealed
  and what governs it, and **nothing about its contents** — the surface never
  holds a key or touches ciphertext, so it neither breaks under BYOK nor
  quietly undermines it. A scan is **a link in the hash-chained audit log**
  rather than a counter, which turns a physical custody gap into a compliance
  finding PDI can produce on demand; only a `found` report writes to the chain,
  because a barcode gun sweeping a pallet must not put four hundred rows into a
  tamper-evidence log. Disclosure defaults to **blind** — naming a regulated
  carrier is itself a disclosure, and should be a decision somebody made rather
  than one they inherited. And a beacon can be placed on a **bare object** with
  no record behind it, which inverts the usual order: custody starts first and
  the record may never arrive.

  Also designed: **the agent at the gate.** A facility beacon rung at 2am
  currently waits for a human who may be asleep, and a moderating agent stands
  in that gap. PDI does not grow a model to do it — every arrow in the tandem
  architecture points *into* PDI, so the agent is a QRME profile over HTTP via
  a `pdi/qrme_client.py` mirroring JIM's, which also means it carries QRME's AI
  mark (somebody being talked to by software at a gate must know it is
  software) and that an unconfigured deployment degrades to exactly the
  human-routing this document already specifies. Its ceiling did not need
  inventing: `positions.py` already lists `incident_response` and
  `safety_compliance` as `HUMAN_IN_LOOP`, and granting entry to a room of
  regulated data is both — so the agent may triage, check arrivals against
  expected transfers, give directions, structure a receipt, open a reception
  airlock and page a human, but may never grant entry, assert a person's
  identity, or let a refusal be a dead end. Every turn lands on the audit chain
  with the transcript sealed in the vault and only its key and hash on the log.

## [0.1.8] — 2026-07-25

### Fixed

- **`[0.1.5]` and `[0.1.6]` linked to releases that do not exist.** Both
  versions were cut — changelog, notes, version bumps — but their `app-v*` tags
  were never pushed, so those two entries pointed at 404s. They now point at
  their release-prep commits. Deliberately **not** fixed by backfilling the
  tags: pushing them now would fire the installer build and publish v0.1.5 and
  v0.1.6 releases *dated after* v0.1.7, putting superseded installers at the top
  of the page people download from. [docs/releasing.md](docs/releasing.md)
  records that reasoning.

### Changed

- **There are no functional changes to PDI in this release.** No API, no
  schema, no behaviour moved, and the vault seals and opens exactly what it
  did at 0.1.7. The substance at 0.1.8 is QRME's: a live desk stops being
  only something you watch — you can ask to come up on the stream, and the
  room's reactions render on the picture rather than beside it. Nothing in
  it asked PDI to change.

## [0.1.7] — 2026-07-25

### Changed

- **The three products are now cut as one release** — documented in
  [docs/releasing.md](docs/releasing.md), and in QRME's and JIM-mini's copies of
  the same file. Same number, same pass, even when a repository has nothing of its own
  to ship that round; an empty round says so in those words rather than being
  padded. Through v0.1.5 each repository cut whenever it happened to have work,
  so the numbers matched only by coincidence — which is how QRME reached 0.1.6
  alone while this one sat at 0.1.5. The doc also writes down the trap that
  follows: tag the release-prep commit rather than the tip of `main`, because
  work keeps landing while a release is cut and anything arriving after the
  changelog is sectioned belongs to `[Unreleased]`, not to the version being
  tagged.

## [0.1.6] — 2026-07-25

### Changed

- **Version aligned across the suite.** QRME, JIM-mini and PDI are built to run
  in tandem, but their version numbers drifted apart whenever a round of work
  landed in one repository and not the others — QRME reached 0.1.6 on its own
  while this one stayed at 0.1.5. From here the three carry the same number, so
  "the suite at 0.1.6" names one combination of three products rather than
  three that merely happen to be nearby. Anyone pinning all three can pin one
  number.

  **There are no functional changes to PDI in this release.** No API, schema,
  or app behaviour moved, and the vault seals and opens exactly what it did at
  0.1.5. Worth noting because it is the interesting part: QRME 0.1.6 added
  signature evidence sealed into the vault, and it needed **nothing new here**
  — the evidence package goes in through the same `put` that rated events
  already used, and chains into the same audit log. A new consumer that
  required no change to the thing it consumes is the vault's interface working
  as intended.

## [0.1.5] — 2026-07-25

### Security

- **BYOK — bring your own key** (`PUT`/`GET`/`DELETE /key`). A tenant can seal
  its records under a key the deployment never stores, which is what makes an
  outsourced collation facility workable for a customer who is one tenant
  among many: the operator's database, backups and snapshots hold only
  ciphertext for that tenant, and a subpoena to the host yields sealed blobs.
  The key travels per request in `x-tenant-key`; a stored HMAC witness — not
  the key — refuses a wrong one *before* it can seal records nothing could
  later open. Adoption re-seals every existing record in one transaction, so
  there is no half-migrated tenant whose readability nobody can determine
  from outside. `GET /key` states the guarantee **and its limits**: it
  protects data at rest, not against a hostile running operator who could
  capture the key as it is presented; there is no escrow; and the operator's
  reseal/rotation skip those tenants and report `customer_managed_skipped`
  rather than silently passing over them. A `kms` provider (key in the
  customer's own KMS) is scoped per tenant but remains an integration seam,
  and is reported as the weaker promise it is — the operator can decrypt
  while the grant is live.
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

- **The native apps are compiled in CI** (`.github/workflows/native.yml`) —
  iOS via XcodeGen + `xcodebuild` on macOS, Android via `gradle assembleDebug`,
  Windows via MSBuild. The Swift, Kotlin and C# had never been through a
  compiler in this repository: they were checked by reading and by brace/XML
  well-formedness, which catches a typo and nothing else. Ported from QRME,
  where the same gate found five real defects. Compile only — signing and
  packaging stay in the release workflow — and it runs only when `native/`
  changes, since macOS runner minutes are not free.
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

### Fixed

- **The iOS project spec was invalid** — its XcodeGen `info:` block had no
  `path` (required), while also setting `GENERATE_INFOPLIST_FILE`, which is
  mutually exclusive with it. `xcodegen generate` failed outright, so the
  Xcode project could never have been produced. The plist is now written from
  the spec, which also means the local-networking exemption the Simulator
  needs to reach `http://127.0.0.1:8000` actually applies.
- **Android would not compile the API client.** A public `var base` already
  generates `setBase(String)` on the JVM, so the explicit `setBase()` helper
  that trimmed trailing slashes was a signature clash — the class could not be
  produced at all. The trimming moved into the property's own setter, which
  keeps both guards and matches the shape qrme and jim-mini use.
- **iOS could not build the language picker.** `languages()` called `request()`
  without the token argument it required. `GET /languages` is genuinely public
  — it is the catalog a client reads before it has a tenant token at all — so
  the token is now optional rather than the call inventing an empty one, which
  would have sent a malformed `Bearer ` header.

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

[Unreleased]: https://github.com/davidsbianchi1984/pdi/compare/app-v0.1.8...HEAD
[0.1.8]: https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.1.8
[0.1.7]: https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.1.7
[0.1.6]: https://github.com/davidsbianchi1984/pdi/commit/11b4187
[0.1.5]: https://github.com/davidsbianchi1984/pdi/commit/b939db4
[0.1.4]: https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.1.4
[0.1.3]: https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.1.3
[0.1.2]: https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.1.2
[0.1.1]: https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.1.1
[0.1.0]: https://github.com/davidsbianchi1984/pdi/releases/tag/app-v0.1.0
