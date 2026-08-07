"""`operator_can_decrypt: false` — checked against the whole database.

`custody()` reports, for a tenant under ``held`` custody, that the key is one
"the deployment never stores". That sentence is the reason outsourced hosting
of this vault is a different product from every other one, and it is the
sentence a security review will quote.

What checked it:

* `test_custody_states_its_own_limits` asserts
  ``body["operator_can_decrypt"] is False`` — which reads the literal back out
  of the dict that hardcodes it, and cannot fail;
* `test_the_check_value_does_not_store_the_key` is real, and narrow. It reads
  **two columns of one table**: ``SELECT check_value, config FROM
  tenant_keys``. That is where a first implementation would put the key, so it
  was the right place to look first — and it is not the claim. The claim is
  *nowhere*.

A key does not have to be stored on purpose to be stored. It arrives in a
header on every request, and this deployment has an operations journal, an
audit trail, an error path and a retention sweep, any of which could carry a
request detail into a row without anybody deciding to. Those are the places a
secret actually leaks, and none of them were being looked at.

So: **walk every table and every column, and look for the key in every
representation it could wear** — the raw bytes, the base64 the client sends,
and hex. The tables come from `sqlite_master` rather than a list written by
hand, because the table that leaks it is the one added after the list was
written.

The same search is then pointed at a record's plaintext, since "the operator
cannot open these records" and "the plaintext is not sitting in a column
somewhere else" are two different claims and only the first was tested.
"""

import base64

from pdi import db

KEY = base64.b64encode(b"k" * 32).decode()
SECRET = "classified-nothing-else-says-this"


def _tenant(client, name="acme"):
    return client.post("/tenants", json={"name": name, "retention": "forever"}
                       ).json()["token"]


def _auth(token, key=None):
    h = {"authorization": f"Bearer {token}"}
    if key:
        h["x-tenant-key"] = key
    return h


def _every_cell():
    """Every value in every column of every table, as text.

    Read from `sqlite_master` for the same reason the tables are not listed
    here: a hand-kept list cannot cover the table a later round adds, and that
    is exactly the table a secret would end up in.
    """
    conn = db.connect()
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%'").fetchall()]
    assert tables, "the sweep found no tables — it is looking at the wrong db"
    for table in tables:
        for row in conn.execute(f"SELECT * FROM {table}").fetchall():
            for column in row.keys():
                value = row[column]
                if value is None:
                    continue
                yield table, column, value if isinstance(value, str) else str(value)


def _find(needles: dict[str, str]) -> list[str]:
    """Where any of these appears, named by table and column."""
    hits = []
    for table, column, text in _every_cell():
        for what, needle in needles.items():
            if needle and needle in text:
                hits.append(f"{table}.{column} contains {what}")
    return hits


def _key_shapes() -> dict[str, str]:
    """Every representation the key could be wearing when it lands in a row.

    Checking only the base64 the client sends would miss a decode-then-store,
    and checking only the raw bytes would miss a log line that echoed the
    header back verbatim.
    """
    raw = base64.b64decode(KEY)
    return {
        "the key as sent (base64)": KEY,
        "the key's raw bytes": raw.decode("latin-1"),
        "the key in hex": raw.hex(),
    }


# --- the claim itself -------------------------------------------------------

def test_adopting_a_key_leaves_it_in_no_column_of_any_table(client):
    """The sentence a security review quotes, checked against the schema
    rather than against the two columns somebody thought of first."""
    token = _tenant(client)
    r = client.put("/key", json={"provider": "held", "key": KEY},
                   headers=_auth(token))
    assert r.status_code == 201, r.text
    hits = _find(_key_shapes())
    assert not hits, (
        "the deployment stored the customer's key: " + "; ".join(hits))


def test_using_the_key_on_every_door_leaves_it_nowhere(client):
    """Adoption is one request. The key rides a header on **every** read and
    write afterwards, and a request detail copied into a journal row is how a
    secret is kept without anybody deciding to keep it."""
    token = _tenant(client)
    client.put("/key", json={"provider": "held", "key": KEY},
               headers=_auth(token))
    client.put("/records", json={"key": "r", "value": SECRET},
               headers=_auth(token, KEY))
    client.get("/records/r", headers=_auth(token, KEY))
    client.get("/records", headers=_auth(token, KEY))
    client.get("/key", headers=_auth(token, KEY))

    hits = _find(_key_shapes())
    assert not hits, (
        "the key reached a row by riding a request: " + "; ".join(hits))


def test_a_refused_key_is_not_kept_either(client):
    """The error path is where secrets go to be logged. A wrong key is
    rejected — and the rejection must not be the thing that files it."""
    token = _tenant(client)
    client.put("/key", json={"provider": "held", "key": KEY},
               headers=_auth(token))
    wrong = base64.b64encode(b"w" * 32).decode()
    client.get("/records/r", headers=_auth(token, wrong))

    hits = _find({"the rejected key": wrong,
                  "the rejected key's bytes": (b"w" * 32).decode("latin-1")})
    assert not hits, (
        "a refused key was written down: " + "; ".join(hits))


# --- the other half: the plaintext ------------------------------------------

def test_the_plaintext_is_in_no_column_either(client):
    """"The operator cannot open these records" and "the plaintext is not
    sitting in a column somewhere else" are different claims, and only the
    first had a test. Ciphertext in `records` proves the record was sealed; it
    proves nothing about a search index, a journal detail or a cached preview.
    """
    token = _tenant(client)
    client.put("/key", json={"provider": "held", "key": KEY},
               headers=_auth(token))
    client.put("/records", json={"key": "r", "value": SECRET},
               headers=_auth(token, KEY))
    client.get("/records/r", headers=_auth(token, KEY))

    hits = _find({"the record's plaintext": SECRET})
    assert not hits, (
        "the plaintext is readable in a column: " + "; ".join(hits))


def test_the_plaintext_is_gone_under_deployment_custody_too(client):
    """Not a BYOK question. A deployment-custody tenant's record is sealed
    under the operator's key by design — but the plaintext still must not be
    lying beside it in some other column."""
    token = _tenant(client)
    client.put("/records", json={"key": "r", "value": SECRET},
               headers=_auth(token))
    client.get("/records/r", headers=_auth(token))
    hits = _find({"the record's plaintext": SECRET})
    assert not hits, "; ".join(hits)


# --- the sweep has to be able to fail ---------------------------------------

def test_the_sweep_would_actually_find_a_leaked_key(client):
    """A guard nobody has watched fail is a guard nobody should trust.

    This writes the key into a row on purpose and asserts the sweep names the
    table and the column — without it, every test above would pass just as
    happily if `_every_cell` were quietly yielding nothing.
    """
    token = _tenant(client)
    client.put("/key", json={"provider": "held", "key": KEY},
               headers=_auth(token))
    conn = db.connect()
    conn.execute("UPDATE tenant_keys SET config = ?", (f'{{"oops": "{KEY}"}}',))
    conn.commit()

    hits = _find(_key_shapes())
    assert hits, "the sweep cannot see a key sitting in a column"
    assert any("tenant_keys.config" in h for h in hits), hits


def test_the_sweep_reads_the_real_schema():
    """And that it is walking tables rather than a list that stopped being
    complete three rounds ago."""
    seen = {table for table, _, _ in _every_cell()}
    tables = {r[0] for r in db.connect().execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%'").fetchall()}
    # Empty tables yield nothing, so the sweep's reach is the schema it reads,
    # not the rows it happened to find.
    assert seen <= tables and tables, (seen, tables)
