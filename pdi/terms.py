"""Terms of Service, versioned and served by the API.

PDI is B2B infrastructure, so acceptance is by the Customer organization:
provisioning a tenant records the terms version in force at that moment
(``tenants.terms_version`` / ``terms_accepted_at``) — the server-side
receipt of which agreement governs that tenant. For PHI, the executed BAA
(docs/baa-template.md) is the controlling instrument and is separately
recorded and enforced by :mod:`pdi.baa`.
"""

from __future__ import annotations

TERMS_VERSION = "1.3"
DOCUMENT = "docs/terms.md"

KEY_POINTS = [
    "This is a beta: features change, data may be lost or reset, and no "
    "fees are charged while the beta runs — displayed plan prices begin "
    "only after the beta, with notice and renewed agreement.",
    "Ability is not a gate: everything works by text alone, voice is "
    "optional, and anything that stands in your way can be reported from "
    "the Accessibility tab — no token, no diagnosis — where it becomes "
    "tracked work.",
    "PDI is encrypted data-custody infrastructure, not advice; its "
    "compliance tooling supports your program but does not make you "
    "compliant.",
    "The Customer owns its data and is responsible for its lawfulness, "
    "consents, tenant-token safekeeping, and connected systems.",
    "PDI holds that data in custody and never in ownership: the "
    "deployment stores and serves it under the Customer's direction, and "
    "neither the Customer's ownership nor PDI's custody diminishes the "
    "statutory rights a data subject has over their own personal data.",
    "PHI requires an executed Business Associate Agreement, recorded on "
    "the tenant — the API refuses HIPAA-program work without one.",
    "No security measure is absolute; the Customer assumes the inherent "
    "risks of networked storage.",
    "The Service is provided as-is, without warranties.",
    "Liability is capped at the greater of 12 months of fees or US $100, "
    "except where the law says otherwise.",
    "Terms may change; the current version is always at GET /terms, and "
    "each tenant records the version in force when it was provisioned.",
]
