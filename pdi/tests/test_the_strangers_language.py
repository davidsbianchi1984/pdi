"""The four pages PDI serves to people who are not tenants, in their language.

## The finding

Every localization path in this vault takes a ``tenant_id``. `get_pref`,
`get_language`, `effective_language` all do, and the response middleware asks
the *calling tenant* what language it reads in. That is right for the API,
whose callers are all tenants under contract.

PDI serves four pages to people who are not tenants and never will be:

* `/s/{id}` — a courier or a warehouse clerk pointing a phone at a sticker on
  a sealed carrier, deciding what to do with the thing in their hands.
* `/s/{id}` on a gate beacon — somebody standing at a controlled facility
  wanting to be let in, or told they cannot be.
* `/s/{id}` for a code that resolves to nothing.
* `/r/{id}` — the recipient of a sealed transfer, who `receive_transfer`
  itself describes as holding "no tenant credential; the token itself is the
  (auditable) authorization".

All four were English only, whatever the reader's browser said. The header was
arriving on every one of those requests and nothing looked at it. It is the
same shape of defect this audit found in QRME's objector screen and JIM's
beacon page, one layer up from the doors themselves: not *can they reach it*
but *can they read it when they do*.

## What this file checks

Not that a table exists — a table nobody consults is the "binding is not a
door" mistake in a new costume. It renders each page, in each language, and
asks whether the English is gone. The list of strings to check is derived from
the table and the pages themselves, so a sentence added next year is covered
without anybody remembering this file.

That derivation caught a real one while this round was being written: eleven
entries went into the table with a literal ``\\u2014`` in the key instead of an
em dash, so their lookups could never match and every page fell back to
English while the table looked full and complete.
"""

from __future__ import annotations

import html
import json
import re

from pdi import i18n, landing

from .conftest import new_tenant

#: Everything except English. `HAND_TRANSLATED` is the module's own name for
#: this, so a language added to `SUPPORTED` is covered here the day it lands.
OTHERS = i18n.HAND_TRANSLATED

CARD = {
    "reference": "PDI-CARRIER-1",
    "badge": "SEALED CUSTODY CARRIER",
    "state": "in transit",
    "programs": ["hipaa", "osha"],
    "held_by": "Acme Freight",
    "note": "Ring for the duty officer.",
}


def _pages(language: str) -> dict[str, str]:
    """Every page a person with no account can be sent to.

    Both branches of the carrier card, because they are different pages to
    the person reading them: one names who to give the thing back to, the
    other explains why it will not. The second was missing from the first
    draft of this fixture and its sentence went untranslated-and-unnoticed
    for as long as that lasted.
    """
    return {
        "sealed carrier": landing.seal_card_page(CARD, language),
        "sealed carrier, holder withheld":
            landing.seal_card_page({k: v for k, v in CARD.items()
                                    if k != "held_by"}, language),
        "facility gate": landing.gate_page(dict(CARD, gate=True), language),
        "dead code": landing.gone(language),
        "recipient": landing.receive_page("t_abc", language),
    }


def _visible(page: str) -> str:
    """The page as a person reads it.

    Scripts out: they are checked separately through their string blobs, and
    leaving them in would mean searching for the row label "State" in a
    document containing `history.replaceState` and the button "Ring" in one
    containing "Ringing" — a check that can never pass and would be deleted
    rather than fixed.

    Entities in: ``html.escape`` turns every apostrophe into ``&#x27;``, so
    six of this page's seven longest sentences do not appear in their own
    markup. Comparing the source against the English would have quietly
    excused exactly the sentences that matter most.
    """
    return html.unescape(re.sub(r"<script>.*?</script>", "", page, flags=re.S))


