# PDI v0.1.4 — release notes

*Ready-to-paste body for the GitHub Release created when you push the
`app-v0.1.4` tag. Kept in sync with [CHANGELOG.md](CHANGELOG.md).*

---

**PDI v0.1.4** — run it your way: one command prints every way to run
the vault console and you pick the device — your phone (scan a QR
straight off the terminal), this PC, a packaged installer, or the
headless API. One of three interoperating products (with
[qrme](https://github.com/davidsbianchi1984/qrme) and
[jim-mini](https://github.com/davidsbianchi1984/jim-mini)).

### Highlights

- **`python -m pdi` — the launcher menu** — every way to run the vault
  console, one command each, so you choose per device: `phone` (the QR
  flow below), `desktop` (the Electron app on this PC), the packaged
  installer (no toolchain needed), or `serve` (the headless API alone).
  Same backend, same data, same token checks behind every door — admin
  endpoints still require `PDI_ADMIN_TOKEN`.
- **`python -m pdi phone` — the whole phone setup in one command** —
  builds the console if it's missing (first-run `npm install` included),
  prints the pairing URL **with a QR code drawn straight into the
  terminal**, and serves on your local network. Scan, Add to Home
  Screen, done.
- **The console on your phone** — the API serves the built operator console at
  `/app` (one origin for UI and API — nothing to configure on the phone);
  `GET /pair` returns the URL on your local network with a scannable QR,
  and the console installs to the home screen as a standalone app with a
  thumb-reachable bottom tab bar. Local network only, by design; the
  service worker never caches API traffic, so sealed records and audit
  state are always live.
- **Terms of Service** — docs/terms.md (v1.0): B2B service terms framing
  PDI as encrypted data-custody infrastructure, not advice — the
  Customer owns its data and answers for its lawfulness, consents,
  tenant-token safekeeping, and connected systems; as-is warranty
  disclaimer and liability cap. Served versioned at `GET /terms`;
  provisioning a tenant records the version in force
  (`terms_version`/`terms_accepted_at`) as the receipt.
- **BAA, executed per customer and enforced in code** — the signable
  template (docs/baa-template.md) carries the required § 164.504(e)
  provisions plus an exhibit mapping each promise to the PDI control
  that keeps it. The operator records each customer's executed BAA
  (`POST /tenants/{id}/baa`); HIPAA-program transfers and intakes are
  refused (403) for tenants without an active record; termination
  re-imposes the block; executions land in the audit chain.
- **Signed, notarized builds wired** — hardened runtime + entitlements +
  notarization in the electron-builder config: adding the Apple/Windows
  signing secrets produces Gatekeeper-clean, SmartScreen-friendly
  installers. docs/releasing.md walks through obtaining the certificates.

### Verification

105 tests green; the desktop console builds clean; the cross-product
suite smoke (run from qrme) passes end to end.

### Install

Download the installer for your OS below (`.dmg` / `.exe` / `.AppImage`), or run
`python -m pdi` from source and pick your device — see the [README](README.md). Installers are signed
only if signing secrets are configured; otherwise they are unsigned (see
[docs/releasing.md](docs/releasing.md)).

**Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
