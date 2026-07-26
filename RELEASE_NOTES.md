# PDI v0.4.0 — release notes

*Ready-to-paste body for the GitHub Release created when you push the
`app-v0.4.0` tag. Kept in sync with [CHANGELOG.md](CHANGELOG.md).*

---

**PDI v0.4.0** — **no functional change to PDI in this release**: no new routes,
no schema, no behaviour. The version moves because the three products are cut as
one release, and a number naming one combination of three is only useful if it
never skips one. One of three interoperating products (with
[qrme](https://github.com/davidsbianchi1984/qrme) and
[jim-mini](https://github.com/davidsbianchi1984/jim-mini)).

### Changed

**The README names its release, and says what each one added.** The same section
went into all three repositories, with one difference that belongs only here:
several rounds land in PDI as *no functional change*, and the table says so
rather than padding them.

That is worth stating plainly rather than hiding. PDI is the bottom layer, and
when the products above it learn to handle something new, the vault's correct
contribution is usually to hold the bytes exactly as it already did. A release
history that invented activity for those rounds would misrepresent what this
product is for.

### Known gap

**`docs/tandem.md` is still 92 lines shorter here than in the sibling
repositories.** That file is meant to be byte-identical across `qrme`, `jim-mini`
and `pdi`, and the *Reaching a real clinician* section added in 0.3.0 never
reached this one — so the vault product's own copy omits the flow that seals
clinical notes into the vault. The gap was invisible from inside this repository,
which is how it survived a release.

The fix is written and is being held with unrelated unreleased work rather than
split apart; it lands next round. It is recorded here rather than left silent,
because a gap nobody wrote down is one that survives another release too.

### What changed in the siblings

- **QRME** — the starter profiles stopped answering from tone alone. All 34
  shipped with zero source material while the packs matching them sat unused in
  the marketplace.
- **JIM-mini** — no functional change either; the README gained a release table,
  and four screens that shipped in 0.3.0 became findable.

### Verification

192 tests green — **the same 192, passing the same way**, which is the point of a
release claiming no functional change. 81 routes, also unchanged. Version strings
moved in exactly five places: `pyproject.toml`, the FastAPI app,
`app/package.json`, and the two root entries in its lockfile (dependency versions
untouched).

### Install

Download the installer for your OS below (`.dmg` / `.exe` / `.AppImage`), or run
`python -m pdi` from source and pick your device — see the [README](README.md). Installers are signed
only if signing secrets are configured; otherwise they are unsigned (see
[docs/releasing.md](docs/releasing.md)).

**Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
