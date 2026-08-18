"""Bequests — vault access that begins only when a condition is attested.

The vault's whole posture is *nobody but you*: your hardware, your keys,
your walls. This module answers the question that posture leaves open —
**what about when you are gone?** A person's medical history, their
guardian's event trail, the sealed exchanges with a specialist: locked
perfectly is also locked away from the daughter settling the estate or
the doctor treating what the deceased knew and she didn't.

A bequest is the owner's answer, written while they are fine: *this
person* may read *these scopes* when *this condition* is attested.

The mechanism's teeth:

* **The credential does not exist until activation.** A bequest at rest
  holds a name and a list of key prefixes — no token, nothing a database
  breach or a curious operator could hand a grantee early. The grant
  token is minted at activation, shown once, and only its hash survives.
* **Activation is the admin's act, with a reference.** The deployment
  operator (PDI_ADMIN_TOKEN) activates against an ``activation_ref`` —
  a JIM vigil event id, a QRME succession ``verification_ref``, a
  death-certificate number — which is stored and mirrored into the
  tamper-evident audit chain. The attestation trail is the product.
* **The grant reads and nothing else.** Scoped to the named prefixes,
  read-only forever; every read lands in the audit chain like any other.
  A grantee is a reader of a bounded shelf, not a successor tenant.
* **Revocation while dormant is the owner's alone.** Until activation the
  tenant can delete the bequest with their own token. After activation
  the grant can be revoked by the admin — the operator who minted it.
"""

from __future__ import annotations

import hashlib
import json
import secrets

from . import audit, db, vault


class BequestError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message
        super().__init__(message)


CONDITIONS = ("executor", "attestation")

#: What a grantee is told when the vault behind their grant is gone.
#:
#: `vault.tenant_by_id` has carried ``AND deleted_at IS NULL`` since it was
#: written, and its docstring says plainly that *"tenants (deleted_at set)
#: resolve to None — their data is unreachable"*. This module resolved the
#: tenant with its own `SELECT * FROM tenants WHERE id=?`, twice, without that
#: clause — so when a tenant deleted their vault, every door of *theirs*
#: answered 401 and an activated grant went on returning record bodies.
#:
#:     asked     can the tenant still reach their vault
#:     mattered  can anyone still reach it
#:
#: On a wipe it was worse than open: the tenant row is deleted outright, so
#: `dict(None)` raised and the grantee met a 500 instead of an answer.
VAULT_CLOSED = ("this vault has been closed by its owner; the bequest cannot "
                "be read")


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create(tenant: dict, grantee_name: str, key_prefixes: list[str],
           condition: str = "executor", note: str | None = None) -> dict:
    grantee_name = (grantee_name or "").strip()
    prefixes = [p.strip() for p in (key_prefixes or []) if p and p.strip()]
    if not grantee_name:
        raise BequestError(422, "a bequest names its grantee")
    if not prefixes:
        raise BequestError(422, "a bequest names at least one key prefix — "
                                "an unbounded grant is not a bequest")
    if condition not in CONDITIONS:
        raise BequestError(422, f"condition must be one of {CONDITIONS}")
    conn = db.connect()
    bid = db.new_id("beq")
    conn.execute(
        "INSERT INTO bequests (id, tenant_id, grantee_name, key_prefixes,"
        " condition, note, created_at) VALUES (?,?,?,?,?,?,?)",
        (bid, tenant["id"], grantee_name, json.dumps(prefixes), condition,
         note, db.utcnow()))
    conn.commit()
    audit.record("bequest_created", tenant_id=tenant["id"], ref=bid)
    return out(_row(bid))


def _row(bid: str):
    """Any tenant's bequest. Only for the admin doors (activate,
    admin_revoke) and the read-back after a write that was itself scoped —
    a tenant-token door goes through `_tenant_row`."""
    return db.connect().execute(
        "SELECT * FROM bequests WHERE id=?",  # tenant-unscoped: activation and admin revoke are deployment-admin doors that reach any tenant's bequest by design
        (bid,)).fetchone()


def _tenant_row(bid: str, tenant_id: str):
    """This tenant's bequest or nothing — the scope is in the SQL."""
    return db.connect().execute(
        "SELECT * FROM bequests WHERE id=? AND tenant_id=?",
        (bid, tenant_id)).fetchone()


def out(row) -> dict:
    return {
        "id": row["id"],
        "tenant_id": row["tenant_id"],
        "grantee_name": row["grantee_name"],
        "key_prefixes": json.loads(row["key_prefixes"]),
        "condition": row["condition"],
        "note": row["note"],
        "created_at": row["created_at"],
        "revoked": bool(row["revoked_at"]),
        "activated": bool(row["activated_at"]),
        "activated_at": row["activated_at"],
        "activation_ref": row["activation_ref"],
    }


