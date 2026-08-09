"""Rows a wipe could not finish, and the command that finishes them.

The siblings gained this because their cascades used to run off hand-written
lists, so every erase before 0.59.9 left forty-odd tables standing. That is
not this product's history: `cascade()` has read the schema since before then,
and the residue those two are cleaning up was never created here.

The reason it belongs here anyway is the other one, and the record next door
is the third. A wipe is a loop over sixty-some tables, and the `tenants` row
is removed by the **caller** rather than by the cascade — deliberately,
because the retention sweep and the operator's wipe hold different locks on
it. Two callers, one of which runs on a schedule with nobody reading the
result. If either ever lands the tenant's removal and not the rest, nothing
in the running product will ever look at what is left.

    asked     does the wipe clear every table
    mattered  what is left when one did not finish

And: `guard_divergences.txt` records a guard carried by two products and
missing from the third, because a fix stops travelling exactly when somebody
decides the third product does not need this one. Deciding that about my own
port would have been the first thing that record was written to catch.

## What this file checks, and what it refuses to borrow

The planting reads the schema **here**, not through `vault.tenant_scoped_tables`,
for the reason 0.59.9's guard names: a test that asks the code under test
which tables to check plants rows only where that code already looks.

The sharp property is not "does it clear the orphans" — it is **"does it leave
a living tenant alone"**. A maintenance command that runs `DELETE` across
sixty-some tables on somebody else's vault has exactly one way to be
catastrophic, and it is checked below with a live tenant seeded beside the
stranded one.
"""

from __future__ import annotations

import pytest

from pdi import db, orphans, vault

from . import ratchets

from .test_an_erase_is_measured_against_the_schema import (
    SUBJECT, _plant, _scoped_from_the_schema)

#: Tables the cascade retires rather than deletes, so the sweep does too.
RETIRED = set(vault.WIPE_RETIRES)


def _tenant(client, name: str) -> str:
    made = client.post("/tenants", json={"name": name})
    assert made.status_code == 201, made.text
    return made.json()["id"]


def _strand(conn, subject: str) -> list[str]:
    """Plant rows for `subject` everywhere and remove only the tenant row.

    Which is the shape of an interrupted wipe: the identity gone, the data
    behind it not, and no route left that will ever ask about it.
    """
    planted = [t for t in _scoped_from_the_schema(conn)
               if t != "tenants" and _plant(conn, t, subject)]
    conn.execute("DELETE FROM tenants WHERE id=?", (subject,))
    conn.commit()
    return planted


def _deletable(planted) -> list[str]:
    return [t for t in planted if t not in vault.WIPE_KEEPS and t not in RETIRED]


def test_the_survey_finds_the_rows_a_gone_subject_left(client):
    subject = _tenant(client, "stranded")
    conn = db.connect()
    planted = _strand(conn, subject)
    assert len(planted) >= ratchets.floor("erase.tables_planted"), (
        f"only planted rows in {len(planted)} tables — the planter is failing "
        "and every assertion below would pass on almost nothing")

    found = orphans.survey()
    assert subject in found["subjects"]
    seen = {t.replace(" (retired)", "") for t in found["tables"]}
    missing = sorted(t for t in _deletable(planted) if t not in seen)
    assert not missing, (
        f"{len(missing)} table(s) hold rows for a tenant that no longer "
        "exists and the survey does not see them:\n    "
        + "\n    ".join(missing))


def test_a_survey_changes_nothing(client):
    """Dry is the default, and the default is the one nobody types."""
    subject = _tenant(client, "stranded")
    conn = db.connect()
    planted = _strand(conn, subject)

    orphans.survey()
    orphans.sweep()                       # no `apply` — still a read
    still = [t for t in planted
             if conn.execute(f"SELECT COUNT(*) FROM {t} WHERE {SUBJECT}=?",
                             (subject,)).fetchone()[0]]
    assert sorted(still) == sorted(planted), (
        "a survey deleted rows. The command a person runs to find out how bad "
        "it is must not be the command that changes it.")


def test_applying_clears_them(client):
    subject = _tenant(client, "stranded")
    conn = db.connect()
    planted = _strand(conn, subject)

    done = orphans.sweep(apply=True)
    assert done["applied"] is True
    left = [t for t in _deletable(planted)
            if conn.execute(f"SELECT COUNT(*) FROM {t} WHERE {SUBJECT}=?",
                            (subject,)).fetchone()[0]]
    assert not left, (
        f"{len(left)} table(s) survived the sweep:\n    "
        + "\n    ".join(sorted(left)))


def test_the_audit_chain_survives_the_sweep(client):
    """`audit` is in `WIPE_KEEPS` because the chain is the proof a wipe
    happened. A cleanup command that tidied it away would be erasing the
    evidence of the thing it is cleaning up after."""
    subject = _tenant(client, "stranded")
    conn = db.connect()
    assert _plant(conn, "audit", subject)
    conn.commit()
    before = conn.execute("SELECT COUNT(*) FROM audit WHERE tenant_id=?",
                          (subject,)).fetchone()[0]
    _strand(conn, subject)

    orphans.sweep(apply=True)
    after = conn.execute("SELECT COUNT(*) FROM audit WHERE tenant_id=?",
                         (subject,)).fetchone()[0]
    assert after >= before, (
        "the sweep cleared audit rows for a gone tenant. The chain is what a "
        "wipe is proved by; it is kept on purpose.")


