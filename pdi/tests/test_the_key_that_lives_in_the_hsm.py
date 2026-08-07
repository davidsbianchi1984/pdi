"""`KmsKeyProvider.kek()` raised `NotImplementedError` and called itself a seam.

That was an honest label and it was load-bearing: `crypto.custody()` reports
``"limits": ["Integration seam — KmsKeyProvider.kek() is not implemented."]``,
so a customer reading the custody statement was told the truth. But a vault
whose production key path does not exist has one deployment mode, and it is the
one where the key sits in an environment variable on the app host.

This file is the other mode, driven.

## What "unwrap, not fetch" buys, and why it is the whole design

PDI does not ask the KMS *for* a key. It stores a **wrapped** KEK — the
ciphertext blob the KMS returned when the key was created — and asks the KMS to
decrypt it. Three things follow, and each has a test here:

* a database or environment leak yields a blob that is useless without the
  KMS, which enforces its own policy on every call;
* every unwrap is a line in the customer's own audit trail rather than
  something that quietly happened inside this process;
* the **encryption context** binds the blob to this deployment and this key
  id, so a blob copied out of one deployment cannot be replayed in another
  that the same KMS key happens to allow.

## Nothing falls back

The refusal tests are the point of the file. A vault that seals under a local
key when the HSM is unreachable has turned an outage into a silent, permanent
downgrade of its central claim — every record written during the outage is
sealed under the wrong key, and nobody finds out until a restore. So every
missing library, missing configuration and failed call raises
:class:`crypto.KmsUnavailable`, and a separate exception class exists so a
caller can tell *the key store is down* from *the key is wrong*.

## What has not been exercised

**No live AWS or HSM call was made from this repository.** That needs
credentials and hardware this project does not have. The contract is driven
against an injected client with boto3's exact `decrypt(CiphertextBlob=,
KeyId=, EncryptionContext=) -> {"Plaintext": ...}` signature — so a double
that satisfies these tests is one that would satisfy AWS — but the `_aws` and
`_pkcs11` call sites themselves are unrun and marked as such. Read them before
pointing a deployment at production.
"""

import base64

import pytest

from pdi import crypto, db


KEK = b"K" * 32
BLOB = b"a-ciphertext-blob-only-the-kms-can-open"


class FakeKms:
    """boto3's `kms` client, as far as this provider uses it.

    The signature is copied from AWS rather than invented, because a double
    with a convenient shape would let the provider be wrong in exactly the way
    the double was wrong too.
    """

    def __init__(self, kek=KEK, expect_context=True):
        self.kek, self.expect_context = kek, expect_context
        self.calls = []

    def decrypt(self, *, CiphertextBlob, KeyId, EncryptionContext=None):
        self.calls.append({"blob": CiphertextBlob, "key_id": KeyId,
                           "context": EncryptionContext})
        if CiphertextBlob != BLOB:
            raise RuntimeError("InvalidCiphertextException")
        if self.expect_context and not EncryptionContext:
            raise RuntimeError("InvalidCiphertextException: context mismatch")
        return {"Plaintext": self.kek, "KeyId": KeyId}


@pytest.fixture(autouse=True)
def _clean_kms(monkeypatch):
    """Every case starts with an empty cache and a configured KMS.

    The cache is process-global on purpose (it is a performance property of
    the deployment, not of a request), which makes clearing it between cases
    a correctness requirement rather than tidiness.
    """
    crypto.clear_kek_cache()
    monkeypatch.setenv("PDI_KMS_KEY_ID", "arn:aws:kms:eu-west-1:1:key/abc")
    monkeypatch.setenv("PDI_KMS_WRAPPED_KEK",
                       base64.b64encode(BLOB).decode())
    yield
    crypto.clear_kek_cache()


# --- the contract -----------------------------------------------------------

def test_the_provider_asks_the_kms_to_unwrap_rather_than_to_hand_over_a_key():
    """The distinction the whole design rests on. `decrypt` of a stored blob,
    never `generate` or a fetch — so what this deployment holds is useless
    without the KMS."""
    fake = FakeKms()
    got = crypto.KmsKeyProvider(client=fake).kek()
    assert got == KEK
    assert len(fake.calls) == 1
    assert fake.calls[0]["blob"] == BLOB
    assert fake.calls[0]["key_id"].startswith("arn:aws:kms:")