def for_tenant(tenant: dict) -> list[dict]:
    rows = db.connect().execute(
        "SELECT * FROM bequests WHERE tenant_id=? ORDER BY created_at",
        (tenant["id"],)).fetchall()
    return [out(r) for r in rows]


def revoke(tenant: dict, bid: str) -> dict:
    row = _tenant_row(bid, tenant["id"])
    if row is None:
        raise BequestError(404, "no such bequest")
    if row["activated_at"]:
        raise BequestError(409, "already activated — an activated grant is "
                                "revoked by the deployment admin, not the "
                                "tenant token, which may be in an estate's "
                                "hands by now")
    conn = db.connect()
    conn.execute("UPDATE bequests SET revoked_at=? WHERE id=? AND tenant_id=?",
                 (db.utcnow(), bid, tenant["id"]))
    conn.commit()
    audit.record("bequest_revoked", tenant_id=tenant["id"], ref=bid)
    return out(_row(bid))


def activate(bid: str, activation_ref: str) -> dict:
    """Mint the grant. Admin-gated at the route; the ref is the attestation
    and it is not optional."""
    activation_ref = (activation_ref or "").strip()
    if not activation_ref:
        raise BequestError(422, "activation requires a reference — what "
                                "attested the condition (a vigil event id, "
                                "a succession verification, a certificate "
                                "number)")
    row = _row(bid)
    if row is None:
        raise BequestError(404, "no such bequest")
    if row["revoked_at"]:
        raise BequestError(409, "this bequest was revoked by its owner")
    if row["activated_at"]:
        raise BequestError(409, "already activated — the grant token was "
                                "shown once, at activation")
    token = secrets.token_urlsafe(32)
    conn = db.connect()
    conn.execute(
        "UPDATE bequests SET activated_at=?, activation_ref=?, grant_hash=?"
        " WHERE id=? AND tenant_id=?",
        (db.utcnow(), activation_ref, _hash(token), bid, row["tenant_id"]))
    conn.commit()
    audit.record("bequest_activated", tenant_id=row["tenant_id"],
                 ref=f"{bid}:{activation_ref}")
    return {**out(_row(bid)), "grant_token": token}


def admin_revoke(bid: str) -> dict:
    row = _row(bid)
    if row is None:
        raise BequestError(404, "no such bequest")
    conn = db.connect()
    conn.execute(
        "UPDATE bequests SET revoked_at=?, grant_hash=NULL"
        " WHERE id=? AND tenant_id=?",
        (db.utcnow(), bid, row["tenant_id"]))
    conn.commit()
    audit.record("bequest_admin_revoked", tenant_id=row["tenant_id"], ref=bid)
    return out(_row(bid))


def _grant(token: str):
    if not token:
        raise BequestError(401, "grant token required")
    row = db.connect().execute(
        "SELECT * FROM bequests WHERE grant_hash=?",  # tenant-unscoped: the grant token, shown once at activation and hash-matched here, is the estate's credential
        (_hash(token),)
    ).fetchone()
    if row is None or row["revoked_at"] or not row["activated_at"]:
        # One refusal for all: a wrong token and a revoked one look alike.
        raise BequestError(404, "no active grant for this token")
    return row


def _in_scope(key: str, prefixes: list[str]) -> bool:
    return any(key.startswith(p) for p in prefixes)


def _living_tenant(tenant_id: str) -> dict:
    """The tenant behind a grant, through the same resolver every other door
    uses. See `VAULT_CLOSED`."""
    tenant = vault.tenant_by_id(tenant_id)
    if tenant is None:
        raise BequestError(410, VAULT_CLOSED)
    return tenant


def grant_keys(token: str, customer_key=None) -> dict:
    """What the grantee may see: keys within scope, and the owner's note."""
    row = _grant(token)
    tenant = _living_tenant(row["tenant_id"])
    prefixes = json.loads(row["key_prefixes"])
    keys = [k for k in vault.list_keys(tenant)
            if _in_scope(k, prefixes)]
    audit.record("bequest_list", tenant_id=row["tenant_id"], ref=row["id"])
    return {"grantee_name": row["grantee_name"], "note": row["note"],
            "key_prefixes": prefixes, "keys": keys}


def grant_read(token: str, key: str, customer_key=None) -> dict:
    row = _grant(token)
    prefixes = json.loads(row["key_prefixes"])
    if not _in_scope(key, prefixes):
        raise BequestError(403, "that key is outside this bequest's scope")
    tenant = _living_tenant(row["tenant_id"])
    # BYOK: "your keys, your walls" survives the owner. A customer-held key
    # is part of the estate — the grantee presents it or reads nothing.
    tenant["customer_key"] = customer_key
    record = vault.get(tenant, key)
    if record is None:
        raise BequestError(404, "no record at that key")
    audit.record("bequest_read", tenant_id=row["tenant_id"],
                 ref=f"{row['id']}:{key}")
    return record