def _ours(page: str) -> str:
    """What is left after the tenant's own words are taken out.

    The card's values — the holder's name, the state, the programs, and the
    free-text note — are passed through verbatim on purpose, and the test
    below asserts that. They are also English, and a note reading "Ring for
    the duty officer" contains the gate button's entire label. Searching the
    whole page for "Ring" therefore finds the tenant's sentence and calls it
    an untranslated button.

    That is this audit's own shape, in a test written for this audit: asking
    whether the English appears *anywhere* when what matters is whether it
    appears in the part of the page we wrote.
    """
    visible = _visible(page)
    for value in CARD.values():
        for word in (value if isinstance(value, list) else [value]):
            visible = visible.replace(str(word), "").replace(
                str(word).upper(), "")
    return visible


def _blobs(page: str) -> list[dict]:
    """The `var S={...}` objects the inline scripts read their words from."""
    return [json.loads(m) for m in
            re.findall(r"var S=(\{.*?\}),", page, flags=re.S)]


def _what_a_recipient_is_told(client, language: str) -> list[str]:
    """Everything the recipient route says back, driven rather than listed.

    Three of this vault's stranger-facing sentences never appear on a page:
    they arrive in the response after the button is pressed — the refusal,
    the revocation, and the custody line on success. That is the moment a
    person is most invested and least able to guess, and the moment the page
    around them stops being the thing they are reading.

    Nothing will ever localize them by any other route. The response
    middleware keys on the calling tenant's language and this caller has no
    tenant — which is the same gap, one layer in, that left these four pages
    English in the first place.
    """
    # The fixture's client, not a fresh `create_app()`: the vault's master
    # key and database come from the fixture's environment, and an app built
    # outside it decrypts a previous run's ciphertext with a new key and
    # fails on the tag rather than on anything this test is about.
    head = {"Accept-Language": language}
    said = []
    token = new_tenant(client)
    made = client.post(
        "/transfers", headers={"Authorization": f"Bearer {token}"},
        json={"recipient": "dana@example.com", "filename": "labs.pdf",
              "content": "x", "programs": []})
    assert made.status_code == 201, made.text
    transfer = made.json()

    wrong = client.post(f"/transfers/{transfer['id']}/receive",
                        headers={**head, "x-receive-token": "nope"})
    said.append(wrong.json()["detail"])

    got = client.post(
        f"/transfers/{transfer['id']}/receive",
        headers={**head, "x-receive-token": transfer["receive_token"]})
    assert got.status_code == 200, got.text
    said.append(got.json()["custody"])

    second = client.post(
        "/transfers", headers={"Authorization": f"Bearer {token}"},
        json={"recipient": "d", "filename": "f", "content": "x",
              "programs": []}).json()
    client.delete(f"/transfers/{second['id']}",
                  headers={"Authorization": f"Bearer {token}"})
    revoked = client.post(
        f"/transfers/{second['id']}/receive",
        headers={**head, "x-receive-token": second["receive_token"]})
    assert revoked.status_code == 410
    said.append(revoked.json()["detail"])
    return said


def test_the_table_is_complete_in_every_language():
    """Ten languages or none.

    A partially translated page is worse than an English one: it reads as
    broken software rather than as software in another language, and the
    person reading it is a courier deciding what to do with a sealed carrier.
    """
    ragged = {text: sorted(set(OTHERS) - set(row))
              for text, row in i18n._PAGE_STRINGS.items()
              if set(OTHERS) - set(row)}
    assert not ragged, (
        "these page strings are missing translations:\n    "
        + "\n    ".join(f"{text[:48]!r}: {missing}"
                        for text, missing in sorted(ragged.items())))


def test_no_page_string_key_carries_an_escape_sequence():
    """The one that actually happened.

    Eleven entries were written with a literal ``\\u2014`` where an em dash
    belonged. Python does not unescape that inside an already-decoded string,
    so the key was six characters longer than any text the page would ever
    ask for. Every lookup missed, every page fell back to English, and the
    table looked complete — 44 entries, all ten languages, all useless.

    Nothing about that failure is visible from the table. It is only visible
    from asking whether the key is the thing the page says.
    """
    escaped = sorted(k for k in i18n._PAGE_STRINGS if re.search(r"\\[uUxN]", k))
    assert not escaped, (
        "these keys contain a backslash escape rather than the character it "
        "names, so nothing will ever match them:\n    "
        + "\n    ".join(repr(k[:60]) for k in escaped))


