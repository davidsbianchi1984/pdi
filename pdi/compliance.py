"""Regulatory compliance programs.

PDI moves files under named compliance regimes (HIPAA, OSHA, CPNI, …). Each
program lists the controls it requires; PDI **natively satisfies** many of them
for every sealed transfer — encryption at rest (AES-256-GCM, AAD-bound to
tenant + key), tamper-evident audit logging, tenant-scoped access control,
enforced retention, and erasure — and reports the remainder as **operational**
(a BAA to sign, consent to capture, a breach-notification workflow to run).
"""

from __future__ import annotations

# Controls PDI enforces on every sealed transfer, by virtue of the vault, the
# hash-chained audit log, tenant isolation, retention windows, and key rotation.
NATIVE = {
    "encryption-at-rest", "encryption-in-transit", "access-logging",
    "audit-logging", "access-control", "minimum-necessary", "retention",
    "recordkeeping", "access-rights", "tenant-isolation", "safeguards",
    "key-rotation", "right-to-erasure", "right-to-delete", "confidentiality",
    "continuous-monitoring", "breach-detection", "availability",
}

# key, label, sector, summary, controls, retention_days
_ROWS = [
    ("hipaa", "HIPAA", "healthcare",
     "US Health Insurance Portability and Accountability Act — PHI privacy & security.",
     ["encryption-at-rest", "encryption-in-transit", "access-logging",
      "minimum-necessary", "retention", "breach-notification", "baa"], 2190),
    ("hitech", "HITECH", "healthcare",
     "Strengthens HIPAA with breach notification and audit requirements.",
     ["encryption-at-rest", "audit-logging", "breach-notification", "access-logging"], 2190),
    ("osha", "OSHA", "workplace-safety",
     "US Occupational Safety and Health Administration recordkeeping (e.g. 300 logs).",
     ["recordkeeping", "retention", "access-rights", "audit-logging"], 1825),
    ("cpni", "CPNI", "telecom",
     "FCC Customer Proprietary Network Information — carrier customer data (AT&T, Verizon, T-Mobile).",
     ["access-control", "audit-logging", "breach-notification", "consent"], 730),
    ("soc2", "SOC 2", "service-orgs",
     "Trust Services Criteria: security, availability, confidentiality.",
     ["encryption-at-rest", "access-control", "audit-logging", "availability",
      "confidentiality"], 365),
    ("pci_dss", "PCI-DSS", "payments",
     "Payment Card Industry Data Security Standard for cardholder data.",
     ["encryption-at-rest", "encryption-in-transit", "access-control",
      "audit-logging", "key-rotation", "breach-notification"], 365),
    ("gdpr", "GDPR", "eu-privacy",
     "EU General Data Protection Regulation.",
     ["encryption-at-rest", "access-logging", "right-to-erasure",
      "data-minimization", "breach-notification"], 0),
    ("ccpa", "CCPA/CPRA", "california-privacy",
     "California Consumer Privacy Act.",
     ["access-logging", "right-to-delete", "opt-out"], 0),
    ("glba", "GLBA", "financial",
     "Gramm-Leach-Bliley Act safeguards for financial data.",
     ["encryption-at-rest", "access-control", "safeguards", "breach-notification"], 730),
    ("sox", "SOX", "financial-reporting",
     "Sarbanes-Oxley recordkeeping for financial reporting.",
     ["audit-logging", "retention", "access-control"], 2555),
    ("ferpa", "FERPA", "education",
     "Family Educational Rights and Privacy Act for student records.",
     ["access-control", "access-logging", "consent"], 0),
    ("fedramp", "FedRAMP", "government-cloud",
     "US federal cloud authorization baseline.",
     ["encryption-at-rest", "continuous-monitoring", "access-control", "audit-logging"], 1095),
    ("cjis", "CJIS", "law-enforcement",
     "FBI Criminal Justice Information Services security policy (lawful-intercept, subpoena data).",
     ["encryption-at-rest", "access-control", "audit-logging", "advanced-authentication"], 1095),
]

_PROGRAMS = {
    key: {"key": key, "label": label, "sector": sector, "summary": summary,
          "controls": controls, "retention_days": days}
    for (key, label, sector, summary, controls, days) in _ROWS
}


def get(key: str) -> dict | None:
    return _PROGRAMS.get(key)


def retention_days(keys: list[str]) -> int:
    """The strictest (longest) retention across the transfer's programs."""
    return max((p["retention_days"] for k in keys if (p := get(k))), default=0)


def controls_for(keys: list[str]) -> dict:
    """Split the union of required controls into those PDI satisfies natively and
    those that remain operational for the corporation to run."""
    required: list[str] = []
    for key in keys:
        p = get(key)
        if not p:
            continue
        for c in p["controls"]:
            if c not in required:
                required.append(c)
    return {
        "required": required,
        "satisfied_by_pdi": [c for c in required if c in NATIVE],
        "operational": [c for c in required if c not in NATIVE],
    }


def catalog() -> dict:
    return {
        "programs": list(_PROGRAMS.values()),
        "count": len(_PROGRAMS),
        "pdi_native_controls": sorted(NATIVE),
    }
