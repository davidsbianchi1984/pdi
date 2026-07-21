# Position & Assistant Builder

The **AI Integration & Role-Mapping Questionnaire**, delivered as a PDI
service. An operator answers a short, industry-agnostic questionnaire about a
role; PDI seals the raw answers in the tenant's vault and returns a derived
**assistant blueprint** — including a ready-to-use system-prompt for a
personalized assistant sub-model.

It works for **any industry**: transit, healthcare, logistics, hospitality,
finance, manufacturing, public administration — the operator types their own
industry and the builder never assumes one.

```
  questionnaire (any industry)          PDI  POST /positions
  ───────────────────────────▶   ┌───────────────────────────────┐
   1 Role overview                │  seal raw answers → vault      │
   2 Daily workflow audit         │    positions/{id}  (AES-256)   │
   3 Decision-making & oversight  │  derive blueprint (returned)   │
   4 Bottlenecks & obsolescence   │  audit: position.create        │
   5 AI adoption & personalization└───────────────┬───────────────┘
   6 Administrative & executive                   ▼
   7 Future AI & workforce evol.        assistant blueprint + spec
```

## What the blueprint contains

| Field | Meaning |
| --- | --- |
| `assistant.tone` / `interaction` | Communication style (directive/neutral/casual/analytical · voice/text/hybrid) |
| `assistant.capabilities[]` | Recommended assistant skills, each with a `why` (requested, or inferred from the workflow audit) |
| `automation.opportunity_score` | 0–1 advisory score of how much of the role is automatable |
| `automation.opportunities[]` | **Tasks** to automate — never people |
| `automation.watch_3_5yr[]` | Functions the operator flagged as changing in 3–5 years |
| `human_in_loop.required[]` | Decisions that must keep a human accountable, regardless of the score |
| `reskilling.suggested_paths[]` | Repositioning paths, surfaced when the person is interested |
| `assistant_spec` | A guardrailed system-prompt for the personalized sub-model |

## Responsible by design

This is **decision support, not an automated staffing decision.**

- High-stakes decisions — incident response, contracts, budgets, staffing, and
  safety/regulatory sign-off — are always flagged **human-in-the-loop**,
  whatever the automation score.
- Obsolescence is framed as **tasks to automate**, never a verdict on a person.
- **Reskilling / repositioning paths** are surfaced alongside, so the output
  points toward growth rather than only reduction.
- The generated assistant spec instructs the sub-model to *surface options and
  defer final judgement to the human it assists* — it suggests, it never
  finalizes.

## Privacy

The raw questionnaire answers are sensitive workforce data. They are sealed
with AES-256-GCM under `positions/{id}` in the tenant's vault — the same
envelope encryption, key rotation, retention, and tamper-evident audit chain
that protect every other PDI record. Only the derived blueprint leaves the
vault; the raw answers never appear in the database in plaintext.

## API

| Method & path | Auth | Purpose |
| --- | --- | --- |
| `POST /positions` | tenant (write) | Seal a role-mapping intake, return the blueprint |
| `GET /positions` | tenant | List saved position ids |
| `GET /positions/{id}` | tenant | Fetch a saved position's blueprint |

The intake body mirrors the seven questionnaire sections (all optional):
`industry`, `role`, `workflow`, `decisions`, `bottlenecks`, `preferences`,
`admin`, `future`. A partial intake still returns a safe, defaulted blueprint.

In the operator console, the **Positions** screen renders the questionnaire and
the resulting blueprint (capabilities, automation meter, human-in-the-loop
guardrails, reskilling paths, and the assistant system-prompt).
