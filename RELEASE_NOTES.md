# PDI v0.4.1 — release notes

*Ready-to-paste body for the GitHub Release created when you push the
`app-v0.4.1` tag. Kept in sync with [CHANGELOG.md](CHANGELOG.md).*

---

**PDI v0.4.1** — **no functional change to the vault in this release**: no new
routes, no schema, no behaviour. One of three interoperating products (with
[qrme](https://github.com/davidsbianchi1984/qrme) and
[jim-mini](https://github.com/davidsbianchi1984/jim-mini)), all three cut
together at this version, so one number names one combination of all three.

### The vault promise says which plans it covers

QRME and JIM-mini gained free tiers whose storage posture is an **open
cloud** under platform custody: the apps hold that data themselves, over
ordinary HTTPS, and it **never reaches PDI at all**. Two claims on this side
were written when a paid plan was the only kind, and read as more than they
are:

- *"The tandem is the only place JIM-mini and QRME may put sensitive
  material"* — true on a paid plan, and the hosting page now says so, naming
  what the free posture is instead (including the short list each product
  refuses to store open, rather than leaving a reader to assume there is
  none).
- *"No raw user data ever leaves your vault"* — that is about what is
  inside, and PDI holds what the integrating apps *send* it. The free plans
  send nothing here. The promise now scopes itself.

Nothing PDI holds is less protected because somebody else is on a free plan.
**A vault has one posture**, `hosting.GUARANTEES` is still one list shared by
all four hosting modes, and a test still asserts no mode can hold fewer.

### Verification

255 tests green, unchanged — which is the point.

### Install

Download the installer for your OS from the assets below (built by the
`desktop-release` workflow from the `app-v0.4.1` tag), or run `python -m pdi`.
Deployed on-premises or in colocation — your hardware, your keys
(`PDI_MASTER_KEY`), your walls.

**Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
