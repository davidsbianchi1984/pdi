"""A tenant's row is reached through its tenant, in the SQL itself.

## The finding

The schema has carried ``tenant_id`` on twenty tables since multi-tenancy
arrived, and the description of the product has always said tenants are
isolated. The enforcement was thinner than the description: **46 statements
read, wrote or deleted rows on those tables keyed by bare ``id``**, trusting
that the id in hand had been fetched tenant-scoped a few lines earlier —
usually by a route helper that fetched the row unscoped and compared
``row["tenant_id"]`` in Python afterward.

That pattern is correct on the day it is written and one refactor away from
not being: a new caller reaches ``connectors.get(cid)`` without the helper, a
counter bump lands on whatever row the id names, a revoke revokes across the
fence. One of the 46 was already past "one refactor away":
``beacons.place`` looked up the transfer or intake a beacon was being
printed for by bare id and then checked the tenant — the check held, but the
unscoped fetch was the only thing between a tenant and printing custody
beacons onto another tenant's transfers.

    asked     is every row's tenant checked
    mattered  can the statement return another tenant's row at all

## The rule

Every statement that touches a tenant-scoped table now constrains
``tenant_id`` **in the SQL**, so the statement cannot return, change or
delete another tenant's row for a Python check to forget. The ten that
genuinely cannot be scoped — a bearer secret is the credential (receive,
submit and grant tokens), the surface is public by design (a printed beacon
code), the caller is the deployment admin, or the statement walks the
deployment-wide audit chain — wear an inline
``# tenant-unscoped: <reason>`` marker at the execute() site and are
recorded, with their reasons, in ``tenant_unscoped.txt``. The record has a
ceiling, so the list only grows on purpose.

The live tests underneath drive the fence from the outside: two tenants,
and every by-id door tried with the other tenant's id, expecting the same
answer a nonexistent id gets — because "not yours" and "not there" must be
one answer, or the ids themselves leak what exists.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from .conftest import auth, new_tenant
from .ratchets import floor

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
RECORD = HERE / "tenant_unscoped.txt"

DML = re.compile(r"^\s*(SELECT|INSERT|UPDATE|DELETE|REPLACE)\b", re.I)


def _tenant_tables() -> set[str]:
    """Read from the live schema, for the reason `tenant_scoped_tables`
    gives: a hand-kept list stops being complete at the next migration."""
    schema = (PKG / "db.py").read_text(encoding="utf-8")
    return {m.group(1)
            for m in re.finditer(r"CREATE TABLE IF NOT EXISTS (\w+)\s*\((.*?)\);",
                                 schema, re.S)
            if "tenant_id" in m.group(2)}


def _literal_sql(node: ast.expr) -> str | None:
    """The SQL a call's first argument evaluates to, when it is built from
    literals — constants, implicit and ``+`` concatenation, f-strings.

    An f-string's interpolations become ``{X}``: what matters here is the
    WHERE clause's columns, which are always written as text.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(str(v.value) if isinstance(v, ast.Constant) else "{X}"
                       for v in node.values)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        a, b = _literal_sql(node.left), _literal_sql(node.right)
        if a is not None and b is not None:
            return a + b
    return None


def _branches(node: ast.expr) -> list[str | None]:
    """Every literal the expression can evaluate to. A conditional tail —
    ``base + (" AND x" if flag else "")`` — is two statements, and both
    must pass; collapsing them to one string would let an unscoped branch
    hide behind a scoped one."""
    if isinstance(node, ast.IfExp):
        return _branches(node.body) + _branches(node.orelse)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        out: list[str | None] = []
        for left in _branches(node.left):
            for right in _branches(node.right):
                out.append(None if left is None or right is None
                           else left + right)
        return out
    return [_literal_sql(node)]


