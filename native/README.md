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

- **Language** (`/languages`, `GET/PUT /language`, picker on the Overview
  screen): PDI's fixed explanatory note strings are hand-translated (es, fr)
  and swapped into every JSON response for tenants who set a language —
  structured data and sealed values pass through untouched, and unknown
  languages keep English notes rather than machine-mangling them.
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
