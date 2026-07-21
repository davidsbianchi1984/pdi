#!/usr/bin/env python3
"""Generate the PDI **desktop** operator-console SVGs — wide, multi-panel
dashboard views of the Private Data Infrastructure vault, in the product's
deep-indigo / vault-cyan design language. A sidebar-nav desktop window per
view, complementing the mobile console in docs/screens/.

Reuses the mobile generator's icon + colour library so both galleries stay
one system. Run: python3 docs/desktop/build.py  ->  docs/desktop/NN-name.svg
"""

from __future__ import annotations

import importlib.util
import math
import os

OUT = os.path.dirname(os.path.abspath(__file__))

# reuse the mobile builder's primitives (icons, palette, text/rrect/pill/…)
_spec = importlib.util.spec_from_file_location(
    "pdimobile", os.path.join(OUT, "..", "screens", "build.py"))
pb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pb)
icon, C, ACCENT, A = pb.icon, pb.C, pb.ACCENT, pb.A
rrect, text, pill, chip = pb.rrect, pb.text, pb.pill, pb.chip
status_dot, spark, meter, ring, button, esc = (pb.status_dot, pb.spark, pb.meter,
                                               pb.ring, pb.button, pb.esc)

# ---- desktop canvas & window geometry -------------------------------------
W, H = 1280, 820
WIN_X, WIN_Y, WIN_W, WIN_H = 24, 24, 1232, 772
TOPBAR_H = 54
SIDE_W = 216
CONTENT_X = WIN_X + SIDE_W
CONTENT_Y = WIN_Y + TOPBAR_H
CONTENT_W = WIN_W - SIDE_W
CONTENT_H = WIN_H - TOPBAR_H
PAD = 28
IX = CONTENT_X + PAD                       # inner content left
IY = CONTENT_Y + PAD                       # inner content top
IW = CONTENT_W - 2 * PAD                   # inner content width

NAV = [("grid", "Overview"), ("lock", "Vault"), ("people", "Tenants"),
       ("shieldok", "Audit"), ("finger", "Encryption"), ("building", "Deployment"),
       ("chart", "Health"), ("gear", "Settings")]


# --------------------------------------------------------------------------- #
# frame
# --------------------------------------------------------------------------- #
def defs():
    return f'''<defs>
      <linearGradient id="gPage" x1="0" y1="0" x2="0.4" y2="1">
        <stop offset="0" stop-color="#0d0a20"/><stop offset="1" stop-color="#080614"/></linearGradient>
      <linearGradient id="gScr" x1="0" y1="0" x2="0.5" y2="1">
        <stop offset="0" stop-color="{C['scrA']}"/><stop offset="1" stop-color="{C['scrB']}"/></linearGradient>
      <linearGradient id="gSide" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#161038"/><stop offset="1" stop-color="#0e0a26"/></linearGradient>
      <linearGradient id="gCard" x1="0" y1="0" x2="0.4" y2="1">
        <stop offset="0" stop-color="{C['card']}"/><stop offset="1" stop-color="{C['card2']}"/></linearGradient>
      <linearGradient id="gBrand" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0" stop-color="{C['brandA']}"/><stop offset="1" stop-color="{C['brandB']}"/></linearGradient>
      <linearGradient id="gAmber" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0" stop-color="{C['amber']}"/><stop offset="1" stop-color="#ffd27a"/></linearGradient>
      <linearGradient id="mG" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#5fb87a"/><stop offset="1" stop-color="{C['green']}"/></linearGradient>
      <linearGradient id="mC" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#6bb6d6"/><stop offset="1" stop-color="{C['cyan']}"/></linearGradient>
      <radialGradient id="orb" cx="36%" cy="30%" r="78%">
        <stop offset="0" stop-color="#cbeeff"/><stop offset="38%" stop-color="{C['brandA']}"/>
        <stop offset="78%" stop-color="#1f6fb2"/><stop offset="100%" stop-color="#0b2438"/></radialGradient>
    </defs>'''


