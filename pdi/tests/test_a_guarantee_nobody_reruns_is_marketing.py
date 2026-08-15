"""Section 10, and the sentence the specification closes on.

    this spec is only worth what Section 10 proves. A guarantee nobody re-runs
    is marketing. Schedule the tests before you sign the lease.

Five acceptance criteria were written down. Three of them were already asked by
guards in this suite, which is the right place for them and the wrong place for
a client — CI being green is a vendor assurance, and a vendor assurance is
precisely what a sovereignty proposition is not selling.

    asked     does the deployment have these properties
    mattered  can the client watch it demonstrate them, on their machine, dated

`pdi/acceptance.py` is that: the five, runnable, returning pass or fail per
check with a timestamp. This file is the guard on the guard — it checks that
the acceptance suite covers what the document says it covers, and that it stays
honest when the property underneath it is removed.

## The one that was actually missing

*"Key rotation with no bulk plaintext exposure"* would have failed. `rotate()`
mints a new DEK and `reseal_all()` then decrypts and re-encrypts every record
under it — correct when a DEK is suspect, and bulk plaintext once a year to
change a key that never touched the records.

`crypto.rewrap` is the operation the envelope model exists for and the module
did not have: unwrap each stored DEK under the old KEK, seal it again under the
new one, records never opened.
"""

from __future__ import annotations

import inspect

import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from pdi import acceptance, crypto, vault


@pytest.fixture()
def sealed(tmp_path, monkeypatch):
    """A deployment with something in it. Several checks are vacuous on an
    empty vault, and a check that passes on nothing is the failure this whole
    file exists to avoid."""
    monkeypatch.setenv("PDI_DB", str(tmp_path / "pdi.db"))
    from pdi import db as pdi_db
    pdi_db.reset()
    tenant = vault.create_tenant("acme")
    vault.put(tenant, "patient/1", "something private")
    vault.get(tenant, "patient/1")
    yield tenant
    pdi_db.reset()


def test_all_five_criteria_are_covered():
    """The document lists five. A suite that quietly dropped one would report
    a clean run over four."""
    assert len(acceptance.CRITERIA) == 5
    assert set(acceptance.CHECKS) == {name for name, _ in acceptance.CRITERIA}


def test_each_criterion_carries_the_documents_own_words():
    """So a client reading the output can match it to the clause they were
    sold, rather than to a name somebody invented for it here."""
    for name, says in acceptance.CRITERIA:
        assert says.endswith("."), f"{says!r} is a label, not the clause"
        # Measured against the check's own name rather than a literal: the
        # claim is that the clause says more than the identifier does, which
        # is what makes it quotable back to the contract.
        assert len(says.split()) > len(name.split("_")), (
            f"{name}: the clause {says!r} says no more than its own name")


def test_a_clean_run_is_clean_and_says_when(sealed):
    """The whole deliverable: dated, pass/fail, per check."""
    out = acceptance.run()
    assert out["of"] == 5
    assert out["clean"] is True, (
        "acceptance is not clean on a healthy deployment:\n    "
        + "\n    ".join(f"{c['check']}: {c['detail']}"
                        for c in out["checks"] if not c["passed"]))
    assert out["at"], "the run is undated, so it proves nothing next quarter"


def test_rotation_opens_no_records(sealed):
    """The criterion that would have failed before this round.

    Driven rather than asserted: `crypto.open_` is replaced with a counter for
    the duration, so "no bulk plaintext" is measured rather than promised.
    """
    opened = []
    real = crypto.open_
    crypto.open_ = lambda *a, **k: (opened.append(1), real(*a, **k))[1]
    try:
        old, new = crypto._kek(), AESGCM.generate_key(bit_length=256)
        out = crypto.rewrap(new, old)
        crypto.rewrap(old, new)
    finally:
        crypto.open_ = real
    assert out["rewrapped"] >= 1
    assert opened == [], (
        f"{len(opened)} record(s) were decrypted to rotate a key that never "
        "touches record data")


def test_the_records_still_open_after_the_key_that_wraps_them_changed(sealed):
    """The point of re-wrapping: the DEK inside is unchanged, so every
    existing ciphertext still decrypts. A rotation that sealed the vault shut
    would pass a "no plaintext" check perfectly."""
    old, new = crypto._kek(), AESGCM.generate_key(bit_length=256)
    crypto.rewrap(new, old)
    monkey = crypto._kek
    crypto._kek = lambda: new
    try:
        assert vault.get(sealed, "patient/1")["value"] == "something private"
    finally:
        crypto._kek = monkey
        crypto.rewrap(old, new)


def test_a_wrong_old_key_changes_nothing(sealed):
    """All or nothing. A keyring half re-wrapped is one where half the records
    are unopenable and nothing says which half — categorically worse than the
    failure it protects against."""
    before = [r["wrapped_dek"] for r in
              crypto.db.connect().execute(
                  "SELECT wrapped_dek FROM key_versions ORDER BY version")]
    wrong = AESGCM.generate_key(bit_length=256)
    with pytest.raises(crypto.CustomerKeyMismatch):
        crypto.rewrap(AESGCM.generate_key(bit_length=256), wrong)
    after = [r["wrapped_dek"] for r in
             crypto.db.connect().execute(
                 "SELECT wrapped_dek FROM key_versions ORDER BY version")]
    assert after == before, "a refused rotation still wrote to the keyring"


def test_the_rewrap_is_recorded(sealed):
    """Section 3 has no exceptions, and a key rotation is exactly the event a
    reviewer goes looking for."""
    from pdi import audit
    old, new = crypto._kek(), AESGCM.generate_key(bit_length=256)
    crypto.rewrap(new, old)
    crypto.rewrap(old, new)
    actions = [e["action"] for e in audit.entries(None)] \
        if hasattr(audit, "entries") else []
    rows = crypto.db.connect().execute(
        "SELECT action FROM audit WHERE action='key.rewrap'").fetchall()
    assert len(rows) >= 2, f"the rotation left no entry (actions seen: {actions})"
    assert "key.rewrap" in audit.ACTIONS, (
        "the action is not in the catalogue, so the log has a row nothing "
        "can explain to a reader")


def test_a_failing_check_repairs_nothing():
    """An audit that quietly fixed what it found would be worse than none —
    the finding is the product."""
    source = inspect.getsource(acceptance)
    for verb in ("reseal_all(", "wipe(", "purge("):
        assert verb not in source, (
            f"acceptance calls {verb} — it is meant to observe, not to mend")


def test_the_report_is_returned_whole_even_when_something_fails(sealed,
                                                                monkeypatch):
    """Section 13 delivers results to the client whether or not they are
    clean, so a run that stopped at the first failure would report one problem
    and hide four."""
    monkeypatch.setitem(acceptance.CHECKS, "chain_verification",
                        lambda: (False, "pretend"))
    out = acceptance.run()
    assert out["of"] == 5 and out["clean"] is False
    assert out["passing"] == 4, (
        "one failure took the others down with it, so the report names one "
        "problem and conceals the rest")
