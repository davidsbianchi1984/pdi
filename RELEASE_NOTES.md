# PDI v0.4.3 — release notes

*Ready-to-paste body for the GitHub Release created when you push the
`app-v0.4.3` tag. Kept in sync with [CHANGELOG.md](CHANGELOG.md).*

---

**PDI v0.4.3** — **no functional change to the vault in this release**: no new
routes, no schema, no behaviour. One of three interoperating products (with
[qrme](https://github.com/davidsbianchi1984/qrme) and
[jim-mini](https://github.com/davidsbianchi1984/jim-mini)), all three cut
together at this version, so one number names one combination of all three.

### What changed in the siblings

QRME and JIM-mini gained a **front door and a key of your own**: email +
password accounts with the address proven by a 6-digit emailed code before
sign-in works, password reset that revokes every session, no endpoint that
reveals who has an account; **bring-your-own model key** riding each request
and never stored server-side; and installers that ship the whole Python
backend **frozen inside them** and spawn it at launch — double-click-and-
done. Nothing on those paths touches PDI: account passwords and codes are
hashed in the siblings' own stores, and the model keys never persist
anywhere.

### Verification

256 tests green, unchanged in behaviour — which is the point.

### Install

Download the installer for your OS from the assets below (built by the
`desktop-release` workflow from the `app-v0.4.3` tag), or run `python -m pdi`.
Deployed on-premises or in colocation — your hardware, your keys
(`PDI_MASTER_KEY`), your walls.

**Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
