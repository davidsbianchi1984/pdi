"""Entry point for the PyInstaller-bundled PDI backend.

The desktop installer ships two halves: the Electron console, and this —
the whole Python vault frozen into one executable (``pdi-backend`` /
``pdi-backend.exe``) that the Electron main process spawns at launch when
no backend is already answering. The sibling products have shipped this
way since their packaging round; PDI's console shipped alone, which meant
every desktop install opened onto "Failed to fetch" — a vault with no
vault behind it.

Defaults are chosen for that double-click launch and only that launch:

* **A master key that persists.** Without ``PDI_MASTER_KEY`` the vault
  runs on an ephemeral key — fine for tests, catastrophic for a desktop
  vault, whose contents would become unreadable at every restart. On
  first run this entry point generates a 32-byte key and stores it next
  to the database (``master.key``); after that it is loaded from there.
  Your hardware, your keys, your walls — the file IS the key, and backing
  it up is backing up the ability to read the vault.
* **Loopback only** (``PDI_HOST`` overrides) — the vault of all things
  does not listen on the network unasked.
* **Data under the app's user-data directory** — never scattered into
  whatever directory the app started from.

Everything remains overridable through the same environment variables the
unbundled backend reads.
"""

from __future__ import annotations

import base64
import os
import secrets
import sys
from pathlib import Path


def _data_dir() -> Path:
    if os.environ.get("PDI_DB"):
        directory = Path(os.environ["PDI_DB"]).parent
        directory.mkdir(parents=True, exist_ok=True)
        return directory
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME",
                                   Path.home() / ".local" / "share"))
    directory = base / "PDI Console"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _ensure_master_key(directory: Path) -> None:
    if os.environ.get("PDI_MASTER_KEY"):
        return
    key_file = directory / "master.key"
    if not key_file.exists():
        key_file.write_text(
            base64.b64encode(secrets.token_bytes(32)).decode())
        try:
            key_file.chmod(0o600)
        except OSError:
            pass    # Windows: ACLs, not modes; the user-data dir is theirs
    os.environ["PDI_MASTER_KEY"] = key_file.read_text().strip()


def main() -> None:
    # The frozen Windows backend inherits a cp1252 stdout; any print of a
    # character outside it would raise mid-request. Replace, never raise.
    for stream in (sys.stdout, sys.stderr):
        if stream and hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    directory = _data_dir()
    os.environ.setdefault("PDI_DB", str(directory / "pdi.db"))
    _ensure_master_key(directory)
    os.environ.setdefault("PDI_CORS_ORIGINS", "*")
    port = int(os.environ.get("PDI_PORT", "8000"))
    host = os.environ.get("PDI_HOST", "127.0.0.1")

    import uvicorn

    from pdi.api import create_app

    print(f"PDI backend — http://{host}:{port} "
          f"(db: {os.environ['PDI_DB']})", flush=True)
    uvicorn.run(create_app(), host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