def frame(title, active):
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" role="img" aria-label="PDI console — {esc(title)}">']
    o.append(defs())
    o.append(rrect(0, 0, W, H, 0, "url(#gPage)"))
    # window
    o.append(f'<rect x="{WIN_X}" y="{WIN_Y}" width="{WIN_W}" height="{WIN_H}" rx="18" '
             f'fill="url(#gScr)" stroke="{C["line"]}" stroke-width="1"/>')
    # sidebar plate (inset so window corners stay clean)
    o.append(rrect(WIN_X, WIN_Y, SIDE_W, WIN_H, 18, "url(#gSide)"))
    o.append(rrect(WIN_X + SIDE_W - 18, WIN_Y, 18, WIN_H, 0, "url(#gScr)"))   # square inner edge
    o.append(f'<line x1="{CONTENT_X}" y1="{WIN_Y}" x2="{CONTENT_X}" y2="{WIN_Y+WIN_H}" stroke="{C["line"]}" stroke-width="1"/>')
    o.append(f'<line x1="{CONTENT_X}" y1="{CONTENT_Y}" x2="{WIN_X+WIN_W}" y2="{CONTENT_Y}" stroke="{C["line"]}" stroke-width="1"/>')
    # window traffic lights
    for i, col in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        o.append(f'<circle cx="{WIN_X+22+i*18}" cy="{WIN_Y+27}" r="5.5" fill="{col}" opacity="0.9"/>')
    # brand
    o.append(f'<circle cx="{WIN_X+96}" cy="{WIN_Y+27}" r="11" fill="url(#orb)"/>')
    o.append(icon("lock", WIN_X + 96, WIN_Y + 27, "rgba(255,255,255,0.95)", 0.6))
    o.append(text(WIN_X + 114, WIN_Y + 25, "PDI", 14, C["txt"], 800, spacing=0.5))
    o.append(text(WIN_X + 114, WIN_Y + 39, "Private Data Infrastructure", 8.5, C["t3"], 500))
    # top bar: breadcrumb (title) + right cluster
    o.append(text(CONTENT_X + PAD, WIN_Y + 33, title, 15, C["txt"], 700, spacing=-0.2))
    # right: tenant switcher, status, gear
    rx = WIN_X + WIN_W - 24
    o.append(icon("gear", rx - 10, WIN_Y + 27, C["t2"], 0.8))
    o.append(status_dot(rx - 34, WIN_Y + 31, "Vault online", "on"))
    tw = 150
    o.append(rrect(rx - 34 - 150 - tw + 22, WIN_Y + 16, tw, 24, 8, "rgba(255,255,255,0.05)", C["line"], 1))
    o.append(icon("people", rx - 34 - 150 - tw + 38, WIN_Y + 28, C["brandA"], 0.6))
    o.append(text(rx - 34 - 150 - tw + 50, WIN_Y + 31, "All tenants", 10.5, C["txt"], 600))
    o.append(text(rx - 34 - 150 - 4, WIN_Y + 31, "▾", 9, C["t3"], 600, "end"))
    # sidebar nav
    ny = CONTENT_Y + 18
    for ic, lbl in NAV:
        on = (lbl == active)
        if on:
            o.append(rrect(WIN_X + 12, ny - 4, SIDE_W - 24, 38, 10, A(C["brandA"], 0.14)))
            o.append(rrect(WIN_X + 12, ny - 4, 3, 38, 2, C["brandA"]))
        col = C["brandA"] if on else C["t2"]
        o.append(icon(ic, WIN_X + 34, ny + 15, col, 0.72))
        o.append(text(WIN_X + 54, ny + 20, lbl, 12.5, C["txt"] if on else C["t2"], 650 if on else 500))
        ny += 46
    # sidebar footer
    o.append(f'<line x1="{WIN_X+16}" y1="{WIN_Y+WIN_H-70}" x2="{WIN_X+SIDE_W-16}" y2="{WIN_Y+WIN_H-70}" stroke="{C["line"]}" stroke-width="1"/>')
    o.append(rrect(WIN_X + 16, WIN_Y + WIN_H - 56, SIDE_W - 32, 40, 10, "rgba(255,255,255,0.04)", C["line"], 1))
    o.append(icon("shieldok", WIN_X + 34, WIN_Y + WIN_H - 36, C["green"], 0.66))
    o.append(text(WIN_X + 52, WIN_Y + WIN_H - 40, "Chain intact", 10.5, C["txt"], 650))
    o.append(text(WIN_X + 52, WIN_Y + WIN_H - 27, "on-prem · Tier III+", 8.5, C["t3"], 500))
    return o


