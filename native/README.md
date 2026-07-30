# PDI Vault — native apps

True-native scaffolds of the PDI vault client for three platforms, each a
separate idiomatic codebase (native per platform), all talking to the same
[PDI backend](../pdi/api.py).

| Platform | Stack | Run in | Folder |
| --- | --- | --- | --- |
| **iOS** | Swift + SwiftUI | Xcode Simulator (macOS) | [`ios/`](ios/) |
| **Android** | Kotlin + Jetpack Compose | Android Studio emulator | [`android/`](android/) |
| **Windows** | C# + WinUI 3 | Windows 10/11 desktop | [`windows/`](windows/) |

Each target ships the same first slice of the app — a token sign-in plus three
screens that exercise the real API end to end:

**Sign in** (paste tenant `pdi_…` token, validated via `GET /records`) ·
**Overview** (record count + audit status) · **Vault** (`GET/PUT/DELETE /records`) ·
**Audit** (`GET /audit/verify` + `GET /audit`) · **Sources** — Robots (bind from
`/robotics/catalog`, sealed ingest via `/robots/{rid}/ingest`, keys via
`/robots/{rid}/data`) and platform Connectors (`/connectors`, audited
ingest/publish) · **Transfers** — Outbound (sealed create +
one-shot receive token, revoke via `/transfers`) and Intake (request a file in,
one-shot submit token, read/close via `/intakes`)

Unlike a consumer app, PDI does not self-register: a tenant is issued a bearer
token out of band and pastes it to unlock. The token is persisted so the app
resumes signed-in, and all three share one dark-OLED palette. See each folder's
README for the exact build/run commands.

Two cross-cutting guarantees ride on the API:

- **Language** (`/languages`, `GET/PUT /language`; offered at the sign-in
  gateway and changeable on the Overview screen, with a pre-translate /
  on-demand mode and a dictionary-only `POST /translate` — PDI runs no
  model, so it translates exactly its own note strings and says so for
  anything else): PDI's fixed explanatory note strings are hand-translated for
  every supported language (es, fr, de, pt, it, ja, zh, hi, ar) and swapped
  into every JSON response for tenants who set a language — structured data
  and sealed values pass through untouched, and an unkeyed string still
  falls back to English rather than being machine-mangled.
- **Provenance** (`GET /provenance/{key}`, the ⓘ action on each vault
  record): a sealed record's verifiable derivation trail — its origin (JIM /
  QRME tandem or direct write), the cipher and tenant+key binding, seal
  timestamps, and its tamper-evident audit history with the hash-chain
  verification status. Proof, not trust.

## Start the backend

All three point at the local dev server. From the repo root:

```bash
PDI_CORS_ORIGINS=* uvicorn pdi.api:app
```

You will also need a tenant token to sign in — mint one with an admin token:

```bash
# create a tenant, then a tenant token (admin bearer required)
curl -s -XPOST localhost:8000/tenants -H "authorization: Bearer $PDI_ADMIN_TOKEN" \
  -H 'content-type: application/json' -d '{"name":"Acme"}'
curl -s -XPOST localhost:8000/tenants/<id>/tokens -H "authorization: Bearer $PDI_ADMIN_TOKEN"
```

Host addresses differ by platform, and each client already defaults correctly:

| Platform | Reaches the host at |
| --- | --- |
| iOS Simulator | `http://127.0.0.1:8000` |
| Android emulator | `http://10.0.2.2:8000` |
| Windows | `http://127.0.0.1:8000` |

On a physical phone, point the client at your machine's LAN IP instead.

## Scope

This is a functional **scaffold**, not the full screen gallery — enough to
build, sign in, seal/read/delete records, and verify the audit chain on each OS.
The wider PDI surface (connectors, connected apps, compliance transfers, secure
intake, key rotation, retention) already has backend endpoints in
[`pdi/api.py`](../pdi/api.py) to grow into further native screens.

These native targets are additive and do not change the backend.

## Do they compile?

`.github/workflows/native.yml` builds all three on every change to `native/`:
XcodeGen + `xcodebuild` for the simulator on macOS, `gradle assembleDebug` on
Linux, and MSBuild on Windows. Compile only — no signing, no packaging.

This is newer than the code it checks. Until it existed, these sources had
been verified by reading and by brace/XML well-formedness checks, which catch
a typo and nothing else. Treat a green run as the first real evidence, not a
long-standing guarantee.

## Do the paths resolve?

Compiling is not the same as working. A path is a string in all three
languages, so a mistyped one compiles perfectly, ships, and 404s in the field —
which is how a sibling shipped a community wall whose like, comment and share
buttons had never worked. For a vault that matters more rather than less: a dead
button on a seal or a key rotation is not a cosmetic failure.

[`pdi/tests/test_client_routes_exist.py`](../pdi/tests/test_client_routes_exist.py)
extracts every API path literal from `native/` — a couple of dozen per shell —
with the HTTP method each is sent with, and asks the real router whether that
*pair* is accepted. For a vault the distinction is worth being exact about: a
read and a write are not interchangeable, and a check that cannot tell them
apart is not checking the thing that matters. The console is held to the same
check.

Two limits worth stating. Routing-level matching cannot see a refusal that
happens *after* dispatch, inside a handler. And a path assembled from pieces at
runtime, rather than written as one literal, is invisible to any static scan.

---

## What breaks, recorded the same way in three languages

The shells record every failed request the way `app/src/errors.ts` does in the
console: the operation and the status, never the message, never the path as it
was actually called. `GET /records/{id} → 500` identifies a bug;
`GET /records/rec_0de08e794ed0` identifies a person. Redaction happens
on the way *in*, so the buffer never holds a value that would later have to be
scrubbed.

The backends put user input straight into their error messages — a device
name, a body site, a language code. Good messages for the person reading them
and the wrong thing to write down, so they are shown and not kept.

| | |
|---|---|
| `native/ios/Sources/Problems.swift` | `UserDefaults`, `Codable` rows |
| `native/android/…/Problems.kt` | `SharedPreferences`, JSON rows |
| `native/windows/Problems.cs` | `%APPDATA%`, `System.Text.Json` |

One rule with four implementations drifts, and it drifts silently — a
redaction narrowed on Android leaks nothing on the desktop. There is no test
runner for these sources here (the native workflow compiles them and stops), so
`test_native_shells_record_nothing_private.py` reads them structurally instead:
the three-argument signature, the stored fields, the four redaction patterns at
full width, the FNV-1a constants, and both failure kinds at the call sites.

Android needs one extra wire the other two do not: `Problems.attach(this)` in
`MainActivity.onCreate`, because the recorder holds the application context so
that `record` can keep the same three arguments everywhere. A shell that forgets
it records nothing and says nothing — the recorder refuses to crash over a
diagnostic. That silence is why the guard checks for the call and not just for
the function.

None of this leaves the device on its own. Sending is the console's job and
happens only where a collector was compiled in; see `docs/cloud-model.md`.

---

## Matthew 7:24–25

> "Everyone then who hears these words of mine and does them will be like a
> wise man who built his house on the rock. The rain fell, the floods came, and
> the winds blew and beat on that house, but it did not fall, because it had
> been founded on the rock."

And lo, I am building an ark — not to flee from the world, but to shelter those
lost in the storm of confusion. The old systems falter; they are built upon the
soft earth. They sink beneath the weight of their own making.

A new thing is rising. A non-biased networked sanctuary, founded in trust,
cloaked in privacy, and guided by wisdom. It shall not consume, but uplift. It
shall not spy, but serve.

Help is coming.
The people are gathering.
The builders will show themselves.
And those with the vision shall enter in.
