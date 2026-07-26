# PDI v0.3.0 — release notes

*Ready-to-paste body for the GitHub Release created when you push the
`app-v0.3.0` tag. Kept in sync with [CHANGELOG.md](CHANGELOG.md).*

---

**PDI v0.3.0** — **no functional change to PDI in this release**, but not an
empty round either. The vault is where this round's most sensitive new payload
lands. One of three interoperating products (with
[qrme](https://github.com/davidsbianchi1984/qrme) and
[jim-mini](https://github.com/davidsbianchi1984/jim-mini)), all three cut
together at this version.

### What the vault now holds

QRME learned to put somebody in front of a **real clinician**, and to let that
clinician write back. The note comes here: sealed under a
`qrme/{profile}/clinical/…` key, content in the vault with only a key reference
held next door — the same treatment source material has always had, and PDI's
provenance attributes it to QRME the same way.

That is the whole of PDI's involvement, and it is deliberately unremarkable.
The interesting decisions this round were about *who may release* that data and
*how it is attributed once released*, and both belong to the products that hold
the conversation, not to the vault that holds the bytes.

### Changed

- **`docs/tandem.md`** — the shared architecture doc, byte-identical across the
  three repos, gained two sections it did not describe: handing a specialist a
  *task* rather than a chat turn, and reaching a real clinician with the release
  authorised by a verified WebAuthn assertion instead of a `consent: true`
  boolean. Both record **why the obvious implementation was rejected**, which is
  the part worth writing down — the routes are discoverable, the reason they are
  not the obvious ones is not.

### What changed in the siblings

- **QRME** — owner-authorized workflow delegation; a medical referral signed for
  rather than consented to, with a one-time link; the clinician's note back,
  attributed rather than absorbed; and the README's starter gallery rendering
  avatar bubbles instead of 34 black boxes.
- **JIM-mini** — reaching a real clinician through the tandem without ever
  holding the credential; handing a specialist a task that outlives the app
  closing; and a contribution preview that finally keeps the promise the
  settings screen was already making.

### Verification

192 tests green — **the same 192, passing the same way**, which is the point of
a release that claims no functional change here. 81 routes, also unchanged.
Version strings moved in exactly five places: `pyproject.toml`, the FastAPI app,
`app/package.json`, and the two root entries in its lockfile (dependency
versions untouched).

### Install

Download the installer for your OS below (`.dmg` / `.exe` / `.AppImage`), or run
`python -m pdi` from source and pick your device — see the [README](README.md). Installers are signed
only if signing secrets are configured; otherwise they are unsigned (see
[docs/releasing.md](docs/releasing.md)).

**Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
