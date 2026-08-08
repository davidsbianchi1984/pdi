"""Customer custody, driven end to end, and the key kept off every disk.

The guard next door — `test_a_header_a_route_needs_is_a_header_its_callers_send`
— reads sources and asks whether a client *can* present `x-tenant-key`. This
one asks the vault. It adopts a customer key the way the Custody screen does,
then does the things an operator does next, and checks that each one works
with the key and is refused without it.

## Why both

The source guard would pass a client that sets the header to the empty string.
This one would pass a client that never sends it at all, because it does not
read clients. Neither is redundant, and the defect they were written for
needed both halves to be wrong at once:

    the console could spell it       on two heir routes
    the vault required it            on every record route
    nothing compared the two

## The refusals are the interesting half

`428 Precondition Required` is the right status and the sentence names the
header, so a client that gets one has been told exactly what to do. That was
true before this round too — and no client could act on it, which is the
difference between a good error message and a way out.

`DELETE /key` is the one to read twice. Handing custody back re-seals every
record under the deployment's key, which means opening them, which means the
customer key. Without it the hand-back is refused, so the button that undoes
customer custody was itself behind customer custody.
"""

from __future__ import annotations

import base64
import re
import secrets
from pathlib import Path

import pytest

from . import clientpaths as cp
from .conftest import new_tenant


def _key() -> str:
    return base64.b64encode(secrets.token_bytes(32)).decode()


@pytest.fixture()
def owned(client):
    """A tenant with a record, then moved under a key it holds itself."""
    auth = {"authorization": f"Bearer {new_tenant(client, 'byok')}"}
    assert client.put("/records", json={"key": "a/b", "value": "hello"},
                      headers=auth).status_code == 200
    key = _key()
    adopted = client.put("/key", json={"provider": "held", "key": key},
                         headers=auth)
    assert adopted.status_code == 201, adopted.text
    assert adopted.json()["custody"]["customer_managed"] is True
    return auth, dict(auth, **{"x-tenant-key": key}), key


def test_reading_a_record_needs_the_key(client, owned):
    without, with_key, _ = owned
    blind = client.get("/records/a/b", headers=without)
    assert blind.status_code == 428, blind.text
    assert "x-tenant-key" in blind.json()["detail"]
    assert client.get("/records/a/b", headers=with_key).json()["value"] == "hello"


def test_writing_a_record_needs_the_key(client, owned):
    without, with_key, _ = owned
    assert client.put("/records", json={"key": "c", "value": "v"},
                      headers=without).status_code == 428
    assert client.put("/records", json={"key": "c", "value": "v"},
                      headers=with_key).status_code == 200


def test_the_key_list_is_not_sealed_and_still_answers(client, owned):
    """Not everything is behind the key, and saying so is the point: an
    operator whose vault half-works is reading a real distinction rather than
    an intermittent fault. Keys are metadata; values are the sealed thing."""
    without, _, _ = owned
    assert client.get("/records", headers=without).status_code == 200
    assert client.get("/key", headers=without).json()["customer_managed"] is True


def test_the_way_back_needs_the_key_too(client, owned):
    """The hand-back is the case that made this a trap rather than a mode."""
    without, with_key, _ = owned
    assert client.delete("/key", headers=without).status_code == 428
    back = client.delete("/key", headers=with_key)
    assert back.status_code == 200, back.text
    assert back.json()["custody"]["customer_managed"] is False
    # And the vault is ordinary again, with the records intact.
    assert client.get("/records/a/b", headers=without).json()["value"] == "hello"


def test_a_wrong_key_is_refused_before_it_writes(client, owned):
    """A wrong key that sealed a record would make that record unopenable by
    anybody, including whoever presented it. Refused in front, deliberately."""
    without, _, _ = owned
    wrong = dict(without, **{"x-tenant-key": _key()})
    said = client.put("/records", json={"key": "d", "value": "v"}, headers=wrong)
    # 403 rather than 428: a key was presented, so this is not a missing
    # precondition — it is the wrong key, and the two need different fixes.
    assert said.status_code == 403, said.text
    assert "not the key" in said.json()["detail"]


