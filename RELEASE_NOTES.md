# PDI v0.2.0 — release notes

*Ready-to-paste body for the GitHub Release created when you push the
`app-v0.2.0` tag. Kept in sync with [CHANGELOG.md](CHANGELOG.md).*

---

**PDI v0.2.0** — the release where who answers a facility's gate stops being a
deployment-wide guess and becomes the tenant's own. One of three interoperating
products (with [qrme](https://github.com/davidsbianchi1984/qrme) and
[jim-mini](https://github.com/davidsbianchi1984/jim-mini)), all three cut
together at this version.

### Highlights

- **`PDI_GATE_ONCALL` named one contact for the whole deployment.** In a
  single-tenant install that is merely thin. In PDI it is wrong, because PDI is
  multi-tenant: one vault, many customers, each with their own facility. A
  courier at customer A's loading dock was handed off to a name belonging to
  whoever set the environment variable — in a colocation facility, the operator
  rather than the tenant. Everything else in this product is scoped to a tenant
  and enforced by a token. The one name a stranger at a door got routed to was
  global.

- **The roster is per tenant, in the database**, written with the tenant's own
  write token — the same authority as placing a beacon. `POST /gate/roster`,
  `GET /gate/roster`, `DELETE /gate/roster/{id}`, `PUT /gate/timezone`. A
  tenant with no roster still gets `PDI_GATE_ONCALL`, so nothing already
  deployed changes.

- **Validation happens on write**, which is the interesting difference from
  JIM-mini's `jim/rota.py`. That module solves the same who-is-on-shift problem
  but has to parse its rota out of an environment variable at the moment
  somebody needs help — which is why it needs a never-raises read path and a
  loud degradation story. PDI has an API, so a malformed shift is a **422 an
  operator reads in daylight** and the bad rota never reaches the door. Same
  property, bought with a gate instead of a guard.

- **Three things it is careful about**, each a way of paging the wrong person:

  - **Shifts cross midnight.** `18:00–06:00` is the shift a facility gate
    exists for, and `start <= now <= end` is false for every minute of it. A
    wrapping shift is two intervals and belongs to the day it *started*: at
    02:00 on Saturday it is Friday's night porter on the desk, not the weekend
    rota.
  - **A facility is somewhere.** Each tenant sets its own IANA zone, and an
    unknown one is **refused** rather than quietly read as UTC — the silent
    version is wrong by the offset, and by a *different* offset in summer, so
    it looks correct for half the year.
  - **A rota has gaps.** The gate then tries everybody rather than nobody, and
    reports `on_shift: false` on the page *and in the envelope*, so whoever it
    wakes knows they were a guess.

- **A failed page moves to the next name.** With one contact, a webhook that
  rejected the page was the end of the line — trying the second is the entire
  point of having a second. Every attempt is its own row, so the morning list
  shows who was tried and in what order rather than one entry saying *failed*.

- **Roster changes land on the audit chain** as `gate.roster`: who can be
  summoned to a controlled facility is a governance fact, not a preference.

### Also

Only one workflow writes the release body now. `desktop-release.yml` published
`RELEASE_NOTES.md` verbatim — preamble and all — two to four minutes after
`sync-release-notes.yml` had already published it correctly, so the build
always won and every release needed re-syncing by hand.

### Verification

192 tests green (15 new this release). 81 routes. Tenant scoping is tested by
trying to read and delete another tenant's roster, and by ringing two tenants'
gates and asserting each reaches its own person — both fail if the scoping is
removed. Version strings moved in exactly five places.

### Install

Download the installer for your OS below (`.dmg` / `.exe` / `.AppImage`), or run
`python -m pdi` from source and pick your device — see the [README](README.md). Installers are signed
only if signing secrets are configured; otherwise they are unsigned (see
[docs/releasing.md](docs/releasing.md)).

**Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
