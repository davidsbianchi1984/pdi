"""Isolation held. Nothing was checking it, for a reason worth naming.

## What was found

The whole GET surface — seventy routes — driven as a second tenant against a
first tenant's seeded data: **no cross-tenant read**. The mutating routes
driven the same way: **no cross-tenant write**. `vault.get` and `vault.put`
scope on `tenant_id`; the `{tenant_id}`-in-path routes check the caller
against the path; the resource routes 404 rather than answer.

So this file does not fix a hole. It closes the thing that actually was
missing: there was no test of any of it. Isolation is the one property this
product exists to provide, and it was true by the care of whoever wrote each
route, with nothing to say so the day one of them is written differently.

## Why nobody would have noticed

`_LOCAL_CALLERS` contains `"testclient"` — Starlette's in-process sentinel —
and `_admin` treats a local caller as authorised when `PDI_ADMIN_TOKEN` is
unset. Every other test in this suite therefore runs with the **admin surface
wide open**, and cannot tell a correctly gated route from an ungated one.

    asked     is the admin surface refused
    mattered  is it refused to somebody the harness is not

That is not a defect in `_admin`: a network peer with no token gets 503, which
is checked below, and a deployment reachable beyond localhost cannot be in the
permissive state at all. It is a defect in what a test can see. The first
version of this audit ran without the token and "found" a tenant filing a
Business Associate Agreement on another tenant's account — a 201 that was the
harness authorising itself as the operator, not a cross-tenant write.

So every sweep here runs **with `PDI_ADMIN_TOKEN` set and from a non-local
client address**. Both, and neither is optional: the token alone still leaves
`testclient` trusted for the routes that have no admin gate to begin with.
"""

from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from . import ratchets
from .clientpaths import all_routes

#: What tenant alpha's data says. If any of it reaches bravo, the sweep says so.
CANARY = "ALPHA-SECRET-CANARY"
ALPHA_NAME = "alpha-unique-tenant-name"

ADMIN = "admin-token-the-tenants-do-not-have"

#: An address that is not this machine. `_LOCAL_CALLERS` trusts `testclient`,
#: so a `TestClient` built the ordinary way is an implicit operator.
FROM_THE_NETWORK = ("203.0.113.9", 51000)


@pytest.fixture()
def deployed(tmp_path, monkeypatch):
    """PDI as it is actually run: an admin token set, and callers off-machine.

    Not the `client` fixture. That one is right for every other test in this
    suite and wrong for this one, in a way that would have made the whole file
    report a result it never measured.
    """
    import base64

    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    from pdi import db as pdi_db
    monkeypatch.setenv("PDI_DB", str(tmp_path / "pdi.db"))
    monkeypatch.setenv("PDI_MASTER_KEY", base64.b64encode(
        AESGCM.generate_key(bit_length=256)).decode())
    monkeypatch.setenv("PDI_ADMIN_TOKEN", ADMIN)
    pdi_db.reset()
    from pdi.api import create_app

    with TestClient(create_app(), client=FROM_THE_NETWORK) as c:
        yield c
    pdi_db.reset()


def _admin_head():
    return {"authorization": f"Bearer {ADMIN}"}


def _two_tenants(client):
    alpha = client.post("/tenants", json={"name": ALPHA_NAME},
                        headers=_admin_head()).json()
    bravo = client.post("/tenants", json={"name": "bravo"},
                        headers=_admin_head()).json()
    return alpha, bravo


def _seed(client, alpha) -> dict:
    """Give alpha something of each kind worth stealing. Returns its ids."""
    head = {"authorization": f"Bearer {alpha['token']}"}
    made = {"tenant_id": alpha["id"]}
    client.put("/records", json={"key": "alpha/secret", "value": CANARY},
               headers=head)
    transfer = client.post("/transfers", json={
        "recipient": "clinic-a", "filename": "a.txt", "content": CANARY},
        headers=head)
    if transfer.status_code == 201:
        made["tid"] = transfer.json()["id"]
        beacon = client.post("/beacons", json={
            "label": CANARY, "ref_kind": "transfer",
            "ref_id": made["tid"]}, headers=head)
        if beacon.status_code == 201:
            made["bid"] = beacon.json()["id"]
    bequest = client.post("/bequests", json={
        "grantee_name": CANARY, "key_prefixes": ["alpha/"]}, headers=head)
    if bequest.status_code == 201:
        made["beq"] = bequest.json()["id"]
    position = client.post("/positions", json={"title": CANARY, "summary": "x"},
                           headers=head)
    if position.status_code == 201:
        made["position_id"] = position.json()["id"]
    return made


