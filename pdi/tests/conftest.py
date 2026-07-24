import base64
import os

import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi.testclient import TestClient

from pdi import db as pdi_db


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("PDI_DB", str(tmp_path / "pdi.db"))
    # Deterministic master key for the test process.
    monkeypatch.setenv("PDI_MASTER_KEY",
                       base64.b64encode(AESGCM.generate_key(bit_length=256)).decode())
    pdi_db.reset()
    # crypto caches nothing that needs reset when PDI_MASTER_KEY is set.
    from pdi.api import create_app

    with TestClient(create_app()) as c:
        yield c
    pdi_db.reset()


def new_tenant(client, name="jim-mini"):
    r = client.post("/tenants", json={"name": name})
    assert r.status_code == 201, r.text
    return r.json()["token"]


def new_tenant_with_baa(client, name="jim-mini"):
    """A tenant whose BAA is on file — the precondition for HIPAA-program
    transfers/intakes (see pdi/baa.py)."""
    r = client.post("/tenants", json={"name": name})
    assert r.status_code == 201, r.text
    body = r.json()
    baa = client.post(f"/tenants/{body['id']}/baa", json={
        "customer_legal_name": f"{name} Inc.",
        "operator_legal_name": "Vault Operations LLC",
        "effective_date": "2026-07-24"})
    assert baa.status_code == 201, baa.text
    return body["token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}