def close():
    return ['</svg>']


# --------------------------------------------------------------------------- #
# widgets
# --------------------------------------------------------------------------- #
def panel(x, y, w, h, title, right=None):
    o = [rrect(x, y, w, h, 14, "url(#gCard)", C["line"], 1)]
    if title:
        o.append(text(x + 18, y + 27, title, 12.5, C["txt"], 700))
    if right:
        o.append(text(x + w - 18, y + 27, right, 10, C["t3"], 600, "end"))
    return o


def tile(x, y, w, h, label, value, sub, col, ic, pillt=None):
    o = [rrect(x, y, w, h, 14, "url(#gCard)", C["line"], 1)]
    o.append(text(x + 18, y + 28, label, 11, C["t2"], 600))
    o.append(text(x + 18, y + 62, value, 27, col, 800))
    o.append(text(x + 18, y + 80, sub, 9.5, C["t3"], 500))
    o.append(chip(x + w - 48, y + 14, ic, col))
    if pillt:
        o.append(pill(x + w - 16, y + h - 14, pillt[0], pillt[1]))
    return o


def areachart(x, y, w, h, pts, col, grad):
    n = len(pts)
    lo, hi = min(pts), max(pts)
    rng = (hi - lo) or 1
    pad = 0.12 * (hi - lo)
    lo -= pad
    rng = (hi - lo) or 1
    coords = [(x + w * i / (n - 1), y + h - (v - lo) / rng * h) for i, v in enumerate(pts)]
    line = " ".join(f"{a:.1f},{b:.1f}" for a, b in coords)
    o = []
    for gy in range(1, 4):
        yy = y + h * gy / 4
        o.append(f'<line x1="{x}" y1="{yy:.1f}" x2="{x+w}" y2="{yy:.1f}" stroke="{A(C["line"],0.5)}" stroke-width="1"/>')
    o.append(f'<polygon points="{x},{y+h} {line} {x+w},{y+h}" fill="{A(col,0.13)}"/>')
    o.append(f'<polyline points="{line}" fill="none" stroke="{col}" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>')
    ex, ey = coords[-1]
    o.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="4" fill="{col}"/>')
    return "".join(o)


def table(x, y, w, cols, rows, rowh=36):
    """cols: [(label, frac, align)]; rows: [[cell,...]] where cell is str or
    (text, color, weight)."""
    o = []
    cx = x
    for label, frac, align in cols:
        cw = w * frac
        ax = cx + 10 if align == "start" else (cx + cw - 10 if align == "end" else cx + cw / 2)
        o.append(text(ax, y + 12, label, 9.5, C["t3"], 700, align, 0.4))
        cx += cw
    o.append(f'<line x1="{x}" y1="{y+22}" x2="{x+w}" y2="{y+22}" stroke="{C["line"]}" stroke-width="1"/>')
    yy = y + 22
    for row in rows:
        cx = x
        for (label, frac, align), cell in zip(cols, row):
            cw = w * frac
            ax = cx + 10 if align == "start" else (cx + cw - 10 if align == "end" else cx + cw / 2)
            if isinstance(cell, tuple):
                txt, tcol, twt = cell
                mono = txt.startswith("~") if False else False
                o.append(text(ax, yy + 24, txt, 10.5, tcol, twt, align))
            else:
                o.append(text(ax, yy + 24, cell, 10.5, C["txt"], 500, align))
            cx += cw
        yy += rowh
        o.append(f'<line x1="{x}" y1="{yy}" x2="{x+w}" y2="{yy}" stroke="{A(C["line"],0.45)}" stroke-width="1"/>')
    return "".join(o)


def op_cell(op):
    col = {"STORE": C["green"], "READ": C["cyan"], "ERASE": C["red"], "LIST": C["t2"]}[op]
    return (op, col, 800)


