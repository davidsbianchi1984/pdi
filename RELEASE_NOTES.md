# PDI v0.6.0 — release notes

*Ready-to-paste body for the GitHub Release created when you push the
`app-v0.6.0` tag. Kept in sync with [CHANGELOG.md](CHANGELOG.md).*

---

**PDI v0.6.0** — **no functional change to the vault in this release**: no
new routes, no schema, no behaviour. One of three interoperating products
(with [qrme](https://github.com/davidsbianchi1984/qrme) and
[jim-mini](https://github.com/davidsbianchi1984/jim-mini)), all three cut
together at this version, so one number names one combination of all three.

### What changed in the siblings

JIM-mini's Apple Watch bridge: an iPhone Shortcuts automation drips Health
readings at a per-user tokened URL (deposit-only — the reply never carries
guidance), and uploading the Health app's export.zip seeds the baseline
from months of history in one step — no events written, drift bands armed
the same day.

### Verification

256 tests green, unchanged in behaviour — which is the point.

### Install

Download the installer for your OS from the assets below (built by the
`desktop-release` workflow from the `app-v0.6.0` tag), or run `python -m pdi`.
Deployed on-premises or in colocation — your hardware, your keys
(`PDI_MASTER_KEY`), your walls.

**Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
