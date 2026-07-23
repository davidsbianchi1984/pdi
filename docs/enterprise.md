# PDI for enterprises — compliance-grade secure file transfer

PDI is a **private data infrastructure** corporations (carriers like AT&T,
Verizon and T-Mobile; broadband, healthcare, financial and public-sector
operators) can run to move files safely for their users under regulatory
compliance — HIPAA, OSHA, CPNI, PCI-DSS, and more.

## Deployment

Run the same software in the posture your compliance and risk profile calls for:

| Option | What it is | Best when |
| --- | --- | --- |
| **On-premises** | A dedicated PDI deployment inside your own or leased facility; you own physical operations, power, cooling, and on-site security. | You need the highest control over the physical environment. |
| **Off-site colocation (Tier III+)** | PDI on your dedicated servers in a professionally managed, 24/7-secured colocation facility with redundant power, climate control, and uptime guarantees. | Lower capital outlay, no facility buildout, immediate deployment. |

Both keep data sovereignty on your side of the wire — no public-network
dependency — and both are forward-compatible with the optional AI-agent services
(the QRME synthetic-profile and JIM guidance systems) when you elect to activate
them.

## How a compliant transfer works

A corporation (a PDI **tenant**) seals a file for a recipient under one or more
compliance programs. PDI's core guarantees carry the regulated controls:

1. **Encrypted at rest** — the file is sealed in the vault with AES-256-GCM,
   AAD-bound to the tenant + key, so a record can't be moved or read across
   tenants.
2. **Audit-logged access** — creation and every retrieval land in the
   tamper-evident, hash-chained audit log and in the transfer's chain of
   custody. `GET /audit/verify` (and each transfer's custody record) attests the
   chain is intact.
3. **Scoped retrieval** — a one-shot **receive token** (only its SHA-256 is
   stored) authorizes the recipient; nothing else can read the file.
4. **Enforced retention** — the record is retained for the strictest window
   across its programs (OSHA 5y, HIPAA 6y, SOX 7y, …). Revoking a transfer cuts
   access but keeps the record until retention expires.

### API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/compliance/programs` | the compliance regimes PDI carries + the controls it satisfies natively |
| `POST` | `/transfers` | seal a file for a recipient under program(s); returns a one-shot receive token |
| `GET` | `/transfers` | the tenant's transfers |
| `GET` | `/transfers/{id}` | transfer metadata |
| `GET` | `/transfers/{id}/custody` | the compliance record: programs, controls, retention, full chain of custody, audit attestation |
| `POST` | `/transfers/{id}/receive` | recipient retrieves the file with `X-Receive-Token` (access is audited) |
| `DELETE` | `/transfers/{id}` | revoke access (record retained through the retention window) |

```bash
# A carrier seals a customer record under CPNI + HIPAA for a recipient.
curl -sX POST $PDI/transfers -H "authorization: Bearer $TENANT_TOKEN" \
  -d '{"recipient":"patient-123","filename":"labs.pdf",
       "content":"…","programs":["hipaa","osha"],"classification":"PHI"}'
# -> { "id": "xfer_…", "retention_days": 2190, "receive_token": "pdi_recv_…",
#      "controls": { "satisfied_by_pdi": ["encryption-at-rest", …],
#                    "operational": ["baa", …] } }
```

## Compliance programs

`GET /compliance/programs` returns the catalog. Each program lists the controls
it requires; PDI reports which it satisfies natively (encryption at rest &
in transit, access & audit logging, access control, minimum-necessary,
retention, recordkeeping, key rotation, erasure, tenant isolation) and which
remain **operational** for the corporation to run (a BAA to sign, consent to
capture, a breach-notification workflow).

Included: **HIPAA · HITECH · OSHA · CPNI · SOC 2 · PCI-DSS · GDPR · CCPA/CPRA ·
GLBA · SOX · FERPA · FedRAMP · CJIS**.

> PDI enforces the technical safeguards. Full regulatory compliance also depends
> on the operational controls above and your organization's policies; PDI gives
> you the encrypted, audited, retained substrate to build on.