# --------------------------------------------------------------------------- #
# views
# --------------------------------------------------------------------------- #
def v_overview():
    o = []
    tw = (IW - 3 * 20) / 4
    tiles = [("Tenants", "2", "qrme · jim-mini", C["brandA"], "people", None),
             ("Records sealed", "1,842", "+312 this month", C["amber"], "db", None),
             ("Audit chain", "OK", "1,845 entries", C["green"], "shieldok", ("VERIFIED", "good")),
             ("Deployment", "Tier III+", "colocation · your keys", C["cyan"], "building", None)]
    for i, (lbl, val, sub, col, ic, pt) in enumerate(tiles):
        tx = IX + i * (tw + 20)
        sz = 27 if val not in ("OK", "Tier III+") else 22
        oo = tile(tx, IY, tw, 96, lbl, val, sub, col, ic, pt)
        # shrink value font for text values
        if val in ("OK", "Tier III+"):
            oo[2] = text(tx + 18, IY + 60, val, 22, col, 800)
        o += oo
    y2 = IY + 96 + 22
    lw = IW * 0.64
    rw = IW - lw - 20
    # left: chart panel
    ph = 268
    o += panel(IX, y2, lw, ph, "Records sealed over time", right="last 12 months")
    o.append(areachart(IX + 20, y2 + 52, lw - 40, ph - 96,
                        [420, 540, 610, 700, 820, 905, 1010, 1180, 1320, 1500, 1690, 1842],
                        C["brandA"], "gBrand"))
    o.append(text(IX + 20, y2 + ph - 16, "Jan", 9, C["t3"], 500))
    o.append(text(IX + lw - 20, y2 + ph - 16, "Dec", 9, C["t3"], 500, "end"))
    # right: chain integrity ring
    o += panel(IX + lw + 20, y2, rw, ph, "Chain integrity")
    ccx, ccy = IX + lw + 20 + rw / 2, y2 + 128
    o.append(ring(ccx, ccy, 58, 1.0, C["green"], 11))
    o.append(icon("shieldok", ccx, ccy - 6, C["green"], 1.9))
    o.append(text(ccx, ccy + 20, "INTACT", 12, C["green"], 800, "middle", 1))
    o.append(text(ccx, y2 + ph - 42, "GET /audit/verify", 10, C["t2"], 600, "middle"))
    o.append(text(ccx, y2 + ph - 26, "no record was retroactively edited", 9, C["t3"], 500, "middle"))
    # bottom row
    y3 = y2 + ph + 22
    bh = CONTENT_Y + CONTENT_H - PAD - y3
    o += panel(IX, y3, lw, bh, "Recent audit", right="live")
    rows = [[op_cell("STORE"), "records/med/contact", "jim-mini", ("10:02", C["t2"], 500)],
            [op_cell("READ"), "profiles/src/ava", "qrme", ("10:01", C["t2"], 500)],
            [op_cell("STORE"), "contributions/qrme/8f3a", "qrme", ("09:58", C["t2"], 500)],
            [op_cell("ERASE"), "records/med/old-contact", "jim-mini", ("09:55", C["t2"], 500)]]
    o.append(table(IX + 18, y3 + 44, lw - 36,
                   [("OP", 0.16, "start"), ("KEY", 0.46, "start"), ("TENANT", 0.22, "start"), ("TIME", 0.16, "end")],
                   rows, rowh=32))
    o += panel(IX + lw + 20, y3, rw, bh, "Tenants")
    ty = y3 + 44
    for name, recs, col in [("qrme", "1,204 records", C["brandA"]), ("jim-mini", "638 records", C["cyan"])]:
        o.append(rrect(IX + lw + 38, ty, rw - 36, 52, 11, "rgba(255,255,255,0.03)", C["line"], 1))
        o.append(f'<circle cx="{IX+lw+62}" cy="{ty+26}" r="15" fill="{A(col,0.20)}" stroke="{col}" stroke-width="1.2"/>')
        o.append(icon("people", IX + lw + 62, ty + 26, col, 0.8))
        o.append(text(IX + lw + 86, ty + 22, name, 12, C["txt"], 700))
        o.append(text(IX + lw + 86, ty + 38, recs, 10, C["t2"], 500))
        o.append(status_dot(IX + lw + 20 + rw - 18, ty + 26, "ACTIVE", "on"))
        ty += 62
    return o


