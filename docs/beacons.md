# Custody beacons — a sealed thing, scannable

*Design. Nothing in this document is built yet — it is the decision record that
the implementation round will follow.*

QRME has **desk beacons**: a printed QR stuck to a shop door, resolving to a
live person who is simply not behind it this minute
([qrme/docs/desks.md](https://github.com/davidsbianchi1984/qrme/blob/main/docs/desks.md#leaving-the-desk-behind--beacons)).
The gesture is *put a code on a physical thing and let a stranger resolve it*.
That ports here cleanly. What it resolves **to** inverts completely.

PDI's subject is not a person, it is **custody of data**. And custody keeps
escaping into the physical world, where PDI currently cannot see it: a records
box in a courier's van, a decommissioned drive on a pallet, a specimen going
between labs, a robot carrying what it recorded, a sealed envelope crossing a
depot. The moment a payload has a handle, custody has a gap.

A **custody beacon** is a printed code on that carrier.

    POST   /transfers/{id}/beacons    place one on an outbound transfer
    POST   /intakes/{id}/beacons      …or an inbound intake
    POST   /beacons                   …or a bare object with no record yet
    GET    /s/{beacon_id}             the seal card — where the QR points
    POST   /s/{beacon_id}/found       the finder's receipt
    POST   /s/{beacon_id}/ring        ring the gate (facility beacons)
    POST   /s/{beacon_id}/agent       a turn with the agent, if one is configured
    GET    /beacons/{id}/custody      the chain, tenant token only
    DELETE /beacons/{id}              retire the code

## The inversion

QRME's beacon exists to reveal a person. PDI's exists to reveal **that
something is sealed, and nothing about what is in it.**

| | desk beacon | custody beacon |
|---|---|---|
| what is revealed | somebody who does exist | that this is under custody, and by what rules |
| what is withheld | location, on a rated desk | **the contents, always** |
| the badge | *Live person — not AI* | *Sealed — this code proves custody, not contents* |
| the stranger's act | ring the bell | **hand it in** |
| a scan is | a counter | **a link in the chain** |

A seal card carries exactly four things:

- **that this object is under custody** and its reference
- **which compliance programs govern it** — HIPAA, CPNI, OSHA — so a finder
  knows this is not ordinary lost property and mishandling it is not an
  ordinary mistake
- **the seal state** — sealed, in transit, opened, closed, retired
- **how to hand it in**

Never the filename, the classification, the counterparty, the retention terms,
or a byte of the payload. `vault.get` is not reachable from this surface at
all; the beacon never holds a key and never touches ciphertext.

## A scan is a link in the chain

This is the idea worth building the feature for.

In QRME a scan increments `scans` and that is all it can be — a stranger
glancing at a door proves nothing. Here, PDI already keeps an **append-only,
hash-chained audit log** where each entry's hash covers the previous one, so a
retroactive edit breaks `verify()`. Which means a scan can be more than a
counter: it can be *evidence*.

So a beacon writes into the existing chain, using the existing
`transfer_receipts` mechanism that transfers and intakes already share
(`transfers._receipt`), plus new entries in `audit.ACTIONS`:

    beacon.place     custody beacon placed on a carrier
    beacon.scan      carrier's code scanned
    beacon.found     carrier reported found by a finder
    beacon.retire    custody beacon retired

Adding these is safe by construction: `category` is derived at read time from
the action, so enriching the catalogue never rewrites — or breaks — the chain.
That property was designed in; this is the first feature to spend it.

The consequence is the point. A drive whose chain reads *sealed at the clinic
Tuesday → scanned at the depot Wednesday → nothing for six weeks* is a
**compliance finding**, and PDI can now produce it on demand, tamper-evident,
without anyone having kept a clipboard. Physical custody gaps become visible in
the same log as logical ones.

To keep that log meaningful rather than noisy: a scan always writes a cheap
`beacon_scans` row, but only a **`found` report** writes an audit-chain link,
capped per beacon per hour. A barcode gun sweeping a pallet must not write four
hundred links into a tamper-evidence chain — volume is how a chain stops being
read.

## Blind by default

QRME's desk beacon names the person; that is the entire product. Here, naming
the tenant can itself be the disclosure — a drive labelled *St. Anne's
Oncology* has told you something about the people inside it before anyone
scanned anything.

So a beacon carries a `disclose` mode:

- **`blind`** *(default)* — a reference number and a route back **through PDI**.
  The finder submits where it is; PDI tells the tenant. The finder never learns
  whose it is.
- **`contact`** — names the tenant and a return address, for carriers where
  "return to" is worth more than anonymity: an intra-site records box, a
  courier bag that never leaves a campus.

The default is the opposite of QRME's for the opposite reason, and the opt-in
direction matters: naming a regulated carrier should be a decision somebody
made, not a default they inherited.

## What the finder can do

One action, and it is not a message: **`POST /s/{id}/found`** is a *custody
receipt*. It records that this object was in someone's hands at a stated time
and that they reported it, and it lands in the chain as `beacon.found` with an
optional free-text location and contact.

That framing is deliberate. A "contact the owner" form is a mailbox. A receipt
is an instrument — it is the thing that later answers *where was this between
Wednesday and the following month*, and it is worth something in an audit even
if nobody ever replies to it.

The finder cannot open, read, decrypt, verify contents, see history, or learn
who else has scanned it. There is nothing on that surface to escalate.

## The agent at the gate

A beacon on a carrier is one case. The other is a beacon **at the facility
itself** — the door of the collation facility, the loading dock, the cage.
Someone rings it: a courier with a delivery nobody scheduled, an engineer
whose access expired last week, a driver at the wrong building at 2am.

Everything above routes that to a human. Often there is no human, or the human
is asleep, and the ring sits until morning. **A moderating agent is what stands
in that gap** — triage the ring, resolve what it can, and hand off what it
cannot.

### PDI does not grow a model

The suite's shape is three products, no shared code, HTTP only — and every
arrow in [tandem.md](tandem.md) points **into** PDI. It is the bottom layer,
it has no LLM module, and that is deliberate: a vault whose availability
depends on a model provider is a worse vault.

So the facility agent is a **QRME synthetic profile**, reached over HTTP
through a `pdi/qrme_client.py` that mirrors JIM's `jim/qrme_client.py`. PDI
sends the ring and the facility's own context; QRME conditions the persona,
moderates the reply, and keeps the memory. Three things follow, and all three
are the reason to do it this way rather than embed a model here:

- **The agent carries QRME's AI mark.** Somebody standing at a gate at 2am
  being talked to by software must know it is software. The suite's oldest
  invariant delivers that for free, on the surface it already governs.
- **Absence degrades to the design above.** No `PDI_QRME_URL` configured, or
  QRME unreachable, and the beacon behaves exactly as this document already
  specifies: route to a human. The unagented path is the floor, never a
  fallback that has to be written twice.
- **PDI stays dependency-light**, and a deployment that wants no AI at the gate
  gets that by not configuring one.

### The ceiling was already written

`positions.py` carries a `HUMAN_IN_LOOP` set — decisions that stay with a
person whatever the automation score — and it already names
`incident_response`, `safety_compliance`, and `staffing`. Granting someone
entry to a room full of regulated data is an incident-response and
safety-compliance decision by this repository's own catalogue.

So the boundary is not caution imported for the occasion. It is doctrine this
repo already published, and this is the first feature to be **governed** by it
rather than to declare it. The rule it produces:

> **The agent's ceiling is whatever a wrong answer cannot undo.**

| The agent may | The agent may not |
|---|---|
| work out what is actually being asked | **grant entry** to a floor, cage, or vault |
| check an arrival against the tenant's expected transfers and scheduled work | **assert that a person is who they say** — it holds no identity proof, and a fluent model stating identity confidently is worse than no agent at all |
| answer wayfinding — which dock, who signs, right building | override an expired or absent authorization |
| structure the `found` receipt properly instead of taking a free-text blob | sign for custody on the tenant's behalf |
| open a **reception** airlock or a parcel locker — reversible, and nothing regulated is behind either | see the contents of anything |
| page the on-call human, work a roster in order, hold the line open | let a refusal be a dead end |

Two of those deserve their reasoning stated rather than assumed.

**The agent inherits the beacon's blindness.** It does not get to see what the
box holds because it is on our side of the wall. It is a stranger with better
manners and a phone list, not an insider, and every argument in *The inversion*
above applies to it unchanged.

**A refusal always carries a route to a human.** Turning someone away at 3am in
the rain is consequential in its own right, and an agent that can only say no
has merely automated the locked door. The refusal is logged with its reason and
the human it routed to.

### Every turn lands on the chain

This is why an agent is defensible *here* specifically. PDI's core competence
is proving what happened, so an agent acting inside it can be held to the
standard the rest of the system is held to — which is the first thing an
auditor will ask about, and the thing most deployments cannot answer.

New catalogue entries, safe to add for the reason given above:

    agent.engage     agent took a beacon ring
    agent.decide     agent resolved a request within its ceiling
    agent.refuse     agent declined, with reason and route
    agent.handoff    agent escalated to a named human

The **transcript is sealed in the tenant's vault**; only its key and its hash
go on the chain. So the chain proves what the agent said without the audit log
becoming a second copy of it — the same split the rest of PDI already uses for
payloads, applied to a conversation.

### Who the agent answers to

The README says the choice that matters about a facility is not whose rack it
sits in, it is **who holds `PDI_MASTER_KEY`**. The agent has the same shape of
question and it should be asked as plainly: an agent configured by the host
rather than the tenant is an agent whose refusals and hand-offs serve the host.
A colocation posture that keeps the key and hands over the gate agent has
given away less than the key and more than it thinks.

## Bare objects

`POST /beacons` with no parent record is the case that makes this more than a
label printer: a physical carrier that PDI has **no record of yet** — the drive
being decommissioned, the box in the basement, the robot going out for service.

Placing a beacon on it is how that object *enters* custody. It gets an id, a
tenant, a compliance program set, a retention clock, and a chain that starts
with `beacon.place` — before anything is sealed, and possibly before anything
is ever digitised at all. The chain is the record.

That inverts PDI's usual order, where a record exists and custody follows it.
Here custody exists first and the record may never arrive, which is exactly the
decommissioned-drive situation: nobody will ever put those bytes in the vault,
but somebody must be able to prove where the thing went.

## Under BYOK

A tenant under customer key custody
([crypto.py](../pdi/crypto.py)) changes nothing here, and that is worth
stating rather than leaving to be discovered: a beacon holds no ciphertext and
no key, so it neither breaks under BYOK nor keeps working in a way that
undermines it. Rotating, retiring, or handing custody back leaves every placed
code resolving exactly as before, because none of them ever pointed at a
payload.

## Shape of the build

New tables, never new columns — the same `CREATE TABLE IF NOT EXISTS`
constraint as the rest of the schema:

    custody_beacons   id, tenant_id, ref_kind, ref_id, label, disclose,
                      programs, state, scans, active, created_at
    beacon_scans      id, beacon_id, at            (cheap; not the chain)
    beacon_rings      id, beacon_id, kind, state, agent_session, vault_key,
                      handed_to, created_at, closed_at

`ref_kind` is one of `transfer`, `intake`, `object`, `facility` — the last
being the gate beacon the agent answers, which points at a place rather than a
carrier. Chain entries continue to live in `transfer_receipts` and `audit`,
which already carry them; `vault_key` on a ring is where the agent transcript
is sealed.

Two details carried from QRME's implementation:

- The seal card is **one self-contained document** — a camera app's in-app
  browser, on cellular, from cold.
- The found form posts to a **relative** URL. An absolute one baked from the
  public base breaks every LAN scan.

## What this does not give you

- **No proof the code is on the object it names.** A sticker can be peeled off
  and moved. The chain records what was reported, not what is true — which is
  what a chain of custody has always been, and the reason it is signed.
- **No tracking.** There is no location telemetry, no scanner identity, and no
  passive position reporting. Everything in the chain was typed by somebody.
- **No unattended facility.** The agent narrows the window in which a ring goes
  unanswered; it does not remove the need for someone reachable. A site whose
  only responder is a model has not automated its front desk, it has removed
  it — and the one decision that matters most at a gate is the one the agent is
  forbidden to make.
- **No contents verification.** A beacon cannot tell a finder, or a tenant,
  that the seal was not broken in transit. It records the claim; tamper-evident
  packaging is a physical control PDI does not supply.
- **No legal weight by itself.** The chain is SHA-256 links with no signature
  and no external anchor ([operations.md](operations.md#audit-log) has the
  structure), so it is evidence of *consistency* — nothing was edited after the
  fact by someone without database access — rather than of authenticity.
  Anyone who can rewrite the table can recompute it. Anchoring a periodic
  checkpoint somewhere outside the deployment is the work that would change
  that, and it is not in this design.
