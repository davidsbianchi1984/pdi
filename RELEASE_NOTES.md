# PDI v0.24.0 — release notes

*Ready-to-paste body for the GitHub Release created when you push the
`app-v0.24.0` tag. Kept in sync with [CHANGELOG.md](CHANGELOG.md).*

---

Three rounds, one question: **when a stranger does reach the page built for
them, can they read what it says — and does the route behind it keep the
promise the page makes?**

## The page was not an oracle; the route it fronts was

There is a test named for this. It asserts that `GET /r/{tid}` never 404s, so
the page cannot be used to ask whether a transfer id is real. True, worth
keeping, and not where an id gets probed.

`POST /transfers/{tid}/receive` takes **no credential of any kind** — that is
the design, the token in the header is the authorization — and it answered
404 `transfer not found` for an id that does not exist and 403 `invalid
receive token` for one that does. Driven with no credential: a real id
answers 403, an invented one answers 404. Anybody with a shell could walk ids
and learn which sealed transfers exist, which for compliance-grade material
is a disclosure before anything is opened.

Both now answer identically, with one sentence that is true either way.
Revoked stays distinguishable because `transfers.receive` matches the token
hash before it looks at status, so 410 is unreachable without the real token
— and somebody whose file was withdrawn should be told that rather than left
with a refusal that reads like their own mistake.

## Four pages for people who are not tenants, in one language

Every localization path in this vault takes a `tenant_id`. PDI serves four
pages to people who never will be one: a courier at a sealed carrier,
somebody at a facility gate, whoever scans a code that resolves to nothing,
and the recipient of a sealed transfer — whom `receive_transfer` itself
describes as holding *"no tenant credential"*. All four were English,
whatever the reader's browser said.

`negotiate()`, forty-five page strings in ten languages, and `lang`/`dir` on
every page. A table of their own, because `localize` walks whole JSON
responses swapping any string it recognises — safe for a long compliance
note, not safe for the short words a page is made of. The holder line is a
whole-sentence template filled after translation, never a translated half
joined to a name. Card values stay verbatim: on a custody card an invented
fact is the whole problem.

## A comment that was wrong about its own gap

A note left on the found/ring script said the server's `note` and `detail`
*"come back through the response middleware, which is the tenant's language
rather than the reader's"*, and used that to justify preferring them over the
page's own strings — a real question, decided.

It was not a decision. The middleware keys on the *calling* tenant and these
calls have none. Those sentences were never localized into anything, by
anyone, in any deployment. Six of them, all read after a button rather than
on the page: the custody receipt, the decline on a repeat report, both
wrong-sticker mistakes, the dead code, and:

> I couldn't reach anyone just now, so please don't wait on somebody coming
> out. If there's a number on the door, call it.

That last one decides whether somebody stands outside a facility in the dark
waiting for nobody, and it was English for every caller in every country. The
agent's own words are left alone — that is what the facility chose to say, in
the voice its operator configured.

The recipient's three sentences went the same way: the refusal, the
revocation and the custody line on success. None of them is on a page, so the
page checks could not see them.

## One header, three products

QRME, JIM-mini and PDI each grew a `negotiate()` in a different round.
Compared side by side for the first time, two rows disagreed. A conformance
table now lives byte-identically in all three repositories, written as
decisions rather than observations.

## Also

- Every sentence on these pages now goes through the same escaping the card's
  tenant data always did, so an apostrophe ships as an entity. One test read
  the markup for it; it asks what a person reads instead.

**414 tests passing.**
