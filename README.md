# Private Data Infrastructure (PDI)

**A private, encrypted data vault with a tamper-evident audit log and a
tenant registry.**

PDI is the storage layer the other two products can optionally run on top
of: sensitive data lives in PDI's encrypted vault instead of their own
databases, reached only over PDI's HTTP API. Both integrations are live —
JIM-mini vaults its medical and context payloads here, and QRME seals its
profile source material — each as its own tenant with its own token. See
[docs/tandem.md](docs/tandem.md).

**Current release: v0.99.1** — see [CHANGELOG.md](CHANGELOG.md).

PDI is one of three products versioned and released together:
[QRME](https://github.com/davidsbianchi1984/qrme) (synthetic profiles) and
[JIM-mini](https://github.com/davidsbianchi1984/jim-mini) (health guardian).
One version number names one tested combination of all three.

**Patents.** The platform is designed to host the AI agent services covered
by two pending applications: *Networked Responsive Personal Guidance System
for Known Conditions* (US 19/038,196, published as US 2025/0246290 A1) and
*Synthetic User Profile Management* (US 19/056,418, published as
US 2025/0265659 A1). See
[docs/invention-disclosure.md](docs/invention-disclosure.md).

## What it provides

- **Private, encrypted data vault** — record values are sealed at rest with
  AES-256-GCM (`pdi/crypto.py`); only ciphertext touches disk. AAD binds each
  record to its tenant + key so ciphertext can't be relocated.
- **Production key management (envelope encryption)** — a key-encryption key
  (KEK) never touches record data; each **key version** owns a random
  data-encryption key (DEK) stored only *wrapped* by the KEK. `POST /keys/rotate`
  mints a new version and re-seals records under it (old versions stay readable
  until `POST /keys/retire`); `GET /keys` reports versions. The KEK lives in the
  env (dev) or a **KMS/HSM** in production (`PDI_KEY_PROVIDER=kms`, a loud
  integration seam — never a silent local fallback).
- **Retention — from a short window up to forever** — per-tenant record
  retention (`7d`/`30d`/`90d`/`180d`/`1y`/`forever`, default **forever**) and a
  global soft-delete recovery window (`PDI_RECOVERY_WINDOW`, default forever);
  `POST /retention/sweep` expires records/purges tombstoned tenants past their
  window — `forever` expires nothing. The audit chain is always kept forever
  (pruning it would break tamper-evidence).
- **Documented audit event schema** — `GET /audit/schema` returns the field
  definitions and the full action catalogue (each action's category and
  meaning); every audit entry carries a derived `category`.
- **Tenant registry** — each integrating system gets a tenant + bearer token;
  data is strictly namespaced per tenant (no cross-tenant reads).
- **Tamper-evident audit log** — every access is recorded in an append-only,
  SHA-256 hash-chained log; `GET /audit/verify` detects any retroactive edit.
- **Disaster-recovery snapshot & restore** — `GET /snapshot` exports
  ciphertext only; `POST /restore` reinserts a snapshot after a loss, with
  AAD still binding every record to its tenant + key.
- **Cloud-model contribution intake** — `POST /contributions` seals
  anonymized model-improvement data from integrating systems under
  `contributions/{source}/…` keys, encrypted and audit-chained;
  `GET /contributions` lists the intake ([docs/cloud-model.md](docs/cloud-model.md)).
- **Position & assistant builder** — `POST /positions` turns a completed
  AI Integration & Role-Mapping Questionnaire (industry-agnostic) into an
  assistant *blueprint* — recommended capabilities, an automation-opportunity
  score, human-in-the-loop guardrails, reskilling paths, and a ready-to-use
  assistant system-prompt. The raw workforce answers are sealed in the vault
  under `positions/{id}`; only the derived blueprint is returned. Decision
  support, never an automated staffing decision
  ([docs/positions.md](docs/positions.md)).
- **Custody beacons** — `POST /beacons` prints a code for a physical carrier
  (a records box, a decommissioned drive, a courier bag) or for the facility
  door itself, so custody stays visible once a payload has a handle. The seal
  card at `GET /s/{id}` says a thing is under custody and what governs it, and
  **never what is in it**. A finder's `POST /s/{id}/found` is a custody
  receipt, not a message: it lands in the hash-chained audit log, so a gap in
  a carrier's chain becomes a compliance finding PDI can produce on demand.
  Plain scans stay off the chain — a barcode gun sweeping a pallet must not
  fill a tamper-evidence log. Blind by default, because naming the tenant can
  itself be the disclosure ([docs/beacons.md](docs/beacons.md)).
- **The agent at the gate** — `POST /s/{id}/ring` triages a facility ring when
  no human is awake. PDI grows no model: the voice is a QRME profile over HTTP
  (`PDI_QRME_URL` + `PDI_GATE_PROFILE`), which also means it carries QRME's AI
  mark, and an unconfigured deployment answers from a written script with no
  model anywhere near it. **The model is the voice, not the decider** —
  `gate.decide()` takes no model output, so there is no code path from
  generated text to a consequential action. The ceiling comes from the
  `HUMAN_IN_LOOP` set `positions.py` already publishes, and is itself published
  at `GET /gate/ceiling`: the agent may direct, check, structure a receipt and
  hand off, and may **never** grant entry, assert identity, override an
  authorization, or see contents. A hand-off is **delivered**, not merely
  filed: PDI posts a signed envelope to `PDI_NOTIFY_URL` and, when nobody was
  reached, says so on the scan page rather than letting *"I've passed this to
  the on-call contact"* leave somebody waiting in the rain for nobody.
- **A per-tenant on-call roster** — `POST /gate/roster` sets who answers *this*
  facility's gate and when, in the tenant's own database rows under the
  tenant's own token. It replaces one deployment-wide `PDI_GATE_ONCALL` that
  routed every customer's courier to the same name. Shifts cross midnight
  correctly (`18:00`–`06:00` belongs to the day it started), the facility's
  IANA timezone is **refused if unknown** rather than silently read as UTC, and
  a page that a webhook rejects moves to the next name — with one contact, a
  failed page was the end of the line.
- **Role-based access control** — `POST /tenants/{id}/tokens` issues scoped
  `read`/`write` tokens; read tokens cannot write or delete, and
  `DELETE /tokens/{token}` revokes instantly.
- **Tokens hashed at rest** — only the SHA-256 hash of each tenant/scoped
  token is stored, so a leak of PDI's own database yields no usable
  credential; the plaintext is shown once at issuance. The admin token is
  compared in constant time.
- **Deployment record** — models the on-premises vs. colocation (Tier III+)
  options from the proposal.

## Product surfaces

| Surface | Where | Notes |
|---|---|---|
| API server | `pdi/` | FastAPI + SQLite. `python -m pdi serve` or `uvicorn pdi.api:app`. |
| Operator console | `app/` | React + TypeScript (Vite); also served by the backend. |
| iOS / Android / Windows | `native/` | Native shells at parity with the console. |
| Desktop app | `python -m pdi desktop` | Electron wrapper; packaged installers on the releases page. |

## Quick start

```bash
pip install -e .[dev]
export PDI_MASTER_KEY=$(python -c "import base64,os;print(base64.b64encode(os.urandom(32)).decode())")
uvicorn pdi.api:app

# or the launcher menu — phone, desktop, installer, headless:
python -m pdi
```

`PDI_DB` sets the SQLite path (default `pdi.db`). `PDI_MASTER_KEY` is base64
of 32 bytes; in production the key-encryption key belongs in your own
KMS/HSM (`PDI_KEY_PROVIDER=kms`) — an ephemeral key is generated if unset,
for development only.

## Configuration

| Variable | Purpose |
|---|---|
| `PDI_MASTER_KEY` | Base64 key-encryption key (dev). Production uses `PDI_KEY_PROVIDER=kms` with `PDI_KMS_BACKEND` / `PDI_KMS_KEY_ID`. |
| `PDI_DB` | SQLite path (default `pdi.db`). |
| `PDI_ADMIN_TOKEN` | Operator token; open admin fails closed off-machine. |
| `PDI_RECOVERY_WINDOW` | Global soft-delete recovery window (default forever). |
| `PDI_CORS_ORIGINS` | Allowed console origins. |

See [docs/hosting.md](docs/hosting.md) and
[docs/operations.md](docs/operations.md) for production deployment.

## Documentation

| Document | Contents |
|---|---|
| [docs/tandem.md](docs/tandem.md) | Running PDI under QRME and JIM-mini. |
| [docs/operations.md](docs/operations.md) | Day-two operations: keys, retention, backups. |
| [docs/hosting.md](docs/hosting.md) | Production hosting. |
| [docs/enterprise.md](docs/enterprise.md) | Enterprise compliance transfer. |
| [docs/baa-template.md](docs/baa-template.md) | Business associate agreement template. |
| [docs/invention-disclosure.md](docs/invention-disclosure.md) | The patent filings. |
| [docs/releasing.md](docs/releasing.md) | How releases are cut. |
| [docs/gallery.md](docs/gallery.md) | The full desktop and mobile console gallery. |

## Release history

<details>
<summary><b>What each release added, newest first</b> — the short version of
how it got here; full detail in <a href="CHANGELOG.md">CHANGELOG.md</a>.</summary>

| Release | What landed |
|---|---|
| Release | What landed |
|---|---|
| **0.99.1** | **Version alignment** — the trio releases together; this release's changes live in the qrme and jim-mini repositories, and nothing changed here since 0.99.0 |
| **0.99.0** | **Version alignment** — the trio releases together; this release's changes live in the jim-mini repository (the wrist becoming a real surface), and nothing changed here since 0.98.0 |
| **0.98.0** | **The posture proves the model answers** — `GET /resident` carries `local_model_standing`: one round trip to the daemon's own `/api/tags` saying reachable-or-not and pulled-or-not, with the fix named (`ollama pull …`, or the container and network to check); a configured server that dies mid-conversation answers a sentence under model `local-unreachable` instead of a raw socket error — and a plan step that got that sentence is a **failed** step wearing it, never a sealed apology marked done |
| **0.97.0** | **The reading tools refuse a recording** — `fetch.url` and `fetch.render` pointed at media used to strip markup from binary and seal mojibake as a capture; both now refuse by name of `fetch.listen`, on the same canonical suffix list the qrme briefcase and lookout read (path-only, query stripped — a page containing a player is still a page) |
| **0.96.0** | **Version alignment** — the trio releases together; this release's changes live in the jim-mini and qrme repositories (the standing voice conversation, the agent's hands on the look, the settings-page device lists, the room picture full-bleed, the reply ceiling back to five), and nothing changed here since 0.94.0 |
| **0.95.0** | **Version alignment** — the trio releases together; this release's changes live in the qrme repository (the ears arc reaching every briefcase door), and nothing changed here since 0.94.0 |
| **0.94.0** | **The capture grows ears** — `fetch.listen` joins the resident's vocabulary: the deployment's transcription sidecar turns a recording into the words said in it, on the facility's own hardware, sealed with the same change-memory the fetches keep; a deployment without ears refuses in words rather than sealing silence or bytes, the planner hears "listen", "transcribe" and "hear", and the published registry names the three fetches that leave the host |
| **0.93.0** | **The capture grows eyes, and the ledger stops editing itself** — `fetch.render` joins the resident's vocabulary (the page as a person meets it, sealed with the same change-memory; the plain fetch stands in and the seal says so on a deployment without eyes), and the runs ledger becomes tamper-evident: the database refuses edits, rows chain per task, a verify door walks the links, and every cycle anchors its hash on the permanent audit chain |
| **0.92.0** | **Version alignment with the tandems** — no functional changes; the trio versions and releases together |
| **0.91.0** | **Version alignment with the tandems** — no functional changes; the trio versions and releases together |
| **0.90.0** | **The fetch notices change, and the vault remembers its rounds** — captures carry a fingerprint (`sha`), `changed_at` (kept while content is identical, moved when it differs) and `first_seen_at`, with pre-fingerprint seals never reported changed by the migration itself; each cycle's summary discloses `(first capture)` / `(unchanged)` / `(changed)`. And every cycle lands one row on a per-task runs ledger — when it ran, done or failed, one line of note — read newest first through `GET /resident/tasks/{tid}/runs` behind the tenant fence, last 200 rounds kept, cancel and wipe sweeping it, a "Past rounds" button on the console and all three shells |
| **0.89.0** | **Ask the vault: grounded answers from what it holds** — `POST /resident/ask` retrieves first: the question ranks this tenant's vectors, the matched seals are read back, and the local model answers *from* them, all inside the host, with `drew_on` naming the keys the answer stood on — an empty list said, not padded. The ask door learns a `prefix` (a character compare narrowing what may ground an answer, over-fetched ahead of the wall so one person's nearest moments are not lost behind strangers') and carries a `system` persona ahead of the grounding block, so the tandems' coaches and profiles survive being grounded. The audit counts characters and keys, quoting neither. On the console and all three shells |
| **0.88.0** | **The voice door, the standing tasks, and the off switch** — `POST /resident/infer` puts local inference behind a single door so the tandems' coaches and profiles can speak from inside the facility (prompt never leaves the host, audit counts characters and quotes nothing, the stub answers under its own name). A plan can carry `every_hours` and the vault re-runs it itself: `pulse()` walks tenants then each tenant's due tasks so the isolation fence holds on the heartbeat, `PDI_RESIDENT_PULSE` starts the in-process loop, `done` is a resting state whose steps reset each cycle, failures retry, overlapping beats never double a run. And `DELETE /resident/tasks/{tid}` is the off switch: a cancel ends the future, not the record — running refuses, cross-tenant finds nothing, every cancel audited. All of it on the console and all three shells |
| **0.87.0** | **Forgetting reaches the vectors, everywhere** — the resident's embedding index gets its doors out: `DELETE /resident/embeddings/{key}` takes one vector, `?prefix=true` takes a person's whole shelf in one call (a character-compare prefix, never a LIKE wildcard), another tenant's forget removes nothing, and every forget lands on the audit chain. The tandems stand their erasure sweeps on it, the console and all three shells wear a per-match forget button — and the vault's own front door keeps the same promise: deleting a record takes any vector indexed under its key, through the one `resident.forget` implementation, with the audit line written only when a vector actually went |
| **0.86.0** | **Tenant isolation in the SQL, and the database made smart** — every one of the forty-six statements that reached tenant-scoped tables by bare id now constrains `tenant_id` in the statement itself, the ten that genuinely cannot wear a written reason with a ceiling, and an AST guard plus live cross-tenant tests hold the fence from both sides. On top of it, the **resident intelligence**: the agent living in the vault process — multi-step plans by deterministic rules, a closed tool registry whose `leaves_host` column travels with every step, structured rows into queryable datasets straight from a fetch, embeddings and cosine search that keep a hash and never the text, and local-only inference with an honest stub — no separate orchestration service, the same doors and privacy over standard HTTPS, on the console and all three shells |
| **0.85.0** | **The front page reads like a product** — the README cut down to a professional overview at the owner's ask, the console galleries moved whole to `docs/gallery.md`, the release table folded but present, and the guards that held the old page holding the same promises across the pair. No functional changes to the vault itself |
| **0.84.0** | **The version, and nothing else** — no code changes in this product. JIM-mini took this release on its own: one window over everything a guardian is running, both people having to agree before a link outlives the call, what the offline coach could not settle becoming a paid errand only where it had to, the day as it was taken in measured against what the roster promised before anything was switched on, a room reading cues rather than keeping footage, and two people on one call each with their own second channel. This product skipped 0.83.0 — that release touched nothing here and the number was left where it was rather than cut for the sake of it — which is exactly the drift the version guard exists to prevent, since a box carrying two numbers reports the mismatch to whoever is using it rather than to whoever deployed it. The three come back onto one number here |
| **0.82.0** | **One page about one machine, and this repository says where it is** — this repository documents running the product on its own; the live beta is four containers on one box, documented once in QRME beside the compose file it describes. An operator standing here at the end of a release had no way to find it. `docs/hosting.md` says where it is, and why there is one copy rather than three — copies of a page about one machine disagree the first time somebody fixes only the one they had open |
| **0.81.0** | **The sentence that forgot how it was built** — `str()` on a `Templated` returns a plain `str`, which drops the template, so a refusal built by `i18n.fill` and passed on as `HTTPException(403, str(exc))` reaches the reader as bare English in every language, looking exactly like a sentence nobody has translated yet. QRME shipped it on the sentence somebody reads while something is going wrong. Nothing here launders a template that way today, and this release is what keeps that true rather than assumed: `i18n.raised` hands a refusal on in the shape it was raised, and a guard carried by all three products fails any route that reaches for `str()` instead |
| **0.80.0** | **The version, and nothing else** — no code changes in this product. QRME took this release on its own (the agent asking people rather than pages, and the ledger of which far hosts keep watching it leave); the cut keeps the three reporting one number to the tandem's version guard |
| **0.79.0** | **Cut in step** — no PDI code changed. QRME's plug-in storefront is what this version is; the vault, the journal and the sealing are unchanged |
| **0.77.0** | **Cut in step** — no PDI code changed. QRME's Agent round and JIM's circle-list fix are what this version is; the vault, the journal and the sealing are unchanged |
| **0.76.0** | No functional changes to PDI. The number moves because the three products are cut as one release; two shared guard records moved rows out of the divergence backlog and into the manifest |
| **0.75.0** | **No functional changes to PDI** — cut with the siblings. The round's work was next door, and one line of it is this repository's: JIM-mini took a port of the hash-chained audit log designed here, `user_id` where PDI has `tenant_id`, including the part that has survived a dozen releases of new actions — fixed stored-and-hashed fields with `category` derived at read time, so a catalogue can grow forever without breaking a single existing hash |
| **0.74.0** | **A guarantee nobody re-runs is marketing** — the infrastructure specification's acceptance section listed five criteria and three were already asked by guards in CI, which is the right place for them and the wrong reader: a vendor assurance is precisely what a sovereignty proposition is not selling. `pdi/acceptance.py` runs the five against a live deployment and returns a dated pass/fail per check, whole, repairing nothing it finds. One criterion would have failed — "key rotation with no bulk plaintext exposure" had no operation behind it — so `crypto.rewrap()` opens each stored data key under the old KEK and seals it again under the new one, all-or-nothing, records never read |
| **0.73.0** | **The phones that never asked which backend** — `/health` has answered a `version` since a stale backend first cost somebody an evening, and every native shell decoded that field away, so a phone pointed at an older install looked alive while newer screens said "Not Found" for no stated reason. All three read it now and raise a dismissible banner naming both versions and the address, in ten languages. The rest of the round is guards: `client_symmetry.txt` names treatments one row per client and refuses any written for fewer than four, because the drift that matters is a treatment three clients have and the fourth does not — and the release checklist's count of version fields is tied to the manifest the guards actually read, having been wrong in both directions |
| **0.72.0** | **No functional changes to PDI** — cut with the siblings. One guard came across: the Swift reader in `test_the_tabs_are_translated_and_the_screens_are_not` stopped at the first quote inside an interpolation and counted a property name as an untranslated sentence. Nothing here trips it yet, which is exactly the case `shared_guards.txt` exists for |
| **0.71.1** | **No functional changes to PDI** — cut with the siblings. In QRME, `widgets.py` imported a POSIX-only module at the top of the file, which took the whole API down on Windows: the frozen desktop backend would not start, and two releases published with no installers attached at all |
| **0.71.0** | **No functional changes to PDI** — cut with the siblings. In JIM-mini, an engaged session stays open until you sign off, acts across your own records through a written allowlist, and lands every change on a trail you can take back; in QRME, an embedded player learned the origin it needs to play and the feed deck became the screen rather than a card on it |
| **0.70.1** | **No functional changes to PDI** — cut with the siblings. In QRME, the widget runner asked whether *an* interpreter existed and never whether it was new enough, so a host carrying Node 18 reported ready and then failed every run |
| **0.70.0** | **The light stopped sitting on the menu, and custody is not ownership in writing** — the vault light and its minimized dot clear the phone's tab bar and speak ten languages; the terms say that PDI's holding confers nothing and that a data subject's statutory rights survive it (terms 1.2 → 1.3); the failure reports come home to this backend; and the doorless backlog on all three shells reaches zero |
| **0.68.0** | **Cut in step** — no PDI code changed; QRME gained the memory door, the steering lock, character-card import and rehearsal rooms that forget on purpose, while JIM's meals, weekly letters, interview drills and bank statements all took their private halves to this vault |
| **0.67.0** | **Cut in step** — no PDI code changed; QRME's licences now carry real substance under a manifest and organizations lease specialists, JIM's tandem sends the triggering vitals across the handoff, collected rooms are scanned for hazards, and a minor's consent became the guardian's own verified click |
| **0.66.0** | **Cut in step** — no PDI code changed; JIM-mini's coach became an offline add-and-norm stack over stored knowledge and current readings, with a jampacked pack, deposits from paid model turns, and a curriculum JIM studies on one press |
| **0.65.0** | **Cut in step** — no PDI code changed; QRME's standing rooms learned to be one place instead of a stamp, its lobby's join pitch gained the door it promised, and its friend faces open the friend's page |
| **0.64.0** | **The footsteps show** — a counter rides `/health` into the console's top-right corner: how many tenants hold a vault here, as an aggregate in ten languages, no name or id riding with the number, no new route and no new door — and it shrank to a footprint the same evening on a field report from the sibling product |
| **0.63.0** | **The screens behind the tabs speak, and the imported link is visited** — the vault, audit chain, robots, connectors, admin and feedback surfaces read from the ten-language tables on all three shells, Windows wording moving out of XAML attributes so a language change can re-read it (untranslated ratchet 65/59/69 → 6/5/1, a floor with names); `POST /connectors/{cid}/scrape` seals what a public page shows anybody as one encrypted record with the URL and fetch time written in, refusing offline before any socket opens; and the console fits the phone it runs on — grid tracks clamp, the app height tracks `100dvh`, the sidebar scrolls on its own |
| **0.62.0** | **Cut in step** — JIM's phones reached parity with its console — eleven rounds in one branch: every backend route gained a door on iOS, Android and Windows (the doorless ledgers close at the four by-design rows), the voice pair landed on all three shells with the device's own voice as fallback, Android learned to say PATCH through a test-pinned override, and the most-touched screens swapped their English for the ten-language tables. No PDI code changed; nothing new crosses into the vault. |
| **0.61.1** | **Ability is not a gate** — an accessibility statement with a door under it: an Accessibility tab on the console and all three shells, three questions with no tenant token (reporting that the vault shut you out must not require the token it may have shut you out of) and no identity column to fill, read only under the admin token. The sidebar's fifteen tab names finally speak all ten languages — the last hardcoded English in the frame. The known-gaps ledger opened at two rows and closes at zero, every closure held by a test, and Terms 1.2 says only what is true |
| **0.61.0** | **The console the policy blanked** — pdisystems.net went live and served a dark, empty page: the nonce Content-Security-Policy meant for the server-rendered pages was stamped on the console bundle no nonce can reach. A policy of its own for `/app`, the bare domain now lands on the console, and the release-bodies sweep survives its first honest run — a script that could not parse, then a fetch that silently lost releases, both repaired and guarded |
| **0.60.9** | **412 release bodies rebuilt** — every release that inherited the frozen v0.24.0 body now carries notes from its own CHANGELOG entry; the record reaches a ceiling of 0 with `app-v0.24.0` kept deliberately. Three checks that reported success while doing nothing are fixed: a sentinel that was one product's number, a backfill that trusted the record over the releases, and a guard that crashed when its count reached one |
| **0.60.8** | **The console reads in ten languages** -- the last six screens; `console_untranslated.txt` reaches 0 and becomes a floor rather than a backlog. A release checklist naming every version field replaces the prose list a bump was driven from. `RELEASE_NOTES.md` and its sync workflow deleted after 412 of 530 releases proved to carry one frozen v0.24.0 body; a reader replaces the writer |
| **0.60.7** | **A screen that imports the translator is not a translated screen** — two screens had been counted as localized since 0.48.3 while still holding fifteen English strings, six of them already in the table under keys the screen was importing `t` to reach. A guard now holds the claim; five more screens localized. 91 → 32. The type checker caught a second `const t = …` shadowing the translator |
| **0.60.6** | **A word boundary is a claim about a language** — Positions and Bridges localized, and the reader grading the work was wrong a third time: it asked for a letter-space-letter, so `Role &amp; industry`, `Human-in-the-loop` and twelve more were English nothing counted. 154 → 168 → 91. The drift guard caught *Bind* colliding with *Connect*; a seventh screen-grep now follows the key |
| **0.60.5** | **Carriers and Exchange, on the criterion of decisions before descriptions** — the console side of the courier's surface, and the screen where nothing has an undo. 225 → 154 across 87 rows. The type checker caught a `map((t) => …)` shadowing the translator; the drift guard caught 7 wordings disagreeing with the shells; two guards that greped English now follow the key |
| **0.60.4** | **The reader was a quarter blind, and both rounds were graded against it** — this console's English was measured by a regex that rejected any run containing a newline, an interpolation, or a lowercase first letter: 233 strings against the 177 it reported. The extractor QRME and JIM use is ported, the ceiling re-baselined honestly, and `VersionGuard` — invisible in all six of its strings — wired |
| **0.60.3** | **A check that cannot fail before the merge is not a check** — this product's CI happened to be green, on the same trigger that hid 29 red runs in QRME and 123 in `native.yml`. Green under a blind trigger is luck, not evidence. Trigger fixed in all three, and a guard that reads the triggers themselves |
| **0.60.2** | **The compiler was in the room the whole time and nothing listened** — the native workflow fires on any branch push now. iOS and Android green first; Windows named two missing `using` lists, a `_base` field the class does not have, a `Get` helper that lives in another product, a `ShowStatus` this page never had, and a public route the client could not ask for |
| **0.60.1** | **The sweep this product's history did not need, and one reason it has it anyway** — `cascade()` has read the schema since before 0.59.9, so the orphan class the siblings are cleaning up was never created here. `python -m pdi.orphans` lands anyway: a wipe removes the `tenants` row from the *caller* rather than the cascade, and one of those two callers is a scheduled sweep nobody reads. `audit` is kept and `bequests` retired, both borrowed from the cascade. Plus the member guard, which read `AppState.Current.X` only when a page spelled it out — next door that widening found 38 broken reaches; this tree came back clean |
| **0.60.0** | **An export is measured against the schema too** — `/snapshot` is the disaster-recovery export and is ciphertext-only on purpose, so nothing answered *what do you hold about us*: hosting history, bequests, beacons and the paperwork on file were not available to the tenant they describe. `GET /export` now answers, derived from the schema, redacting credentials **and** the sealed bytes that belong in the snapshot |
| **0.59.9** | **An erase is measured against the schema, not a list somebody wrote** — this vault already derived its wipe from the schema and was the only one of the three that did; both siblings carried hand-written lists and left forty-odd tables standing. The behaviour was right and unguarded, so the round that carried it next door also wrote it down here: plant a row in every tenant-scoped table, wipe, and look |
| **0.59.8** | **The check that covered one client of four** — 0.59.7 asked whether the shape a screen declares is the shape its route answers with, and asked it of the console alone. The three shells decode the same answers into their own types, and a wrong one there throws the same way. Extended to all four clients (console 116 · iOS 31 · Android 24 · Windows 20); no disagreements, and the reach is now a record that cannot go down, because a reader that stops matching reports agreement |
| **0.59.7** | **`req<T>` is a cast, and a cast is a claim nothing checks** — `GET /hosting/{tenant_id}/history` answers `{tenant_id, history}`; the console declared `Row[]` and the Custody screen called `.map` on it, throwing `history.map is not a function` during render on any vault that had ever been moved — which no fresh test vault ever has. Now read per call expression across all three consoles, with the reader's own blind spot kept as a test |
| **0.59.6** | **The clients agreed with each other and were all wrong** — a tenant that moved its vault under a customer-managed key locked **every client in this product** out of every record: `x-tenant-key` is required by the auth dependency and was sent on two heir routes and nowhere else. The hand-back button that undoes customer custody was itself behind it. The console and all three shells now carry the key in memory and present it on every request, never storing it; the requirement is now read out of the application's own dependency tree |
| **0.59.5** | **The third sink, where both the escaping and the policy miss** — `_js` and `_strings` here were bare `json.dumps`, which escapes what ends a JavaScript *string* and says nothing about `</script`, which ends the *element*. QRME had it right. Both now share one primitive, verified by behaviour rather than trusted by name — the guard's first draft whitelisted `_strings` while this product's `_strings` was the unsafe one. Consoles swept and clean |
| **0.59.4** | **The sweep that found the last one, kept** — the sibling products' reflected XSS was found by walking every f-string that builds markup, by hand, once. It is now a guard with a ratcheted record: **7 rows**, all pre-escaped composites the analysis cannot follow. It follows escaping through single assignments and helper returns, and refuses to read prose containing angle brackets as a page. `<html lang=…>`, the option values and the policy nonce are now escaped too |
| **0.59.3** | **What a page promises a browser** — the sealed-carrier card and the receive page are read by a stranger on a device that is not theirs, and both went out with no `Content-Security-Policy`, no `nosniff`, no frame or referrer policy. `pagehead.py` now stamps all four plus a per-response nonce the policy names; the three inline scripts carry it. The sibling products' sign-in callback was reflecting `?error=` as live markup — this product has no such route, and the sweep is what says so |
| **0.59.2** | **A crash the browser threw away** — an unhandled 500 is rendered by Starlette *outside* every middleware the app adds, including CORS, so it went back with no `access-control-allow-origin` and the browser discarded it whole. Every crash reached its user as "Failed to fetch", indistinguishable from a backend that is not running. No in-process test could see it: a `TestClient` sends no `Origin` and applies no browser rule. Fixed with a catch-all inside the CORS layer, and guarded by a file that boots a real server |
| **0.59.1** | **`serve` never opened CORS for its own console** — the frozen backend always did, so the installed app worked and the from-source one answered every console request with no access-control header at all; measured over HTTP, the preflight was a bare 405. Found by a sweep of test-function names across the three products: `test_serve_cors.py` existed in two of them and not here, and so did the code. The shared vocabulary is now written down and checked |
| **0.59.0** | **A floor nobody raised** — every floor in the suite swept against what it measures. 58 carried their own literal. Two **passed**: the console's `> 100` against 121 and the native `> 20` against 35, both honest here and decoration in QRME, because one number written for three repositories is calibrated for whichever was smallest. `ratchets.py` gives each floor a measurement; the rest are a backlog that only shrinks |
| **0.58.9** | **Ten against fifty-four** — the L10n guard's floor has not moved since it was written, and these shells hold no dotless rows at all, so the dead-row path reports nothing whatsoever when the call reader goes dark. Narrowing the pattern to `L10n.t("…")` blinds C# alone — Windows 54 → 0. Per-shell floors on both halves, plus a spread across the three ports that needs no hand-chosen number |
| **0.58.8** | **The route reader had one floor and four clients** — six files ask `clientpaths` what each client calls, so a reader read short narrows all of them at once, in the safe direction. An absolute floor per client and a spread check across the three shells, with this product's own measured numbers; the console sits outside the spread because its 121 call sites against 35 per phone are a real difference in surface |
| **0.58.7** | **A wire model is data, and data has no methods** — the empty-model hole that hid a broken pin here for a release is closed: every pin asserts on both ends, and three checks audit the readers themselves. Clean here; the finding was QRME's missing brace, which put ninety-five client methods inside a wire model |
| **0.58.6** | **The refusal surfaces** — the compliance catalogue is pinned, and the reader learns to follow a module table handed out whole. The trap was the guard's own and it was here: this repo declares one-line structs, the property pattern required end-of-line, so the model read as empty and the pin had been checking nothing at all |
| **0.58.5** | **The disclosure that showed nobody** — the pinned table's reader learns to follow a dict built in pieces and a list built by appending, and to refuse a `**` it cannot resolve. Clean here; the finding was QRME's live-microphone disclosure, which rendered as nobody on all three clients |
| **0.58.4** | **The key was right and the shape was wrong** — a per-route key check is not derivable by reading; what shipped instead pins a shell model to the backend function whose `return` is its contract, inferring nothing. Clean here; the finding was QRME's guided tour, blank on both phones and correct on Windows |
| **0.58.3** | **The key the server never sends** — every key a shell decodes is now read against everything this backend can put on a response. Clean here across all three shells; the finding was next door, where the overlay disclosure showed nobody and Sign in with Google and Apple could not start on either phone |
| **0.58.2** | **The colour that wasn't in the palette** — 0.58.1 checked the one receiver whose type is known for free; this checks all eight, adding the API client, the theme object and `App.xaml`'s brushes. Clean here across 36 client call sites and the whole palette; the finding was QRME's Android theme, and this product gets the check because the next one could be here |
| **0.58.1** | **The member that isn't there** — the offline-posture card reached `state.api` on an `AppState` that has no client at all, which Swift does not compile. A guard now reads every member the screens reach for against the one file that declares them |
| **0.58.0** | The sibling products found a header the console sent and no shell did — the person's own model key. This product runs no generation, so there is nothing to carry; what it gets is the check in its honest form, asserting the header has not appeared here either |
| **0.57.9** | The language guard could say *the header is set with the resolver* and could not say *every request carries it* — 3 of 4 Windows sends went round the shared helper. One dispatcher, and the check now walks dispatch sites rather than header lines |
| **0.57.8** | The untranslated-literal guard lands here too. Seven sites — `Language` on all three shells, `Connectors` on two, the audit page's preview link — and one worth naming: the iPhone's sources picker rendered its own enum raw values, so **both tabs read English on every device**, a rule the transfers screen next door had already settled and never had applied to it |
| **0.57.7** | The version a person installs. The iOS spec, the Gradle config and the `.csproj` all reported `0.1.0` or nothing while the release said `0.57.6`. Checked against `pyproject.toml` now, with the Android `versionCode` derived rather than kept by hand, and a capability check that will catch the first screen here to open a camera without saying why |
| **0.57.6** | The parse check reaches the XAML the Windows shell's screens are actually written in — five pages across the other two products did not parse, and none of them were here. Four markup checks, clean on all ten pages; four injected defects confirm each can fail |
| **0.57.5** | The shells get a parse check — duplicate declarations in one scope, and braces that do not balance — after QRME shipped a Swift compile error no text-reading guard could see. Clean here; three injected defects confirm it can fail |
| **0.57.4** | Nothing to collect here — QRME's shells needed six inputs its screens never asked for; this product's were already correct, and the request-body guard stays green at a ceiling of zero. Cut with the others |
| **0.57.3** | Request bodies get the guard on all three native shells — and the port found the Windows reader returning zero writes, because this client builds its messages by hand where QRME wraps them in a helper. Only the per-client reach floor could catch that. With both shapes read: nothing wrong |
| **0.57.2** | Request bodies get the guard responses have had since 0.56.4 — 42 writes, 33 readable, 34 matched to a model, nothing wrong. QRME was clean too; JIM-mini had two silently discarded health readings. Three injected defects confirm this guard can still fail |
| **0.57.1** | The console gets the shape guard the native clients have had since 0.56.4 — 33 shapes, 224 fields, 60 GET bindings, 27 driven, and nothing wrong. QRME's console had four defects and JIM-mini's two; three injected defects confirm this guard can still fail |
| **0.57.0** | The Kotlin guard arrives and finds this client correct — 18 routes, 31 keys, 15 driven, nothing recorded at a ceiling of zero. The port failed in 0.56.9 over a required `JSONObject(` wrapper this client does not use; three injected defects confirm the guard can still fail |
| **0.56.9** | QRME found eight wrong reads in its Kotlin client, all already fixed in its C#. The guard is not here yet: ported across, its extractor found zero routes — this client calls the backend in a different shape, and lowering the threshold until it passed would ship a guard that asserts on nothing |
| **0.56.8** | The shape guard reads Swift now as well as C# — QRME's iOS client was carrying nine fictions already fixed on its Windows side. This client came back clean |
| **0.56.7** | The shape guard now checks that a declared type can decode what arrives, not just that the name is there — QRME's `/wearables` sent a map where the record said `string[]`. Five live crashes found there; none here |
| **0.56.6** | **Eight watch faces that were not on the page** — reported from a phone. An HTML table is as wide as its longest row, so one `<tr>` with fifteen cells beside rows of three left twelve blank columns everywhere and clipped the rest off a phone. Every gallery is a uniform grid now — four across for screens and watch faces, two for desktop frames — with a guard that reads the widest row, not the first |
| **0.56.5** | QRME's shape guard is here now, rewritten to see this client — it builds each request itself and carries the tenant token beside it, so a borrowed regex finds zero calls. Clean sweep; the unverified record stays at ceiling zero |
| **0.56.4** | Cut together at one version; QRME found fourteen client records declaring fields their routes have never sent, and a guard that drives every binding to check. That guard is not in this repo yet — next round's work, named here |
| **0.56.3** | Cut together at one version; QRME's collision record falls 28 → 24 — three counts that shared a name with the boolean they counted, and one client bug wearing the same disguise |
| **0.56.2** | **The compiler nobody ran** — `tsc` and a wire-name guard join the suite. Two collisions recorded, of which `sealed` matters most for a vault: a sealing detail in one place and a boolean in another |
| **0.56.1** | **The key that lives in the HSM** — the KMS provider was a documented `NotImplementedError`; it now unwraps a stored blob through kms:Decrypt or PKCS#11, binds it to this deployment with an encryption context, and refuses rather than falling back to a local key. No live AWS call has been made from this repo, and the custody statement says so |
| **0.56.0** | **A wipe that cleared three tables of twenty** — a permanently-wiped tenant left its key configuration and its signed BAA behind. The cascade now reads the schema instead of a list, the scheduled purge runs the same one, and the audit chain is the only thing either is allowed to keep |
| **0.55.0** | Cut together at one version; the hand sweep that once found forty unlabelled boxes on these forms is now a guard that will notice the forty-first |
| **0.54.1** | Cut together at one version; the same care a vault takes between a label on a posture block and the identifier a route compares |
| **0.54.0** | Cut together at one version; a promise stated for one reader and not another is the same defect as a promise stated and unenforced |
| **0.53.1** | **`operator_can_decrypt: false`, checked against the whole database** — every column of every table swept for the customer's key in base64, raw and hex, including after a refused key. Nothing leaked; two columns of one table were all that had been checked |
| **0.53.0** | Cut together at one version; a stated posture needs a test that could catch it lying, and that test cannot be a read of the statement — the vault's own subject, applied to a bridge |
| **0.52.0** | Cut together at one version; the round's work withholds before the content exists rather than handing a client a flag, and names what it held — this repo's two arguments, on a speaker |
| **0.51.0** | Cut together at one version; the round's work is a dial that changes wording and no capability, and a count offered rather than earned — both stated as fields a client renders |
| **0.50.0** | Cut together at one version; the round's work is JIM-mini's presence — refusals on the wire rather than in a docstring, and an offline path that is the floor rather than the fallback |
| **0.49.0** | Cut together at one version; the round's work is QRME's public stream and JIM-mini's GET-only door onto it — the rule about what plays asserted on the wire rather than in four clients, the same shape as this repo's posture blocks |
| **0.48.3** | Custody and Continuity read in the tenant's language — *can the operator decrypt this?* and what happens to a sealed file after a death, 229 → 177 |
| **0.48.2** | The console gets its first localization table, and the language picker is the first screen wired — 250 → 229 English strings |
| **0.48.1** | This console has no localization table at all — 250 English strings behind a language picker, counted and ratcheted for the first time |
| **0.48.0** | The split-wording guard arrives with nothing to record — an empty floor, in place before the rows are |
| **0.47.9** | Cut together at one version; the shared guard gains `_ARRAY`, the Swift twin of the `listOf` shape |
| **0.47.8** | **The sentence that says how to get the file back** — Transfers localized on all three shells, including the two out-of-band instructions that sit under a token shown once and name the only way the file can be retrieved (iOS 90→65, Android 73→59, Windows 101→69) |
| **0.47.7** | **The console's own posture statement was English** — the paragraph about what it sends when something fails, its two-step reveal, and the key-rotation verdict all sat in the code-behind as assignments the XAML rule could not read |
| **0.47.6** | **The buttons that write to the vault were English** — *Seal record*, *Rotate key*, *Request file* and the admin-token field went through wrapper composables the untranslated rule could not read (75 → 73) |
| **0.47.5** | **The welcome screen greeted everyone in English** — the accountless screen never passed `DeviceLanguage()` on any shell; plus the PaneFooter sign-out fix in its third product, and the dead-key guard ported (294 → 266) |
| **0.47.4** | Version alignment — the round's work was JIM's Overview and its enum-backed tab strips |
| **0.47.3** | The route audit's new guard-on-guard, ported — nothing unattributed here beyond two recorded non-calls |
| **0.47.2** | Version alignment — the round's work was JIM's Family and Connect screens; PDI's native record stands at 294 |
| **0.47.1** | Ternary blind spot ported and corrected — 282 → 294, nothing regressed |
| **0.47.0** | Version alignment with QRME's native round |
| **0.46.9** | Version alignment with QRME's native round |
| **0.46.8** | Version alignment with QRME's native round |
| **0.46.7** | Version alignment with QRME's native round |
| **0.46.6** | Version alignment with QRME's native round |
| **0.46.5** | Version alignment with QRME's native round |
| **0.46.4** | **Forty fields a person fills in and nothing named them** — five bare selects, eight placeholder-only boxes, a nameless date input and the whole Positions questionnaire get labels, then the field-label table gets them: 91 → 51 |
| **0.46.3** | Version alignment with QRME's console round |
| **0.46.2** | Version alignment with QRME's console round |
| **0.46.1** | Version alignment with QRME's console round |
| **0.46.0** | Version alignment with QRME's console round |
| **0.45.9** | Version alignment with QRME's console round |
| **0.45.8** | Version alignment with QRME's console round |
| **0.45.7** | Version alignment with QRME's console round |
| **0.45.6** | Version alignment with QRME's lobby, presence and voice round |
| **0.45.5** | Version alignment with QRME's objection, live and marketplace round |
| **0.45.4** | Version alignment with QRME's watch-party, delegation and beacon round |
| **0.45.3** | Version alignment with QRME's succession, signing and placement round |
| **0.45.2** | Version alignment with QRME's three-screen localization round |
| **0.45.1** | Version alignment with JIM's console-to-zero round |
| **0.45.0** | Version alignment with the eighth localization-ratchet round — QRME's console record goes under a thousand |
| **0.44.9** | Version alignment with the seventh localization-ratchet round |
| **0.44.8** | Version alignment with the sixth localization-ratchet round |
| **0.44.7** | Version alignment with the fifth localization-ratchet round |
| **0.44.6** | Version alignment with the fourth localization-ratchet round |
| **0.44.5** | Version alignment with the third localization-ratchet round |
| **0.44.4** | Version alignment with the second localization-ratchet round |
| **0.44.3** | Version alignment with QRME's and JIM's localization-ratchet round |
| **0.44.2** | Version alignment with QRME's last-doors round (the doorless records run to zero on all three shells) |
| **0.44.1** | Version alignment with QRME's sticker/queue/stamp round (beacons, moderation, reviews, watermarks, media, wearables on the phones) |
| **0.44.0** | Version alignment with QRME's keys/till/lifeline round (accounts, money, status+help on the phones) |
| **0.43.9** | Version alignment with QRME's face round (portrait, badge, page, surfaces, bodies, dials, wrist on the phones) |
| **0.43.8** | Version alignment with JIM's watch-picker round |
| **0.43.7** | Version alignment with QRME's record/veil/exit round |
| **0.43.6** | Version alignment with QRME's workshop round |
| **0.43.5** | Version alignment with QRME's seal/mail/screen round |
| **0.43.4** | Version alignment with QRME's body/case/lobby round |
| **0.43.3** | Version alignment with QRME's place/camera/organization/tour round |
| **0.43.2** | Version alignment with QRME's crowd/couch/loan round |
| **0.43.1** | Version alignment with the QRME inbox round — nothing new crosses into the vault |
| **0.43.0** | **Version alignment** — QRME's phones learned to do business; nothing new crosses into the vault |
| **0.42.9** | **Version alignment** — QRME's social surface reached its phones; nothing new crosses into the vault |
| **0.42.8** | **Version alignment** — QRME and JIM labelled the 161 recorded fields their forms had started asking for; nothing new crosses into the vault; the console gained the suite's always-on light — one lamp, green while the vault answers, never silently absent |
| **0.42.7** | **Version alignment** — QRME and JIM gained messaging, feature switches and homepage sandboxes; nothing new crosses into the vault |
| **0.42.6** | **Version alignment** — JIM gained booking/scheduling with bottom-rung reminders and self-only email; nothing new crosses into the vault |
| **0.42.5** | **Version alignment** — QRME grew standalone shops (not desks) and JIM grew the tandem buyer's side; purchase histories stay in the buyer's own JIM |
| **0.42.4** | **Version alignment** — JIM's money guardian gained its native doors; the account numbers those phones register still land here, sealed, or nowhere |
| **0.42.3** | **The last thirteen unaudited screens** — five PDI components sat `unaudited` since the manifest was seeded. `Records` was only unlabelled (it heads itself "Vault", screens 2+3); Continuity, Operations, Positions and Settings had never been drawn. Screens **53-56** are the drawings, ceilings at zero, `undrawn=0` true at last |
| **0.42.2** | **Version alignment** — the round the vault was built for: JIM's money guardian seals account, routing and exchange credentials here and refuses to store them anywhere else |
| **0.42.1** | **Version alignment** — cut with QRME's starter dossiers; no PDI code changed |
| **0.42.0** | **Version alignment** — cut with QRME's desk service connections and JIM's signal-quality door fix; no PDI code changed |
| **0.41.0** | **The workflow round-trips and nothing walked the whole arc** — `workflows.py` names three properties a delegated multi-phase goal has to keep, each unit-tested on its own side of the wire; the one check that boots all three products drove a single exchange and stopped, never calling `start_workflow`, `advance` or `specialist_tasks` across the boundary. Driving it surfaced the Pro gate and the owner's opt-in as steps rather than surprises, and the arc now walks research → draft → send and pauses at `confirm` |
| **0.40.9** | **The README said v0.18.0** — the first bold line of every README named a release twenty-two cuts old, on the line directly above one promising the three products are versioned and cut together; the history table underneath stopped at 0.30.6, leaving seventeen shipped releases in the changelog and off the page anybody reads. Both are now checked against `pyproject.toml` and the changelog |
| **0.40.8** | **The refusal named the field the API calls it** — An earlier round took the 422 from `[{"type":"missing",...}]` to one sentence a person can read, in their own language. |
| **0.40.7** | **The record that outlived the code** — `public_untranslated.txt` opened with a paragraph explaining that `Onboarding.tsx` — the screen every person in the world meets first — carried forty-odd English strings, that translating them was "its own round", and that a half-translated sign-up form would be worse than an English one. |
| **0.40.6** | **Cut alongside qrme and jim-mini** — No change in this product. The round finishes localizing QRME's **accountless screen** — the one built for somebody who has found a synthetic profile of themselves and has no account, and therefore no profile language to take a setting from. |
| **0.40.5** | **Every door of theirs answered 401; the grantee's answered with the record** — `vault.tenant_by_id` has carried its qualifier since it was written, and says so in its own docstring: `bequests.py` did not use it. |
| **0.40.4** | **Cut alongside qrme and jim-mini** — No change in this product. The round is about which surfaces may put words in a synthetic profile's mouth, and PDI generates nothing — it seals what the other two produce. |
| **0.40.3** | **Cut alongside qrme and jim-mini** — No change in this product. The round is about what a model-backed product says when the model it was asked for does not answer, and PDI has no inference path of its own — it stores what the other two seal. |
| **0.40.2** | **The refusals, finished** — 0.24.0 translated the eleven refusals any route can raise and **wrote the rest down**. |
| **0.40.1** | **The language no client was sending** — PDI's most exposed reader has no account by design: the person on the other end of a handoff, opening an intake with a submit token and nothing else. |
| **0.40.0** | **Version alignment** — The three products are cut together at one version, and this release's work is in the siblings. |
| **0.30.9** | **An HTTP verb where a path goes** — This product's Android client declares its shared helper `request(path, method, body, token)`. |
| **0.30.8** | **The tab bar answers in your language. Everything behind it does not.** — The QRME repo has carried a console guard since those rounds — `test_the_nav_is_translated_and_nothing_behind_it_is.py` — which found forty-six translated sidebar labels in front of 1577 English screens, and said why that is worse than ship |
| **0.30.7** | **Offline mode became readable** — `PDI_OFFLINE` refuses anything bound for another machine, and until this release a deployment could set it and had no way to show anyone the result. |
| **0.29.0** | **0.29.0** — Aligned with QRME and JIM-mini 0.29.0. The three products carry one version, so a release that only moves in two of them still moves in all three. |
| **0.28.0** | **0.28.0** — Aligned with JIM-mini 0.28.0. The three products carry one version, so a release that only moves in one of them still moves in all three. |
| **0.27.0** | **Kotlin's other interpolation** — `_spans` routes every `${`-carrying pattern to a brace counter, which is right for the nested-template problem it was written for and blind to the *other* form the same language uses. |
| **0.26.0** | **Three copies of one guard, three different blind spots** — `clientpaths.py` says of itself, in its own docstring, that it is *byte- identical in qrme, jim-mini and pdi*. |
| **0.25.0** | **0.25.0** — Aligned with QRME 0.25.0. The three products carry one version, so a release that only moves in one of them still moves in all three — otherwise a support question about "0.25" has three different answers depending on which app is being asked about. |
| **0.30.6** | **The plan gate speaks the reader's language** — carried from the sibling audit. PDI has no plan gate, so there is no sentence of this shape here; the mechanism that keeps a translated frame from closing around an untranslated slot is already in place, and this release aligns the version with the two products where the sentence exists |
| **0.30.5** | **The plan gate said HTTP 402** — carried from the sibling audit: `detail` is a string for most refusals, a dict for a structured one and a list for a 422, and only the list had been given a top-level `message`. Every refusal now carries the sentence in one place whatever shape the structure has, and `localize_detail` reaches the level the handler actually wraps to — so PDI's first structured refusal cannot ship untranslated the way the sibling's did |
| **0.30.4** | **A refusal whose English is not a constant** — f-string refusals had been named as uncovered for three releases, because a sentence built by interpolation has no English source to key on at the moment it is raised. `i18n.Templated` carries the template and its slots beside the finished English text; 4 converted. The slot is the whole design: whitespace means prose, and a prose slot keeps the entire refusal English rather than producing a sentence half in each language |
| **0.30.3** | **The refusal that arrived as a list** — a 422's `detail` is pydantic's rows, not a string, and all four client families rendered it by a path written for one: the console and Android printed the raw JSON, iOS and Windows fell back to `HTTP 422`. The sentence translated last release was correct, arrived, and was read by nobody. The server composes one sentence now, carrying nothing the rows do not; the guard took three attempts, and the first two passed on code that was fully broken |
| **0.30.2** | **The synthetic self enters the tandem contract** — the shared boundary, byte-identical in three repositories, written before the code that obeys it. The vault's stake is the destination: a guardian's brief reaches a person's own synthetic profile through QRME's owner-gated source route, and QRME seals source material into PDI when a vault is configured — so consented medication names come to rest encrypted here rather than beside the profile |
| **0.30.1** | **Isolation held, and nothing was checking it** — seventy GET routes driven as a second tenant against a first tenant's data, plus the mutating routes: no cross-tenant read, no cross-tenant write, and now a guard that says so. It runs with an admin token set and from an address that is not this machine, because `testclient` is a trusted local caller and every other test in the suite runs with the admin surface open. Also: a 422 was returning the submitted body — a record value in plaintext on the one path that never touches the encryption layer |
| **0.30.0** | **The stranger's page was already right; the tenant's was not** — the recipient's server-rendered page reads their browser's language and its two refusals are localized at the route, while every one of the tenant's sixty refusals was English on an account whose language picker had been answered. The reverse of the usual direction. Three exception handlers built responses three different ways; all of them go through one place now, and a guard fails the next one that does not |
| **0.24.0** | **The page was not an oracle; the route it fronts was** — `POST /transfers/{tid}/receive` takes no credential and answered 404 for a fake id and 403 for a real one, so anybody could enumerate sealed transfers. Both now answer alike, and revoked still reaches the person holding the token. The four pages built for people who are not tenants speak ten languages, as do the six sentences a courier reads after pressing a button — including the one telling somebody at a gate not to wait for anyone to come out |
| **0.23.0** | **The recipient had nowhere to put their token** — a file sealed under HIPAA or OSHA or CPNI arrives with a one-shot receive token, and the only thing calling that route was the sender's own *Receive it as the recipient* rehearsal button. There is now a page at `/r/{id}`, with the token in the URL fragment so the link survives mail and proxies without leaving an authorization in anybody's log, and a **Copy the recipient's link** control that resolves it before the sender sends it. Android and Windows can also read back the keys a bound robot sealed |
| **0.22.0** | **Cut with the siblings** — the console backlog run to zero, and the fixes the audit turned up on the way |
| **0.21.0** | **Cut with the siblings** — four door-audit rounds across the three products |
| **0.20.1** | **The union hid a surface** — *some* client reaching a route was being counted as *this* client reaching it, so the console's own gaps were invisible. A guard per client, and the doors that answered it |
| **0.20.0** | **Failures from the phone and the desktop shell** — error capture reaches the native shells, and a guard that invented work is corrected: it demanded doors for routes that already had them |
| **0.19.1** | **Cut with the siblings** — the drawings and lessons the error-reporting surface shipped without |
| **0.19.0** | **It can tell you it broke without telling anybody what you said** — content-free error capture in the console and on every native shell, sent to a collector that never receives a word of your content |
| **0.18.0** | **Cut with the siblings** — JIM and QRME finish native parity and catch their drawings up |
| **0.17.0** | **Cut with the siblings** — JIM's community door and QRME's voice enrollment reach all three native shells |
| **0.16.0** | **Cut with the siblings** — JIM's closed guidance loop and anonymity, QRME's uploads and new model doors |
| **0.15.0** | **Cut with the siblings** — JIM's guided wellness and QRME's temperament dials |
| **0.14.5** | **Cut with the siblings** — JIM's fall path, native crash watch, and docs web |
| **0.14.4** | **The console names a version mismatch** — the same guard as the siblings |
| **0.14.3** | **Docs binding pass** — every README held to the same closing convention, test-enforced |
| **0.14.2** | **Cut with the siblings** — the tandem contract documents suite mode and the shared `suite:qrme-vault` tenant |
| **0.14.1** | **Cut with the siblings** — suite tandem wiring in QRME; coach awareness in JIM |
| **0.14.0** | **Operations entries prove themselves** — provenance one click from each journal entry |
| **0.13.1** | **Cut with the siblings** — docs caught up; QRME demo org + hardening |
| **0.13.0** | **The operations journal** — QRME-sealed coordination records readable in place, every read on the audit chain |
| **0.12.0** | **Cut with the siblings** — no functional change; QRME mined its filed patent spec: hybrid profiles, real-time simulation, environmental adaptation |
| **0.11.1** | **The desktop app finally carries its own vault** — bundled backend, version handshake, a master key generated once and persisted (your keys, your walls), and a release gate that creates a tenant, seals, restarts and reads back on every OS before packaging |
| **0.11.0** | **Cut with the siblings** — no functional change to the vault |
| **0.10.0** | **Cut with the siblings** — no functional change to the vault |
| **0.9.1** | **Cut with the siblings** — no functional change to the vault |
| **0.9.0** | **Cut with the siblings** — no functional change to the vault |
| **0.8.0** | **Bequests** — named scopes of the vault unlock to a named person only when a condition is attested; the grant token does not exist until activation, reads only its shelf, and every step lands in the audit chain |
| **0.7.0** | **The last version anyone fetches by hand** — the desktop app checks GitHub Releases on launch; Windows/Linux download the update and offer one restart, macOS is shown the download. The window is finally titled PDI |
| **0.6.1** | **Cut with the siblings** — no functional change to the vault |
| **0.6.0** | **Cut with the siblings** — no functional change to the vault |
| **0.5.0** | **Cut with the siblings** — no functional change to the vault |
| **0.4.8** | **Cut with the siblings** — no functional change to the vault |
| **0.4.7** | **Cut with the siblings** — no functional change to the vault |
| **0.4.6** | **Cut with the siblings** — no functional change to the vault |
| **0.4.5** | **The round where the siblings' verification matched the deployment** — cut with them, carrying no part of it. No functional change to the vault |
| **0.4.4** | **The round where the siblings' Windows signup 500 died** — cut with them, carrying no part of it. No functional change to the vault |
| **0.4.3** | **The round where the siblings got a front door and a key of your own** — cut with them, carrying no part of it. No functional change to the vault: accounts, model keys and the self-running installers all live in QRME and JIM-mini, and nothing on those paths touches PDI |
| **0.4.2** | **The round where the installer you download actually gets you running** — cut with the siblings, whose first-run fixes it carries no part of. No functional change to the vault: the version moves so one number keeps naming one combination of all three, and the installers stop being labelled 0.3.3 (all five version strings now guarded together) |
| **0.4.1** | **The round where the vault promise said which plans it covers.** QRME and JIM-mini gained free tiers under platform custody — the apps hold that data themselves, over ordinary HTTPS, and it never reaches PDI at all — so the claim that the tandem is "the only place" sensitive material may go is now scoped to the paid plans it was always about. Documentation only: a vault has one posture, the four hosting modes share it, and nothing PDI holds changed |
| **0.4.0** | **The round where PDI said what it costs, and got a guide of its own.** Four places a vault can live — our facility and your own device both **free**, leased space and your own facility quoted — with one shared guarantee list so the free option is not the weakened one. Plus the console walkthrough PDI was the only product without, and a corner pane replacing the lights panel that had no lid. Neither can read a record, and under BYOK neither can the operator |
| **0.3.3** | **No functional change to the vault** — the round belongs to the console. The agent status light lands on screens 39 and 40, with an overlay on every desktop view, because on a gate console amber means somebody is standing at a door. Plus a README that leads with the screens |
| **0.3.2** | **No functional change to PDI.** The round belongs to QRME's starter gallery |
| **0.3.1** | **No functional change to PDI.** This README, and a known gap recorded rather than left silent: `docs/tandem.md` is still 92 lines shorter here than in the siblings, and the fix lands next round |
| **0.3.0** | **No functional change to PDI** — but the round's most sensitive new payload lands here. QRME learned to put somebody in front of a real clinician and let that clinician write back; the note is sealed under a `qrme/{profile}/clinical/…` key, content in the vault with only a key reference held next door |
| **0.2.2** | A documentation release — no code changed in any of the three products |
| **0.2.1**–**0.2.0** | **A per-tenant on-call roster**, so an escalation reaches a named person rather than a queue |
| **0.1.9** | **A hand-off reaches a person now.** Custody beacons designed and built, the agent at the gate, and a phone that scans a custody beacon lands on a page rather than on JSON |
| **0.1.8**–**0.1.7** | Release-link repairs, and the point at which the three products began being **cut as one release** |
| **0.1.6**–**0.1.5** | Version aligned across the suite. **BYOK — bring your own key.** Open admin now **fails closed** off-machine, and a published deployment refuses an ephemeral key. Native apps compiled in CI, one-container deploy |
| **0.1.4**–**0.1.2** | `python -m pdi` launcher, running it on your phone, Terms of Service, **BAA enforcement** and template, macOS notarization |
| **0.1.1** | Native iOS / Android / Windows apps at parity. First-run onboarding. Enterprise compliance transfer, robots as vault-backed data sources, connected platforms, language & provenance |
| **0.1.0** | First public release — the **encrypted vault**, envelope encryption & key management, **tamper-evident audit**, tenant registry & RBAC, retention up to forever, and tenant deletion |

</details>

## License

Copyright © 2026 David Bianchi. Use requires prior written permission —
see [LICENSE](LICENSE).

---

## The error reports come home

`POST /v1/problems` — the same content-free intake the Cloud Model Gateway
serves (whitelist screening in `pdi/problems.py`, folded into counters, never
a message or an id), on this backend, so a deployment with no gateway still
collects its own failures; the console falls back to it when no collector is
stamped into the build, behind the same first-run notice and switch.
`GET /v1/problems` is the operator's read — `PDI_PROBLEMS_KEY`, or the
backend's own machine.

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
