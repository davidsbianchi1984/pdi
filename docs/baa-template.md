# Business Associate Agreement (BAA) — template

*A production-ready starting point for the agreement a PDI operator (the
**Business Associate**) signs with each customer that is a HIPAA **Covered
Entity** (or an upstream Business Associate) before Protected Health
Information flows through a PDI deployment. Pair it with the safeguards
mapping in Exhibit B, which ties each contractual promise to the concrete
PDI control that keeps it.*

> **This is a template, not legal advice.** Have qualified counsel review and
> adapt it to your parties, state law, and deployment before signing. Where a
> value is required, it appears as `[BRACKETED]`.

---

## Business Associate Agreement

This Business Associate Agreement ("**Agreement**") is entered into as of
`[EFFECTIVE DATE]` (the "Effective Date") by and between `[COVERED ENTITY
LEGAL NAME]` ("**Covered Entity**") and `[PDI OPERATOR LEGAL NAME]`
("**Business Associate**"), each a "Party."

### 1. Definitions

Terms used but not otherwise defined in this Agreement have the meanings
given in the Health Insurance Portability and Accountability Act of 1996 and
its implementing regulations at 45 C.F.R. Parts 160 and 164, as amended,
including by the HITECH Act ("**HIPAA**"). "**PHI**" means Protected Health
Information created, received, maintained, or transmitted by Business
Associate for or on behalf of Covered Entity under the Services described in
Exhibit A.

### 2. Permitted Uses and Disclosures

2.1 Business Associate may use and disclose PHI only (a) to perform the
Services described in **Exhibit A**, (b) as required by law, or (c) as
expressly permitted in writing by Covered Entity — and in each case
consistent with the minimum-necessary standard.

2.2 Business Associate may use PHI for its own proper management and
administration, and may disclose PHI for those purposes only where the
disclosure is required by law or the recipient gives reasonable written
assurances of confidentiality and breach notification.

2.3 Business Associate shall not sell PHI, use PHI for marketing, or
de-identify PHI except as directed by Covered Entity in writing.

### 3. Safeguards

Business Associate shall implement administrative, physical, and technical
safeguards that comply with the Security Rule (45 C.F.R. Part 164, Subpart C)
for all electronic PHI, including without limitation the technical controls
described in **Exhibit B** (encryption at rest, tenant isolation, access
control, tamper-evident audit logging, key management, and verified
deletion), and shall not degrade those controls during the term.

### 4. Reporting

4.1 Business Associate shall report to Covered Entity any use or disclosure
of PHI not permitted by this Agreement, any Security Incident of which it
becomes aware, and any Breach of Unsecured PHI as required by 45 C.F.R.
§ 164.410, without unreasonable delay and in no case later than
`[NUMBER, e.g. 10]` business days after discovery.

4.2 Each report shall include, to the extent known, the identity of affected
individuals, a description of what happened, the PHI involved, and the
mitigation taken — drawing on the deployment's audit chain (Exhibit B §3),
which records every access to every sealed record.

### 5. Subcontractors

Business Associate shall ensure that any subcontractor that creates,
receives, maintains, or transmits PHI on its behalf (including hosting,
colocation, KMS/HSM, and backup providers) agrees in writing to restrictions
and conditions at least as protective as this Agreement, per 45 C.F.R.
§§ 164.308(b)(2) and 164.502(e)(1)(ii).

### 6. Individual Rights

6.1 **Access (§ 164.524).** Business Associate shall make PHI in a Designated
Record Set available to Covered Entity within `[NUMBER]` business days of
request. (PDI surfaces a tenant's records and each user's own access history
directly — Exhibit B §5.)

6.2 **Amendment (§ 164.526).** Business Associate shall incorporate
amendments to PHI as directed by Covered Entity.

6.3 **Accounting of disclosures (§ 164.528).** Business Associate shall
document disclosures and make that documentation available to Covered
Entity; the deployment's append-only audit log satisfies the recording
obligation for system-level access.

