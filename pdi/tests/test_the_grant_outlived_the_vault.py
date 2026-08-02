"""Every door of theirs answered 401. The grantee's door answered with the
record.

## The finding

`vault.tenant_by_id` has carried its qualifier since it was written, and says
so in its own docstring:

    SELECT * FROM tenants WHERE id=? AND deleted_at IS NULL
    ...tenants (deleted_at set) resolve to None — their data is unreachable

`bequests.py` did not use it. It resolved the tenant twice with its own
`SELECT * FROM tenants WHERE id=?`, no qualifier, no `_scrub`. Driven end to
end against a tenant who deleted their vault:

    DELETE /tenants/{id}?mode=soft   200
    GET /records/{key}   (owner's token)     401   access cut
    GET /bequests/grant/keys                 200   ["jim/u1/medical/note"]
    GET /bequests/grant/read?key=...         200   {"value": "a private note"}

    asked     can the tenant still reach their vault
    mattered  can anyone still reach it

Soft-delete is the *recoverable* one — a tombstone with a window — which is
exactly why nothing about it looks like an emergency, and why the door it left
open stayed open quietly. A grantee holding an activated bequest read the
plaintext of a vault whose owner had closed it.

## The other half

On `mode=wipe` the tenant row is deleted outright, so the same line evaluated
`dict(None)` and the grantee met a **500** rather than a refusal. And the wipe
retired `tenant_tokens` while leaving the `bequests` rows themselves — a grant
hash still live against a tenant that no longer existed. `delete_tenant`'s
docstring says it removes "the tenant's records, scoped tokens, and the tenant
row"; the bequest grant is a scoped token that lives in a different table.

## What changed

Both call sites go through `vault.tenant_by_id`, so the bequest path asks the
same question every other door asks and gets the same answer. A wipe revokes
the tenant's bequests and clears their grant hashes.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from pdi import bequests, db, i18n

from .conftest import new_tenant


def _repo_root() -> Path:
    for d in Path(__file__).resolve().parents:
        if (d / "pyproject.toml").exists():
            return d
    raise RuntimeError("no pyproject.toml above this test")


REPO = _repo_root()


def _auth(token):
    return {"authorization": f"Bearer {token}"}


def _bequest(client, token, **over):
    body = {"grantee_name": "June Bianchi",
            "key_prefixes": ["jim/u1/medical/"],
            "note": "For my daughter — the medical records, nothing else."}
    body.update(over)
    r = client.post("/bequests", json=body, headers=_auth(token))
    assert r.status_code == 201, r.text
    return r.json()


def _activated(client):
    """A tenant with one record, one activated bequest over it, and the
    grantee's header."""
    token = new_tenant(client)
    tenant_id = db.connect().execute(
        "SELECT id FROM tenants ORDER BY created_at DESC LIMIT 1").fetchone()["id"]
    r = client.put("/records", headers=_auth(token),
                   json={"key": "jim/u1/medical/note", "value": "a private note"})
    assert r.status_code in (200, 201), r.text
    b = _bequest(client, token)
    act = client.post(f"/bequests/{b['id']}/activate",
                      json={"activation_ref": "cert-1"})
    assert act.status_code == 200, act.text
    return tenant_id, token, {"x-grant-token": act.json()["grant_token"]}


# --- driven -----------------------------------------------------------------

def test_a_soft_deleted_vault_is_shut_to_its_grantee_too(client):
    """The defect, driven. Before this round: 200, with the key list."""
    tenant_id, token, grant = _activated(client)
    assert client.get("/bequests/grant/keys", headers=grant).status_code == 200
    assert client.delete(f"/tenants/{tenant_id}?mode=soft").status_code == 200
    # The owner's own door, for the comparison the whole finding rests on.
    assert client.get("/records/jim/u1/medical/note",
                      headers=_auth(token)).status_code == 401
    r = client.get("/bequests/grant/keys", headers=grant)
    assert r.status_code == 410, (
        f"the owner's token is refused and the grantee's is not "
        f"({r.status_code})")
    assert r.json()["detail"] == bequests.VAULT_CLOSED


def test_the_record_body_does_not_come_back(client):
    """The consequence rather than the status code: the plaintext."""
    tenant_id, _token, grant = _activated(client)
    client.delete(f"/tenants/{tenant_id}?mode=soft")
    r = client.get("/bequests/grant/read",
                   params={"key": "jim/u1/medical/note"}, headers=grant)
    assert r.status_code == 410, r.text
    assert "a private note" not in r.text


