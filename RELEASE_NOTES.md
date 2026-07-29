# PDI v0.6.1 — release notes

*Ready-to-paste body for the GitHub Release created when you push the
`app-v0.6.1` tag. Kept in sync with [CHANGELOG.md](CHANGELOG.md).*

---

**PDI v0.6.1** — **no functional change to the vault in this release**: no
new routes, no schema, no behaviour. One of three interoperating products
(with [qrme](https://github.com/davidsbianchi1984/qrme) and
[jim-mini](https://github.com/davidsbianchi1984/jim-mini)), all three cut
together at this version, so one number names one combination of all three.

### What changed in the siblings

The model layer became honest about degrades: JIM-mini's coach no longer
answers chat with crisis-flavored fallback text, every reply names the
provider that actually produced it (with an amber warning and the reason
on a degrade), and both consoles' settings say plainly when the built-in
offline helper is what will answer.

### Verification

256 tests green, unchanged in behaviour — which is the point.

### Install

Download the installer for your OS from the assets below (built by the
`desktop-release` workflow from the `app-v0.6.1` tag), or run `python -m pdi`.
Deployed on-premises or in colocation — your hardware, your keys
(`PDI_MASTER_KEY`), your walls.

**Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
