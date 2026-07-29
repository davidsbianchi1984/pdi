# PDI v0.8.0 — release notes

*Ready-to-paste body for the GitHub Release created when you push the
`app-v0.8.0` tag. Kept in sync with [CHANGELOG.md](CHANGELOG.md).*

---

**PDI v0.8.0** — the continuity round: the vault learns what happens when
you are gone. One of three interoperating products, all three cut
together at this version.

### Bequests

The vault's whole posture is *nobody but you* — your hardware, your keys,
your walls. Locked perfectly is also locked away from the daughter
settling the estate or the doctor treating what the deceased knew and she
didn't. A **bequest** is the owner's answer, written while they are fine:
*this person* may read *these scopes* when *this condition* is attested.

- **No credential exists until activation.** A bequest at rest holds a
  name and a list of key prefixes — no token, nothing a database breach
  or a curious operator could hand a grantee early. The grant token is
  minted at activation, shown once; only its hash survives.
- **Activation requires an attestation** — a JIM-mini vigil event id, a
  QRME succession verification, a death-certificate number — recorded in
  the tamper-evident audit chain. The attestation trail is the product.
- **The grant reads its shelf and nothing else, forever.** Every read is
  audited. The owner can revoke while alive; the admin after activation.
  A customer-held key (BYOK) remains part of the estate — the grantee
  presents it or reads nothing.

### Verification

266 tests green, including that a bequest at rest holds no credential,
that activation without a reference is refused, that the grant cannot
read outside its scopes, that a revoked grant and a wrong token look
alike, and that every step lands in the audit chain with the attestation
reference on it.

### Install

If you have 0.7.0, this arrives on its own — one restart when prompted.
Otherwise, download the installer for your OS from the assets below, or
run `python -m pdi`. Deployed on-premises or in colocation — your
hardware, your keys (`PDI_MASTER_KEY`), your walls.

**Full changelog:** https://github.com/davidsbianchi1984/pdi/blob/main/CHANGELOG.md