def v_vault():
    o = []
    lw = IW * 0.66
    rw = IW - lw - 20
    hh = CONTENT_H - 2 * PAD
    o += panel(IX, IY, lw, hh, "Records", right="1,842 sealed · ciphertext only")
    rows = []
    data = [("records/med/contact", "jim-mini", "312 B", "10:02"),
            ("records/med/allergies", "jim-mini", "208 B", "09:41"),
            ("profiles/src/ava/notes", "qrme", "4.1 KB", "09:38"),
            ("profiles/src/ava/voice", "qrme", "88 KB", "09:37"),
            ("contributions/qrme/8f3a", "qrme", "1.2 KB", "09:58"),
            ("records/med/contact-2", "jim-mini", "298 B", "08:50"),
            ("profiles/src/dana/bio", "qrme", "2.6 KB", "08:22"),
            ("handoffs/qrme/rt-77", "qrme", "3.0 KB", "07:15")]
    for k, tn, sz, up in data:
        rows.append([(k, C["txt"], 600), tn, sz, ("🔒", C["green"], 700) if False else ("sealed", C["green"], 600), (up, C["t2"], 500)])
    o.append(table(IX + 18, IY + 46, lw - 36,
                   [("KEY", 0.42, "start"), ("TENANT", 0.2, "start"), ("SIZE", 0.14, "end"),
                    ("STATUS", 0.14, "middle"), ("UPDATED", 0.1, "end")],
                   rows, rowh=40))
    # detail panel
    o += panel(IX + lw + 20, IY, rw, hh, "Record detail")
    dx = IX + lw + 38
    dw = rw - 36
    o.append(rrect(dx, IY + 46, dw, 46, 10, A(C["brandA"], 0.08), C["brandA"], 1))
    o.append(icon("lock", dx + 22, IY + 69, C["brandA"], 0.8))
    o.append(text(dx + 42, IY + 64, "records/med/contact", 11.5, C["txt"], 700))
    o.append(text(dx + 42, IY + 80, "tenant: jim-mini", 9.5, C["t2"], 500))
    fields = [("Tenant", "jim-mini"), ("Key namespace", "records/med"),
              ("Cipher", "AES-256-GCM"), ("AAD", "tenant=jim-mini · key=…contact"),
              ("Sealed", "today 10:02:14"), ("Size", "312 B ciphertext")]
    fy = IY + 108
    for k, val in fields:
        o.append(text(dx, fy + 12, k.upper(), 8.5, C["t3"], 700, "start", 0.4))
        o.append(text(dx, fy + 28, val, 11, C["txt"], 600))
        fy += 44
    o.append(text(dx, fy + 8, "CIPHERTEXT", 8.5, C["t3"], 700, "start", 0.4))
    o.append(rrect(dx, fy + 14, dw, 54, 8, "#0d0a24", C["line"], 1))
    for i, ln in enumerate(["9f2a c4e1 77bd 0a3e 51cc", "e71b 8840 …  (AAD-bound)"]):
        o.append(text(dx + 12, fy + 32 + i * 18, ln, 10, C["cyan"], 500, "start", 0.4, True))
    fy += 84
    o.append(button(dx, fy, (dw - 12) / 2, "Re-seal", "brand", 38))
    o.append(button(dx + (dw - 12) / 2 + 12, fy, (dw - 12) / 2, "Delete", "danger", 38))
    return o


def v_audit():
    o = []
    # verify banner
    o.append(rrect(IX, IY, IW, 56, 13, A(C["green"], 0.09), C["green"], 1.2))
    o.append(icon("shieldok", IX + 30, IY + 28, C["green"], 1.1))
    o.append(text(IX + 54, IY + 25, "Chain intact — 1,845 entries verified", 13, C["txt"], 700))
    o.append(text(IX + 54, IY + 41, "append-only, SHA-256 hash-chained · no retroactive edit detected", 10, C["t2"], 500))
    o.append(button(IX + IW - 148, IY + 10, 132, "Re-verify chain", "brand", 36))
    y2 = IY + 56 + 22
    hh = CONTENT_Y + CONTENT_H - PAD - y2
    o += panel(IX, y2, IW, hh, "Audit log", right="newest first")
    rows = []
    data = [(1845, "ERASE", "jim-mini", "records/med/old-contact", "e71b…3f9a"),
            (1844, "STORE", "qrme", "contributions/qrme/8f3a", "3f9a…c4e1"),
            (1843, "READ", "qrme", "profiles/src/ava/notes", "c4e1…77bd"),
            (1842, "STORE", "jim-mini", "records/med/contact", "77bd…0a3e"),
            (1841, "LIST", "qrme", "profiles/src/ava", "0a3e…51cc"),
            (1840, "READ", "jim-mini", "records/med/allergies", "51cc…8840"),
            (1839, "STORE", "qrme", "profiles/src/dana/bio", "8840…19ff"),
            (1838, "STORE", "jim-mini", "records/med/contact-2", "19ff…2b7d"),
            (1837, "READ", "qrme", "handoffs/qrme/rt-77", "2b7d…a0e6")]
    for seq, op, tn, key, h in data:
        rows.append([(f"#{seq}", C["t2"], 600), op_cell(op), tn, (key, C["txt"], 500),
                     (h, C["cyan"], 500), ("verified", C["green"], 600)])
    o.append(table(IX + 18, y2 + 46, IW - 36,
                   [("SEQ", 0.09, "start"), ("OP", 0.11, "start"), ("TENANT", 0.14, "start"),
                    ("KEY", 0.36, "start"), ("HASH  (prev→curr)", 0.18, "start"), ("CHAIN", 0.12, "end")],
                   rows, rowh=38))
    return o


