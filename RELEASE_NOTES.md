# PDI v0.4.2 — release notes

*Ready-to-paste body for the GitHub Release created when you push the
`app-v0.4.2` tag. Kept in sync with [CHANGELOG.md](CHANGELOG.md).*

---

**PDI v0.4.2** — **no functional change to the vault in this release**: no new
routes, no schema, no behaviour. One of three interoperating products (with
[qrme](https://github.com/davidsbianchi1984/qrme) and
[jim-mini](https://github.com/davidsbianchi1984/jim-mini)), all three cut
together at this version, so one number names one combination of all three.

### The installers are named for their release now

`app/package.json` carried its own version and no cut ever bumped it, so
0.4.0 and 0.4.1 both attached installers stamped **0.3.3** — built from the
right tag, named for the wrong release, and invisible to the auto-updater.
This is the first release whose installers come out named for it, and the
guard got wider on the way: **all five version strings must now agree**
(pyproject had quietly sat at 0.4.0 through the last cut, the lockfile
roots at 0.3.3 through two — each a duplicated number with nothing to fail).

### What changed in the siblings

QRME and JIM-mini fixed their first run, driven by one bug report from a
real Windows install: identity fields stop pre-filling sample values,
*"Failed to fetch"* becomes a screen that names the missing backend,
`serve` answers the packaged console by default, JIM's window stops calling
itself QRME, and both default their Anthropic provider to `claude-opus-5`.
Nothing on that path touches PDI — the free plans those consoles onboard
into send nothing here.

### Verification

256 tests green, unchanged in behaviour — which is the point. The five-way
version agreement is guarded.

### Install

Download the installer for your OS from the assets below (built by the
`desktop-release` workflow from the `app-v0.4.2` tag — and named 0.4.2,
which is the point), or run `python -m pdi`. Deployed on-premises or in
colocation — your hardware, your keys (`PDI_MASTER_KEY`), your walls.

**Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
