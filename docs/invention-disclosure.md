# Invention Disclosure — PDI (Private Data Infrastructure)

*Inventor: David Bianchi. Recorded 2026-07-29. This document, together
with this repository's commit history and tagged releases, is a dated
public record of conception and reduction to practice. It is written to
be handed to a patent attorney as the starting point for provisional
applications. It is a factual record, not legal advice and not a license
(see LICENSE).*

## 1. Personal encrypted vault as the custody layer of a product family

**The process:** an individually keyed encrypted vault
(`PDI_MASTER_KEY` — your hardware, your keys, your walls) serving as the
seal point for a family of interoperating products: a guardian's
biometric events, tandem specialist exchanges, and clinical captures are
sealed at write time, with per-record provenance (origin, seal details,
audit history) readable back through a custody viewer scoped to the
record owner.

## 2. Custody posture as a plan property, not a deployment property

**The process:** whether data is vaulted moves from "how the server was
deployed" to "what the user's plan promises" — a free platform-custody
tier that holds nothing private and says so at every surface, against
paid tiers whose writes seal to the vault; the gate lives at the plan
boundary so a deployment cannot silently change a user's custody
(shipped v0.4.0–v0.4.1 line).

## 3. Hosting spectrum with identical API surface

**The process:** the same vault API served across free colocation,
leased space, self-hosting, and the user's own device, so custody can be
upgraded without the product family changing a call (shipped v0.4.0
line). Admin key rotation is performed from the product apps themselves.

## 4. Bequests — vault access that begins at attestation

**The process:** the vault owner names, in advance, a grantee, a bounded
set of key scopes, and a condition; **no credential exists until the
condition is attested** — the grant token is minted at activation by the
deployment operator against a mandatory attestation reference (a
guardian's silence-vigil event id, an ownership-succession verification,
a certificate number) recorded in the tamper-evident audit chain. The
grant is read-only forever, bounded to its scopes, revocable by the owner
while dormant and by the operator after activation; customer-held keys
(BYOK) remain part of the estate — the grantee presents the key or reads
nothing. (`pdi/bequests.py`; shipped v0.8.0.)

## 6. Continuity: reviewer-gated succession joined to guardian and vault

**The process:** profile ownership succession is gated by a reviewer with
a verification reference rather than the owner token (the owner may be
unable to authorize); with no named successor the profile sunsets to a
frozen memorial rather than an orphan. Cross-product, the same
attestation reference joins the guardian's silence vigil (JIM-mini) and
the vault's bequest activation (PDI), so one attested event carries a
person's absence through all three products. (`qrme/routers/profiles.py`
succession + memorial, shipped v0.3.x line; cross-product join v0.8.0.)

## The operations journal — a view, never a side door

**The process:** third-product records sealed into a tenant's encrypted
vault (`qrme/coordination/*`) listed back to that tenant as a journal
whose every entry is read through the ordinary audited decryption path,
so the journal adds no second door: each journal read lands on the
tamper-evident hash-chained audit log exactly as a direct read would
(`GET /operations`; shipped v0.13.0, recorded 2026-07-29).

---

*Attorney notes: repository first became public before this disclosure;
for jurisdictions with grace periods, the earliest public commit and the
earliest tagged release containing each mechanism are the operative
dates.*