def test_the_blob_is_bound_to_this_deployment_by_an_encryption_context():
    """Without it, a wrapped KEK lifted from one deployment's environment
    decrypts in any other the same KMS key allows — the blob stops being a
    secret about *this* vault and becomes a bearer token for the key."""
    fake = FakeKms()
    crypto.KmsKeyProvider(client=fake).kek()
    ctx = fake.calls[0]["context"]
    assert ctx, "no encryption context was sent"
    assert ctx["pdi:key_id"] == "arn:aws:kms:eu-west-1:1:key/abc"
    assert ctx["pdi:purpose"] == "record-kek"


def test_a_tenants_own_key_id_wins_over_the_deployments():
    """BYOK. A tenant that brought its own key must not be unwrapped against
    the operator's."""
    fake = FakeKms()
    crypto.KmsKeyProvider(key_id="tenant-key-9", client=fake).kek()
    assert fake.calls[0]["key_id"] == "tenant-key-9"
    assert fake.calls[0]["context"]["pdi:key_id"] == "tenant-key-9"


def test_the_unwrapped_key_actually_opens_what_it_sealed():
    """The end of the contract. A provider that returned the right number of
    bytes and the wrong bytes would pass every assertion above."""
    fake = FakeKms()
    kek = crypto.KmsKeyProvider(client=fake).kek()
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    aes, nonce = AESGCM(kek), b"n" * 12
    sealed = aes.encrypt(nonce, b"a private note", None)
    again = crypto.KmsKeyProvider(client=FakeKms()).kek()
    assert AESGCM(again).decrypt(nonce, sealed, None) == b"a private note"


# --- the cache --------------------------------------------------------------

def test_the_key_is_cached_so_throughput_is_not_a_kms_quota():
    """An unwrap per record would make this vault's speed a function of
    somebody else's rate limit, and every call is billed."""
    fake = FakeKms()
    p = crypto.KmsKeyProvider(client=fake)
    for _ in range(5):
        assert p.kek() == KEK
    assert len(fake.calls) == 1


def test_the_cache_is_bounded_rather_than_forever():
    """A revoked key has to stop working within a bounded time, and "until the
    next deploy" is not bounded."""
    assert 0 < crypto.KEK_CACHE_SECONDS <= 3600


def test_clearing_the_cache_makes_the_next_call_ask_again(monkeypatch):
    """What a rotation or a retirement has to be able to do."""
    fake = FakeKms()
    p = crypto.KmsKeyProvider(client=fake)
    p.kek()
    crypto.clear_kek_cache()
    p.kek()
    assert len(fake.calls) == 2


def test_two_key_ids_do_not_share_a_cache_entry():
    """A cache keyed on nothing would hand one tenant's BYOK key to another —
    the worst possible bug in this file, and one a single-tenant test would
    never see."""
    a, b = FakeKms(kek=b"A" * 32), FakeKms(kek=b"B" * 32)
    assert crypto.KmsKeyProvider(key_id="tenant-a", client=a).kek() == b"A" * 32
    assert crypto.KmsKeyProvider(key_id="tenant-b", client=b).kek() == b"B" * 32


# --- nothing falls back -----------------------------------------------------

def test_a_missing_key_id_refuses_rather_than_reaching_for_a_local_key(monkeypatch):
    monkeypatch.delenv("PDI_KMS_KEY_ID", raising=False)
    with pytest.raises(crypto.KmsUnavailable, match="PDI_KMS_KEY_ID"):
        crypto.KmsKeyProvider(client=FakeKms()).kek()


def test_a_missing_blob_refuses_rather_than_inventing_a_key(monkeypatch):
    """Inventing one here would make every record already in the vault
    unreadable, which is worse than not starting."""
    monkeypatch.delenv("PDI_KMS_WRAPPED_KEK", raising=False)
    with pytest.raises(crypto.KmsUnavailable, match="WRAPPED_KEK"):
        crypto.KmsKeyProvider(client=FakeKms()).kek()


def test_a_corrupt_blob_refuses(monkeypatch):
    monkeypatch.setenv("PDI_KMS_WRAPPED_KEK", "not base64 at all!!")
    with pytest.raises(crypto.KmsUnavailable, match="base64"):
        crypto.KmsKeyProvider(client=FakeKms()).kek()


