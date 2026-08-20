"""The runs ledger cannot edit its own account.

Raised by the outside reviewer: the ledger that answers "what did the
vault do while you slept" was a mutable table — anything that could
write the database could rewrite the past it reports. Now the database
itself refuses edits, each row chains to the task's previous cycle, a
verify door walks the links, and every cycle anchors its hash on the
permanent audit chain.

    asked     can the ledger's past be quietly rewritten
    mattered  a ledger that can edit its own account is a diary in pencil
"""

import sqlite3

import pytest

from pdi import db, resident

from .conftest import auth, new_tenant


def _standing(client, token, monkeypatch, text="all quiet"):
    page = {"text": text}
    monkeypatch.setattr(resident, "_fetch_text", lambda url: page["text"])
    body = client.post("/resident/tasks", json={
        "goal": "keep an eye on the page",
        "every_hours": 1.0,
        "steps": [{"tool": "fetch.url",
                   "args": {"url": "https://example.com/menu"}}],
    }, headers=auth(token)).json()
    return body["id"], page


def _cycle(task_id):
    conn = db.connect()
    conn.execute("UPDATE resident_tasks SET"
                 " next_run_at='2000-01-01T00:00:00+00:00' WHERE id=?",
                 (task_id,))
    conn.commit()
    assert resident.pulse()["ran"] == 1


def test_the_database_itself_refuses_an_edit(client, monkeypatch):
    """Not a code-review promise — a trigger. UPDATE on the ledger aborts
    with the rule in its own words, whoever holds the connection."""
    token = new_tenant(client)
    task_id, _ = _standing(client, token, monkeypatch)
    _cycle(task_id)
    with pytest.raises(sqlite3.DatabaseError) as caught:
        db.connect().execute(
            "UPDATE resident_runs SET status='done', note='all fine'")
    assert "does not edit its own account" in str(caught.value)


def test_an_untouched_ledger_verifies_intact(client, monkeypatch):
    token = new_tenant(client)
    task_id, page = _standing(client, token, monkeypatch)
    for i in range(3):
        page["text"] = f"cycle {i}"
        _cycle(task_id)
    out = client.get(f"/resident/tasks/{task_id}/runs/verify",
                     headers=auth(token)).json()
    assert out["intact"] is True
    assert out["entries"] == 3 and out["predate_chain"] == 0


def test_a_forged_row_breaks_the_chain(client, monkeypatch):
    """UPDATE is refused, so the tamper that remains is delete-and-forge —
    and the forged row cannot mint the hash its neighbors expect."""
    token = new_tenant(client)
    task_id, _ = _standing(client, token, monkeypatch)
    _cycle(task_id)
    _cycle(task_id)
    conn = db.connect()
    row = conn.execute(
        "SELECT * FROM resident_runs WHERE task_id=?"
        " ORDER BY ran_at DESC, rowid DESC LIMIT 1", (task_id,)).fetchone()
    conn.execute("DELETE FROM resident_runs WHERE id=?", (row["id"],))
    conn.execute(
        "INSERT INTO resident_runs (id, tenant_id, task_id, ran_at, status,"
        " note, prev_hash, hash) VALUES (?,?,?,?,?,?,?,?)",
        (row["id"], row["tenant_id"], row["task_id"], row["ran_at"],
         "done", "nothing went wrong here", row["prev_hash"], row["hash"]))
    conn.commit()
    out = client.get(f"/resident/tasks/{task_id}/runs/verify",
                     headers=auth(token)).json()
    assert out["intact"] is False


def test_a_deleted_middle_breaks_the_links(client, monkeypatch):
    token = new_tenant(client)
    task_id, page = _standing(client, token, monkeypatch)
    for i in range(3):
        page["text"] = f"cycle {i}"
        _cycle(task_id)
    conn = db.connect()
    middle = conn.execute(
        "SELECT id FROM resident_runs WHERE task_id=?"
        " ORDER BY ran_at ASC, rowid ASC LIMIT 1 OFFSET 1",
        (task_id,)).fetchone()
    conn.execute("DELETE FROM resident_runs WHERE id=?", (middle["id"],))
    conn.commit()
    out = client.get(f"/resident/tasks/{task_id}/runs/verify",
                     headers=auth(token)).json()
    assert out["intact"] is False


def test_the_trim_window_does_not_read_as_tampering(client, monkeypatch):
    """The ledger answers "lately": trimming the oldest rows is the design,
    and the verify door keeps saying intact — the head's outward link is
    reported, never judged."""
    monkeypatch.setattr(resident, "RUNS_KEPT", 2)
    token = new_tenant(client)
    task_id, page = _standing(client, token, monkeypatch)
    for i in range(4):
        page["text"] = f"cycle {i}"
        _cycle(task_id)
    runs = client.get(f"/resident/tasks/{task_id}/runs",
                      headers=auth(token)).json()
    assert len(runs) == 2
    out = client.get(f"/resident/tasks/{task_id}/runs/verify",
                     headers=auth(token)).json()
    assert out["intact"] is True and out["entries"] == 2
    assert out["head_prev"] not in (None, resident.RUNS_GENESIS)


def test_every_cycle_anchors_on_the_permanent_chain(client, monkeypatch):
    """The ledger answers "lately"; the audit chain answers "ever". Each
    cycle's audit entry carries the run row's hash prefix, so even a
    deleted ledger row leaves its shadow where nothing edits."""
    token = new_tenant(client)
    task_id, _ = _standing(client, token, monkeypatch)
    _cycle(task_id)
    conn = db.connect()
    run = conn.execute(
        "SELECT hash FROM resident_runs WHERE task_id=?", (task_id,)).fetchone()
    anchors = conn.execute(
        "SELECT ref FROM audit WHERE action='resident.task' AND ref LIKE ?",
        (f"{task_id}#%",)).fetchall()
    assert anchors and anchors[-1]["ref"] == f"{task_id}#{run['hash'][:16]}"


def test_rows_from_before_the_chain_are_said_not_guessed(client, monkeypatch):
    token = new_tenant(client)
    task_id, _ = _standing(client, token, monkeypatch)
    _cycle(task_id)
    conn = db.connect()
    conn.execute(
        "INSERT INTO resident_runs (id, tenant_id, task_id, ran_at, status,"
        " note) VALUES (?,?,?,'2025-01-01T00:00:00+00:00','done','old row')",
        (db.new_id("rrun"), conn.execute(
            "SELECT tenant_id FROM resident_tasks WHERE id=?",
            (task_id,)).fetchone()["tenant_id"], task_id))
    conn.commit()
    out = client.get(f"/resident/tasks/{task_id}/runs/verify",
                     headers=auth(token)).json()
    assert out["predate_chain"] == 1 and out["intact"] is True
