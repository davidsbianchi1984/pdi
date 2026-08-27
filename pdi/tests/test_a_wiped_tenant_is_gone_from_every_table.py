"""`mode=wipe` said *permanently removes*. It removed three tables of twenty.

`DELETE /tenants/{id}?mode=wipe` is the strongest promise this product makes
after custody itself, and `vault.delete_tenant` implemented it as:

    DELETE FROM records        WHERE tenant_id=?
    DELETE FROM tenant_tokens  WHERE tenant_id=?
    UPDATE bequests SET revoked_at=?, grant_hash=NULL WHERE tenant_id=?
    DELETE FROM tenants        WHERE id=?

Four statements against a schema with **twenty tenant-scoped tables**. Driven
against a tenant that had done nothing unusual — signed a BAA, sealed one
record, adopted a customer-held key, set a hosting mode and a dock preference —
a permanent wipe left rows behind in four of them:

    baa_records          1
    dock_prefs           1
    tenant_key_versions  1
    tenant_keys          1

`tenant_keys` is the customer's key-provider configuration and its check value.
`baa_records` is an executed Business Associate Agreement carrying two
companies' legal names and an effective date. Both outlived the account they
belonged to, in the product whose whole argument is that it holds less of you
than the alternatives.

## Why the previous fix did not prevent this one

The `bequests` line above was added the round somebody noticed a grant hash was
outliving the account it had been cut from — a real find, correctly fixed, and
fixed **one table at a time**. That is the whole lesson: the repair was applied
to the instance rather than to the shape, so the next fifteen instances stayed.
`vault.cascade` now derives the table list from `sqlite_master` at call time,
so a migration is covered by being written rather than by somebody remembering
this function.

## Why the sweep mattered more than the wipe

There are two ways a tenant stops existing here. An operator running a wipe is
watching the response. `retention.sweep` purging a soft-deleted tenant past its
recovery window is not watched by anybody — it is a scheduled job whose output
is two integers — and it carried a copy of the same short list. It now runs the
same cascade.

## What a wipe deliberately keeps

The audit chain. It is the record that the deletion happened, it is
hash-linked, and removing rows from it would both destroy the evidence and
break `verify()` for every entry after them. A vault that erases its own proof
of erasure is worse than one that never promised to erase — so `audit` is the
single member of `vault.WIPE_KEEPS`, and this file pins that it is the *only*
one.
"""

import base64
import json

import pytest

from pdi import audit, db, retention, vault
from . import ratchets

KEY = base64.b64encode(b"k" * 32).decode()


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _busy_tenant(client, name="acme"):
    """A tenant that has used the product, rather than one that just exists.

    An empty tenant is wiped correctly by any implementation, including the
    broken one — every table it does not appear in is a table it cannot be left
    in. Each call below is chosen because it writes to a *different* table.
    """
    body = client.post("/tenants", json={"name": name}).json()
    tid, token = body["id"], body["token"]
    h = _auth(token)
    client.post(f"/tenants/{tid}/baa", json={
        "customer_legal_name": f"{name} Inc.",
        "operator_legal_name": "Vault Operations LLC",
        "effective_date": "2026-07-24"})
    client.put("/records", json={"key": "r1", "value": "a sealed thing"},
               headers=h)
    client.put("/key", json={"provider": "held", "key": KEY}, headers=h)
    client.put(f"/hosting/{tid}", json={"mode": "leased"}, headers=h)
    client.put(f"/dock/{tid}", json={"visible": True}, headers=h)
    client.post(f"/tenants/{tid}/tokens", json={"role": "reader"}, headers=h)
    return tid, token


def _rows_naming(tenant_id: str) -> dict[str, int]:
    """Every table holding a row that names this tenant, and how many.

    Walks `sqlite_master` rather than a list, for the same reason the cascade
    does: the table that keeps a wiped tenant's data is the one added after the
    list was written.
    """
    conn = db.connect()
    out = {}
    for (name,) in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%'").fetchall():
        cols = [c[1] for c in conn.execute(f"PRAGMA table_info({name})")]
        if "tenant_id" not in cols:
            continue
        n = conn.execute(f"SELECT COUNT(*) FROM {name} WHERE tenant_id=?",
                         (tenant_id,)).fetchone()[0]
        if n:
            out[name] = n
    return out