def _findings() -> tuple[list[str], list[str]]:
    """(violations, markers) across every module in the package.

    A violation is a DML statement on a tenant table with no ``tenant_id``
    in its text and no marker; a marker row is ``<file> :: <reason>``,
    which is what the record holds.
    """
    tables = _tenant_tables()
    violations: list[str] = []
    markers: list[str] = []
    for path in sorted(PKG.glob("*.py")):
        src = path.read_text(encoding="utf-8")
        lines = src.splitlines()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr in ("execute", "executemany")
                    and node.args):
                continue
            reason = None
            for i in range(max(0, node.lineno - 2),
                           min(len(lines), node.lineno + 1)):
                if "# tenant-unscoped:" in lines[i]:
                    reason = lines[i].split("# tenant-unscoped:", 1)[1].strip()
            for sql in _branches(node.args[0]):
                if sql is None:
                    # Non-literal SQL (a name, a dict lookup) cannot be read
                    # here, so it must carry the marker saying why it is safe.
                    if reason is None:
                        violations.append(
                            f"{path.name}:{node.lineno} — SQL is not a "
                            "literal and wears no tenant-unscoped marker")
                    break
                flat = " ".join(sql.split())
                if not DML.match(flat):
                    continue
                if not any(re.search(rf"\b{t}\b", flat) for t in tables):
                    continue
                if "tenant_id" in flat:
                    continue
                if reason is None:
                    violations.append(f"{path.name}:{node.lineno} — {flat[:120]}")
            if reason is not None:
                markers.append(f"{path.name} :: {reason}")
    return violations, markers