def test_a_wiped_vault_answers_rather_than_raising(client):
    """A 500 is not a refusal. `dict(None)` was what the grantee met once the
    tenant row itself was gone."""
    tenant_id, _token, grant = _activated(client)
    assert client.delete(f"/tenants/{tenant_id}?mode=wipe").status_code == 200
    for path, params in (("/bequests/grant/keys", None),
                         ("/bequests/grant/read",
                          {"key": "jim/u1/medical/note"})):
        r = client.get(path, params=params, headers=grant)
        assert r.status_code < 500, (
            f"{path} raised rather than refusing ({r.status_code})")
        assert r.status_code in (404, 410), r.text


def test_a_wipe_retires_the_bequest_itself(client):
    """Not only the read path: the row stops naming a grantee and a shelf, and
    the grant hash goes."""
    tenant_id, _token, _grant = _activated(client)
    client.delete(f"/tenants/{tenant_id}?mode=wipe")
    row = db.connect().execute(
        "SELECT revoked_at, grant_hash FROM bequests WHERE tenant_id=?",
        (tenant_id,)).fetchone()
    assert row is not None, "the bequest row vanished — it is the estate record"
    assert row["revoked_at"], "a wiped tenant still has a standing bequest"
    assert row["grant_hash"] is None, "the grant hash outlived the tenant"


def test_a_restored_vault_opens_to_its_grantee_again(client):
    """Soft-delete is the recoverable one, and the refusal must recover with
    it — a bequest that silently died on a restorable tombstone would be its
    own defect."""
    tenant_id, _token, grant = _activated(client)
    client.delete(f"/tenants/{tenant_id}?mode=soft")
    assert client.post(f"/tenants/{tenant_id}/restore").status_code == 200
    r = client.get("/bequests/grant/keys", headers=grant)
    assert r.status_code == 200, r.text
    assert r.json()["keys"] == ["jim/u1/medical/note"]


def test_a_live_vault_is_untouched(client):
    """The gate refuses a closed vault and must not touch an open one."""
    _tenant_id, _token, grant = _activated(client)
    r = client.get("/bequests/grant/read",
                   params={"key": "jim/u1/medical/note"}, headers=grant)
    assert r.status_code == 200 and r.json()["value"] == "a private note"


# --- the generalisation -----------------------------------------------------

def _tenant_lookups(rel: str) -> list[tuple[int, str]]:
    """Every SQL literal in a module that selects from `tenants` by id.

    Structural rather than by function name: the two that were wrong sat in
    two different functions, and naming them would have been the same mistake
    a second time.
    """
    src = (REPO / rel).read_text(encoding="utf-8")
    out = []
    for node in ast.walk(ast.parse(src)):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        text = " ".join(node.value.split())
        if re.search(r"FROM tenants\b", text) and "WHERE id=?" in text:
            out.append((node.lineno, text))
    return out


def test_nothing_resolves_a_tenant_without_asking_whether_it_is_open(client):
    """The generalisation. `bequests.py` is the module that hands a stranger a
    tenant's records, so a lookup here that skips the tombstone is the whole
    defect, wherever in the file it sits."""
    unqualified = [f"pdi/bequests.py:{line}  {text[:70]}"
                   for line, text in _tenant_lookups("pdi/bequests.py")
                   if "deleted_at IS NULL" not in text]
    assert not unqualified, (
        f"{len(unqualified)} tenant lookup(s) in the bequest path ignore the "
        "soft-delete tombstone, so a closed vault stays readable through a "
        "grant — use vault.tenant_by_id:\n    " + "\n    ".join(unqualified))


def test_the_bequest_path_goes_through_the_shared_resolver(client):
    """The positive form of the same rule, so the fix cannot be satisfied by
    copying the qualifier into a third hand-rolled SELECT."""
    src = (REPO / "pdi/bequests.py").read_text(encoding="utf-8")
    assert "vault.tenant_by_id" in src, (
        "the bequest path no longer uses the shared tenant resolver — every "
        "other door in this product asks `vault` whether a tenant is open, and "
        "the one that answers a stranger asks for itself")


def test_the_refusal_is_one_the_grantee_can_be_given_in_their_language(client):
    """A grantee is very often not the person who chose this deployment's
    language. The new sentence went into the table, not the backlog."""
    assert bequests.VAULT_CLOSED in i18n._REFUSALS
    row = i18n._REFUSALS[bequests.VAULT_CLOSED]
    missing = [c for c in i18n.SUPPORTED if c != i18n.DEFAULT and c not in row]
    assert not missing, f"the new refusal is missing {missing}"
