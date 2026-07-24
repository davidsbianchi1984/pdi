"""The starter vault: a demo tenant with sealed records to explore.

A fresh PDI deployment is an empty vault — every guarantee (AES-256-GCM at
rest, AAD tenant+key binding, hash-chained audit) is real but invisible
until something is sealed. Seeding fixes the cold start: one demo tenant
("starter-demo") with sample records covering every provenance origin
(direct write, a JIM Guardian deposit, a QRME deposit), a bound home robot
with sealed collection data, and a read-back so the audit trail already has
history worth inspecting.

The tenant token is returned exactly once, from the run that creates the
tenant — the same rule every tenant lives by. Seeding is idempotent: if a
tenant named "starter-demo" already exists, nothing is created and no token
is (or can be) re-issued.

    python -m pdi.seed          # or POST /seed (admin)
"""

from __future__ import annotations

import json

from . import db, robotics, vault

TENANT_NAME = "starter-demo"

# key -> plaintext value. Prefixes exercise every provenance origin:
# jim/ (Guardian deposit), qrme/ (QRME deposit), anything else (direct).
STARTER_RECORDS: list[tuple[str, str]] = [
    ("welcome/readme",
     "Welcome to your Private Data Infrastructure vault. Every value here "
     "is sealed with AES-256-GCM before it touches disk, bound to this "
     "tenant and key, and every touch is hash-chained in the audit log. "
     "Try GET /provenance/welcome/readme to see the proof."),
    ("jim/demo-user/medical/checkin-001", json.dumps({
        "source": "JIM Guardian", "type": "wellness_checkin",
        "heart_rate": 62, "note": "calm morning baseline"})),
    ("qrme/demo-profile/sources/note-001", json.dumps({
        "source": "QRME", "kind": "writing",
        "content": "A note the synthetic profile was grounded in."})),
    ("finance/2025/summary", json.dumps({
        "type": "annual_summary", "year": 2025,
        "note": "sample financial summary — direct tenant write"})),
]

ROBOT_MODEL = "neo"
ROBOT_NAME = "Hall NEO (demo)"


def _existing_tenant() -> dict | None:
    row = db.connect().execute(
        "SELECT id, name FROM tenants WHERE name=? AND deleted_at IS NULL",
        (TENANT_NAME,)).fetchone()
    return dict(row) if row else None


def seed() -> dict:
    """Create the starter tenant with sealed demo data (idempotent: an
    existing "starter-demo" tenant means nothing is created)."""
    existing = _existing_tenant()
    if existing:
        return {"created": False, "tenant_id": existing["id"],
                "name": TENANT_NAME,
                "note": "starter tenant already exists; its token was "
                        "issued once at creation and cannot be re-issued"}

    tenant = vault.create_tenant(TENANT_NAME)
    for key, value in STARTER_RECORDS:
        vault.put(tenant, key, value)

    robot = robotics.create(tenant["id"], robotics.get(ROBOT_MODEL),
                            ROBOT_NAME)
    robotics.ingest(tenant, robot, "map",
                    "floorplan sweep: hallway, kitchen, living room")
    robotics.ingest(tenant, robot, "sensor_log",
                    "battery 94%, 3 obstacle events, docked 14:02")

    # Read one record back so the demo audit trail shows a full custody
    # cycle (seal -> access), not just writes.
    vault.get(tenant, "welcome/readme")

    return {
        "created": True,
        "tenant_id": tenant["id"],
        "name": TENANT_NAME,
        # Returned once, here — same rule as POST /tenants.
        "token": tenant["token"],
        "records": len(STARTER_RECORDS),
        "robot": {"id": robot["id"], "model": robot["model"],
                  "name": ROBOT_NAME, "ingested": 2},
        "note": "store the token now; only its hash is persisted",
    }


if __name__ == "__main__":
    print(json.dumps(seed(), indent=2))