def _fill(path: str, made: dict) -> str:
    defaults = {"key": "alpha/secret", "key:path": "alpha/secret",
                "learner_id": "l1", "number": "1", "face": "guide",
                "name": "guide", "iid": "itk_x", "rid": "rob_x",
                "cid": "con_x", "bid": "bcn_x", "tid": "xfer_x",
                "position_id": "pos_x"}
    def one(match):
        raw = match.group(1)
        bare = raw.split(":")[0]
        return str(made.get(bare) or defaults.get(raw) or defaults.get(bare, "x"))
    return re.sub(r"\{([^}]+)\}", one, path)


def _read_sweep(client, made, head):
    """Returns (routes that leaked, routes that crashed).

    Crashes are collected because of what stops an unscoped query here. The
    ciphertext's associated data is `f"{tenant_id}:{key}"`, so a record read
    without the `tenant_id` in its `WHERE` clause does not return another
    tenant's value — it fails to decrypt and raises. That is real defence in
    depth and it is the reason a leak-only check is not enough: it would call
    a crashing route *isolated*, and a 500 on a cross-tenant read is isolation
    happening by accident.

        asked     did another tenant's data come back
        mattered  did the query ask for another tenant's data at all
    """
    needles = [CANARY, made["tenant_id"], ALPHA_NAME]
    leaked, crashed = [], []
    for route in all_routes(client.app):
        if "GET" not in (route.methods or ()):
            continue
        path = _fill(route.path, made)
        try:
            answer = client.get(path, headers=head)
        except Exception as raised:               # noqa: BLE001 - reported
            crashed.append((route.path, type(raised).__name__))
            continue
        if answer.status_code >= 500:
            crashed.append((route.path, str(answer.status_code)))
            continue
        found = [n for n in needles if n in answer.text]
        if found:
            leaked.append((route.path, answer.status_code, found))
    return leaked, crashed


def test_the_sweep_can_see_what_it_is_looking_for(deployed):
    """A guard on the guard, and the one this file cannot do without.

    A sweep that finds nothing is either a product with no leaks or a probe
    with no eyes, and the two look identical in a passing test. Run as
    **alpha**, the same sweep must light up on alpha's own data.
    """
    alpha, _ = _two_tenants(deployed)
    made = _seed(deployed, alpha)
    seen, _ = _read_sweep(deployed, made,
                          {"authorization": f"Bearer {alpha['token']}"})
    assert len(seen) >= ratchets.floor("isolation.routes_seen"), (
        f"the sweep found alpha's own data on only {len(seen)} routes. It is "
        "not looking at anything, and the isolation check below would pass on "
        f"a product it never asked. Seeded: {sorted(made)}")


def test_a_tenant_reads_nothing_of_another_tenants(deployed):
    """Seventy GET routes, every one of them, as the wrong tenant."""
    alpha, bravo = _two_tenants(deployed)
    made = _seed(deployed, alpha)
    leaked, crashed = _read_sweep(deployed, made,
                                  {"authorization": f"Bearer {bravo['token']}"})
    assert not leaked, (
        f"{len(leaked)} route(s) showed one tenant another's data:\n    "
        + "\n    ".join(f"{p} → {s} leaks {f}" for p, s, f in leaked))
    assert not crashed, (
        f"{len(crashed)} route(s) failed rather than refused when read by the "
        "wrong tenant:\n    "
        + "\n    ".join(f"{p} → {why}" for p, why in crashed)
        + "\n  A cross-tenant read that raises is a query that asked for "
          "another tenant's row and was stopped by the cipher's associated "
          "data. The scope belongs in the query.")


