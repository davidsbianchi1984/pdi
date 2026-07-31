"""A route the backend made public, in a client that made it private.

This file reports **nothing wrong**, and that is why it exists.

QRME's copy found three public routes reachable only after signing up to the
platform being asked about. JIM's found one, and a worse one: `relay_guidance`
says *"Public: the person standing over a colleague has no account and needs
an answer in ninety seconds"*, and its only door was inside a signed-in
console screen belonging to somebody else.

PDI has a route of exactly the same kind. `receive_transfer` says so:

    The recipient retrieves the file with their receive token — no tenant
    credential; the token itself is the (auditable) authorization.

A corporation seals a file for somebody under HIPAA or OSHA or CPNI. That
somebody is, by construction, not a PDI tenant: they have a one-shot receive
token in an email and no vault of their own. They are the same person as
QRME's objector and JIM's passer-by — the one the feature is for, and the one
with no account.

PDI got it right on its own, twice over:

* `receiveTransfer` binds the receive token in a header of its own rather
  than as a bearer credential, and `api.ts` says why: *"The recipient is not
  the tenant... Binding it as a bearer credential is a 403 every time."*
* PDI's console has **no sign-in gate**. `App.tsx` renders its nav
  immediately; a tenant token is entered per-action, so a recipient who
  follows a link is not stopped at a door.

Neither of those is written down anywhere as a decision, which is the only
thing wrong with them: a console that grew a `if (!session.token) return
<Welcome />` — the shape both other products have — would strand every
recipient of every sealed transfer, and nothing would fail.

That is what this file is: a pin, not a finding.
"""

from __future__ import annotations

import re
from pathlib import Path

from pdi.api import app

from . import clientpaths


def _repo_root() -> Path:
    for d in Path(__file__).resolve().parents:
        if (d / "pyproject.toml").exists():
            return d
    raise RuntimeError("no pyproject.toml above this test")


REPO = _repo_root()

PUBLIC_ROUTE = "POST /transfers/{tid}/receive"


def test_the_public_route_is_still_a_route():
    """A guard on the guard: every check below searches for a string."""
    routed = {f"{m} {r.path}"
              for r in clientpaths.all_routes(app)
              for m in (r.methods or set()) - {"HEAD", "OPTIONS"}}
    assert PUBLIC_ROUTE in routed, (
        f"{PUBLIC_ROUTE} is not a route any more, so the checks below are "
        "vacuous")


def test_the_backend_still_takes_no_tenant_credential():
    """The premise. If a tenant credential is ever added here, the recipient
    of a sealed transfer stops being able to collect it, and the failure will
    look like a 403 to somebody who never had an account to begin with."""
    text = (REPO / "pdi" / "api.py").read_text(encoding="utf-8")
    body = text[text.index("def receive_transfer"):]
    body = body[:body.index("\n    @app.")]
    assert "Depends(_tenant)" not in body and "Depends(_writer)" not in body, (
        "receive_transfer now requires a tenant — but its caller is the "
        "recipient of a sealed file, who has a receive token and no vault")
    assert "x_receive_token" in body, (
        "the receive token is no longer how this route authorizes; whatever "
        "replaced it needs checking against the same question")


def test_the_recipient_has_a_door_of_their_own():
    """The check this file should have had, and did not.

    Its first version asserted that the console reaches `receiveTransfer` and
    that PDI's console has no sign-in gate, and concluded PDI "got it right".
    Both facts were true. The conclusion was wrong, and wrong in the way this
    audit has now named seven times: a call site is not reachability.

    The only caller of that binding is `Exchange.tsx`'s **"Receive it as the
    recipient"** button. Its own tooltip gives it away — *"Fetch it the way
    the recipient would"*, disabled unless `receipts[t.id]` is present, which
    is a token the sender's session captured at creation and which the tooltip
    admits is usually gone: *"The receive token was shown once, in another
    session"*. It is the sender rehearsing. The recipient — who holds the
    token, and who the route's own docstring says is not a tenant — had
    nowhere in the entire product to use it.

    So the absence of a sign-in gate was never the recipient having access. It
    was the recipient having nothing to be gated out of.
    """
    api = (REPO / "pdi" / "api.py").read_text(encoding="utf-8")
    assert '@app.get("/r/{tid}"' in api, (
        "there is no recipient page. The only thing calling the receive route "
        "is the console's rehearsal button, which needs the sender's own "
        "session — a person with a receive token in an email has nowhere to "
        "put it.")

    page = (REPO / "pdi" / "landing.py").read_text(encoding="utf-8")
    body = page[page.index("def receive_page"):]
    assert "x-receive-token" in page, (
        "the recipient page does not send the receive token in its header")
    assert "location.hash" in page, (
        "the link does not carry the token in the URL fragment — a query "
        "string puts a one-shot authorization for compliance-grade material "
        "into every access log and Referer header on the way")
    assert "replaceState" in page, (
        "the fragment is not cleared from the address bar after it is read")
    assert body  # the function exists, not just the strings


def test_the_recipient_page_does_not_confirm_which_ids_exist():
    """A 404 here would turn the page into an oracle.

    Whether a transfer exists is the token's business to answer. If the URL
    answered it, anybody could walk ids and learn which sealed transfers are
    real — which is exactly the kind of thing a compliance-grade transfer
    exists to avoid leaking.
    """
    api = (REPO / "pdi" / "api.py").read_text(encoding="utf-8")
    route = api[api.index('@app.get("/r/{tid}"'):]
    route = route[:route.index("\n    @app.")]
    code = re.sub(r'""".*?"""', "", route, flags=re.S)
    assert "404" not in code, (
        "the recipient page 404s on an unknown id, which makes it a way of "
        "asking whether a transfer id is real")


def test_the_console_binding_sends_the_receive_token_not_a_bearer():
    """What PDI already got right, written down so it stays right.

    Kept, and narrowed: this says the *binding* is shaped correctly. It says
    nothing about whether anybody the route was written for can reach it —
    which is precisely the conflation the test above now covers.
    """
    api = (REPO / "app" / "src" / "api.ts").read_text(encoding="utf-8")
    binding = api[api.index("receiveTransfer:"):]
    binding = binding[:binding.index("\n  intakes:")]
    assert "x-receive-token" in binding, (
        "receiveTransfer no longer sends the receive token in its own header")
    assert not re.search(r"\btoken\s*[,}]", binding), (
        "receiveTransfer is sending a tenant bearer credential — the "
        "recipient does not have one, and the server answers 403")


def test_the_console_does_not_gate_the_recipient_behind_a_session():
    """The regression this file is really here to catch.

    QRME's console and JIM's both open with `if (!session.<id>) return
    <Onboarding />`, and in both that early return was found to be stranding
    somebody the product was written to serve. PDI's does not have one. If a
    future round adds the same shape here for consistency's sake, every
    recipient of every sealed transfer loses their only door at once.
    """
    app_tsx = (REPO / "app" / "src" / "App.tsx").read_text(encoding="utf-8")
    code = re.sub(r"/\*.*?\*/|//[^\n]*", "", app_tsx, flags=re.S)
    gate = re.search(r"if\s*\(\s*!\s*session\.\w+\s*\)\s*return", code)
    assert gate is None, (
        "PDI's console has grown a sign-in gate. The recipient of a sealed "
        "transfer is not a tenant and has no credential to get past it — "
        "check that Exchange, or wherever `receiveTransfer` is called, is "
        "still reachable without one before removing this test.")
