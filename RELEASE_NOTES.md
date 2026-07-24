# PDI v0.1.3 — release notes

*Ready-to-paste body for the GitHub Release created when you push the
`app-v0.1.3` tag. Kept in sync with [CHANGELOG.md](CHANGELOG.md).*

---

**PDI v0.1.3** — the trust release: B2B service terms with a per-tenant
receipt, and a Business Associate Agreement the vault enforces in code.
One of three interoperating products (with
[qrme](https://github.com/davidsbianchi1984/qrme) and
[jim-mini](https://github.com/davidsbianchi1984/jim-mini)).

### Highlights

- **Run it on your phone** — the API serves the built operator console at
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

101 tests green; the desktop console builds clean; the cross-product
suite smoke (run from qrme) passes end to end.

### Install

Download the installer for your OS below (`.dmg` / `.exe` / `.AppImage`), or run
the backend from source — see the [README](README.md). Installers are signed
only if signing secrets are configured; otherwise they are unsigned (see
[docs/releasing.md](docs/releasing.md)).

**Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
