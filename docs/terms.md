# PDI (Private Data Infrastructure) Terms of Service

*Version 1.1 — effective 2026-08-10. Served by the API at `GET /terms`.
PDI is business-to-business infrastructure: the "Customer" is the
organization whose tenant is provisioned, and these Terms bind the
Customer and every system and user it connects. The version in force is
recorded on the tenant at provisioning. This is a template maintained
with the product — have counsel review and localize it before commercial
launch.*

**By requesting a tenant, holding a tenant token, or sending data to the
Service, the Customer agrees to these Terms.**

## Beta status

The Service is currently a **beta**. That means, concretely:

- It is offered for testing and evaluation. Features may change, break, or
  be removed without notice, and availability is not guaranteed.
- **Your data may be lost.** Backups are best-effort; the beta may be reset
  or migrated. Do not make the Service the only home of anything you cannot
  afford to lose.
- **No fees are charged during the beta.** Plans that display a future
  price are free while the beta runs; the displayed price is the intended
  charge after the beta ends, and no charge will begin without notice and
  your renewed agreement.
- The operator may suspend or end the beta, or any tester's access, at any
  time. Where practical, reasonable notice will be given before data is
  removed.

## 1. The Service

1.1 PDI is an **encrypted vault and data-custody service**: sealed
storage with envelope encryption, tenant isolation, provenance and audit
records, connectors, retention and legal-hold controls, and compliance
tooling. It stores and protects the Customer's data; it does not
interpret, verify, or take responsibility for the data's content.

1.2 The Service is **infrastructure, not advice**. Compliance features
(audit trails, retention, the HIPAA program) are tools that support the
Customer's compliance program — they do not make the Customer compliant,
and nothing in the Service is legal advice.

## 2. Customer data and responsibilities

2.1 **The Customer owns its data.** PDI processes it only to provide the
Service: sealing, storing, serving, and deleting it as directed through
the API. Export and deletion are available at any time through the
documented endpoints; deletion honors the tenant's soft-delete recovery
window, then is permanent.

2.2 The Customer is responsible for: the lawfulness of the data it
stores; obtaining any consents its data subjects require; **safeguarding
its tenant token** (the token is shown once at issuance and only its
hash is retained — anyone holding the token is the tenant); configuring
retention, legal holds, and access roles to match its own obligations;
and the conduct of every system it connects.

2.3 **Acceptable use.** The Customer will not use the Service to store
or distribute unlawful content, to violate third-party rights, to probe
or degrade the Service, or to process regulated data outside the
programs provisioned for its tenant.

## 3. Protected health information (HIPAA)

Tenants may only process PHI under the HIPAA program after a Business
Associate Agreement is executed and recorded — the signable template is
`docs/baa-template.md`, and the Service **enforces this in code**:
HIPAA-program transfers and intakes are refused (HTTP 403) until an
active BAA is recorded for the tenant. Terminating the BAA re-imposes
the block. Where these Terms and an executed BAA conflict regarding PHI,
the BAA controls.

## 4. Security; assumption of risk

4.1 PDI seals records with envelope encryption, isolates tenants,
audit-logs access, and supports key rotation, as documented. The
Customer acknowledges that **no security measure is absolute** and
assumes the risks inherent in networked storage — including
unavailability, latency, and the consequences of a compromised tenant
token or of the Customer's own connected systems.

4.2 To the maximum extent permitted by law, the Customer **releases the
Service operator, its owners, employees, and licensors (the "Released
Parties") from claims arising out of use of the Service** — including
data loss, unavailability, retention or deletion outcomes directed
through the API, and acts of the Customer's connected systems — except
where caused by the Released Parties' gross negligence or willful
misconduct, or where such a release is not permitted by law.

## 5. Disclaimer of warranties

THE SERVICE IS PROVIDED **"AS IS" AND "AS AVAILABLE"** WITHOUT
WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT, OR UNINTERRUPTED OR
ERROR-FREE OPERATION.

## 6. Limitation of liability

TO THE MAXIMUM EXTENT PERMITTED BY LAW, THE RELEASED PARTIES SHALL NOT
BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL,
EXEMPLARY, OR PUNITIVE DAMAGES, OR FOR LOSS OF DATA, PROFITS, OR
GOODWILL. THE RELEASED PARTIES' AGGREGATE LIABILITY FOR ALL CLAIMS
SHALL NOT EXCEED THE GREATER OF (A) AMOUNTS THE CUSTOMER PAID FOR THE
SERVICE IN THE TWELVE MONTHS BEFORE THE CLAIM OR (B) US $100. Some
jurisdictions do not allow certain limitations; these apply to the
fullest extent permitted.

## 7. Indemnification

The Customer will defend, indemnify, and hold harmless the Released
Parties from third-party claims arising out of the Customer's data, its
breach of these Terms, or the conduct of its connected systems.

## 8. Suspension; termination; survival

We may suspend or terminate a tenant for material breach (including
non-payment or acceptable-use violations), with notice where
practicable. On termination the Customer may export its data during the
recovery window, after which it is deleted per the retention
configuration. Sections 2, 4–7, and 9 survive termination.

## 9. Changes; governing law

We may update these Terms by publishing a new version at `GET /terms`;
continued use after the effective date is acceptance. Governing law and
dispute resolution: `[GOVERNING LAW / VENUE / ARBITRATION CLAUSE — set
by counsel]`

---

*Related: the Business Associate Agreement template
(docs/baa-template.md, machine-enforced per §3), the enterprise posture
(docs/enterprise.md), and the operations guide (docs/operations.md).*

## Accessibility commitment

Ability is not a gate to this Service. Every feature is usable by text
alone — nothing requires hearing or speech — and voice interaction is an
additional input path, never a requirement. The operator maintains an
active accessibility program driving screen-reader, keyboard-only,
reduced-motion and related support to complete, with gaps recorded as
tracked work. If a disability — named anywhere or not — stands between
you and any part of the Service, say so through the Service's help
surface; such reports are treated as sensitive and become tracked work.
Nothing in these Terms limits rights you hold under applicable
accessibility law.