# --- the promise ------------------------------------------------------------

def test_a_wipe_leaves_no_row_naming_the_tenant_anywhere(client):
    """The sentence on the route, checked against the schema instead of
    against the four statements somebody wrote first."""
    tid, _ = _busy_tenant(client)
    before = _rows_naming(tid)
    assert len(before) >= 5, (
        f"the fixture only reached {sorted(before)} — it is not exercising "
        f"enough of the schema to prove anything about a cascade")

    r = client.delete(f"/tenants/{tid}?mode=wipe")
    assert r.status_code == 200, r.text

    left = _rows_naming(tid)
    allowed = vault.WIPE_KEEPS | set(vault.WIPE_RETIRES)
    assert set(left) <= allowed, (
        "a permanent wipe left the tenant in " + ", ".join(
            f"{t} ({n} row(s))" for t, n in sorted(left.items())
            if t not in allowed))


def test_a_retired_table_keeps_the_record_and_not_the_credential(client):
    """The third category, checked on both halves.

    `bequests` survives a wipe on purpose — it is the estate record, and a
    grantee whose credential fails with silence reads that as a bug where
    *revoked* is the truth. What must not survive is the live credential. This
    would pass trivially if the fixture never made a bequest, which is exactly
    why one is made here.
    """
    tid, token = _busy_tenant(client)
    b = client.post("/bequests", json={
        "grantee_name": "June Bianchi",
        "key_prefixes": ["jim/u1/medical/"],
        "note": "For my daughter — the medical records, nothing else."},
        headers=_auth(token))
    assert b.status_code == 201, b.text
    # Activated, because an unactivated bequest has no grant hash and the
    # half of this test that matters is the credential going.
    act = client.post(f"/bequests/{b.json()['id']}/activate",
                      json={"activation_ref": "cert-1"})
    assert act.status_code == 200, act.text
    assert db.connect().execute(
        "SELECT COUNT(*) FROM bequests WHERE tenant_id=? AND grant_hash IS NOT NULL",
        (tid,)).fetchone()[0] == 1, "the fixture never minted a live grant"

    client.delete(f"/tenants/{tid}?mode=wipe")
    rows = db.connect().execute(
        "SELECT revoked_at, grant_hash FROM bequests WHERE tenant_id=?",
        (tid,)).fetchall()
    assert rows, "the estate record was erased rather than retired"
    for row in rows:
        assert row["revoked_at"], "a wiped tenant still has a standing bequest"
        assert row["grant_hash"] is None, "the grant hash outlived the tenant"


def test_the_retention_sweep_leaves_no_row_either(client, monkeypatch):
    """The unwatched path. An operator reads a wipe's response; nobody reads
    the sweep's, which is why it is the worse place for a short list."""
    tid, _ = _busy_tenant(client)
    assert len(_rows_naming(tid)) >= 5
    client.delete(f"/tenants/{tid}?mode=soft")

    # Recovery window of zero days: the soft-deleted tenant is immediately
    # past it, so one sweep does what a month of them would.
    monkeypatch.setenv("PDI_RECOVERY_WINDOW", "1")
    db.connect().execute(
        "UPDATE tenants SET deleted_at='2020-01-01T00:00:00Z' WHERE id=?",
        (tid,))
    db.connect().commit()

    out = retention.sweep()
    assert out["purged_tenants"] == 1, out

    left = _rows_naming(tid)
    allowed = vault.WIPE_KEEPS | set(vault.WIPE_RETIRES)
    assert set(left) <= allowed, (
        "the scheduled purge left the tenant in " + ", ".join(
            f"{t} ({n} row(s))" for t, n in sorted(left.items())
            if t not in allowed))


def test_the_customers_key_configuration_does_not_outlive_the_account(client):
    """Named on its own because it is the one that would end a security
    review. `tenant_keys` holds the key-provider configuration and a check
    value for a customer under `held` custody — the row that says *which* key
    opens this tenant — and it survived a permanent wipe."""
    tid, token = _busy_tenant(client)
    client.put("/key", json={"provider": "held", "key": KEY},
               headers=_auth(token))
    conn = db.connect()
    assert conn.execute("SELECT COUNT(*) FROM tenant_keys WHERE tenant_id=?",
                        (tid,)).fetchone()[0] == 1

    client.delete(f"/tenants/{tid}?mode=wipe")
    conn = db.connect()
    for table in ("tenant_keys", "tenant_key_versions"):
        assert conn.execute(f"SELECT COUNT(*) FROM {table} WHERE tenant_id=?",
                            (tid,)).fetchone()[0] == 0, table