def test_a_tenant_writes_nothing_of_another_tenants(deployed):
    """The other half, and the one a read-only audit would miss.

    Includes the compliance record deliberately. A BAA is the precondition
    this vault uses to unblock HIPAA-program transfers, so a tenant able to
    file or terminate one on another's account would be altering what that
    account is legally permitted to do — not reading anything, and worse.
    """
    alpha, bravo = _two_tenants(deployed)
    made = _seed(deployed, alpha)
    head = {"authorization": f"Bearer {bravo['token']}"}
    attempts = [
        ("POST", f"/tenants/{alpha['id']}/baa",
         {"customer_legal_name": "FORGED BY BRAVO",
          "operator_legal_name": "Vault Ops",
          "effective_date": "2026-07-24"}),
        ("DELETE", f"/tenants/{alpha['id']}/baa", None),
        ("PUT", f"/tenants/{alpha['id']}/retention", {"retention": "7d"}),
        ("PUT", f"/dock/{alpha['id']}", {"faces": []}),
        ("PUT", f"/hosting/{alpha['id']}", {"mode": "colocated"}),
        ("DELETE", "/records/alpha/secret", None),
        ("DELETE", f"/tenants/{alpha['id']}", None),
    ]
    for key in ("beq", "tid"):
        if key in made:
            prefix = "bequests" if key == "beq" else "transfers"
            attempts.append(("DELETE", f"/{prefix}/{made[key]}", None))

    accepted = []
    for method, path, body in attempts:
        answer = deployed.request(method, path, json=body, headers=head)
        if answer.status_code < 400:
            accepted.append(f"{method} {path} → {answer.status_code}")
    assert not accepted, (
        f"{len(accepted)} write(s) by one tenant against another's:\n    "
        + "\n    ".join(accepted))

    alpha_head = {"authorization": f"Bearer {alpha['token']}"}
    assert deployed.get("/records/alpha/secret",
                        headers=alpha_head).status_code == 200, (
        "alpha's record did not survive bravo's attempts")
    assert deployed.get("/baa", headers=alpha_head).json()["executed"] is False, (
        "bravo filed a Business Associate Agreement on alpha's account. That "
        "is not a read — it changes what alpha's account is permitted to do.")


def test_the_admin_surface_is_closed_to_the_network_without_a_token(deployed,
                                                                    tmp_path,
                                                                    monkeypatch):
    """The assumption everything above rests on, checked rather than assumed.

    `_admin` treats a local caller as authorised when `PDI_ADMIN_TOKEN` is
    unset, which is what makes a laptop deployment usable. If that fallback
    were reachable from a network, every admin route in this product would be
    open, and this file's other three tests would be describing a posture
    nobody actually has.

    Driven from an address that is not this machine, with the variable removed.
    """
    import base64

    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    from pdi import db as pdi_db
    monkeypatch.setenv("PDI_DB", str(tmp_path / "open.db"))
    monkeypatch.setenv("PDI_MASTER_KEY", base64.b64encode(
        AESGCM.generate_key(bit_length=256)).decode())
    monkeypatch.delenv("PDI_ADMIN_TOKEN", raising=False)
    pdi_db.reset()
    from pdi.api import create_app
    app = create_app()

    stranger = TestClient(app, client=FROM_THE_NETWORK)
    assert stranger.get("/retention").status_code == 503, (
        "an unconfigured deployment answered an admin route to a caller from "
        "the network. Every tenant's name and retention window is on that "
        "route.")
    assert stranger.post("/tenants/ten_x/baa", json={
        "customer_legal_name": "x", "operator_legal_name": "y",
        "effective_date": "2026-01-01"}).status_code == 503

    # And the fallback still works for the laptop it exists for.
    on_the_box = TestClient(app)
    assert on_the_box.get("/retention").status_code == 200


def test_the_harness_trusts_itself_and_this_file_says_so():
    """Why the rest of the suite could not have caught any of this.

    `"testclient"` is in `_LOCAL_CALLERS`, so an ordinary `TestClient` is an
    implicit operator on every admin route. That is deliberate and it is what
    makes the other four hundred tests writable — and it means none of them
    can distinguish a gated route from an ungated one.

    Asserted so that if somebody removes `testclient` from that set, this
    file's elaborate fixture stops being necessary and says so, rather than
    quietly testing the same thing twice.
    """
    from pdi.api import _LOCAL_CALLERS
    assert "testclient" in _LOCAL_CALLERS, (
        "the harness is no longer trusted as a local caller. The `deployed` "
        "fixture in this file exists to work around that trust; if it is "
        "gone, simplify this file rather than leaving the workaround.")
    assert FROM_THE_NETWORK[0] not in _LOCAL_CALLERS
