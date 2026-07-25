# PDI v0.1.6 — release notes

*Ready-to-paste body for the GitHub Release created when you push the
`app-v0.1.6` tag. Kept in sync with [CHANGELOG.md](CHANGELOG.md).*

---

**PDI v0.1.6** — a version-alignment release. QRME, JIM-mini and PDI are built
to run in tandem, and from here they carry the same version number, so *the
suite at 0.1.6* names one combination of three products rather than three that
happen to be nearby. One of three interoperating products (with
[qrme](https://github.com/davidsbianchi1984/qrme) and
[jim-mini](https://github.com/davidsbianchi1984/jim-mini)).

### What changed in PDI

Nothing functional. No API, no schema, no app behaviour moved, and the vault
seals and opens exactly what it did at 0.1.5.

That is worth one more sentence than it sounds like, because of what happened
on the other side of the seam. QRME 0.1.6 added a new kind of record to the
vault — WebAuthn signature evidence, sealed and chained so the existence and
order of signatures is protected by something other than the table they live
in. It needed **nothing new here**. The evidence package goes in through the
same `put` that rated events already used and lands in the same audit chain. A
new consumer that required no change to the thing it consumes is the vault's
interface doing its job.

**If you are already running 0.1.5, this upgrade is optional.** Take it if you
want the three products to report matching versions; skip it and you lose
nothing.

### Still true from v0.1.5

The substance of the last release is what you are actually running:

- **BYOK — bring your own key** (`PUT` / `GET` / `DELETE /key`). A tenant seals
  its records under a key the deployment never stores; the operator's database,
  backups and snapshots hold only ciphertext for that tenant, and a subpoena to
  the host yields sealed blobs. A stored HMAC witness — not the key — refuses a
  wrong one *before* it can seal records nothing could later open.
- **`GET /key` states the limits as loudly as the guarantee.** At rest, not
  against a hostile *running* operator. No escrow: a lost customer key means
  lost records, by design. Operator reseal and rotation skip those tenants and
  say `customer_managed_skipped` rather than passing over them silently.
- **Open admin fails closed off-machine** — `PDI_ADMIN_TOKEN` unset is still
  development mode, but only for callers on the same machine.
- **A published deployment refuses an ephemeral key** — sealing fails closed
  rather than encrypting under a process-local key that vanishes on restart.
- **Deployable as one container** — non-root, vault on a `/data` volume, health
  at `/health`, and **no key material baked in**.
- **[docs/hosting.md](docs/hosting.md)** — who holds the key-encryption key,
  across self-hosted, colocation and managed, and what the deployment does not
  give you: no rate limiting, no backups, no key escrow, no attestation.
- **The native apps are compiled in CI** — iOS, Android and Windows, on every
  change that touches `native/`.

### Verification

134 tests green — the same 134, passing the same way, which is rather the
point of a release that claims to change nothing. Version strings moved in
exactly five places: `pyproject.toml`, the FastAPI app, `app/package.json`,
and the two root entries in its lockfile (dependency versions untouched).

### Install

Download the installer for your OS below (`.dmg` / `.exe` / `.AppImage`), or run
`python -m pdi` from source and pick your device — see the [README](README.md). Installers are signed
only if signing secrets are configured; otherwise they are unsigned (see
[docs/releasing.md](docs/releasing.md)).

**Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
