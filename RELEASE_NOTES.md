# PDI v0.5.0 — release notes

*Ready-to-paste body for the GitHub Release created when you push the
`app-v0.5.0` tag. Kept in sync with [CHANGELOG.md](CHANGELOG.md).*

---

**PDI v0.5.0** — **no functional change to the vault in this release**: no
new routes, no schema, no behaviour. One of three interoperating products
(with [qrme](https://github.com/davidsbianchi1984/qrme) and
[jim-mini](https://github.com/davidsbianchi1984/jim-mini)), all three cut
together at this version, so one number names one combination of all three.

### What changed in the siblings

JIM-mini learned a threshold around *your* baseline rather than a textbook
range — a personal drift band per metric, watched on the edges that matter,
silent while the baseline is still provisional. It also gained a voice:
speak a question to the coach and hear the answer back, through ElevenLabs
or OpenAI, with the browser's own speech as the fallback. Both consoles
gained a model picker that shows each provider by its own glyph.

### Verification

256 tests green, unchanged in behaviour — which is the point.

### Install

Download the installer for your OS from the assets below (built by the
`desktop-release` workflow from the `app-v0.5.0` tag), or run `python -m pdi`.
Deployed on-premises or in colocation — your hardware, your keys
(`PDI_MASTER_KEY`), your walls.

**Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