def test_every_page_string_is_asked_for_by_a_page(client):
    """A table entry nobody looks up is a translation nobody reads.

    The mirror of the check below, and the reason both exist: that one finds
    English left on a translated page, this one finds a translation that no
    page will ever show. Between them there is nowhere for a string to hide.
    """
    english = "".join(_ours(p) for p in _pages("en").values())
    english += "".join(json.dumps(b, ensure_ascii=False)
                       for p in _pages("en").values() for b in _blobs(p))
    # The route's own sentences count as reachable too — they are read by the
    # same person, a second after the page is.
    english += "".join(_what_a_recipient_is_told(client, "en"))
    orphans = sorted(
        text for text in i18n._PAGE_STRINGS
        # The holder line is a template; its English never appears whole.
        if "{" not in text and text not in english)
    assert not orphans, (
        "these strings are translated into nine languages and shown to "
        "nobody:\n    " + "\n    ".join(repr(t[:56]) for t in orphans))


def test_no_english_survives_on_a_translated_page():
    """The check that would have failed before this round, on all four pages.

    Derived rather than listed: every entry in the table whose English shows
    up on an English rendering must be gone from the translated one. A
    sentence added to a page next year is covered by this the day somebody
    adds its translations, and fails it loudly if they do not.
    """
    english_pages = {name: _ours(p) for name, p in _pages("en").items()}
    left = []
    for language in OTHERS:
        for name, page in _pages(language).items():
            visible = _ours(page)
            for text in i18n._PAGE_STRINGS:
                if "{" in text or text not in english_pages[name]:
                    continue
                if text in visible:
                    left.append(f"{language} / {name}: {text[:52]!r}")
    assert not left, (
        "these pages still show English to somebody whose browser asked for "
        "another language:\n    " + "\n    ".join(left))


def test_the_scripts_speak_the_readers_language_too():
    """"Recording…", "No connection", "Passed to" — the words a person sees
    *after* they press the button, which is when they are most invested and
    least able to guess.

    The server's own `note` and `detail` still win where it sends them: those
    come back through the response middleware in the tenant's language, and
    the tenant's specific sentence beats this file's generic one. That is a
    deliberate choice and not what this checks.
    """
    english = {value for page in _pages("en").values()
               for blob in _blobs(page) for value in blob.values()}
    assert english, "the pages carry no script strings — has the blob moved?"
    stuck = []
    for language in OTHERS:
        for name, page in _pages(language).items():
            for blob in _blobs(page):
                stuck += [f"{language} / {name}: {k}={v[:34]!r}"
                          for k, v in blob.items() if v in english]
    assert not stuck, (
        "these inline scripts still say their words in English:\n    "
        + "\n    ".join(stuck))


def test_the_page_declares_the_language_and_the_direction():
    """`lang` is what a screen reader picks a voice from, and these pages are
    read by people with their hands full. `dir` because Arabic is one of the
    ten and a right-to-left page laid out left-to-right is unreadable rather
    than merely untranslated."""
    for language in i18n.SUPPORTED:
        expected = "rtl" if language == "ar" else "ltr"
        for name, page in _pages(language).items():
            assert f'<html lang="{language}" dir="{expected}">' in page, (
                f"the {name} page does not declare lang={language} "
                f"dir={expected}")


def test_the_option_values_stay_in_the_apis_vocabulary():
    """What the visitor reads is translated; what `ring` matches on is not.

    Translating `value="delivery"` would make every gate call from a
    non-English phone arrive with a kind the backend has never heard of, and
    the failure would look like a data problem rather than a translation one.
    """
    for language in i18n.SUPPORTED:
        page = landing.gate_page(dict(CARD, gate=True), language)
        for value in ("delivery", "collection", "access", "other"):
            assert f'<option value="{value}">' in page, (
                f"the {language} gate page has lost the {value!r} option "
                "value — the backend matches on these")


