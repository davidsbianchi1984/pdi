# PDI v0.4.4 — release notes

*Ready-to-paste body for the GitHub Release created when you push the
`app-v0.4.4` tag. Kept in sync with [CHANGELOG.md](CHANGELOG.md).*

---

**PDI v0.4.4** — **no functional change to the vault in this release**: no
new routes, no schema, no behaviour. One of three interoperating products
(with [qrme](https://github.com/davidsbianchi1984/qrme) and
[jim-mini](https://github.com/davidsbianchi1984/jim-mini)), all three cut
together at this version, so one number names one combination of all three.

### What changed in the siblings

The Windows signup 500 died: the emailed-code banner used characters the
frozen Windows backend's console encoding cannot print, so every signup
crashed mid-request. ASCII banner, replace-don't-raise stdout, a cp1252
guard test, and consoles that show a server's actual words instead of a
JSON-parse exception.

### Verification

256 tests green, unchanged in behaviour — which is the point.

### Install

Download the installer for your OS from the assets below (built by the
`desktop-release` workflow from the `app-v0.4.4` tag), or run
`python -m pdi`. Deployed on-premises or in colocation — your hardware,
your keys (`PDI_MASTER_KEY`), your walls.

**Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
