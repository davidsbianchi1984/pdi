"""An erase is measured against the schema, not against a list somebody wrote.

## Where this came from

This product already does it right, and 0.59.9 is the round that found out
why that mattered. Its siblings each carried a hand-written list of tables in
their erase handler — JIM-mini named twenty-one against a schema of
sixty-three, QRME twenty-four against sixty-six — so an operation advertised
as *every trace* left forty-odd tables standing in both, including a medicine
cabinet, a set of clinical photographs, and standing permissions that let
those products go on acting for somebody who had asked to be forgotten.

The fix was here already, and its docstring already said the general thing:
*a migration that adds a table is covered by writing it, not by remembering
this function.* It had never been written down as a **test**, so nothing
carried it next door.

    asked     did we delete what the handler names
    mattered  did we delete what the schema holds

## What this adds here

The cascade was correct and unguarded. This plants a row in every
tenant-scoped table, wipes, and looks — so a table added by a migration that
somehow escapes the cascade is named on the next run rather than the next
audit.

`WIPE_RETIRES` is exempt from the row count on purpose: a retired bequest is
a row that *should* survive with its credential cleared, and
`test_a_wipe_retires_the_bequest_itself` is what holds it to that.

## The test does not borrow the reader it is checking

The first cut planted rows in the cascade's own table reader. Narrowing the
cascade narrowed the planting with it, so an injected hand-written list
produced *a blind reader* rather than *forty surviving tables*. It reads the
schema itself now.
"""

from __future__ import annotations

import ast
import inspect
import textwrap
from pathlib import Path

import pytest

from . import ratchets

from pdi import db, vault

#: The column that names the subject, per table shape.
SUBJECT = "tenant_id"


def _columns(conn, table: str) -> list[tuple]:
    return list(conn.execute(f"PRAGMA table_info({table})"))


def _filler(kind: str):
    kind = (kind or "").upper()
    if "INT" in kind:
        return 0
    if any(k in kind for k in ("REAL", "FLOA", "DOUB", "NUM", "DEC")):
        return 0.0
    if "BLOB" in kind:
        return b""
    return ""


def _plant(conn, table: str, subject: str) -> bool:
    """Put one row naming `subject` into `table`. False if it will not take."""
    names, values = [], []
    for cid, name, kind, notnull, default, pk in _columns(conn, table):
        if name == SUBJECT:
            names.append(name)
            values.append(subject)
        elif name == "id":
            names.append(name)
            values.append(f"erase-probe-{table}")
        elif notnull and default is None and not pk:
            names.append(name)
            values.append(_filler(kind))
    marks = ",".join("?" for _ in names)
    try:
        conn.execute(f"INSERT INTO {table} ({','.join(names)}) VALUES ({marks})",
                     values)
        return True
    except Exception:
        return False


def plantable() -> int:
    """How many scoped tables will take a probe row.

    Registered as a floor of its own: the planter is the half of this file
    that can go quiet without the sweep noticing — every insert failing looks
    exactly like a schema with nothing in it.
    """
    conn = db.connect()
    return sum(1 for t in _scoped_from_the_schema(conn)
               if _plant(conn, t, "erase-probe-count"))


def scoped_tables() -> list[str]:
    """The registry's reader: this file's own view of the schema."""
    return _scoped_from_the_schema(db.connect())


def _scoped_from_the_schema(conn) -> list[str]:
    """The tables this test will plant in — read here, not borrowed.

    Deliberately not `vault.tenant_scoped_tables()`. A test that asks the code
    under test which tables to check plants rows only where that code already
    looks, so narrowing the cascade narrows the test with it and the run stays
    green. Found by injecting the old hand-written list: the check reported a
    blind *reader* rather than forty-three surviving tables.
    """
    out = []
    for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%'").fetchall():
        if SUBJECT in {c[1] for c in _columns(conn, row[0])}:
            out.append(row[0])
    return sorted(out)


