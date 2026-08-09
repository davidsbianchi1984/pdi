"""An export is measured against the schema too — and drops the credentials.

0.59.9 derived the **erase** from the schema in all three products. The export
is the same question turned round, and this product's answer to it was
`/snapshot`: records, ciphertext only, existing to be restored.

## What it was

`export_snapshot` is honest about what it is — a disaster-recovery export, and
`restore_records` reads its shape, so it is not the place to answer *what do
you hold about us*. Nothing else answered it. A tenant could not see their
hosting history, their bequests, their beacons, or the paperwork on file, and
those describe them.

Next door the same question had worse answers: QRME's export said *access
everything* and returned six tables of sixty-six, and JIM-mini had no export
at all while holding a medicine cabinet and a money guardian's mandates.

    asked     can a tenant delete everything we hold
    mattered  can a tenant see everything we hold

## Two properties, and the second is not the first

An export must be **complete** and must **not hand back a live credential**.
The honest resolution is per column: a bequest row is the estate record and
belongs to the tenant, and the `grant_hash` beside it is the credential an
heir is holding. `ciphertext` is redacted here for a different reason — the
sealed bytes belong in the snapshot, which exists to be restored.

The redaction is a **rule** rather than a list. The first cut was a list of
exact column names and the sibling's guard caught it on its first run: three
credential columns in tables the export reaches, none of them in the list.

## How this checks it

The same way the erase guard does — plant a row in every scoped table, ask for
the export, and look.
"""

from __future__ import annotations

import ast
import inspect
import textwrap

import pytest

from pdi import db, vault

from . import ratchets
from .test_an_erase_is_measured_against_the_schema import (
    SUBJECT, _columns, _plant, _scoped_from_the_schema)


def _tenant(client) -> dict:
    made = client.post("/tenants", json={"name": "export-probe"})
    assert made.status_code == 201, made.text
    return made.json()


def test_the_export_reaches_every_table_the_schema_scopes(client):
    """The completeness half."""
    conn = db.connect()
    subject = _tenant(client)["id"]
    planted = [t for t in _scoped_from_the_schema(conn)
               if t != "tenants" and _plant(conn, t, subject)]
    conn.commit()
    assert len(planted) >= ratchets.floor("erase.tables_planted"), (
        f"only planted rows in {len(planted)} tables — the planter is failing "
        "and the check below would pass on almost nothing")

    bundle = vault.export_everything(subject)
    missing = sorted(t for t in planted if t not in bundle["tables"])
    assert not missing, (
        f"{len(missing)} table(s) hold rows for this person and are not in "
        "their export:\n    " + "\n    ".join(missing)
        + "\n  *Everything we hold* is a claim about the schema. Derive the "
          "export from it, as the erase cascade does.")


def test_the_export_carries_no_live_credential(client):
    """The half that is not completeness.

    Checked against the rows that come back rather than against the redaction
    tuple: a tuple is a list of names somebody wrote, and this file exists
    because lists of names go stale.
    """
    conn = db.connect()
    subject = _tenant(client)["id"]
    for table in _scoped_from_the_schema(conn):
        if table != "users":
            _plant(conn, table, subject)
    conn.commit()

    leaked = []
    for table, rows in vault.export_everything(subject)["tables"].items():
        for row in rows:
            for column in row:
                # The same marks the redaction rule uses, and deliberately
                # not the bare word `hash`: this product's audit chain is
                # hash-linked, and `hash`/`prev_hash` are the record a tenant
                # needs in order to verify their own export. A credential is
                # what somebody can present; a chain link is not.
                if any(mark in column.lower() for mark in
                       ("token", "secret", "password", "api_key",
                        "private_key", "grant_hash", "check_value")):
                    leaked.append(f"{table}.{column}")
    assert not leaked, (
        "the export hands back live credentials:\n    "
        + "\n    ".join(sorted(set(leaked)))
        + "\n  A bundle is downloaded, mailed and copied. Carry the row and "
          "drop the column.")


def test_the_export_is_not_a_hand_written_list():
    """The structural half, which survives the next migration."""
    source = inspect.getsource(vault.export_everything)
    tree = ast.parse(textwrap.dedent(source))
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Tuple, ast.List)):
            continue
        words = [e.value for e in node.elts
                 if isinstance(e, ast.Constant) and isinstance(e.value, str)]
        assert len(words) < 5, (
            f"the export carries a list of {len(words)} table names "
            f"({words[:4]}…). Read the schema instead.")
    assert "tenant_scoped_tables" in source, (
        "export_everything no longer asks the schema what this tenant has")


def test_the_export_and_the_erase_reach_the_same_tables(client):
    """The symmetry, asserted rather than assumed.

    A table the erase clears and the export omits is a person who can delete
    something they were never shown. A table the export carries and the erase
    misses is the defect 0.59.9 was about. Both are one comparison.
    """
    conn = db.connect()
    subject = _tenant(client)["id"]
    planted = {t for t in _scoped_from_the_schema(conn)
               if t != "tenants" and _plant(conn, t, subject)}
    conn.commit()
    shown = set(vault.export_everything(subject)["tables"]) & planted
    # The third category, which only this product has. `audit` survives a
    # wipe because it is the proof the wipe happened, and `bequests` is
    # retired rather than deleted so an heir's credential fails with
    # *revoked* instead of silence. Both are still the tenant's to read, so
    # the export carries them and the erase does not clear them — the one
    # place where these two answers differ on purpose.
    planted -= (set(vault.WIPE_KEEPS) | set(vault.WIPE_RETIRES))
    shown &= planted
    vault.delete_tenant(subject, "wipe")
    left = {t for t in planted
            if conn.execute(f"SELECT COUNT(*) FROM {t} WHERE {SUBJECT}=?",
                            (subject,)).fetchone()[0]}
    cleared = planted - left
    assert shown == cleared, (
        "the export and the erase disagree about this person's data:\n"
        f"    shown but not cleared: {sorted(shown - cleared)}\n"
        f"    cleared but not shown: {sorted(cleared - shown)}")


def test_the_route_is_reachable_and_owner_only(client):
    """A person's own bundle, and nobody else's."""
    mine = _tenant(client)
    theirs = _tenant(client)
    ok = {"authorization": f"Bearer {mine['token']}"}
    mine_body = client.get("/export", headers=ok)
    assert mine_body.status_code == 200, mine_body.text
    assert mine_body.json()["tenant"]["id"] == mine["id"]
    assert client.get("/export", headers={}).status_code == 401
    # The route is scoped by the bearer, so a second tenant's bundle is
    # simply not reachable from this one — it names no id to ask for.
    theirs_body = client.get(
        "/export", headers={"authorization": f"Bearer {theirs['token']}"})
    assert theirs_body.json()["tenant"]["id"] == theirs["id"]
