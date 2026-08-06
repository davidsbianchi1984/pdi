"""The last eighty-four doors, and what building them found.

This closes PDI's console backlog, and with it the audit across all three
products. It stood at 84 — routes reachable from the phone shells and from
no part of the desktop console — and it is now zero, as are the union
backlog and the unused-binding record. All three files are empty rather than
short, and the tests below assert emptiness.

## What building the doors found

Nothing in the vault was broken, and that is worth saying plainly rather
than manufacturing a defect to match the earlier rounds. What driving the
routes against a running vault found was **six places where the route table
and the wire disagree**, every one of which would have shipped as a dead
button:

1. `POST /transfers/{id}/receive` and `POST /intakes/{id}/submit` do **not**
   take the tenant's token. They take `x-receive-token` and `x-submit-token`
   — headers of their own — because the party receiving a transfer is a
   clinic and the party submitting to an intake is a records office, and
   neither is the tenant, has a tenant credential, or should. Passing the
   tenant's bearer token is a 403 every time.

2. `GET /s/{bid}` serves **HTML** and two `qr.svg` routes serve **SVG**.
   PDI's `req` runs `JSON.parse` on every body without guarding it, so
   binding them through it does not return the wrong thing — it throws a
   `SyntaxError` from inside the client, which reaches the operator as
   "Unexpected token <" and names nothing.

3. A key provider is `held` or `kms`. It is **not** `customer`, which is
   what the concept is called in the plan copy, in the hosting guarantees,
   and in the field `customer_managed` two lines from the one that rejects
   it.

4. A beacon's `disclose` is a single value, `blind` or `contact` — not the
   list of fields to reveal that the name suggests.

5. `ref_kind` is one of four (`transfer`, `intake`, `object`, `facility`)
   and a ring's `kind` one of four others. Both closed, both enforced.

6. A token's role is `read` or `write`.

Every one of those is the same shape: a plausible guess that the server
rejects, where a single call would have said so. Three of them the server
answers with the exact set of legal values, in the 422 body — so the unions
in `api.ts` are transcribed from the vault rather than invented.

## The audit could not see three of its own new doors

Adding `reqText` made the scan page and both `qr.svg` routes invisible to
`clientpaths`, which reads one shape of call. It reported them as newly
doorless in the same commit that gave them working buttons.

That is the third false positive an extractor has produced here — after the
nested template and the `<img src>` — and the lesson has not changed: the
audit reads one shape of call, so a new shape of call reads as no call.

## Two guards that could only pass while the problem existed

`test_the_union_is_still_wider_than_the_console` asserted the union backlog
was **strictly** smaller than the console's. `test_the_audit_is_actually_
looking_at_something` asserted the snapshot file was non-empty. Both were
sound while the backlog was hypothetical to close, and both could only be
satisfied by it staying open. They have been rewritten to check what they
were for — the console must still be producing call sites — rather than
what they happened to measure.
"""

from __future__ import annotations

import re
from pathlib import Path


def _repo_root() -> Path:
    for d in Path(__file__).resolve().parents:
        if (d / "pyproject.toml").exists():
            return d
    raise RuntimeError("no pyproject.toml above this test")


REPO = _repo_root()
API = REPO / "app" / "src" / "api.ts"
SCREENS = REPO / "app" / "src" / "screens"
HERE = Path(__file__).resolve().parent


def _api() -> str:
    return API.read_text(encoding="utf-8")


def _screen(name: str) -> str:
    return (SCREENS / name).read_text(encoding="utf-8")


L10N = REPO / "app" / "src" / "l10n.ts"
LANGS = ["en", "es", "fr", "de", "pt", "it", "ja", "zh", "hi", "ar"]


def _says(screen: str, key: str, english: str) -> list[str]:
    """A sentence a screen must keep, now that screens are localized.

    **0.48.2.** Every check in this file that a screen still says something
    greps the screen for the English. The moment a screen reads its words from
    a table instead, the sentence is still on the screen and the grep goes
    blind — which is this whole audit's shape, arriving in the audit's own
    guards. `test_the_guide_screen_keeps_both_of_its_refusals` was the first to
    hit it, and it went red on the round that localized the screen, which is
    the ratchet working rather than failing.

        asked     is this sentence in the screen file
        mattered  does the screen say it, in every language it offers

    So the sentence is followed to wherever it lives: the screen must ask for
    the key, and the table must hold it in all ten languages. That is stricter
    than the grep it replaces, which only ever proved the English existed.
    """
    problems = []
    if f'"{key}"' not in screen:
        problems.append(f"the screen no longer asks for {key}")
        return problems
    table = L10N.read_text(encoding="utf-8")
    m = re.search(r'"%s":\s*\{(.*?)\n  \}' % re.escape(key), table, re.S)
    if not m:
        problems.append(f"l10n.ts has no row for {key}")
        return problems
    row = m.group(1)
    missing = [l for l in LANGS if not re.search(r"\b%s:\s*\"" % l, row)]
    if missing:
        problems.append(f"{key} is missing {missing}")
    if english not in row:
        problems.append(f"{key}'s English is no longer {english!r}")
    return problems