def v_tenants():
    o = []
    # tenant cards
    cw = (IW - 20) / 2
    for i, (name, sub, recs, toks, col) in enumerate([
            ("qrme", "AI synthetic profiles", "1,204", "3", C["brandA"]),
            ("jim-mini", "Guardian personal guidance", "638", "2", C["cyan"])]):
        cx = IX + i * (cw + 20)
        o += panel(cx, IY, cw, 128, None)
        o.append(f'<circle cx="{cx+42}" cy="{IY+44}" r="20" fill="{A(col,0.18)}" stroke="{col}" stroke-width="1.4"/>')
        o.append(icon("people", cx + 42, IY + 44, col, 1.0))
        o.append(text(cx + 74, IY + 40, name, 15, C["txt"], 750))
        o.append(text(cx + 74, IY + 57, sub, 10, C["t2"], 500))
        o.append(status_dot(cx + cw - 18, IY + 44, "ACTIVE", "on"))
        for j, (lbl, val) in enumerate([("Records", recs), ("Tokens", toks), ("Isolation", "AAD")]):
            bx = cx + 24 + j * ((cw - 48) / 3)
            o.append(text(bx, IY + 92, val, 18, col, 800))
            o.append(text(bx, IY + 110, lbl, 9.5, C["t3"], 600, "start", 0.3))
    # tokens table
    y2 = IY + 128 + 22
    hh = CONTENT_Y + CONTENT_H - PAD - y2
    o += panel(IX, y2, IW, hh, "Access tokens", right="hashed at rest · shown once at issuance")
    rows = []
    data = [("pdi_live_k7Q2••••3f9a", "qrme", "write", "2026-01-04", "10:02", "active"),
            ("pdi_live_m2X9••••b1c8", "qrme", "read", "2026-02-11", "10:01", "active"),
            ("pdi_live_p5R7••••9d0e", "jim-mini", "write", "2026-01-04", "09:55", "active"),
            ("pdi_live_t8W1••••4a6f", "jim-mini", "read", "2026-03-20", "08:50", "active"),
            ("pdi_live_z3K4••••7c2b", "qrme", "read", "2025-12-01", "—", "revoked")]
    for tok, tn, scope, created, used, st in data:
        scol = C["amber"] if scope == "write" else C["green"]
        stcol = C["green"] if st == "active" else C["t3"]
        rows.append([(tok, C["cyan"], 600), tn, (scope, scol, 700), created, (used, C["t2"], 500),
                     (st, stcol, 600)])
    o.append(table(IX + 18, y2 + 46, IW - 36,
                   [("TOKEN", 0.28, "start"), ("TENANT", 0.16, "start"), ("SCOPE", 0.12, "start"),
                    ("CREATED", 0.16, "start"), ("LAST USED", 0.14, "start"), ("STATUS", 0.14, "end")],
                   rows, rowh=38))
    return o


