# PDI v0.1.1 — release notes

*Ready-to-paste body for the GitHub Release created when you push the
`app-v0.1.1` tag. Kept in sync with [CHANGELOG.md](CHANGELOG.md).*

---

**PDI (Private Data Infrastructure) v0.1.1** — the vault goes enterprise and
gets native apps everywhere. One of three interoperating products (with
[qrme](https://github.com/davidsbianchi1984/qrme) and
[jim-mini](https://github.com/davidsbianchi1984/jim-mini)).

### Highlights

- **Native apps at parity** — iOS, Android, and Windows carry the whole
  operator console: Overview (language, feedback, and **in-app admin key
  management** — load / rotate / retire key versions with the deployment's
  admin token, kept in memory only), Vault, Audit, Robots, Connectors,
  Transfers, and Secure Intake.
- **Enterprise compliance transfer** — HIPAA / OSHA / CPNI-grade secure file
  transfer for corporations, plus **secure intake** so subscribers and
  partner companies can send files *in* — sealed and audit-chained end to
  end, receipts included.
- **Robots as vault-backed data sources** — bind catalog robots, seal their
  maps / snapshots / sensor logs on ingest, and keep tenant-owned custody
  even after unbinding.
- **Connected platforms** — all 16 suite connection platforms, the
  Apple / Google / Microsoft / Canva connected-apps catalog, and
  per-assistant screens for Apple Intelligence, Gemini, and Copilot.
- **Language & provenance** — per-tenant language with hand-translated vault
  notes in all supported languages, sign-in gateway choice, dictionary
  translate, and sealed-record provenance (origin, seal details, audit
  trail).
- **Positions / assistant builder** — the AI-integration & role-mapping
  questionnaire that blueprints an assistant for any industry role.
- **Starter vault** — a seeded demo tenant with sealed records covering every
  provenance origin and a full custody cycle to explore.
- **Two form factors documented** — every capability screen now renders in
  both the phone frame and a wide desktop operator-console frame.
- **First-run onboarding** — welcome → provider login → key setup → token
  grant → connected systems → all set.

### Verification

88 tests green; live-server smoke flows pass (seal / read / audit-verify);
the desktop app builds clean; the cross-product suite smoke (run from qrme)
passes end to end.

### Install

Download the installer for your OS below (`.dmg` / `.exe` / `.AppImage`), or run
the backend from source — see the [README](README.md). Installers are signed
only if signing secrets are configured; otherwise they are unsigned (see
[docs/releasing.md](docs/releasing.md)).

**Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