### 7. Availability to the Secretary

Business Associate shall make its internal practices, books, and records
relating to the use and disclosure of PHI available to the Secretary of
Health and Human Services for purposes of determining compliance.

### 8. Term and Termination

8.1 This Agreement is effective from the Effective Date and continues until
all PHI is returned or destroyed under §8.3.

8.2 Covered Entity may terminate this Agreement (and the underlying Services)
if Business Associate materially breaches it and fails to cure within
`[NUMBER]` days of written notice.

8.3 On termination, Business Associate shall, at Covered Entity's election,
return or destroy all PHI it maintains, and retain no copies. Destruction is
performed with the deployment's verified-deletion path (Exhibit B §6), and a
destruction certificate referencing the audit-chain entries is provided. If
return or destruction is infeasible for specific PHI, the protections of
this Agreement survive for that PHI for as long as it is maintained.

### 9. Covered Entity Obligations

Covered Entity shall notify Business Associate of (a) any limitation in its
notice of privacy practices, (b) changes in or revocation of individual
permissions, and (c) any restriction it has agreed to under § 164.522, in
each case to the extent it affects Business Associate's permitted uses.

### 10. Miscellaneous

Any ambiguity shall be interpreted to permit compliance with HIPAA. A
reference to a section in HIPAA means the section as amended. This Agreement
supersedes prior BAAs between the Parties for the Services.

| | Covered Entity | Business Associate |
| --- | --- | --- |
| Signature | ______________________ | ______________________ |
| Name | `[NAME]` | `[NAME]` |
| Title | `[TITLE]` | `[TITLE]` |
| Date | `[DATE]` | `[DATE]` |

---

## Exhibit A — Services

Business Associate operates a **Private Data Infrastructure (PDI)**
deployment providing: sealed (encrypted-at-rest) record storage under a
dedicated tenant; compliance-grade secure file **transfer** and **intake**
under the programs designated by Covered Entity (e.g. HIPAA, OSHA, CPNI);
tamper-evident audit logging; and the operational services in
[docs/enterprise.md](enterprise.md). Deployment posture:
`[ON-PREMISES | TIER III+ COLOCATION]` at `[FACILITY]`.

## Exhibit B — Technical safeguards mapping

| # | Contractual promise | PDI control that keeps it |
| --- | --- | --- |
| 1 | Encryption at rest (§ 164.312(a)(2)(iv)) | Every record sealed with AES-256-GCM; ciphertext AAD-bound to tenant + key version so records cannot be moved or read across tenants |
| 2 | Access control (§ 164.312(a)) | Per-tenant bearer tokens (stored only as SHA-256 hashes), read vs. write scopes, instant revocation; admin surface gated by a separate `PDI_ADMIN_TOKEN` |
| 3 | Audit controls (§ 164.312(b)) | Append-only, SHA-256 hash-chained audit log of every store/read/erase; `GET /audit/verify` proves no retroactive edit |
| 4 | Key management (§ 164.312(a)(2)(iv)) | Envelope encryption: versioned DEKs wrapped by a KEK held in `[ENV | KMS/HSM PROVIDER]`; rotate → re-seal → retire without downtime |
| 5 | Individual access & disclosure accounting (§§ 164.524, 164.528) | Tenant record listing; per-user access history surfaced to the data subject through the integrating application |
| 6 | Verified deletion / return (§ 164.310(d)(2)) | Record deletion and tenant wipe are audited events in the same chain; snapshot export provides return-in-kind |
| 7 | Transmission security (§ 164.312(e)) | Service boundaries deployed behind TLS termination; no plaintext PHI transport |
| 8 | Retention | Per-tenant retention windows, from days to `forever`, enforced by the vault |

## Related

- [enterprise.md](enterprise.md) — deployment postures and the compliance
  transfer/intake flows this agreement governs.
- The JIM-mini repo's `docs/hipaa-baa.md` — the integrating application's
  HIPAA posture and its pre-production checklist, which includes executing
  this BAA.