# --- what it deliberately keeps ---------------------------------------------

def test_the_audit_chain_survives_the_wipe_and_still_verifies(client):
    """The exception, and the reason for it. Deleting audit rows would destroy
    the record that the deletion happened *and* break the hash chain for every
    entry filed after them."""
    tid, _ = _busy_tenant(client)
    client.delete(f"/tenants/{tid}?mode=wipe")

    kept = db.connect().execute(
        "SELECT COUNT(*) FROM audit WHERE tenant_id=?", (tid,)).fetchone()[0]
    assert kept, "the wipe erased its own audit trail"
    assert audit.verify()["intact"], "the chain broke"


def test_the_wipe_records_which_tables_it_cleared(client):
    """"Rows were deleted" is the claim. Which tables and how many is what
    makes the claim checkable a year later by somebody who was not here."""
    tid, _ = _busy_tenant(client)
    body = client.delete(f"/tenants/{tid}?mode=wipe").json()
    assert body["cleared"], body
    assert "records" in body["cleared"], body

    row = db.connect().execute(
        "SELECT ref FROM audit WHERE tenant_id=? AND action='tenant.wipe'",
        (tid,)).fetchone()
    assert row, "the wipe is not on the chain"
    on_chain = json.loads(row["ref"])
    assert on_chain == body["cleared"], (on_chain, body["cleared"])
    assert "tenant_keys" in on_chain, (
        "the response and the chain agree, and both omit the key row — the "
        "cascade is not reaching it")


# --- the shape of the guard itself ------------------------------------------

def test_the_cascade_reads_the_schema_rather_than_a_list(client):
    """The whole point of the fix. A hand-kept list is complete the day it is
    written; `sqlite_master` is complete every day."""
    _busy_tenant(client)
    conn = db.connect()
    live = {name for (name,) in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%'").fetchall()
        if "tenant_id" in [c[1] for c in conn.execute(f"PRAGMA table_info({name})")]}
    assert set(vault.tenant_scoped_tables()) == live
    assert len(live) >= ratchets.floor("vault.tenant_scoped_tables"), (
        f"only {len(live)} tenant-scoped table(s) found — the scan has stopped "
        f"matching and every check in this file would pass on nothing")


def test_audit_is_the_only_thing_a_wipe_is_allowed_to_keep(client):
    """A second name in `WIPE_KEEPS` is how this defect comes back: a table
    that is awkward to clear gets excused, the excuse is a constant nobody
    reads, and the promise quietly narrows again. Widening this needs a
    deliberate edit here and a reason written down."""
    assert vault.WIPE_KEEPS == frozenset({"audit"}), vault.WIPE_KEEPS
    assert set(vault.WIPE_RETIRES) == {"bequests"}, sorted(vault.WIPE_RETIRES)


def test_the_check_would_actually_catch_a_missed_table(client):
    """A guard nobody has watched fail is a guard nobody should trust.

    This puts a row back after the wipe and asserts `_rows_naming` names the
    table — without it, every test above would pass just as happily if the
    walk were quietly returning an empty dict.
    """
    tid, _ = _busy_tenant(client)
    client.delete(f"/tenants/{tid}?mode=wipe")
    allowed = vault.WIPE_KEEPS | set(vault.WIPE_RETIRES)
    assert set(_rows_naming(tid)) <= allowed

    conn = db.connect()
    conn.execute("INSERT INTO gate_settings (tenant_id, timezone, updated_at)"
                 " VALUES (?, ?, ?)", (tid, "UTC", db.utcnow()))
    conn.commit()
    left = _rows_naming(tid)
    assert "gate_settings" in left, (
        "the walk cannot see a row sitting in a tenant-scoped table")
    with pytest.raises(AssertionError):
        assert set(left) <= allowed
