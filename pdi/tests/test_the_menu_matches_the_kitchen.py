"""Every option the vault offers, the vault must accept.

A catalog endpoint is a menu. The console and the three shells render it
directly — a language picker, a robot catalog, a connector list — so whatever it
lists is what a tenant can choose. If the endpoint that *consumes* the choice
refuses one of those values, the tenant picks it from a dropdown and meets an
error for doing exactly what they were offered.

This is the shape of the bug that left a sibling's community wall with dead
buttons: the request routes perfectly, and the refusal happens inside the
handler, after dispatch. The route guard in this directory says plainly that it
cannot see that far. This one can, because it stops reading source and sends the
request.

What it does not cover: a choice the client invents rather than reads from a
catalog, and a refusal that depends on state this fixture does not set up — a
BAA on file, a retention hold, an exhausted one-shot token. Those have their own
tests.
"""

from __future__ import annotations

import pytest

from .conftest import new_tenant


def _auth(token: str) -> dict:
    return {"authorization": f"Bearer {token}"}


def _accepted(response) -> bool:
    """A 2xx, or a refusal clearly about something other than the value.

    409 is the one status that is not evidence of a bad vocabulary: it means the
    server understood the value and objected to the state — already bound,
    already connected.
    """
    return response.status_code < 400 or response.status_code == 409


def _check(label, offered, send):
    assert offered, f"{label}: the catalog offered nothing, so nothing was checked"
    refused = []
    for value in offered:
        response = send(value)
        if not _accepted(response):
            refused.append(f"{value!r} -> {response.status_code} "
                           f"{response.text[:120]}")
    assert not refused, (
        f"{label}: the vault offers these and then refuses them:\n  "
        + "\n  ".join(refused)
        + "\n(a value the tenant picked from a list the server itself supplied)"
    )


@pytest.mark.parametrize("mode", ["pre", "on_demand"])
def test_every_offered_language_can_be_set(client, mode):
    """Both delivery modes, because the pair is validated together.

    A language accepted in one mode and refused in the other would be invisible
    to a test that only tried the default.
    """
    token = new_tenant(client)
    offered = [row["code"] for row in
               client.get("/languages", headers=_auth(token)).json()["languages"]]
    _check(
        f"language ({mode})", offered,
        lambda code: client.put("/language", headers=_auth(token),
                                json={"language": code, "mode": mode}),
    )


def test_every_robot_in_the_catalog_can_be_bound(client):
    token = new_tenant(client)
    catalog = client.get("/robotics/catalog",
                         headers=_auth(token)).json()["robots"]
    _check(
        "robot", [r["model"] for r in catalog],
        lambda model: client.post("/robots", headers=_auth(token),
                                  json={"model": model}),
    )


def test_every_connector_in_the_catalog_can_be_connected(client):
    """Provider and app together, which is how the catalog is keyed."""
    token = new_tenant(client)
    catalog = client.get("/connectors/catalog",
                         headers=_auth(token)).json()["providers"]
    pairs = [(p["provider"], app["app"])
             for p in catalog for app in (p.get("apps") or [])]
    _check(
        "connector", pairs,
        lambda pair: client.post("/apps", headers=_auth(token),
                                 json={"provider": pair[0], "app": pair[1]}),
    )
