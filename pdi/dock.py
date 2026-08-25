"""The helper dock: the console's glances, in a pane that tucks into a corner.

The third of three, and the one whose corner was already occupied. PDI's
console has carried a pinned agent-lights overlay on every desktop view since
the light landed — three quarters of this feature with no lid on it. As in
QRME, the dock **replaces** it rather than joining it: two floating boxes in one
corner is what you get by adding the second.

**It shows, and it routes. It never acts.** The rule holds hardest here. This
is an operator console: the buttons it would float over rotate keys, revoke
tokens and wipe vaults, and `pdi/gate.py`'s doctrine — *the agent's ceiling is
whatever a wrong answer cannot undo* — puts every one of those far above
anything a pane in a corner may reach.

**And it cannot show a record.** Same rule as `pdi/tutorial.py` and
`pdi/assistant.py`, for the same reason: under BYOK the operator reading this
console frequently cannot decrypt the data, and a pane that displayed a record
would be claiming a capability the product is built to deny. A test asserts the
module never imports the vault. What the faces carry are **counts and states** —
how many records, whether the chain verifies, which tenants are live — which is
what an operator is watching for anyway.

**It is inside every screenshot**, and on an operator console that matters more
than on a phone: console screenshots go into tickets, runbooks and vendor
threads. :data:`NEVER` holds tenant names, keys, record keys and audit payloads.
"""

from __future__ import annotations

import json

from . import db
from . import i18n

CORNERS: dict[str, str] = {
    "bottom_right": "the default",
    "bottom_left": "to uncover something under it",
}
DEFAULT_CORNER = "bottom_right"

STATES: dict[str, str] = {
    "hidden": "nothing in the corner at all",
    "handle": "the helper button only — tucked away",
    "open": "the pane, showing one face",
}
# Open, like QRME's desktop and for the same reason the lights panel gave: an
# operator has no wrist, and a chain that stopped verifying is exactly the
# state nobody thinks to go and check.
DEFAULT_STATE = "open"
DEFAULT_FACE = "agents"

BOX = {"width": 168, "height": 132, "handle": 44, "inset": 16}

# Counts and states. Never a record, never a key.
FACES: dict[str, str] = {
    "helper": "the console guide — ask it anything about operating PDI",
    "agents": "the gate agents' status lights and their counts — no names",
    "chain": "whether the audit chain verifies, and when it was last checked",
    "vault": "how many records are held, and how much is sealed",
    "tenants": "how many tenants are live — a count, not a list",
}

# What may never appear. Console screenshots go into tickets, runbooks and
# vendor threads, which is a wider audience than a phone's camera roll.
NEVER: dict[str, str] = {
    "record_contents": "the guide cannot read a record and neither can this; "
                       "under BYOK nobody here can",
    "record_keys": "a key names what a record is about, which is most of it",
    "tenant_names": "who is a customer is the customer's business",
    "tokens": "nothing that authorises anything belongs on a captured surface",
    "audit_payloads": "an audit entry's detail is the thing being audited",
    "customer_keys": "never stored, and never shown",
}

ROUTES: dict[str, dict] = {
    "helper": {"screen": 41, "path": "/console/guide",
               "title": "Console Guide"},
    "agents": {"screen": 39, "path": "/gate/agents", "title": "Gate Agents"},
    "chain": {"screen": 9, "path": "/audit/verify", "title": "Verify Chain"},
    "vault": {"screen": 2, "path": "/vault", "title": "Vault"},
    "tenants": {"screen": 5, "path": "/tenants", "title": "Tenants"},
}


class DockError(ValueError):
    """A dock that cannot be drawn. Text meant for a person."""


def vocabulary() -> dict:
    return {
        "faces": FACES,
        "corners": CORNERS,
        "states": STATES,
        "box": BOX,
        "never": NEVER,
        "routes": ROUTES,
        "default_state": DEFAULT_STATE,
        "default_face": DEFAULT_FACE,
        "acts": False,
        "reads_records": False,
    }


def route(face: str) -> dict:
    if face not in ROUTES:
        raise DockError(i18n.fill(i18n.NO_SUCH_FACE, got=repr(face), choices=', '.join(FACES)))
    return {"face": face, **ROUTES[face], "opens_dock_face": face}


def _check_face(face: str) -> None:
    if face not in FACES:
        raise DockError(i18n.fill(i18n.NO_SUCH_FACE, got=repr(face), choices=', '.join(FACES)))


def settings(tenant_id: str) -> dict:
    row = db.connect().execute(
        "SELECT * FROM dock_prefs WHERE tenant_id=?", (tenant_id,)).fetchone()
    if row is None:
        return {"tenant_id": tenant_id, "corner": DEFAULT_CORNER,
                "state": DEFAULT_STATE, "face": DEFAULT_FACE,
                "faces": list(FACES), "set": False}
    return {"tenant_id": tenant_id, "corner": row["corner"],
            "state": row["state"], "face": row["face"],
            "faces": json.loads(row["faces"]), "set": True}


def configure(tenant_id: str, corner: str | None = None,
              state: str | None = None, face: str | None = None,
              faces: list[str] | None = None) -> dict:
    now = settings(tenant_id)
    corner = now["corner"] if corner is None else corner
    state = now["state"] if state is None else state
    face = now["face"] if face is None else face
    chosen = list(now["faces"] if faces is None else faces)

    if corner not in CORNERS:
        raise DockError(
            i18n.fill(i18n.PANE_BOTTOM_CORNER, choices=', '.join(CORNERS)))
    if state not in STATES:
        raise DockError(i18n.fill(i18n.UNKNOWN_STATE, got=repr(state), choices=', '.join(STATES)))
    for f in chosen:
        _check_face(f)
    if not chosen:
        raise DockError("a pane with no faces is the helper button on its own "
                        "— set the state to 'handle' instead")
    _check_face(face)
    if face not in chosen:
        raise DockError(i18n.fill(i18n.FACE_NOT_CARRIED, got=repr(face)))

    conn = db.connect()
    conn.execute(
        "INSERT INTO dock_prefs (tenant_id, corner, state, face, faces,"
        " updated_at) VALUES (?,?,?,?,?,?)"
        " ON CONFLICT (tenant_id) DO UPDATE SET corner=excluded.corner,"
        " state=excluded.state, face=excluded.face, faces=excluded.faces,"
        " updated_at=excluded.updated_at",
        (tenant_id, corner, state, face, json.dumps(chosen), db.utcnow()))
    conn.commit()
    return settings(tenant_id)


def face(tenant_id: str, name: str) -> dict:
    """One face, as the pane would draw it.

    Counts and states only — see :data:`NEVER`. There is no argument by which
    this returns a record, because it never reaches the vault to get one.
    """
    _check_face(name)
    return {
        "face": name,
        "shows": FACES[name],
        "tenant_id": tenant_id,
        "route": route(name),
        "acts": False,
        "reads_records": False,
        "box": BOX,
        "never": list(NEVER),
    }