def test_a_kms_that_returns_the_wrong_size_key_refuses():
    """Caught here rather than at first use, where it would surface as an AES
    error three layers down naming nothing useful."""
    with pytest.raises(crypto.KmsUnavailable, match="32"):
        crypto.KmsKeyProvider(client=FakeKms(kek=b"short")).kek()


def test_an_unknown_backend_refuses(monkeypatch):
    monkeypatch.setenv("PDI_KMS_BACKEND", "something-fashionable")
    with pytest.raises(crypto.KmsUnavailable, match="no such KMS backend"):
        crypto.KmsKeyProvider().kek()


def test_the_outage_and_the_wrong_key_are_different_exceptions():
    """A caller has to tell *the key store is down* — retry, page somebody —
    from *this key is wrong*, which retrying will never fix."""
    assert not issubclass(crypto.KmsUnavailable, crypto.CustomerKeyMismatch)
    assert not issubclass(crypto.CustomerKeyMismatch, crypto.KmsUnavailable)


def test_a_failed_unwrap_never_yields_a_key():
    """The failure that would matter most: a provider that swallowed the KMS
    error and returned *something* would seal every record written during an
    outage under a key nobody can reproduce."""
    class Broken:
        def decrypt(self, **kw):
            raise RuntimeError("KMSInternalException")

    with pytest.raises(Exception) as exc:
        crypto.KmsKeyProvider(client=Broken()).kek()
    assert not isinstance(exc.value, bytes)
    crypto.clear_kek_cache()
    assert crypto._KEK_CACHE == {}, "a failed unwrap cached something"


# --- the key still reaches no column ----------------------------------------

def test_an_unwrapped_kek_lands_in_no_row_of_any_table(client):
    """The sweep from `test_the_key_is_nowhere_in_the_database` pointed at the
    new path. A KEK that came from an HSM and then got written to a log line
    is in exactly the same place as one that never left the app host.
    """
    kek = crypto.KmsKeyProvider(client=FakeKms()).kek()
    token = client.post("/tenants", json={"name": "acme"}).json()["token"]
    h = {"authorization": f"Bearer {token}"}
    client.put("/records", json={"key": "r", "value": "a private note"},
               headers=h)
    client.get("/records/r", headers=h)

    shapes = {"the kek's raw bytes": kek.decode("latin-1"),
              "the kek in hex": kek.hex(),
              "the kek in base64": base64.b64encode(kek).decode(),
              "the wrapped blob": base64.b64encode(BLOB).decode()}
    conn = db.connect()
    hits = []
    for (name,) in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%'").fetchall():
        for row in conn.execute(f"SELECT * FROM {name}").fetchall():
            for column in row.keys():
                value = row[column]
                if value is None:
                    continue
                text = value if isinstance(value, str) else str(value)
                for what, needle in shapes.items():
                    if needle and needle in text:
                        hits.append(f"{name}.{column} contains {what}")
    assert not hits, "; ".join(hits)


# --- the custody statement keeps up -----------------------------------------

def test_the_custody_statement_keeps_up_with_the_code(client):
    """`custody()` is written to be quoted in a security review.

    A limits list naming a seam that has since been built is a document that
    makes the product sound worse than it is — and the same staleness, pointed
    the other way, is one that makes it sound better. This reads the real
    statement for a real tenant rather than a module constant, because the
    statement is what a customer is shown.
    """
    token = client.post("/tenants", json={"name": "acme"}).json()["token"]
    r = client.put("/key", json={"provider": "kms",
                                 "config": {"key_id": "tenant-key-9"}},
                   headers={"authorization": f"Bearer {token}"})
    assert r.status_code == 201, r.text
    said = client.get("/key", headers={"authorization": f"Bearer {token}"})
    assert said.status_code == 200, said.text
    body = said.json()
    limits = " ".join(body.get("limits") or [])
    assert "not implemented" not in limits.lower(), limits
    assert "seam" not in limits.lower(), limits
    # And it still says the two things that remain true, rather than going
    # quiet: the cache window, and that no live run has been verified here.
    assert "cached" in limits.lower(), limits
    assert "no verified live run" in limits.lower(), limits
