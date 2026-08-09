"""Rows a wipe could not finish, for deployments that ran one.

The siblings gained this command because their cascades used to run off
hand-written lists, so every erase before 0.59.9 left forty-odd tables
standing. That is not this product's history — `cascade()` has read the
schema since before then, and the class of residue those two are cleaning up
was never created here.

So the honest reason this file exists is the other one. A wipe is a loop over
sixty-some tables inside one transaction, and the `tenants` row is deleted by
the caller rather than by the cascade — deliberately, because the retention
sweep and the operator's wipe hold different locks on it. Two callers, one of
which *runs on a schedule with nobody reading the result*. If either ever
lands the tenant's removal and not the rest, nothing in the running product
will look at what is left: the tenant is gone, so every route 404s, so no
code path visits those rows.

    asked     does the wipe clear every table
    mattered  what is left when one did not finish

Porting it here is also the record's own rule applied to me. A guard that
lands in two of three products is a divergence, and the reason that record
exists is that fixes stop travelling exactly when somebody decides the third
product does not need this one.

## What it will and will not touch

The scope is exactly what :func:`vault.cascade` clears —
`vault.tenant_scoped_tables()` minus `vault.WIPE_KEEPS`. `audit` is kept for
the reason it is always kept: the chain is the proof a wipe happened, and a
sweep that tidied it away would be erasing the evidence of the thing it is
cleaning up after.

`WIPE_RETIRES` is the interesting case and it is handled the way the cascade
handles it. A `bequests` row for a gone tenant is **retired, not deleted** —
somebody on the other side is holding a grant, and erasing the row makes
their credential fail with silence where retiring it makes the same
credential fail with *revoked*, which is the truth.

A row is an orphan only when its `tenant_id` names a tenant that is **not in
`tenants`**. Rows with a NULL or empty subject are left alone.

## Dry by default

`survey()` reads. `sweep(apply=True)` writes, and nothing calls it without
that argument::

    python -m pdi.orphans              # count them, change nothing
    python -m pdi.orphans --apply      # clear them
    python -m pdi.orphans --json       # the same survey, machine-readable
"""

from __future__ import annotations

import json
import sys

from . import db, vault

#: The identity table. A `tenant_id` naming no row here belongs to nobody.
LIVING = "tenants"


def _in_scope() -> list[str]:
    """The tables the cascade reaches."""
    return [t for t in vault.tenant_scoped_tables()
            if t not in vault.WIPE_KEEPS and t != LIVING]


def survey() -> dict:
    """Count rows belonging to tenants this deployment no longer has.

    Returns ``{"rows": int, "tables": {name: count}, "subjects": [id, ...]}``.
    A retired-but-unfinished bequest is counted under its own name, so the
    report does not promise a deletion the sweep will not perform.
    """
    conn = db.connect()
    living = {r[0] for r in conn.execute(f"SELECT id FROM {LIVING}").fetchall()}
    tables: dict[str, int] = {}
    subjects: set[str] = set()

    for table in _in_scope():
        rows = conn.execute(
            f"SELECT tenant_id, COUNT(*) FROM {table} "
            "WHERE tenant_id IS NOT NULL AND tenant_id != '' "
            "GROUP BY tenant_id").fetchall()
        stranded = [(tid, n) for tid, n in rows if tid not in living]
        if stranded:
            name = f"{table} (retired)" if table in vault.WIPE_RETIRES else table
            tables[name] = sum(n for _, n in stranded)
            subjects.update(tid for tid, _ in stranded)

    return {"rows": sum(tables.values()), "tables": tables,
            "subjects": sorted(subjects)}


def sweep(apply: bool = False) -> dict:
    """Survey, and — only when asked — finish what the wipe did not.

    Each statement repeats the survey's own predicate rather than working
    from the ids it collected: between the two, a row could have been written
    for a tenant that has since been created, and `NOT IN (SELECT id FROM
    tenants)` is true of exactly the rows that are still stranded when it
    runs.
    """
    found = survey()
    found["applied"] = bool(apply)
    if not apply or not found["rows"]:
        return found

    conn = db.connect()
    stale = (f"tenant_id IS NOT NULL AND tenant_id != '' "
             f"AND tenant_id NOT IN (SELECT id FROM {LIVING})")
    for table in _in_scope():
        if table in vault.WIPE_RETIRES:
            # The cascade's own SET clause with this command's WHERE. Retiring
            # rather than deleting is a decision an earlier round made about
            # what an heir presenting a grant should be told — *revoked*, not
            # silence — and a cleanup command is not the place to overturn it.
            # Borrowing the clause rather than restating it keeps the two in
            # step the same way the scope does.
            head = vault.WIPE_RETIRES[table].split(" WHERE ", 1)[0]
            conn.execute(f"{head} WHERE {stale} AND revoked_at IS NULL",
                         (db.utcnow(),))
            continue
        conn.execute(f"DELETE FROM {table} WHERE {stale}")
    conn.commit()
    return found


def _report(found: dict) -> str:
    if not found["rows"]:
        return ("Nothing stranded: every tenant-scoped row belongs to a "
                "tenant this deployment still has.")
    verb = "Cleared" if found.get("applied") else "Found"
    lines = [f"{verb} {found['rows']} row(s) across {len(found['tables'])} "
             f"table(s), belonging to {len(found['subjects'])} tenant(s) "
             "that no longer exist:"]
    for table, n in sorted(found["tables"].items(), key=lambda kv: -kv[1]):
        lines.append(f"    {n:>7}  {table}")
    if not found.get("applied"):
        lines.append("")
        lines.append("Nothing was changed. Re-run with --apply to clear them.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    unknown = [a for a in argv if a not in ("--apply", "--json")]
    if unknown:
        print(f"unknown argument(s): {' '.join(unknown)}\n"
              "usage: python -m pdi.orphans [--apply] [--json]",
              file=sys.stderr)
        return 2
    found = sweep(apply="--apply" in argv)
    print(json.dumps(found, indent=2) if "--json" in argv else _report(found))
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())
