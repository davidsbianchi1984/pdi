# PDI v0.19.0 — release notes

*Ready-to-paste body for the GitHub Release created when you push the
`app-v0.19.0` tag. Kept in sync with [CHANGELOG.md](CHANGELOG.md).*

---

**PDI v0.19.0** — the console can tell you what broke, without telling you
anything about anybody.

Every failed request is now recorded and, where a build has somewhere to
send, reported. What gets kept is the *operation* and the status code:
`POST /bequests/{id}/activate → 500` identifies a bug, where the
unredacted version of that path identifies a person and an arrangement
they made. Only the first is written down, and the redaction happens
before the row is stored, so there is no moment at which the buffer holds
something that would later have to be scrubbed. A query string can name a
vault key; it never survives.

**Nothing goes before you have been asked.** Sending is opt-out, which
only means something if the opting-out can happen before the first report
rather than being discovered afterwards in a panel nobody opened. A
first-run notice holds everything until it is answered — and it shows the
actual payload rather than describing it, from the same function that
sends it, so it cannot go stale while still reading honestly. The switch
in Settings is that same answer, changeable whenever.

Counts are sent as **deltas**: each row remembers how much of itself has
been reported, so reopening the app twenty times does not turn one broken
screen into twenty. A failed send moves nothing, and the next launch
retries.

**The receiving gateway refuses rather than redacts.** It accepts exactly
five top-level keys and five per problem and rejects anything else — an
unknown field, a `platform` string long enough to hide a sentence, a `day`
carrying a time of day, a path with an unredacted id still in it. It could
redact that path itself; doing so would let a build whose redaction had
broken keep working while nobody learned that every report from those
users had been arriving with an id in it.

**Nothing here touches the vault.** No record, no key and no seal is
involved — the log holds route shapes and status codes, and the vault's
own contract is unchanged. Nothing in this release alters what a key
opens.

**Off by default, by absence rather than by flag.** The collector address
is compiled in at build time and unset, so an installer built without one
has nowhere to send and no code path that could acquire one. There is no
address for a later mistake to switch on.

**Fixed** — four bugs found by running the thing rather than reasoning
about it. The gateway had no CORS at all, so every browser preflight would
have been refused and every report would have failed silently. Its
validators were anchored with `$`, which in Python also matches before a
trailing newline, so `Win32\n` passed a check whose error message promised
newlines were not allowed. A counter file that was valid JSON of the wrong
shape was adopted wholesale and took the read endpoint down with it. And
the test guarding the payload shape ran only in the repository that ships
the gateway, not here.
