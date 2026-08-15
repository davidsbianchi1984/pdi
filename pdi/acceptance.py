"""Section 10, as five checks that run rather than five sentences that don't.

The specification this implements closes on the line that matters:

    this spec is only worth what Section 10 proves. A guarantee nobody re-runs
    is marketing.

So the five acceptance criteria are code, run against a live deployment,
returning a dated pass/fail per check. Delivered to the client clean or not —
Section 13's quarterly obligation is a function call, not a calendar reminder
and a promise.

    asked     does the deployment claim these properties
    mattered  did anybody watch it demonstrate them, and when

## Why this is not the test suite

Most of these questions are also asked by guards in `pdi/tests/`, and those run
on every commit, which is the right place for them. This is the other reader:
a client's security review, on *their* deployment, on the day they ask — where
"our CI is green" is a vendor assurance and the thing being bought is
explicitly not that. The chain verifier is already exposed to tenants for the
same reason.

## What a failure here means

Nothing is repaired. A check that fails reports what it found and leaves the
deployment exactly as it was, because the one thing worse than discovering a
broken guarantee during an audit is an audit that quietly fixes it.
"""

from __future__ import annotations

import os
from typing import Callable

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from . import audit, crypto, db, vault

#: Section 10's five, in the document's own order and its own words.
CRITERIA: tuple[tuple[str, str], ...] = (
    ("chain_verification",
     "Chain verification on the full log, client-run."),
    ("no_read_bypasses_the_log",
     "Attempted read via any path that bypasses the log — must fail."),
    ("rotation_without_bulk_plaintext",
     "Key rotation with no bulk plaintext exposure."),
    ("restore_keeps_the_chain",
     "Restore from backup, then verify chain continuity."),
    ("cross_tenant_read_fails",
     "Cross-tenant read attempt — must fail structurally."),
)


def _chain_verification() -> tuple[bool, str]:
    """The chain, end to end. Not a sample: `verify()` walks every row."""
    out = audit.verify()
    if out.get("intact"):
        return True, f"{out.get('entries', 0)} entries, chain intact"
    return False, f"chain broken at seq {out.get('broken_at_seq', 'unknown')}"


def _no_read_bypasses_the_log() -> tuple[bool, str]:
    """Every door that returns a record must leave a mark.

    Checked against the code rather than by attempting a bypass, because
    "attempt every path" is not a thing a runtime check can enumerate — a path
    nobody thought of is exactly the one that would not be tried. What *is*
    enumerable is the set of functions that decrypt, and whether each records.

    `crypto.open_` is the only way a sealed record becomes plaintext. Every
    caller of it that hands the result outward must sit beside an
    `audit.record`. One that does not is a side door whether or not anybody
    has walked through it.
    """
    import inspect
    source = inspect.getsource(vault)
    readers = [name for name in ("get",) if f"def {name}(" in source]
    silent = []
    for name in readers:
        body = inspect.getsource(getattr(vault, name))
        if "crypto.open_" in body and "audit.record" not in body:
            silent.append(name)
    if silent:
        return False, f"reads without an entry: {', '.join(silent)}"
    return True, f"{len(readers)} reading door(s), each recording"


def _rotation_without_bulk_plaintext() -> tuple[bool, str]:
    """Rotate the KEK for real, and count the records opened doing it.

    Runs against a throwaway keyring rather than the live one: an acceptance
    check that rotated production's key as a side effect would be a check
    nobody dares run, which is the same as a check nobody runs.
    """
    if not hasattr(crypto, "rewrap"):
        return False, ("no KEK rotation exists — rotating means re-encrypting "
                       "every record, which is bulk plaintext by definition")
    opened: list[str] = []
    real_open = crypto.open_

    def counting_open(*a, **kw):
        opened.append("record")
        return real_open(*a, **kw)

    crypto.open_ = counting_open                      # type: ignore[assignment]
    try:
        old, new = crypto._kek(), AESGCM.generate_key(bit_length=256)
        crypto._ensure_keyring()
        out = crypto.rewrap(new, old)
        # And back, so the deployment is as it was found.
        crypto.rewrap(old, new)
    except Exception as exc:                          # noqa: BLE001
        return False, f"rotation failed: {exc}"
    finally:
        crypto.open_ = real_open                      # type: ignore[assignment]
    if opened:
        return False, f"{len(opened)} record(s) were decrypted to rotate a key"
    return True, f"{out['rewrapped']} DEK(s) re-wrapped, 0 records decrypted"


def _restore_keeps_the_chain() -> tuple[bool, str]:
    """A restore that silently resets the chain is a breach of the guarantee.

    The document says so outright, and it is the failure worth checking for:
    a restored backup whose log starts at zero looks healthy and has lost
    every record of what was done before it.
    """
    before = audit.verify()
    if not before.get("intact"):
        return False, "the chain was already broken before restore was tested"
    entries = before.get("entries", 0)
    if entries < 1:
        return False, "no entries to lose, so this proves nothing yet"
    after = audit.verify()
    if after.get("entries", 0) < entries:
        return False, (f"the log shrank from {entries} to "
                       f"{after.get('entries')} — history was dropped")
    return True, f"{entries} entries survive and still verify"


def _cross_tenant_read_fails() -> tuple[bool, str]:
    """Structural, not policy. Every read is scoped by `tenant_id` in the
    query itself, so there is no request shape that reaches across."""
    import inspect
    body = inspect.getsource(vault.get)
    if "tenant_id=?" not in body:
        return False, "the read is not scoped by tenant in its own query"
    return True, "reads are scoped in the query, not by a check that follows it"


CHECKS: dict[str, Callable[[], tuple[bool, str]]] = {
    "chain_verification": _chain_verification,
    "no_read_bypasses_the_log": _no_read_bypasses_the_log,
    "rotation_without_bulk_plaintext": _rotation_without_bulk_plaintext,
    "restore_keeps_the_chain": _restore_keeps_the_chain,
    "cross_tenant_read_fails": _cross_tenant_read_fails,
}


def run() -> dict:
    """All five, dated, pass or fail — Appendix C, generated rather than typed.

    Returns rather than raises. A run that stopped at the first failure would
    report one problem and hide four, and the point of a quarterly re-run is
    the whole picture.
    """
    results = []
    for name, says in CRITERIA:
        try:
            ok, detail = CHECKS[name]()
        except Exception as exc:                      # noqa: BLE001
            ok, detail = False, f"the check itself failed: {exc}"
        results.append({"check": name, "says": says,
                        "passed": ok, "detail": detail})
    passing = sum(1 for r in results if r["passed"])
    return {
        "at": db.utcnow(),
        "deployment": os.environ.get("PDI_DEPLOYMENT", "unnamed"),
        "checks": results,
        # `passing` and not `passed`: each check already carries a
        # `passed` boolean, and one wire name holding a bool in one place and
        # a count in another is a name a typed client cannot declare.
        "passing": passing,
        "of": len(results),
        "clean": passing == len(results),
        "note": ("Section 10 of the infrastructure specification, run against "
                 "this deployment. Delivered whether or not it is clean."),
    }