def _recorded() -> list[str]:
    return [line.strip() for line in RECORD.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")]


# -- the rule ----------------------------------------------------------------

def test_every_tenant_rows_reach_is_scoped_or_named():
    """The defect class, closed in both shapes: a bare ``WHERE id=?`` on a
    tenant table, and SQL this file cannot read at all."""
    violations, _ = _findings()
    assert not violations, (
        f"{len(violations)} statement(s) touch a tenant-scoped table without "
        "constraining tenant_id in the SQL and without a written reason:\n    "
        + "\n    ".join(violations)
        + "\n  Scope the statement (WHERE ... AND tenant_id=?), or — only if "
          "a bearer secret, a public surface or the audit chain genuinely "
          "replaces the scope — mark it `# tenant-unscoped: <reason>` and "
          "record it in tenant_unscoped.txt.")


def test_the_unscoped_list_matches_the_record():
    """Both directions, so the record can neither rot nor understate."""
    _, markers = _findings()
    measured, recorded = sorted(markers), sorted(_recorded())
    new = [m for m in measured if m not in recorded]
    stale = [r for r in recorded if r not in measured]
    problems = []
    if new:
        problems.append("marker(s) not in tenant_unscoped.txt:\n    "
                        + "\n    ".join(new))
    if stale:
        problems.append("recorded row(s) whose marker is gone — strike them:"
                        "\n    " + "\n    ".join(stale))
    assert not problems, "\n\n".join(problems)


def test_the_scan_is_reading_statements_at_all():
    """A guard on the guard: a parser that stopped matching would report a
    package in perfect order by finding nothing. The package holds over a
    hundred statements on tenant tables; sixty is far below any honest
    count and far above a broken parse."""
    tables = _tenant_tables()
    assert len(tables) >= floor("tenant.scoped_tables_read"), (
        f"only {len(tables)} tenant tables parsed")
    count = 0
    for path in sorted(PKG.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr in ("execute", "executemany")
                    and node.args):
                for sql in _branches(node.args[0]):
                    if sql and any(re.search(rf"\b{t}\b", sql) for t in tables):
                        count += 1
                        break
    assert count >= floor("tenant.statements_scanned"), (
        f"only {count} statements on tenant tables were parsed — the checks "
        "above would pass on almost nothing")


# -- the fence, driven from outside ------------------------------------------

def _mine_and_theirs(client):
    return new_tenant(client, "mine"), new_tenant(client, "theirs")


def test_another_tenants_record_is_not_there(client):
    mine, theirs = _mine_and_theirs(client)
    put = client.put("/records", json={"key": "diary", "value": "mine alone"},
                     headers=auth(mine))
    assert put.status_code in (200, 201), put.text
    assert client.get("/records/diary",
                      headers=auth(theirs)).status_code == 404
    gone = client.delete("/records/diary", headers=auth(theirs))
    assert gone.status_code == 404
    still = client.get("/records/diary", headers=auth(mine))
    assert still.status_code == 200
    assert still.json()["value"] == "mine alone"


def test_another_tenants_connector_cannot_be_seen_or_revoked(client):
    mine, theirs = _mine_and_theirs(client)
    made = client.post("/connectors", json={
        "platform": "instagram", "direction": "collect",
        "scope": ["posts"]}, headers=auth(mine))
    assert made.status_code == 201, made.text
    cid = made.json()["id"]
    assert client.get(f"/connectors/{cid}/beacon",
                      headers=auth(theirs)).status_code == 404
    assert client.delete(f"/connectors/{cid}",
                         headers=auth(theirs)).status_code == 404
    assert all(c["id"] != cid
               for c in client.get("/connectors",
                                   headers=auth(theirs)).json())
    kept = [c for c in client.get("/connectors", headers=auth(mine)).json()
            if c["id"] == cid]
    assert kept and kept[0]["status"] == "active"


def test_another_tenants_transfer_is_not_reachable(client):
    mine, theirs = _mine_and_theirs(client)
    made = client.post("/transfers", json={
        "recipient": "auditor@example.com", "filename": "q3.pdf",
        "content": "the figures", "programs": []}, headers=auth(mine))
    assert made.status_code == 201, made.text
    tid = made.json()["id"]
    for verb, path in (("get", f"/transfers/{tid}"),
                       ("get", f"/transfers/{tid}/custody"),
                       ("delete", f"/transfers/{tid}")):
        r = getattr(client, verb)(path, headers=auth(theirs))
        assert r.status_code == 404, (verb, path, r.status_code)
    kept = client.get(f"/transfers/{tid}", headers=auth(mine))
    assert kept.status_code == 200
    assert kept.json()["status"] != "revoked"


def test_another_tenants_intake_is_not_reachable(client):
    mine, theirs = _mine_and_theirs(client)
    made = client.post("/intakes", json={
        "from_party": "Dr. Reyes", "party_type": "partner",
        "purpose": "referral file", "programs": []}, headers=auth(mine))
    assert made.status_code == 201, made.text
    iid = made.json()["id"]
    assert client.get(f"/intakes/{iid}",
                      headers=auth(theirs)).status_code == 404
    assert client.delete(f"/intakes/{iid}",
                         headers=auth(theirs)).status_code == 404
    assert client.get(f"/intakes/{iid}",
                      headers=auth(mine)).json()["status"] == "open"


def test_another_tenants_beacon_and_its_reference_stay_theirs(client):
    """Two fences on one screen: the beacon door itself, and the reference
    check inside `place` — the one that was a Python comparison behind an
    unscoped fetch, and is now scope in the SQL."""
    mine, theirs = _mine_and_theirs(client)
    made = client.post("/transfers", json={
        "recipient": "auditor@example.com", "filename": "q3.pdf",
        "content": "the figures", "programs": []}, headers=auth(mine))
    tid = made.json()["id"]
    # Printing a custody beacon onto the other tenant's transfer: refused
    # as "no such transfer", not as "not yours" — the id must not leak that
    # it exists.
    printed = client.post("/beacons", json={
        "ref_kind": "transfer", "ref_id": tid, "label": "crate 7"},
        headers=auth(theirs))
    assert printed.status_code in (404, 409, 422), printed.text
    assert "transfer" in printed.text

    ours = client.post("/beacons", json={
        "ref_kind": "transfer", "ref_id": tid, "label": "crate 7"},
        headers=auth(mine))
    assert ours.status_code == 201, ours.text
    bid = ours.json()["id"]
    assert client.get(f"/beacons/{bid}",
                      headers=auth(theirs)).status_code == 404
    assert client.delete(f"/beacons/{bid}",
                         headers=auth(theirs)).status_code == 404
    assert client.get(f"/beacons/{bid}",
                      headers=auth(mine)).status_code == 200


def test_another_tenants_audit_trail_is_not_in_the_answer(client):
    mine, theirs = _mine_and_theirs(client)
    client.put("/records/diary", json={"value": "x"}, headers=auth(mine))
    lines = client.get("/audit", headers=auth(theirs))
    assert lines.status_code == 200
    spilled = [e for e in lines.json() if e.get("ref") == "diary"]
    assert not spilled, "one tenant's audit answer carries another's writes"


def test_not_yours_and_not_there_are_one_answer(client):
    """The refusal must not say which of the two it is. A 404 for a made-up
    id and a 404 for a real, foreign id have to be indistinguishable, or
    guessing ids becomes a way to map another tenant's shelf."""
    mine, theirs = _mine_and_theirs(client)
    made = client.post("/intakes", json={
        "from_party": "Dr. Reyes", "party_type": "partner",
        "purpose": "referral file", "programs": []}, headers=auth(mine))
    real = client.get(f"/intakes/{made.json()['id']}", headers=auth(theirs))
    fake = client.get("/intakes/itk_never_was", headers=auth(theirs))
    assert real.status_code == fake.status_code == 404
    assert real.json() == fake.json()