# --- the three records reach zero -------------------------------------------

def test_the_console_backlog_record_is_empty():
    """Not short — empty. Every route in the vault is reachable from the
    desktop console on its own, without borrowing a phone."""
    rec = (HERE / "console_doorless.txt").read_text().strip()
    assert rec == "", f"still recorded as doorless from the console:\n{rec}"


def test_the_union_backlog_record_is_empty():
    rec = (HERE / "doorless_routes.txt").read_text().strip()
    assert rec == "", f"still recorded as doorless everywhere:\n{rec}"


def test_the_unused_binding_record_is_empty():
    rec = (HERE / "unused_bindings.txt").read_text().strip()
    assert rec == "", f"still called by nothing:\n{rec}"


# --- the six the wire corrected ---------------------------------------------

def test_receive_and_submit_use_their_own_tokens():
    """The correction that matters most, because both routes exist precisely
    so somebody who is *not* the tenant can use them."""
    src = _api()
    assert '"x-receive-token": receiveToken' in src, (
        "receiveTransfer is not sending the receive token — if it is sending "
        "a bearer token instead, the route is a 403 for everyone")
    assert '"x-submit-token": submitToken' in src
    assert "receiveTransfer: (tid: string, receiveToken: string)" in src
    assert "submitToIntake: (iid: string, submitToken: string," in src


def test_the_screen_says_the_tokens_are_not_the_tenants():
    flat = " ".join(_screen("Exchange.tsx").split())
    assert "The submit token is theirs, not yours" in flat
    assert "never served again" in flat


def test_the_markup_routes_do_not_go_through_the_json_helper():
    """`req` runs JSON.parse unguarded, so a markup body throws rather than
    returning something wrong — the loudest possible version of this bug and
    the least informative."""
    src = _api()
    assert "async function reqText(" in src
    for binding in ("scanPage:", "scanQr:", "connectorQr:"):
        i = src.index(binding)
        window = src[i:i + 200]
        assert "reqText(" in window, (
            f"{binding} is bound through the JSON helper again — it will "
            "throw 'Unexpected token <' rather than fail usefully")


def test_the_closed_sets_are_unions_rather_than_strings():
    """The server names every member of each in its own 422 body."""
    src = _api()
    for member in ('"transfer" | "intake" | "object" | "facility"',
                   '"delivery" | "access" | "collection" | "other"'):
        assert member in src, f"a closed set has drifted: {member}"
    assert 'disclose?: "blind" | "contact"' in src, (
        "`disclose` is a single value, not a list of fields to reveal")
    assert '"held" | "kms"' in src, (
        "the key provider union is gone — `customer` is the obvious guess "
        "and it is a 422")
    assert 'role: "read" | "write"' in src


def test_the_key_provider_is_not_called_customer_anywhere_in_the_binding():
    """The trap is that `customer` is the right word everywhere else — the
    field two lines away is literally `customer_managed`."""
    src = _api()
    i = src.index("setTenantKey:")
    assert '"customer"' not in src[i:i + 300]


# --- the screens actually call what they claim ------------------------------

