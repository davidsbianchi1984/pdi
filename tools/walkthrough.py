"""Drive every road of the vault, and photograph it driven.

The trio's 3.0.0 gate, applied to the storage layer: seal, read back,
verify the chain, rotate a key, snapshot, ask the resident, mint a
position, place a beacon — each to the end, without a wall. Same
booted backend and built console the camera uses; every verdict line
carries the status that actually came back.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO))

import shoot_screens as camera

OUT = REPO / "docs" / "walkthrough"


def call(method, path, body=None, token=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(camera.BASE + path, data=data,
                                 method=method)
    req.add_header("content-type", "application/json")
    if token:
        req.add_header("authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}")
        except Exception:
            return e.code, {}
    except Exception as e:
        return 0, {"error": str(e)}


rows: list[tuple[str, str, bool]] = []


def step(road, note, ok, detail=None):
    rows.append((road, note, ok))
    line = ("  ok  " if ok else "  WALL") + f"  {road}: {note}"
    if detail and not ok:
        line += f"  << {json.dumps(detail)[:220]}"
    print(line)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    camera.build_console()
    proc = camera.start_backend()
    session = camera.enrol()
    tok = session["tenantToken"]
    try:
        # 1 · The vault: seal a record, read it back, list.
        s, r = call("PUT", "/records",
                    {"key": "walkthrough/note",
                     "value": "sealed by the drive"}, tok)
        step("vault", f"a record seals ({s})", s in (200, 201), r)
        s, r = call("GET", "/records/walkthrough/note", token=tok)
        back = (r or {}).get("value") == "sealed by the drive"
        step("vault", f"it reads back intact ({s})", s == 200 and back, r)
        s, r = call("GET", "/records", token=tok)
        step("vault", f"the listing answers ({s})", s == 200, r)

        # 2 · The chain: every access above is on it, and it verifies.
        s, r = call("GET", "/audit/verify", token=tok)
        ok = s == 200 and (r.get("ok") is True or r.get("intact") is True
                           or r.get("valid") is True)
        step("audit", f"the chain verifies ({s}: {json.dumps(r)[:60]})",
             ok, r if not ok else None)

        # 3 · Keys: reported, and a rotation re-seals.
        s, r = call("GET", "/keys", token=tok)
        step("keys", f"the versions report ({s})", s == 200, r)
        s, r = call("POST", "/keys/rotate", token=tok)
        step("keys", f"a rotation re-seals ({s})", s in (200, 201), r)

        # 4 · Snapshot: ciphertext out.
        s, r = call("GET", "/snapshot", token=tok)
        step("snapshot", f"the export answers ({s})", s == 200, r
             if s != 200 else None)

        # 5 · Retention: the sweep runs and says what it removed.
        s, r = call("POST", "/retention/sweep", token=tok)
        step("retention", f"the sweep answers ({s})", s in (200, 201), r)

        # 6 · The resident: posture honest, a question asked.
        s, r = call("GET", "/resident", token=tok)
        step("resident", f"the posture reports ({s})", s == 200, r
             if s != 200 else None)
        s, r = call("POST", "/resident/ask",
                    {"question": "what does this vault hold about the "
                                 "starter tenant?"}, tok)
        step("resident", f"a question is answered or honestly refused "
             f"({s})", s in (200, 201, 422, 503), r)

        # 7 · Positions: the blueprint door says what it needs.
        s, r = call("GET", "/positions", token=tok)
        step("positions", f"the desk answers ({s})", s == 200, r)

        # 8 · Custody: a beacon prints, its seal card reads.
        s, b = call("POST", "/beacons",
                    {"ref_kind": "facility",
                     "label": "The walkthrough door"}, tok)
        step("custody", f"a beacon prints ({s})", s in (200, 201), b)
        bid = (b or {}).get("id") or (b or {}).get("beacon", {}).get("id")
        if bid:
            # The seal card is a page for a stranger's browser, not a
            # JSON door — fetched as what it is.
            try:
                with urllib.request.urlopen(
                        camera.BASE + f"/s/{bid}", timeout=30) as raw:
                    card = raw.read().decode()
                    s = raw.status
            except Exception as e:
                s, card = 0, str(e)
            step("custody", f"the seal card reads blind ({s})",
                 s == 200 and len(card) > 100,
                 card[:200] if s != 200 else None)

        # 9 · The gate: the ceiling is published.
        s, r = call("GET", "/gate/ceiling")
        step("gate", f"the ceiling is published ({s})", s == 200, r
             if s != 200 else None)

        # The photographs.
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path="/opt/pw-browsers/chromium")
            page = browser.new_page(viewport=camera.VIEWPORT,
                                    device_scale_factor=2)
            page.goto(camera.BASE + "/", wait_until="networkidle")
            page.evaluate("s => localStorage.setItem('pdi.session', s)",
                          json.dumps(session))
            page.reload(wait_until="networkidle")
            for tab, name in (("overview", "01-overview"),
                              ("records", "02-records"),
                              ("audit", "03-audit"),
                              ("keys", "04-keys"),
                              ("custody", "05-custody"),
                              ("resident", "06-resident")):
                try:
                    if camera.open_tab(page, tab):
                        camera.answer_the_notice(page)
                        time.sleep(1.2)
                        page.screenshot(path=str(OUT / f"{name}.png"))
                        step("photo", f"{name} photographed", True)
                    else:
                        step("photo", f"{tab} tab did not open", False)
                except Exception as e:
                    step("photo", f"{tab}: {e}", False)
            browser.close()
    finally:
        proc.terminate()

    walls = [r for r in rows if not r[2]]
    print()
    print(f"{len(rows)} steps, {len(walls)} wall(s)")
    return 1 if walls else 0


if __name__ == "__main__":
    raise SystemExit(main())