#: Per client: (the key handed to a store call, any store call at all).
#:
#: A relationship rather than a distance. The first cut of this measured
#: *proximity* — the key named within four hundred characters of a store call
#: — and it fired on `heldKey` being declared below `clearBase()`, which
#: writes the base URL. Nearness is not the property; being the argument is.
KEY = r"heldKey|tenantKey|_tenantKey|TenantKeyBox"

PERSISTENCE = {
    "console": (cp.CONSOLE,
                r"(?:localStorage|sessionStorage)\.setItem\([^)]*(?:" + KEY + ")",
                r"localStorage\.setItem\("),
    "ios": (cp.IOS,
            r"(?:UserDefaults[^\n]*|SecItemAdd)[^\n]*(?:" + KEY + ")",
            r"UserDefaults"),
    "android": (cp.ANDROID,
                r"put\w+\([^)]*(?:" + KEY + ")",
                r"prefs\.edit\(\)"),
    "windows": (cp.WINDOWS,
                r"(?:LocalSettings|ApplicationData|PasswordVault)[^\n]*(?:" + KEY + ")",
                r"ApplicationData|LocalSettings"),
}

#: Comments and doc comments, in all four languages. Stripped before the
#: sweep runs, because every one of these clients now carries a paragraph
#: explaining that the key never goes near the platform's store — and a sweep
#: that read the prose would fail on the promise being kept.
_COMMENT = re.compile(r"/\*.*?\*/|^\s*(?:///|//|\*|<!--)[^\n]*$", re.S | re.M)


def _code(text: str) -> str:
    return _COMMENT.sub("", text)


@pytest.mark.parametrize("name", sorted(PERSISTENCE))
def test_no_client_writes_the_customer_key_down(name):
    """The half of this that is a security property rather than a feature.

    Making the key work everywhere is easy to do by storing it, and storing
    it is the one thing this custody mode promises nobody does. A client that
    kept it would move the whole guarantee from *the customer holds the key*
    to *the customer's browser profile holds the key*.
    """
    lang, stores_key, _ = PERSISTENCE[name]
    if not lang.root.exists():
        pytest.skip(f"{name} is not in this checkout")
    written = []
    for f in sorted(lang.root.rglob("*")):
        if f.suffix not in lang.suffixes or not f.is_file():
            continue
        text = _code(f.read_text(encoding="utf-8", errors="ignore"))
        for m in re.finditer(stores_key, text):
            written.append(f"{f.name}:{text[:m.start()].count(chr(10)) + 1}"
                           f" — {m.group(0).strip()}")
    assert not written, (
        f"{name} hands the customer key to storage:\n    "
        + "\n    ".join(written)
        + "\n  It is presented per request and held nowhere; being asked for "
          "it again after a restart is the guarantee working.")


def test_the_persistence_sweep_can_see_a_store_call():
    """A guard on the guard above: a pattern that matches nothing would
    report every client clean. Each client does store *something* — the base
    URL, the token — so the store shape must be reachable in its source."""
    for name, (lang, _, any_store) in sorted(PERSISTENCE.items()):
        if not lang.root.exists():
            continue
        seen = any(re.search(any_store, _code(
            f.read_text(encoding="utf-8", errors="ignore")))
            for f in lang.root.rglob("*")
            if f.suffix in lang.suffixes and f.is_file())
        assert seen, (f"{name}: {any_store!r} matches nothing in this client, "
                      "so the sweep above is passing on an empty search")


def test_the_console_holds_the_key_outside_react_state():
    """Where the console keeps it, and where it must not.

    Module scope in `api.ts`, not component state: React state is walked by
    devtools and serialised into every error overlay, and the Custody screen
    would otherwise carry the key in a props tree for as long as it is open.
    """
    src = (Path(cp.CONSOLE.root) / "api.ts").read_text(encoding="utf-8")
    assert re.search(r"^let heldKey: string \| null = null;", src, re.M), (
        "api.ts no longer holds the key at module scope")
    assert 'headers["x-tenant-key"] = heldKey' in src, (
        "the console holds a key it does not send")
    screen = (Path(cp.CONSOLE.root) / "screens" / "Custody.tsx").read_text(
        encoding="utf-8")
    assert "holdKey(" in screen, "no screen arms the key"
    assert "useState(keyIsHeld())" in screen, (
        "the screen tracks whether a key is armed, not the key itself")