def test_each_new_screen_calls_its_family():
    expected = {
        "Carriers.tsx": ("api.beacons(", "api.beacon(", "api.placeBeacon(",
                         "api.setBeaconState(", "api.liftBeacon(",
                         "api.beaconCustody(", "api.scanPage(",
                         "api.scanCard(", "api.scanQr(", "api.reportFound(",
                         "api.ringHolder(", "api.rings(",
                         "api.ringTranscript("),
        "Exchange.tsx": ("api.transfers(", "api.transfer(",
                         "api.sendTransfer(", "api.transferCustody(",
                         "api.withdrawTransfer(", "api.receiveTransfer(",
                         "api.intakes(", "api.intake(", "api.requestIntake(",
                         "api.intakeCustody(", "api.intakeFile(",
                         "api.cancelIntake(", "api.submitToIntake("),
        "Custody.tsx": ("api.tenantKey(", "api.setTenantKey(",
                        "api.surrenderTenantKey(", "api.resealUnderNewKey(",
                        "api.retireOldKeys(", "api.snapshot(",
                        "api.restoreRecords(", "api.restoreTenant(",
                        "api.deleteRecord(", "api.deleteTenant(",
                        "api.mintToken(", "api.revokeToken(",
                        "api.compliancePrograms(", "api.baaStatus(",
                        "api.tenantBaa(", "api.recordBaa(", "api.rescindBaa(",
                        "api.hostingModes(", "api.hosting(",
                        "api.hostingHistory(", "api.setHosting(",
                        "api.recordDeployment("),
        "Bridges.tsx": ("api.connectorCatalog(", "api.connectors(",
                        "api.addConnector(", "api.removeConnector(",
                        "api.connectorBeacon(", "api.connectorQr(",
                        "api.ingestToConnector(", "api.publishFromConnector(",
                        "api.roboticsCatalog(", "api.robots(",
                        "api.bindRobot(", "api.unbindRobot(",
                        "api.robotData(", "api.robotIngest(",
                        "api.contributions(", "api.contribute(",
                        "api.withdrawContribution(", "api.seedDemo("),
        "Guiding.tsx": ("api.guide(", "api.guideStep(", "api.guideForScreen(",
                        "api.guideProgress(", "api.startGuide(",
                        "api.finishGuideStep(", "api.askConsole(",
                        "api.dockFaces(", "api.dockWhere(", "api.dock(",
                        "api.dockFace(", "api.setDock(", "api.languages(",
                        "api.language(", "api.setLanguage(", "api.translate(",
                        "api.improvements(", "api.suggestImprovement("),
    }
    missing = []
    for name, bindings in expected.items():
        src = _screen(name)
        missing += [f"{name}: {b}" for b in bindings if b not in src]
    assert not missing, "screens no longer call:\n    " + "\n    ".join(missing)


def test_the_three_orphans_found_screens():
    """`api.auditSchema`, `api.gateChannel` and `api.revokeBequestGrant` were
    the whole of the unused-binding record and predate this round."""
    assert "api.auditSchema(" in _screen("Audit.tsx")
    assert "api.gateChannel(" in _screen("Continuity.tsx")
    assert "api.revokeBequestGrant(" in _screen("Continuity.tsx")


def test_the_audit_screen_can_say_what_an_action_means():
    """A log whose vocabulary is undocumented in the one place it is read is
    a log somebody has to guess at during an incident."""
    flat = " ".join(_screen("Audit.tsx").split())
    assert "What do these mean?" in flat


def test_nothing_paged_is_told_apart_from_nothing_could_be():
    """An empty page list on a deployment with no channel is not a quiet
    week. The screen showed the first and meant the second."""
    flat = " ".join(_screen("Continuity.tsx").split())
    assert "nothing could have been" in flat


def test_revoking_a_grant_is_offered_as_its_own_act():
    """Revoking the bequest and killing the token it already handed out are
    different things, and only the softer one had a button."""
    flat = " ".join(_screen("Continuity.tsx").split())
    assert "Revoke the grant token" in flat
    assert "not the same act" in flat


# --- what the screens must keep saying --------------------------------------

def test_the_carrier_card_says_custody_not_contents():
    flat = " ".join(_screen("Carriers.tsx").split())
    assert "there is no value of `disclose` that changes that" in flat


def test_the_custody_screen_leads_with_the_only_question():
    """Everything else on that page is downstream of whether the operator
    can decrypt, so it goes first and in the server's own words."""
    flat = " ".join(_screen("Custody.tsx").split())
    assert "Can the operator decrypt this?" in flat
    assert re.search(r"\{key\.note\}", flat)


def test_the_reseal_reports_what_it_could_not_touch():
    flat = " ".join(_screen("Custody.tsx").split())
    assert "customer_managed_skipped" in flat
    assert "how much of the vault the operator could not touch" in flat


def test_the_contributions_listing_is_a_count_not_contents():
    flat = " ".join(_screen("Bridges.tsx").split())
    assert "never contents" in flat


def test_the_guide_screen_keeps_both_of_its_refusals():
    """It has no name and no face, and it does no machine translation. Both
    are things the server states and a console could quietly imply away."""
    flat = " ".join(_screen("Guiding.tsx").split())
    problems = _says(flat, "gd.refused", "it cannot read")
    assert not problems, "the guide's refusal:\n    " + "\n    ".join(problems)
    assert "translated.engine" in flat or "engine:" in flat
