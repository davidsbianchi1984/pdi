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

`ref_kind` is one of `transfer`, `intake`, `object`; chain entries continue to
live in `transfer_receipts` and `audit`, which already carry them.

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