def test_the_card_data_is_never_translated():
    """The labels are ours; the values are the tenant's.

    `held_by` is a company's name, `state` and the program chips are the
    card's own facts. Running them through a translation table would be
    inventing, and on a custody card an invented fact is the whole problem.
    """
    for language in OTHERS:
        page = landing.seal_card_page(CARD, language)
        assert "Acme Freight" in page, (
            f"the holder's name was altered on the {language} page")
        assert "in transit" in page, (
            f"the card's state was altered on the {language} page")
        assert "HIPAA" in page and "OSHA" in page, (
            f"the program chips were altered on the {language} page")


# --- what the header actually does ------------------------------------------


def test_negotiate_reads_a_header_the_way_a_browser_sends_one():
    assert i18n.negotiate(None) == "en"
    assert i18n.negotiate("") == "en"
    assert i18n.negotiate("es-ES,es;q=0.9,en;q=0.8") == "es"
    assert i18n.negotiate("es-419") == "es", "the region must be dropped"
    assert i18n.negotiate("tlh,ja") == "ja", "unknown tags are skipped"
    assert i18n.negotiate("xx,yy") == "en", "nothing known falls back"
    assert i18n.negotiate("fr;q=0.4,de;q=0.9") == "de", "q is honoured"
    assert i18n.negotiate("fr,es") == "fr", "equal q keeps the header's order"
    assert i18n.negotiate("ar;q=0") == "en", "q=0 means 'not this one'"
    assert i18n.negotiate("JA-JP") == "ja", "tags are case-insensitive"


def test_the_recipient_page_answers_in_the_language_the_browser_asked_for():
    """Driven through the route, not the function.

    The function taking a `language` argument proves nothing about whether
    anything passes one — that is this audit's most repeated mistake, and it
    would be a poor round that reproduced it in the fix.
    """
    from fastapi.testclient import TestClient

    from pdi.api import create_app

    with TestClient(create_app()) as client:
        plain = client.get("/r/t_abc")
        assert plain.status_code == 200
        assert '<html lang="en"' in plain.text, (
            "a request with no Accept-Language must still get English")

        hindi = client.get("/r/t_abc",
                           headers={"Accept-Language": "hi-IN,en;q=0.5"})
        assert '<html lang="hi"' in hindi.text, (
            "the recipient route is not passing Accept-Language through to "
            "the page — the header arrives and nothing reads it, which is "
            "the whole defect this round is about")
        assert i18n.tr_page("Collect it", "hi") in hindi.text, (
            "the page came back declaring Hindi and speaking English")
        assert "Collect it" not in _visible(hindi.text)

        arabic = client.get("/r/t_abc", headers={"Accept-Language": "ar"})
        assert '<html lang="ar" dir="rtl">' in arabic.text, (
            "an Arabic reader is getting a left-to-right page")


def test_the_scanned_sticker_answers_in_the_readers_language(client):
    """The courier's page, through a real beacon on a real deployment."""
    token = new_tenant(client)
    made = client.post("/beacons",
                       json={"ref_kind": "object", "label": "crate 9"},
                       headers={"Authorization": f"Bearer {token}"})
    assert made.status_code == 201, made.text
    bid = made.json()["id"]

    english = client.get(f"/s/{bid}")
    assert english.status_code == 200
    assert '<html lang="en"' in english.text

    japanese = client.get(f"/s/{bid}", headers={"Accept-Language": "ja"})
    assert '<html lang="ja"' in japanese.text, (
        "the scanned-sticker route is not passing Accept-Language through — "
        "a courier in Osaka gets the carrier card in English")
    assert i18n.tr_page("I found this", "ja") in japanese.text
    assert "I found this" not in _visible(japanese.text)

    # And the page for a code that resolves to nothing, which is served on the
    # same route and was the easiest of the four to forget.
    missing = client.get("/s/does-not-exist",
                         headers={"Accept-Language": "de-DE"})
    assert missing.status_code == 404
    assert '<html lang="de"' in missing.text, (
        "the page for a code that resolves to nothing is served on the same "
        "route and was the easiest of the four to leave in English")
    assert i18n.tr_page("Nothing here", "de") in missing.text


