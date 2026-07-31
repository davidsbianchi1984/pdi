# PDI v0.22.0 — release notes

*Ready-to-paste body for the GitHub Release created when you push the
`app-v0.22.0` tag. Kept in sync with [CHANGELOG.md](CHANGELOG.md).*

---

**PDI v0.22.0 — the console backlog reaches zero, and closes the audit across all three products.**

The desktop console could not reach **84** of the vault's routes. Every one was
present on a phone shell.

| | at the start of this release | now |
|---|---|---|
| Console-doorless routes | 84 | **0** |
| Routes no client anywhere calls | 3 | **0** |
| `api.ts` bindings nothing calls | 3 | **0** |

All three record files are now **empty rather than short**, and the tests that
read them assert emptiness.

## Five new screens

Screens 48–52, one per family:

- **Carriers** — a sealed thing, and the code on the outside of it. The scan
  side takes no credential at all, deliberately: a code on a crate is for
  whoever is holding the crate. What they learn is capped by `disclose`, what
  they can do is leave a note in the chain of custody, and `contents` is null
  on every card. The card says it in its own words — *this code proves custody,
  not contents*.
- **Exchange** — what leaves sealed and what is asked to come in, with the
  chain of custody and the audit-chain verification above it rather than under
  it. A custody list nobody can check is a list of claims.
- **Custody** — the key, the hardware, the paperwork. The question at the top is
  the only one this product really answers: *can the operator decrypt this?*
  Everything below it is downstream of the answer.
- **Bridges** — what reaches in: a connected account, a robot on a floor,
  another product's contributions. The contributions listing is a count and a
  set of keys and never contents.
- **Guiding** — the console's own guide, its corner pane, and the words it uses.

Each with a walkthrough lesson and assistant phrasing.

## What driving the routes found

Nothing in the vault was broken. Six places where the route table and the wire
disagree, every one of which would have shipped as a dead button:

- **`receive` and `submit` take tokens of their own, in headers of their own**
  — `x-receive-token` and `x-submit-token`, not the tenant's bearer token. The
  party receiving a transfer is a clinic and the party submitting to an intake
  is a records office; neither is the tenant, has a tenant credential, or
  should. Bound as bearer credentials both are a 403 every time.
- **The scan page is HTML and two `qr.svg` routes are SVG.** PDI's client runs
  `JSON.parse` on every body without guarding it, so binding them through it
  did not return the wrong thing — it threw `SyntaxError: Unexpected token <`
  from inside the client, which names nothing.
- **A key provider is `held` or `kms`** — not `customer`, which is what the
  concept is called in the plan copy, in the hosting guarantees, and in the
  field `customer_managed` two lines from the one that rejects it.
- **A beacon's `disclose` is a single value**, `blind` or `contact`, not the
  list of fields to reveal that the name suggests.
- **`ref_kind` and a ring's `kind` are four values each**, and a token's role is
  `read` or `write`.

Three of those the server answers with the exact set of legal values in its
422 body, so the unions in the client are transcribed from the vault rather
than invented.

## Three things the console never offered

- **What an audit action means, on the screen that lists it.** The backend has
  published the action glossary since the log existed; the console showed raw
  action names beside it. A log whose vocabulary is undocumented where it is
  read is a log somebody has to guess at during an incident.
- **Whether a page could have been delivered at all.** The gateway listed pages
  and whether each arrived, and never said whether a channel was configured —
  so a deployment with none showed *nothing paged*, which reads as a quiet week
  and means the opposite.
- **Revoking a grant token.** Revoking a bequest and killing the token it has
  already handed to a person are different acts. Only the softer one had a
  button.

## The audit could not see three of its own new doors

Adding the text helper made the scan page and both `qr.svg` routes invisible to
`clientpaths`, which reads one shape of call — it reported them as newly
doorless in the same commit that gave them working buttons. That is the third
extractor false positive here, after the nested template and the `<img src>`,
and the lesson has not changed.

## Two guards that could only pass while the problem existed

One asserted the union backlog was *strictly* smaller than the console's; the
other asserted the snapshot file was non-empty. A check that can only be
satisfied by the problem still existing is not a check. Both rewritten.

**Suite: 359 passing, 1 skipped.**

---

Cut in step with [QRME](https://github.com/davidsbianchi1984/qrme) and
[JIM-mini](https://github.com/davidsbianchi1984/jim-mini), both also at
v0.22.0. All three reached zero on the same audit in this release.
