"""A client record is a claim about a route. Drive the route and check it.

QRME built this guard in 0.56.4 after chasing a wire-name collision into a
Windows record for its composition route that declared two fields —

    [property: JsonPropertyName("name")] string? Name,
    [property: JsonPropertyName("share")] double? Share);

— the route has never sent. It sends `display_name` and `weight`. Both decoded
to null on every response, and the button wired to them drew a row of
separators with nothing between them. Fourteen records over there were the
same guess at a shape, written without ever driving the route.

    asked     do the names match
    mattered  did anybody ever run the route

Nothing in this repository was checking the same thing. This is the port.

## The one thing that is different here

The sibling guard in `test_one_name_one_type_on_the_wire.py` was copied across
all three products verbatim, because it only reads records. This one has to
find the *calls*, and PDI's client does not make them the way the other two
do. There is no `Get(path)` helper: every call builds its own
`HttpRequestMessage` and passes the tenant token alongside, because in this
product a token is not a session — it is the tenant, and a call without one
has nobody to be.

    Send<VaultRecord>(new HttpRequestMessage(HttpMethod.Get, $"/records/{key}"), token)

So the binding pattern below is this product's, not a copy, and
`test_the_extractor_finds_this_products_calls` exists because a regex tuned
for a different client would find nothing here and report a clean sweep.

## What it does

Drives each GET binding against a live app and asserts every
`JsonPropertyName` in the bound record is a key the route actually returned.
One level of nesting is followed.

The assertion is one-directional on purpose. A record *omitting* a key the
route returns is fine — a client decodes what it needs. A record *declaring* a
key the route never sends is a promise to the reader that the wire does not
keep.
"""

import json
import pathlib
import re

from .conftest import auth, new_tenant

REPO = pathlib.Path(__file__).resolve().parents[2]
WINDOWS_CLIENT = REPO / "native/windows/ApiClient.cs"
RECORD = pathlib.Path(__file__).resolve().parent / "wire_shapes_unverified.txt"

_SRC = WINDOWS_CLIENT.read_text(encoding="utf-8")

# This product's call shape — see the module docstring.
_BINDING = re.compile(
    r'Send<([\w\[\]]+)\??>\(\s*new HttpRequestMessage\(\s*'
    r'HttpMethod\.Get,\s*\$?"([^"]+)"', re.S)
# The closing paren stays inside the captured body. Without it the field regex
# below — which needs a `,` or `)` after the property name — silently drops the
# *last* field of every record. That is how QRME's version of this guard first
# reported a clean client, and it is why the extractor is asserted on.
_RECORD_BLOCK = re.compile(r'public record (\w+)\((.*?\));', re.S)
_FIELD = re.compile(
    r'JsonPropertyName\("([\w_]+)"\)\]\s+([\w\[\]\?<>,\.\s]+?)\s+\w+\s*[,)]')


def _records() -> dict[str, list[tuple[str, str]]]:
    """Record name -> [(wire name, declared C# type)]."""
    return {name: [(n, t.strip().rstrip("?")) for n, t in _FIELD.findall(body)]
            for name, body in _RECORD_BLOCK.findall(_SRC)}


def _bindings() -> list[tuple[str, str]]:
    """[(record name, path template)] for every GET the client makes."""
    return [(t.replace("[]", ""), p) for t, p in _BINDING.findall(_SRC)]


def _recorded() -> set[str]:
    """Rows, with trailing reasons stripped.

    A row's reason may wrap onto the next line — an indented `#` that is not a
    row of its own. Filtering on the *result* rather than on the raw line is
    what keeps a wrapped reason from counting as an empty row.
    """
    rows = (line.split("#")[0].strip()
            for line in RECORD.read_text(encoding="utf-8").splitlines())
    return {row for row in rows if row}


def _returned_keys(body) -> set[str] | None:
    """The keys a response actually carried, or None if it carried none."""
    if isinstance(body, dict):
        return set(body)
    if isinstance(body, list):
        seen = [set(x) for x in body if isinstance(x, dict)]
        return set().union(*seen) if seen else None
    return None


def _descend(body, key):
    """The value under `key`, unwrapped from a list, or None."""
    if isinstance(body, list):
        body = next((x for x in body if isinstance(x, dict)), None)
    if not isinstance(body, dict) or key not in body:
        return None
    return body[key]


def _mismatches(record: str, body, recs, seen=()) -> list[str]:
    """Wire names `record` declares that `body` did not carry."""
    if record not in recs or record in seen:
        return []
    got = _returned_keys(body)
    if got is None:
        return []
    out = []
    for wire, typ in recs[record]:
        if wire not in got:
            out.append(f"{record}.{wire}")
            continue
        nested = typ.replace("[]", "").split(".")[-1]
        out += _mismatches(nested, _descend(body, wire), recs, seen + (record,))
    return out


