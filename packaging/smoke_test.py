"""Release-gate smoke test: the exact first run a user meets, driven
against the exact frozen binary, on this runner's real OS — before the
installer is allowed to exist.

The flow is the one that failed in the field: open the app, create a
tenant named after yourself, seal a record, read it back. Plus the
desktop-specific guarantee the siblings learned the hard way: the master
key persists, so a restarted vault can still read what it sealed.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request

BINARY = sys.argv[1]
PORT = "8123"
BASE = f"http://127.0.0.1:{PORT}"


def req(method, path, body=None, token=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, method=method,
                               headers={"content-type": "application/json",
                                        **({"authorization": f"Bearer {token}"}
                                           if token else {})})
    with urllib.request.urlopen(r, timeout=10) as resp:
        return json.loads(resp.read() or b"{}")


def start(env):
    proc = subprocess.Popen([BINARY], env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    for _ in range(60):
        try:
            health = req("GET", "/health")
            assert health["version"], "health carries no version"
            return proc
        except Exception:
            time.sleep(1)
    proc.kill()
    raise SystemExit("backend never answered /health")


def stop(proc):
    if sys.platform == "win32":
        # The PyInstaller bootloader spawns a child that survives kill();
        # take the tree down or the next start meets a busy port.
        subprocess.run(["taskkill", "/pid", str(proc.pid), "/T", "/F"],
                       capture_output=True)
    else:
        proc.kill()
    proc.wait(timeout=30)
    time.sleep(2)


def main():
    workdir = tempfile.mkdtemp(prefix="pdi-smoke-")
    env = {**os.environ, "PDI_PORT": PORT,
           "PDI_DB": os.path.join(workdir, "pdi.db"),
           "PYTHONIOENCODING": "cp1252:strict" if sys.platform == "win32"
           else "utf-8"}
    env.pop("PDI_MASTER_KEY", None)     # first run generates and persists one

    proc = start(env)
    try:
        tenant = req("POST", "/tenants", body={"name": "David Bianchi myself forever"})
        token = tenant["token"]
        req("PUT", "/records", body={"key": "hello/first", "value": "sealed"},
            token=token)
        got = req("GET", "/records/hello/first", token=token)
        assert got["value"] == "sealed", got
        print("first run: tenant created, record sealed and read back")
    finally:
        stop(proc)

    # The restart: same data dir, no PDI_MASTER_KEY in the env. If the key
    # did not persist, this read raises — which is the whole point.
    proc = start(env)
    try:
        got = req("GET", "/records/hello/first", token=token)
        assert got["value"] == "sealed", got
        print("restart: the sealed record is still readable — key persisted")
    finally:
        stop(proc)
    print("smoke test passed")


if __name__ == "__main__":
    main()