def test_a_bequest_is_retired_rather_than_deleted(client):
    """The heir on the other side is holding a grant. Erasing the row makes
    their credential fail with silence; retiring it makes the same credential
    fail with *revoked*, which is the truth — and it is a decision an earlier
    round made deliberately, not one a cleanup command gets to overturn."""
    subject = _tenant(client, "stranded")
    conn = db.connect()
    assert _plant(conn, "bequests", subject)
    conn.execute("UPDATE bequests SET revoked_at=NULL, grant_hash='LIVE' "
                 "WHERE tenant_id=?", (subject,))
    conn.commit()
    _strand(conn, subject)

    orphans.sweep(apply=True)
    rows = conn.execute("SELECT revoked_at, grant_hash FROM bequests "
                        "WHERE tenant_id=?", (subject,)).fetchall()
    assert rows, "the sweep deleted a bequest the cascade would have retired"
    for revoked_at, grant_hash in rows:
        assert revoked_at, "the bequest was left live for a tenant that is gone"
        assert grant_hash is None, (
            "the bequest kept its live credential through the sweep")


def test_a_living_subject_is_not_touched(client):
    """The property that matters more than any of the above."""
    stranded = _tenant(client, "stranded")
    living = _tenant(client, "living")
    conn = db.connect()

    kept = [t for t in _scoped_from_the_schema(conn)
            if t != "tenants" and _plant(conn, t, living)]
    conn.commit()
    _strand(conn, stranded)
    assert len(kept) >= ratchets.floor("erase.tables_planted"), (
        "the living tenant was not seeded")

    orphans.sweep(apply=True)

    lost = [t for t in kept
            if not conn.execute(f"SELECT COUNT(*) FROM {t} WHERE {SUBJECT}=?",
                                (living,)).fetchone()[0]]
    assert not lost, (
        f"the sweep deleted {len(lost)} table(s) of data belonging to a "
        "tenant that still exists:\n    " + "\n    ".join(sorted(lost))
        + "\n  An orphan is a row whose subject is gone. Nothing else is.")
    assert conn.execute("SELECT COUNT(*) FROM tenants WHERE id=?",
                        (living,)).fetchone()[0] == 1


def test_a_row_with_no_subject_is_left_alone(client):
    """An empty `tenant_id` is not the residue of a wiped tenant. It is
    something else, and a command written for one problem does not get to
    decide about a different one."""
    conn = db.connect()
    # The first table that will take one: several carry constraints that
    # refuse an empty subject outright, which is its own kind of correct.
    table = next((t for t in _scoped_from_the_schema(conn)
                  if t != "tenants" and t not in vault.WIPE_KEEPS
                  and t not in RETIRED and _plant(conn, t, "")), None)
    assert table, "no scoped table accepts a row with an empty subject"
    conn.commit()
    before = conn.execute(
        f"SELECT COUNT(*) FROM {table} WHERE {SUBJECT}=''").fetchone()[0]
    assert before

    orphans.sweep(apply=True)
    after = conn.execute(
        f"SELECT COUNT(*) FROM {table} WHERE {SUBJECT}=''").fetchone()[0]
    assert after == before, (
        f"the sweep deleted {before - after} row(s) with no subject at all")


def test_a_healthy_deployment_reports_nothing(client):
    """And says so in a sentence, rather than printing an empty table."""
    _tenant(client, "living")
    found = orphans.survey()
    assert found["rows"] == 0 and found["tables"] == {}
    assert "Nothing stranded" in orphans._report(found)


def test_the_scope_is_the_cascades_and_not_a_second_list():
    """The structural half, which survives the next migration."""
    import inspect
    source = inspect.getsource(orphans)
    assert "vault.tenant_scoped_tables()" in source, (
        "the sweep no longer asks the cascade's reader which tables are in "
        "scope, so it has become a second list of the kind the cascade removed")
    assert "vault.WIPE_KEEPS" in source and "vault.WIPE_RETIRES" in source
    for table in vault.WIPE_KEEPS:
        assert table not in orphans._in_scope(), (
            f"{table} is kept from a wipe and is in the sweep's scope")


def test_the_command_line_is_dry_by_default(client, capsys):
    subject = _tenant(client, "stranded")
    conn = db.connect()
    planted = _deletable(_strand(conn, subject))

    assert orphans.main([]) == 0
    assert "Nothing was changed" in capsys.readouterr().out
    assert conn.execute(
        f"SELECT COUNT(*) FROM {planted[0]} WHERE {SUBJECT}=?",
        (subject,)).fetchone()[0]

    assert orphans.main(["--apply"]) == 0
    assert "Cleared" in capsys.readouterr().out

    assert orphans.main(["--wipe-everything"]) == 2