def v_encryption():
    o = []
    lw = IW * 0.6
    rw = IW - lw - 20
    hh = CONTENT_H - 2 * PAD
    o += panel(IX, IY, lw, hh, "Encryption pipeline")
    # flow: Plaintext -> AES-256-GCM -> Ciphertext
    fy = IY + 92
    bw = 170
    o.append(rrect(IX + 40, fy, bw, 72, 13, A(C["amber"], 0.10), C["amber"], 1.3))
    o.append(text(IX + 40 + bw / 2, fy + 32, "Plaintext", 13, C["amber"], 700, "middle"))
    o.append(text(IX + 40 + bw / 2, fy + 50, "in memory only", 9.5, C["t2"], 500, "middle"))
    mx = IX + 40 + bw + (lw - 80 - 2 * bw) / 2
    o.append(f'<circle cx="{mx}" cy="{fy+36}" r="30" fill="{A(C["brandA"],0.14)}" stroke="{C["brandA"]}" stroke-width="1.6"/>')
    o.append(icon("lock", mx, fy + 32, C["brandA"], 1.4))
    o.append(text(mx, fy + 84, "AES-256-GCM", 11, C["brandA"], 800, "middle", 0.4))
    o.append(text(mx, fy + 100, "AAD = tenant + key", 9, C["t2"], 500, "middle"))
    o.append(f'<path d="M{IX+40+bw+8} {fy+36} L{mx-34} {fy+36}" stroke="{C["t3"]}" stroke-width="1.5" marker-end="url(#ah)"/>')
    o.append(f'<path d="M{mx+34} {fy+36} L{IX+lw-48-bw-8} {fy+36}" stroke="{C["t3"]}" stroke-width="1.5"/>')
    o.append(rrect(IX + lw - 48 - bw, fy, bw, 72, 13, A(C["cyan"], 0.10), C["cyan"], 1.3))
    o.append(text(IX + lw - 48 - bw / 2, fy + 32, "Ciphertext", 13, C["cyan"], 700, "middle"))
    o.append(text(IX + lw - 48 - bw / 2, fy + 50, "on disk", 9.5, C["t2"], 500, "middle"))
    # properties list
    py = fy + 148
    for ic, col, k, s in [("finger", "brand", "AAD binds tenant + key", "ciphertext can't be relocated between tenants"),
                          ("shieldok", "green", "Authenticated encryption", "tamper is detected on decrypt"),
                          ("lock", "cyan", "Only ciphertext touches disk", "the database on disk holds nothing readable")]:
        o.append(rrect(IX + 24, py, lw - 48, 52, 11, "rgba(255,255,255,0.03)", C["line"], 1))
        o.append(chip(IX + 36, py + 9, ic, ACCENT[col]))
        o.append(text(IX + 82, py + 24, k, 12, C["txt"], 650))
        o.append(text(IX + 82, py + 40, s, 10, C["t2"], 500))
        py += 62
    # right: key management
    o += panel(IX + lw + 20, IY, rw, hh, "Key management")
    kx = IX + lw + 38
    kw = rw - 36
    rows = [("lock", "brand", "PDI_MASTER_KEY", "base64 · 32-byte AES-256", ("SET", "good")),
            ("building", "cyan", "KMS / HSM", "inside your private facility", None),
            ("finger", "green", "Per-record AAD", "binds tenant + key", None),
            ("warn", "amber", "Ephemeral if unset", "dev only — never production", None)]
    ky = IY + 46
    for ic, col, k, s, pt in rows:
        o.append(rrect(kx, ky, kw, 60, 11, "rgba(255,255,255,0.03)", C["line"], 1))
        o.append(chip(kx + 12, ky + 13, ic, ACCENT[col]))
        o.append(text(kx + 58, ky + 27, k, 12, C["txt"], 650))
        o.append(text(kx + 58, ky + 43, s, 9.5, C["t2"], 500))
        if pt:
            o.append(pill(kx + kw - 14, ky + 27, pt[0], pt[1]))
        ky += 70
    o.append(rrect(kx, ky + 4, kw, 44, 11, A(C["brandA"], 0.08), C["brandA"], 1))
    o.append(icon("clock", kx + 24, ky + 26, C["brandA"], 0.8))
    o.append(text(kx + 46, ky + 22, "Rotation", 11, C["txt"], 650))
    o.append(text(kx + 46, ky + 37, "re-seal under a new key, audited", 9.5, C["t2"], 500))
    return o


