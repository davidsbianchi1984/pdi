# PDI v0.2.1 — release notes

*Ready-to-paste body for the GitHub Release created when you push the
`app-v0.2.1` tag. Kept in sync with [CHANGELOG.md](CHANGELOG.md).*

---

**PDI v0.2.1** — **there are no functional changes to PDI in this release.** The
three products version as one, and this round's work was next door. One of three
interoperating products (with [qrme](https://github.com/davidsbianchi1984/qrme)
and [jim-mini](https://github.com/davidsbianchi1984/jim-mini)), all three cut
together at this version.

### What changed in the siblings

- **QRME** — a profile front page (skills, experience, reviews, rating), a help
  box on every screen that is structurally not a synthetic profile, and real
  portraits on the screens that used to draw a generic orb.
- **JIM-mini** — signal confidence for biometrics. `escalation.decide` always
  took a `confidence` but only forecasts supplied one, so a measurement was a
  fact by virtue of arriving; a reading the system does not trust now caps at
  `check_in` instead of ringing an emergency contact.

### Verification

192 tests green — the same 192, passing the same way, which is rather the point
of a release that claims no functional change here. 81 routes. Version strings
moved in exactly five places: `pyproject.toml`, the FastAPI app,
`app/package.json`, and the two root entries in its lockfile (dependency
versions untouched).

### Install

Download the installer for your OS below (`.dmg` / `.exe` / `.AppImage`), or run
`python -m pdi` from source and pick your device — see the [README](README.md). Installers are signed
only if signing secrets are configured; otherwise they are unsigned (see
[docs/releasing.md](docs/releasing.md)).

**Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
