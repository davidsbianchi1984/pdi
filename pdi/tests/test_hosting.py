"""Hosting posture: safe to publish, and pairing that works either way.

A PDI deployment is the collation facility — self-hosted or run for you by
someone else. Either way it may sit on a routable address, which is a
different threat model from a laptop on Wi-Fi.
"""

import base64

import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi.testclient import TestClient

from pdi import db as pdi_db, mobile


@pytest.fixture()
def remote_client(tmp_path, monkeypatch):
    """A client that presents a routable peer address, as a caller from off
    this machine would."""
    monkeypatch.setenv("PDI_DB", str(tmp_path / "pdi.db"))
    monkeypatch.setenv("PDI_MASTER_KEY",
                       base64.b64encode(AESGCM.generate_key(bit_length=256)).decode())
    monkeypatch.delenv("PDI_ADMIN_TOKEN", raising=False)
    pdi_db.reset()
    from pdi.api import create_app

    with TestClient(create_app(), client=("203.0.113.9", 44321)) as c:
        yield c
    pdi_db.reset()


def test_open_admin_fails_closed_when_reachable_off_machine(remote_client):
    """No admin token + a routable caller = admin stays shut. An open admin
    surface on a published address would hand anyone tenant creation, token
    minting, vault wipes, and snapshot restore."""
    r = remote_client.post("/tenants", json={"name": "attacker"})
    assert r.status_code == 503
    detail = r.json()["detail"]
    assert "PDI_ADMIN_TOKEN" in detail
    # Every admin surface, not just tenant creation.
    assert remote_client.post("/deployments", json={"operator": "x"}).status_code == 503
    assert remote_client.delete("/tenants/ten_whatever").status_code == 503


def test_configured_admin_token_opens_it_for_remote_operators(remote_client, monkeypatch):
    """With a token set, a remote operator works normally — and a wrong
    token is still refused."""
    monkeypatch.setenv("PDI_ADMIN_TOKEN", "s3cret-admin")
    ok = remote_client.post("/tenants", json={"name": "acme"},
                            headers={"authorization": "Bearer s3cret-admin"})
    assert ok.status_code == 201
    assert remote_client.post(
        "/tenants", json={"name": "nope"},
        headers={"authorization": "Bearer wrong"}).status_code == 403
    assert remote_client.post("/tenants", json={"name": "nope"}).status_code == 401


def test_local_development_stays_open(client):
    """On this machine, no token needed — the dev loop is unchanged."""
    assert client.post("/tenants", json={"name": "local-dev"}).status_code == 201


def test_pairing_advertises_the_published_url_when_hosted(client, monkeypatch):
    """A hosted deployment's QR must point at the address the phone can
    actually reach — its public URL, not a LAN address the phone can't see."""
    monkeypatch.setenv("PDI_PUBLIC_URL", "https://vault.example.com/")
    body = client.get("/pair").json()
    assert body["hosted"] is True
    assert body["console_url"] == "https://vault.example.com/app/"
    assert body["reachable"] is True
    assert "HTTPS" in body["note"]


def test_pairing_falls_back_to_lan_when_not_published(client, monkeypatch):
    """No public URL = the laptop posture, unchanged."""
    monkeypatch.delenv("PDI_PUBLIC_URL", raising=False)
    monkeypatch.setenv("PDI_LAN_HOST", "192.168.1.42")
    body = client.get("/pair").json()
    assert body["hosted"] is False
    assert body["console_url"].startswith("http://192.168.1.42:")
    assert "local network only" in body["note"].lower()


def test_public_base_normalises_trailing_slash(monkeypatch):
    monkeypatch.setenv("PDI_PUBLIC_URL", "https://vault.example.com/")
    assert mobile.public_base() == "https://vault.example.com"
    monkeypatch.delenv("PDI_PUBLIC_URL")
    assert mobile.public_base() is None


def test_published_deployment_refuses_an_ephemeral_key(tmp_path, monkeypatch):
    """An ephemeral key lives only in this process: everything sealed under
    it is unreadable after a restart. On a published deployment that is
    silent, unrecoverable data loss, so key-less startup fails closed."""
    monkeypatch.setenv("PDI_DB", str(tmp_path / "pdi.db"))
    monkeypatch.delenv("PDI_MASTER_KEY", raising=False)
    monkeypatch.setenv("PDI_PUBLIC_URL", "https://vault.example.com")
    pdi_db.reset()

    from pdi import crypto
    monkeypatch.setattr(crypto, "_EPHEMERAL", None)
    with pytest.raises(RuntimeError) as excinfo:
        crypto.seal("a subscriber record")
    message = str(excinfo.value)
    assert "PDI_MASTER_KEY" in message and "unreadable after the next restart" in message
    pdi_db.reset()


def test_local_development_still_gets_an_ephemeral_key(tmp_path, monkeypatch):
    """Unpublished and key-less is the laptop case — it still just works."""
    monkeypatch.setenv("PDI_DB", str(tmp_path / "pdi.db"))
    monkeypatch.delenv("PDI_MASTER_KEY", raising=False)
    monkeypatch.delenv("PDI_PUBLIC_URL", raising=False)
    pdi_db.reset()

    from pdi import crypto
    monkeypatch.setattr(crypto, "_EPHEMERAL", None)
    sealed = crypto.seal("a note", aad="ten_1")
    assert crypto.open_(sealed, aad="ten_1") == "a note"
    pdi_db.reset()