def v_deployment():
    o = []
    lw = IW * 0.52
    rw = IW - lw - 20
    # left: deployment tiers
    o += panel(IX, IY, lw, 300, "Deployment", right="models the proposal's tiers")
    opts = [("building", "brand", "On-premises", "in your own facility · your hardware", True),
            ("shieldup" if False else "shieldok", "cyan", "Colocation · Tier III+", "carrier-grade data center, your keys", False)]
    dy = IY + 46
    for ic, col, k, s, on in opts:
        c = ACCENT[col]
        o.append(rrect(IX + 24, dy, lw - 48, 76, 13, A(c, 0.10) if on else "rgba(255,255,255,0.03)", c if on else C["line"], 1.4 if on else 1))
        o.append(chip(IX + 38, dy + 21, ic, c))
        o.append(text(IX + 84, dy + 34, k, 13.5, C["txt"], 700))
        o.append(text(IX + 84, dy + 52, s, 10, C["t2"], 500))
        if on:
            o.append(status_dot(IX + lw - 40, dy + 38, "ACTIVE", "on"))
        dy += 88
    o.append(rrect(IX + 24, dy, lw - 48, 44, 11, A(C["green"], 0.08), C["green"], 1))
    o.append(icon("finger", IX + 46, dy + 22, C["green"], 0.85))
    o.append(text(IX + 68, dy + 19, "Your hardware, your keys, your walls", 11, C["txt"], 650))
    o.append(text(IX + 68, dy + 34, "PDI_MASTER_KEY lives in your KMS/HSM", 9.5, C["t2"], 500))
    # right: health tiles
    tw = (rw - 16) / 2
    hx = IX + lw + 20
    tiles = [("Uptime", "99.99%", "30-day", C["green"], "bolt"),
             ("p50 latency", "8 ms", "seal + audit", C["brandA"], "clock"),
             ("Requests", "1.2k", "per minute", C["amber"], "chart"),
             ("Tenants", "2", "isolated", C["cyan"], "people")]
    for i, (lbl, val, sub, col, ic) in enumerate(tiles):
        tx = hx + (i % 2) * (tw + 16)
        ty = IY + (i // 2) * 100
        o += tile(tx, ty, tw, 84, lbl, val, sub, col, ic)
    # bottom: services status full width
    y2 = IY + 300 + 22
    hh = CONTENT_Y + CONTENT_H - PAD - y2
    o += panel(IX, y2, IW, hh, "System health", right="GET /health · continuous verify")
    svc = [("API", "pdi.api", "live", "200 OK"),
           ("Vault store", "AES-256-GCM", "sealed", "ciphertext only"),
           ("Audit chain", "hash-chain", "intact", "1,845 verified"),
           ("Snapshot", "DR export", "ready", "ciphertext only")]
    colw = (IW - 36) / 4
    for i, (name, impl, st, note) in enumerate(svc):
        sx = IX + 18 + i * colw
        o.append(rrect(sx, y2 + 44, colw - 16, hh - 64, 12, "rgba(255,255,255,0.03)", C["line"], 1))
        o.append(f'<circle cx="{sx+22}" cy="{y2+72}" r="6" fill="{C["green"]}"/>')
        o.append(text(sx + 38, y2 + 76, name, 12.5, C["txt"], 700))
        o.append(text(sx + 16, y2 + 100, impl, 10, C["t2"], 500))
        o.append(pill(sx + colw - 30, y2 + 74, st, "good"))
        o.append(text(sx + 16, y2 + 124, note, 9.5, C["t3"], 500))
    return o


VIEWS = [
    (1, "Overview", "Overview", v_overview),
    (2, "Vault", "Vault", v_vault),
    (3, "Audit Log", "Audit", v_audit),
    (4, "Tenants & Access", "Tenants", v_tenants),
    (5, "Encryption & Keys", "Encryption", v_encryption),
    (6, "Deployment & Health", "Deployment", v_deployment),
]


def render(num, title, nav, fn):
    o = frame(title, nav)
    o.append('<marker id="ah" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">'
             f'<path d="M0 0 L6 3 L0 6 Z" fill="{C["t3"]}"/></marker>')
    o += fn()
    o += close()
    return "".join(o)


def main():
    for num, title, nav, fn in VIEWS:
        slug = title.lower().replace(" & ", "-").replace(" ", "-")
        with open(os.path.join(OUT, f"{num:02d}-{slug}.svg"), "w") as f:
            f.write(render(num, title, nav, fn))
    print(f"generated {len(VIEWS)} desktop screens")


if __name__ == "__main__":
    main()