# --- what the route says, not what the page says ----------------------------


def test_the_recipient_route_is_not_an_oracle(client):
    """The guard beside this one reads the wrong file.

    `test_the_recipient_page_does_not_confirm_which_ids_exist` asserts that
    `GET /r/{tid}` never 404s, so the page cannot be used to ask whether a
    transfer id is real. That is true and worth keeping. It is also not where
    an id gets probed.

    `POST /transfers/{tid}/receive` takes **no credential of any kind** — that
    is the whole design, the token in the header is the authorization — and
    until this round it answered 404 "transfer not found" for an id that did
    not exist and 403 "invalid receive token" for one that did. Anybody with
    a shell could walk ids and learn which sealed transfers are real. For
    compliance-grade material that is a disclosure before anything is opened.

    The audit's recurring shape, on a route rather than a screen this time:

        asked     does the *page* confirm which ids exist
        mattered  does the *route* — the one anybody can call directly
    """
    token = new_tenant(client)
    made = client.post(
        "/transfers", headers={"Authorization": f"Bearer {token}"},
        json={"recipient": "dana@example.com", "filename": "labs.pdf",
              "content": "x", "programs": []})
    assert made.status_code == 201, made.text
    real = made.json()["id"]

    exists = client.post(f"/transfers/{real}/receive",
                         headers={"x-receive-token": "wrong"})
    absent = client.post("/transfers/xfer_nothinghere/receive",
                         headers={"x-receive-token": "wrong"})
    assert exists.status_code == absent.status_code, (
        f"a real transfer answers {exists.status_code} and an invented id "
        f"answers {absent.status_code}, so this route tells anybody with a "
        "shell which transfer ids exist")
    assert exists.json() == absent.json(), (
        "the two answers differ in their body, which is the same oracle one "
        f"layer down:\n    real:   {exists.json()}\n    "
        f"invented: {absent.json()}")


def test_revocation_still_reaches_the_person_holding_the_token(client):
    """The other half, and why collapsing the two above is safe.

    A revoked transfer must still say so — to the recipient. `transfers.
    receive` matches the token hash *before* it looks at status, so 410 is
    unreachable without the real token and discloses nothing to anybody
    walking ids. Somebody who was sent a file and finds it withdrawn should
    be told that, not left with a refusal that reads like their own mistake.
    """
    token = new_tenant(client)
    made = client.post(
        "/transfers", headers={"Authorization": f"Bearer {token}"},
        json={"recipient": "d", "filename": "f", "content": "x",
              "programs": []}).json()
    client.delete(f"/transfers/{made['id']}",
                  headers={"Authorization": f"Bearer {token}"})

    with_token = client.post(
        f"/transfers/{made['id']}/receive",
        headers={"x-receive-token": made["receive_token"]})
    assert with_token.status_code == 410, (
        "the recipient is no longer told the transfer was revoked")

    without = client.post(f"/transfers/{made['id']}/receive",
                          headers={"x-receive-token": "wrong"})
    assert without.status_code != 410, (
        "410 is reachable without the receive token, so 'revoked' has become "
        "a way of confirming an id exists")


def test_what_the_recipient_is_told_arrives_in_their_language(client):
    """The refusal, the revocation and the custody line.

    None of them is on the page, so the four checks above cannot see them,
    and nothing else will ever translate them: the response middleware keys
    on the calling tenant's language and this caller has no tenant. That is
    the same gap that left these pages English, one layer in — and it lands
    at the moment somebody has just pressed the button and something has
    either gone wrong or been recorded about them.
    """
    english = _what_a_recipient_is_told(client, "en")
    assert all(s in i18n._PAGE_STRINGS for s in english), (
        f"the route says something the table does not have: {english}")

    for language in ("es", "ja", "ar"):
        said = _what_a_recipient_is_told(client, language)
        assert len(said) == len(english)
        for source, got in zip(english, said):
            assert got == i18n.tr_page(source, language), (
                f"the recipient route still answers in English for a "
                f"{language} reader: {source[:44]!r}")
