# PDI v0.11.1 — release notes

*Ready-to-paste body for the GitHub Release created when you push the
`app-v0.11.1` tag. Kept in sync with [CHANGELOG.md](CHANGELOG.md).*

---

**PDI v0.11.1** — the desktop app finally carries its own vault. One of
three interoperating products, all three cut together at this version.

### The bug, as reported

Creating a tenant met **"Failed to fetch"** — because PDI's installer
shipped only the console window, pointed at a port where nothing was
listening. The sibling products got the bundled-backend treatment in
their packaging round; PDI never did. Every desktop install failed the
same way.

### What 0.11.1 ships

- **The whole vault, inside the installer** — a frozen one-file backend
  the app starts on launch, with every lesson the siblings paid for:
  version-matched adoption (no zombie backends), a free port when a
  stranger holds the default, the whole process tree killed on quit.
- **A master key that persists.** First run generates a 32-byte key and
  stores it beside the database — *your hardware, your keys, your
  walls*. Back up that file (`master.key`) and you back up the ability
  to read your vault; without this, a desktop vault would forget its own
  contents at every restart.
- **The release gate proves the first run**: on every OS, the exact
  frozen binary creates a tenant, seals a record, reads it back —
  restarts — and reads it again. No installer ships a first run that
  was not performed.

### Verification

266 tests green; the packaging smoke (tenant → seal → read → restart →
read) passed on Windows, macOS and Linux runners before the installers
were allowed to exist.

### Install

Download the installer for your OS from the assets below — and from this
version on, PDI updates itself like its siblings.

**Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