def _standing(client) -> tuple[str, str]:
    """A tenant with something in the vault, and the key it is under.

    An empty vault answers most of these routes with an empty list, and a list
    with nothing in it cannot disagree with a record about anything. Sealing
    one value is what makes the record and provenance shapes readable at all.
    """
    token = new_tenant(client)
    client.put("/records", json={"key": "note", "value": "a sealed thing"},
               headers=auth(token))
    return token, "note"


def _drive(client, token: str, key: str):
    """Every binding, driven. Yields (template, record, mismatches|None).

    `None` means this fixture could not reach the route.
    """
    recs = _records()
    for record, template in _bindings():
        if record not in recs:
            continue
        path = template.replace("{key}", key)
        if "{" in path:
            yield template, record, None
            continue
        response = client.get(path, headers=auth(token))
        if response.status_code != 200:
            yield template, record, None
            continue
        try:
            body = response.json()
        except (ValueError, json.JSONDecodeError):
            yield template, record, None
            continue
        if _returned_keys(body) is None:
            yield template, record, None
            continue
        yield template, record, _mismatches(record, body, recs)


# --- the guard ---------------------------------------------------------------

def test_no_client_record_promises_a_field_the_route_never_sends(client):
    """The `CompositionSource.name` shape: a field that decodes to null on
    every single response, wired to a button, shipped."""
    token, key = _standing(client)
    loose = []
    for _, record, missing in _drive(client, token, key):
        for row in missing or []:
            if row not in _recorded():
                loose.append(row)
    assert not loose, (
        "these client fields are not on the wire:\n    "
        + "\n    ".join(sorted(set(loose)))
        + "\n  The route was driven and did not return them. Correct the "
          "record to the shape the route actually has, or record the row "
          "with the state that produces it — recording is ratcheted.")


def test_the_unverified_record_only_shrinks():
    text = RECORD.read_text(encoding="utf-8")
    ceiling = int(re.search(r"^# ceiling: (\d+)$", text, re.M).group(1))
    assert len(_recorded()) <= ceiling, (
        f"{len(_recorded())} rows recorded, above the {ceiling} ceiling")


def test_every_recorded_row_names_a_field_that_exists():
    """A row for a field nobody declares any more is a reader being told to
    distrust a client that is fine."""
    declared = {f"{rec}.{wire}"
                for rec, fields in _records().items() for wire, _ in fields}
    stale = sorted(_recorded() - declared)
    assert not stale, (
        "these rows name fields the client no longer declares:\n    "
        + "\n    ".join(stale) + "\n  Strike them.")


# --- the scan has to be able to see, and to fail -----------------------------

def test_the_extractor_finds_this_products_calls():
    """A regex tuned for QRME's `Get(path)` helper finds nothing in this file,
    and nothing found reads as nothing wrong. That is the failure mode this
    assertion exists for."""
    assert len(_bindings()) >= 15, (
        f"only {len(_bindings())} GET binding(s) found — this client builds "
        f"its own HttpRequestMessage, and a pattern borrowed from another "
        f"product will not see them")


def test_the_scan_reaches_a_real_share_of_the_bindings(client):
    token, key = _standing(client)
    driven = [m for _, _, m in _drive(client, token, key) if m is not None]
    assert len(driven) >= 10, (
        f"only {len(driven)} binding(s) were reachable — the fixture or the "
        f"extractor has stopped working")


def test_the_extractor_reads_every_record_field():
    """Counted against the sibling guard in
    `test_one_name_one_type_on_the_wire.py`, which reads the same file with a
    flat regex. A record-aware extractor seeing fewer wire names than the flat
    one is dropping fields."""
    from .test_one_name_one_type_on_the_wire import _declared

    names = {wire for fields in _records().values() for wire, _ in fields}
    assert len(names) >= len(_declared()), (len(names), len(_declared()))

def test_no_extracted_record_swallowed_the_next_one():
    """The block regex is non-greedy, so an unbalanced paren anywhere would let
    one record's body run on into the next — and the fields would then be
    reported against the wrong record name, which reads as a real finding and
    is not one. Seen while injecting a deliberately malformed field to check
    this guard fires.
    """
    for name, body in _RECORD_BLOCK.findall(_SRC):
        assert "public record" not in body, name


def test_the_guard_would_catch_a_fictional_field():
    """Driven against the shape QRME's `CompositionSource` had, so the check is
    known to fire rather than assumed to."""
    recs = {"Card": [("sources", "Row[]")],
            "Row": [("display_name", "string"), ("share", "double")]}
    body = {"sources": [{"display_name": "Dana", "weight": 0.6}]}
    assert _mismatches("Card", body, recs) == ["Row.share"]


def test_the_guard_allows_a_record_to_decode_less_than_it_is_sent():
    """A client need not read every key. The defect is the other direction."""
    recs = {"Row": [("key", "string")]}
    body = {"key": "note", "sealed_at": "2026-08-07", "provenance": None}
    assert _mismatches("Row", body, recs) == []
