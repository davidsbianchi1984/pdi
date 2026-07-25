# PDI v0.1.9 — release notes

*Ready-to-paste body for the GitHub Release created when you push the
`app-v0.1.9` tag. Kept in sync with [CHANGELOG.md](CHANGELOG.md).*

---

**PDI v0.1.9** — the release where handing off at the gate stops meaning
*writing a name down*. One of three interoperating products (with
[qrme](https://github.com/davidsbianchi1984/qrme) and
[jim-mini](https://github.com/davidsbianchi1984/jim-mini)), all three cut
together at this version.

### Highlights

- **A hand-off reaches a person now.** The agent at the gate could always hand
  off. What it could not do was *tell anybody*: `handed_to` recorded the on-call
  contact, the ring went to `handed_off`, and somebody could stand at a door at
  2am waiting for a person who did not know they were there. An escalation that
  escalated to a database row.

- **PDI ships no vendor.** It cannot know how a deployment reaches its people —
  a manned NOC, one on-call phone, a pager system, a chat webhook — so it posts
  a signed JSON envelope to `PDI_NOTIFY_URL` and stops. No SDK, no account, and
  the same envelope shape JIM-mini uses, so an operator running both can point
  them at one receiver.

- **The sentence that made this worth building.** Every scripted hand-off says
  some version of *I've passed this to the on-call contact* — which a person at
  a door reads as **someone now knows I am here**. When the page does not go
  out, that reading is false, and the cost of it is somebody waiting outside in
  the dark. So the reply carries `reached_somebody: false` and an
  `unreached_note`, and the scan page renders it as its own warning above the
  *Passed to* row. Not as a clause at the end of a paragraph, and not by editing
  words a model may have written.

- **A page never fails a ring.** The caller gets their answer whether or not the
  webhook answered; a dead webhook is recorded rather than raised. The envelope
  inherits the beacon's blindness — kind, outcome, and where to read the rest
  under the tenant's own token, with **not even the caller's own note**, which
  is free text typed by a stranger and belongs in the sealed transcript rather
  than in an outbound webhook that may be a third-party chat room. A test reads
  the whole envelope as one string and looks for the filename, the counterparty,
  the classification and the caller's words in it.

- **Three audit actions rather than one** — `agent.page`, `agent.page_queued`,
  `agent.page_failed` — because *a human was told* and *a human was not told*
  are the two things an auditor is actually asking about, and one action would
  have hidden the second inside the first. An expected delivery pages nobody at
  all: waking the on-call for a parcel that was booked in is how a pager becomes
  something people ignore.

- **Unconfigured stays supported.** With no URL the page is `queued` — exactly
  what the gate did before — except it is now a row
  `GET /gate/pages?undelivered_only=true` can list rather than an absence nobody
  could see. `GET /gate/channel` says whether a page can go out at all, without
  revealing the URL, so it is checkable in the afternoon rather than at 3am.

- **The tandem doc was describing a past release** — and missing this
  repository's own arrow. `pdi/qrme_client.py`'s docstring cited *"every arrow
  in docs/tandem.md points into PDI"* while being the thing that made it false.
  [docs/tandem.md](docs/tandem.md) is now identical byte-for-byte in all three
  repos, with a `pdi ✕ qrme` section, a beacon-family section, and
  `docs/diagrams/tandem-flow.svg` generated rather than hand-drawn.

### Verification

177 tests green (11 new this release). 78 routes. Version strings moved in
exactly five places: `pyproject.toml`, the FastAPI app, `app/package.json`, and
the two root entries in its lockfile (dependency versions untouched).

### Install

Download the installer for your OS below (`.dmg` / `.exe` / `.AppImage`), or run
`python -m pdi` from source and pick your device — see the [README](README.md). Installers are signed
only if signing secrets are configured; otherwise they are unsigned (see
[docs/releasing.md](docs/releasing.md)).

**Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