def test_the_erase_reaches_every_table_the_schema_scopes(client):
    """The whole check, and it needs no feature to be wired to find a gap."""
    # A real tenant, not an invented id: `delete_tenant` looks the row up
    # first and answers None for a tenant that was never there, so a probe
    # with a made-up id measures nothing and says every table survived.
    made = client.post("/tenants", json={"name": "erase-probe"})
    assert made.status_code == 201, made.text
    subject = made.json()["id"]
    conn = db.connect()
    planted = [t for t in _scoped_from_the_schema(conn)
               if _plant(conn, t, subject)]
    conn.commit()
    assert len(planted) >= ratchets.floor("erase.tables_planted"), (
        f"only planted rows in {len(planted)} tables — the planter is failing "
        "on this schema and the check below would pass on almost nothing")

    vault.delete_tenant(subject, "wipe")

    left = []
    for table in planted:
        n = conn.execute(
            f"SELECT COUNT(*) FROM {table} WHERE {SUBJECT}=?", (subject,)
        ).fetchone()[0]
        if n and table not in (vault.WIPE_KEEPS | set(vault.WIPE_RETIRES)):
            left.append(table)
    assert not left, (
        f"{len(left)} table(s) still hold rows for a user who asked to be "
        "forgotten:\n    " + "\n    ".join(sorted(left))
        + "\n  The handler says *every trace*. Derive the cascade from the "
          "schema, or put the table in ERASE_KEEPS with the reason.")


def test_the_cascade_is_not_a_hand_written_list():
    """The structural half.

    A behavioural check passes the moment the list is long enough *today*,
    and says nothing about the table added next week. This is the part that
    survives the next migration.
    """
    # `cascade` rather than `delete_tenant`: this product split the two, and
    # the cascade is where the tables are chosen. The siblings have one
    # function doing both, which is why the ported check names theirs.
    source = inspect.getsource(vault.cascade)
    # `cleandoc` normalises a docstring, not a function body — it strips the
    # `def` line's indentation and leaves the rest, which does not parse.
    tree = ast.parse(textwrap.dedent(source))
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Tuple, ast.List)):
            continue
        words = [e.value for e in node.elts
                 if isinstance(e, ast.Constant) and isinstance(e.value, str)]
        assert len(words) < 5, (
            f"the cascade carries a list of {len(words)} table names "
            f"({words[:4]}…). Every list of this shape in the estate has gone "
            "stale; read the schema instead.")
    assert "tenant_scoped_tables" in source, (
        "the cascade no longer asks the schema which tables to clear")


def test_the_scoped_reader_sees_the_whole_schema(client):
    """A reader that goes blind reports an erase with nothing left to do."""
    conn = db.connect()
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%'").fetchall()]
    scoped = vault.tenant_scoped_tables()
    assert len(scoped) >= ratchets.floor("erase.scoped_tables"), (
        f"{len(scoped)} scoped tables out of {len(tables)} — the schema "
        "reader has stopped matching, and an empty cascade deletes nothing "
        "while reporting success")
    assert set(scoped) <= set(tables)


def test_what_is_kept_is_named_and_reasoned():
    """`ERASE_KEEPS` is the only way a table survives, so it is the only place
    a promise is broken. Empty today; a row in it is a deliberate edit that a
    reader can see and argue with."""
    assert isinstance((vault.WIPE_KEEPS | set(vault.WIPE_RETIRES)), frozenset)
    for table in (vault.WIPE_KEEPS | set(vault.WIPE_RETIRES)):
        assert table in vault.tenant_scoped_tables(), (
            f"{table!r} is kept from an erase and is not in the schema")


def test_a_retired_table_is_the_only_row_that_survives():
    """Three categories, and the third is the interesting one.

    Deleting a bequest row makes an heir's credential fail with silence,
    which reads as a bug; retiring it makes the same credential fail with
    *revoked*, which is the truth. Every retired table must still be a table
    the schema scopes, or the map has gone stale.
    """
    for table in vault.WIPE_RETIRES:
        assert table in vault.tenant_scoped_tables(), (
            f"{table!r} is retired by a wipe and is not tenant-scoped")
    assert not (vault.WIPE_KEEPS & set(vault.WIPE_RETIRES)), (
        "a table cannot be both kept whole and retired")
