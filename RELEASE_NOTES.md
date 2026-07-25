# PDI v0.1.5 — release notes

*Ready-to-paste body for the GitHub Release created when you push the
`app-v0.1.5` tag. Kept in sync with [CHANGELOG.md](CHANGELOG.md).*

---

**PDI v0.1.5** — the release about who holds the key. A tenant can now
seal its records under a key the deployment never stores, which is what
makes an outsourced collation facility workable for a customer who is one
tenant among many. Plus: the vault ships as one container, and the native
apps finally go through a compiler. One of three interoperating products
(with [qrme](https://github.com/davidsbianchi1984/qrme) and
[jim-mini](https://github.com/davidsbianchi1984/jim-mini)).

### Highlights

- **BYOK — bring your own key** (`PUT` / `GET` / `DELETE /key`). The operator's
  database, backups and snapshots hold only ciphertext for that tenant, and a
  subpoena to the host yields sealed blobs. The key travels per request in
  `x-tenant-key`; a stored HMAC witness — **not** the key — refuses a wrong one
  *before* it can seal records nothing could later open. Adoption re-seals
  every existing record in one transaction, so there is no half-migrated
  tenant whose readability nobody can determine from outside.
- **`GET /key` states the limits as loudly as the guarantee.** It protects data
  at rest, not against a hostile *running* operator who could capture the key
  as it is presented. There is no escrow — a lost customer key means lost
  records, by design. And the operator's own reseal and rotation skip those
  tenants and report `customer_managed_skipped` rather than passing over them
  silently. The `kms` provider is scoped per tenant but is still an integration
  seam, and is reported as the weaker promise it is: the operator can decrypt
  while the grant is live.
- **Open admin now fails closed off-machine.** `PDI_ADMIN_TOKEN` unset is still
  development mode, but only for callers on the same machine. From a routable
  address the admin surface returns 503 rather than exposing tenant creation,
  token minting, tenant deletion and snapshot restore to anyone who finds the
  URL.
- **A published deployment refuses an ephemeral key.** With `PDI_PUBLIC_URL`
  set and no `PDI_MASTER_KEY`, sealing fails closed instead of encrypting under
  a process-local key that vanishes on restart — which would have made every
  sealed record silently unreadable. Laptop use without a key is unchanged.
- **Deployable as one container** — a two-stage `Dockerfile` builds the vault
  console and installs the API into one image. Non-root user, vault on a
  `/data` volume, honours `$PORT`, health at `/health`. **No key material is
  baked in**: `PDI_MASTER_KEY` is supplied at runtime, so the image itself is
  safe to push to a registry.
- **[docs/hosting.md](docs/hosting.md) — the only line that matters when you
  outsource a collation facility: *who holds the key-encryption key*.**
  Self-hosted, colocation and managed side by side, with what each means for
  whether the host can read your records and what a subpoena to them yields.
  Plus what the image cannot protect for you (the volume, and the key) and what
  the deployment does not give you: no rate limiting, no backups, no key
  escrow, no attestation.
- **The native apps are compiled in CI.** Until this release the Swift, Kotlin
  and C# in `native/` had never been through a compiler here. Three defects
  surfaced on the first run, and all three were fatal rather than cosmetic:
  - The **iOS project spec was invalid** — its XcodeGen `info:` block had no
    `path`, so `xcodegen generate` failed outright and `PdiVault.xcodeproj`
    could never have been produced at all.
  - **Android would not compile the API client** — a public `var base` already
    generates `setBase(String)` on the JVM, so the explicit `setBase()` helper
    was a signature clash.
  - **iOS could not build the language picker** — `languages()` omitted a
    required token argument. `GET /languages` is genuinely public, so the token
    is now optional rather than the call inventing an empty `Bearer ` header.

### Verification

134 tests green. The desktop console builds clean. The native compile gate is
green on all three platforms — the first time that has ever been true here.

### Install

Download the installer for your OS below (`.dmg` / `.exe` / `.AppImage`), or run
`python -m pdi` from source and pick your device — see the [README](README.md). Installers are signed
only if signing secrets are configured; otherwise they are unsigned (see
[docs/releasing.md](docs/releasing.md)).

**Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
