#!/usr/bin/env python3
"""Generate the PDI operator-console screen SVGs — one screen per capability of
the Private Data Infrastructure vault, in the product's deep-indigo / vault-cyan
style. Every screen is a self-contained SVG (no fonts, images, or scripts), so it
renders identically in a browser, a README, and any converter.

Run:    python3 docs/screens/build.py
Output: docs/screens/NN-name.svg
Design language: Deep Indigo #1A1333 · Vault Cyan #38BDF8 · Soft Cyan #9FD8E8
                 · Soft Silver #C7C9D9 · SF-style system type · liquid-glass cards.
"""

from __future__ import annotations

import html
import math
import os

OUT = os.path.dirname(os.path.abspath(__file__))

# ---- palette (QRME design language) ---------------------------------------
C = {
    "scrA": "#181235", "scrB": "#0c0920", "frameA": "#2a2352", "frameB": "#0a0818",
    "card": "#201a48", "card2": "#181240", "line": "#302a60", "tab": "#0e0a26",
    "txt": "#f2effc", "t2": "#9a93c6", "t3": "#6a6399",
    "brandA": "#38bdf8", "brandB": "#7dd3fc",          # vault cyan
    "amber": "#ffb84d", "green": "#7bc47f", "cyan": "#9fd8e8",
    "red": "#e0687a", "gold": "#ffce54", "silver": "#c7c9d9", "pink": "#e78bd0",
    "indigo": "#5b54d6",
}
ACCENT = {"brand": C["brandA"], "amber": C["amber"], "green": C["green"],
          "cyan": C["cyan"], "red": C["red"], "gold": C["gold"],
          "silver": C["silver"], "pink": C["pink"], "indigo": C["indigo"]}
FONT = ("-apple-system,BlinkMacSystemFont,'SF Pro Display','SF Pro Text',"
        "'Segoe UI',Roboto,system-ui,sans-serif")

W, H = 320, 660
PX, PY, PW, PH = 10, 12, 300, 636
SX, SY, SW, SH = 20, 22, 280, 616
CX, CW = 34, 252            # content left / width


def esc(s):
    return html.escape(str(s), quote=True)


def A(hexcol, a):
    """hex #rrggbb + alpha 0..1 -> rgba() string. cairosvg-safe (8-digit hex
    alpha renders opaque there; rgba() is honoured everywhere)."""
    h = hexcol.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{a})"


# --------------------------------------------------------------------------- #
# tiny vector icon set (drawn, not emoji, so it renders identically anywhere)
# --------------------------------------------------------------------------- #
def icon(name, cx, cy, col, s=1.0):
    def sc(v):
        return v * s
    p = f'fill="{col}"'
    st = f'fill="none" stroke="{col}" stroke-width="{1.7*s:.2f}" stroke-linecap="round" stroke-linejoin="round"'
    if name == "person":
        return (f'<circle cx="{cx}" cy="{cy-sc(4)}" r="{sc(3.6)}" {st}/>'
                f'<path d="M{cx-sc(6)} {cy+sc(7)} c0 -{sc(6)} {sc(12)} -{sc(6)} {sc(12)} 0" {st}/>')
    if name == "people":
        return (f'<circle cx="{cx-sc(4)}" cy="{cy-sc(4)}" r="{sc(3)}" {st}/>'
                f'<circle cx="{cx+sc(4)}" cy="{cy-sc(4)}" r="{sc(3)}" {st}/>'
                f'<path d="M{cx-sc(9)} {cy+sc(6)} c0 -{sc(5)} {sc(6)} -{sc(5)} {sc(6)} 0 M{cx-sc(1)} {cy+sc(6)} c0 -{sc(5)} {sc(7)} -{sc(5)} {sc(9)} -{sc(1)}" {st}/>')
    if name == "mask":
        return (f'<path d="M{cx-sc(8)} {cy-sc(5)} c{sc(4)} -{sc(2)} {sc(12)} -{sc(2)} {sc(16)} 0 '
                f'c0 {sc(8)} -{sc(5)} {sc(11)} -{sc(8)} {sc(11)} c-{sc(3)} 0 -{sc(8)} -{sc(3)} -{sc(8)} -{sc(11)} Z" {st}/>'
                f'<circle cx="{cx-sc(3)}" cy="{cy-sc(1)}" r="{sc(1)}" {p}/><circle cx="{cx+sc(3)}" cy="{cy-sc(1)}" r="{sc(1)}" {p}/>')
    if name == "star2":  # creator persona
        return (f'<path d="M{cx} {cy-sc(8)} l{sc(2.4)} {sc(5)} {sc(5.4)} {sc(0.6)} -{sc(4)} {sc(3.8)} {sc(1.1)} {sc(5.3)} '
                f'-{sc(4.9)} -{sc(2.7)} -{sc(4.9)} {sc(2.7)} {sc(1.1)} -{sc(5.3)} -{sc(4)} -{sc(3.8)} {sc(5.4)} -{sc(0.6)} Z" {st}/>')
    if name == "building":
        return (f'<rect x="{cx-sc(6)}" y="{cy-sc(8)}" width="{sc(12)}" height="{sc(16)}" rx="1.5" {st}/>'
                + "".join(f'<rect x="{cx-sc(4)+j*sc(3)}" y="{cy-sc(5)+i*sc(3.4)}" width="{sc(2)}" height="{sc(2)}" rx="0.4" {p}/>'
                          for i in range(3) for j in range(3)))
    if name == "photo":
        return (f'<rect x="{cx-sc(8)}" y="{cy-sc(6)}" width="{sc(16)}" height="{sc(12)}" rx="2" {st}/>'
                f'<circle cx="{cx-sc(3)}" cy="{cy-sc(1)}" r="{sc(1.8)}" {st}/>'
                f'<path d="M{cx-sc(8)} {cy+sc(4)} l{sc(5)} -{sc(4)} {sc(4)} {sc(3)} {sc(3)} -{sc(2)} {sc(4)} {sc(3)}" {st}/>')
    if name == "pen":
        return (f'<path d="M{cx-sc(7)} {cy+sc(7)} l{sc(2)} -{sc(5)} {sc(9)} -{sc(9)} {sc(3)} {sc(3)} -{sc(9)} {sc(9)} -{sc(5)} {sc(2)} Z" {st}/>'
                f'<path d="M{cx+sc(2)} {cy-sc(6)} l{sc(3)} {sc(3)}" {st}/>')
    if name == "cal":
        return (f'<rect x="{cx-sc(7)}" y="{cy-sc(6)}" width="{sc(14)}" height="{sc(13)}" rx="2" {st}/>'
                f'<path d="M{cx-sc(7)} {cy-sc(2)} h{sc(14)} M{cx-sc(3)} {cy-sc(8)} v{sc(3)} M{cx+sc(3)} {cy-sc(8)} v{sc(3)}" {st}/>')
    if name == "db":
        return (f'<ellipse cx="{cx}" cy="{cy-sc(5)}" rx="{sc(7)}" ry="{sc(2.6)}" {st}/>'
                f'<path d="M{cx-sc(7)} {cy-sc(5)} v{sc(10)} c0 {sc(1.5)} {sc(3)} {sc(2.6)} {sc(7)} {sc(2.6)} '
                f's{sc(7)} -{sc(1.1)} {sc(7)} -{sc(2.6)} v-{sc(10)} M{cx-sc(7)} {cy} c0 {sc(1.5)} {sc(3)} {sc(2.6)} {sc(7)} {sc(2.6)} s{sc(7)} -{sc(1.1)} {sc(7)} -{sc(2.6)}" {st}/>')
    if name == "mic":
        return (f'<rect x="{cx-sc(3)}" y="{cy-sc(8)}" width="{sc(6)}" height="{sc(11)}" rx="{sc(3)}" {st}/>'
                f'<path d="M{cx-sc(6)} {cy} c0 {sc(5)} {sc(12)} {sc(5)} {sc(12)} 0 M{cx} {cy+sc(5)} v{sc(3)}" {st}/>')
    if name == "chat":
        return f'<path d="M{cx-sc(8)} {cy-sc(6)} h{sc(16)} a2 2 0 0 1 2 2 v{sc(7)} a2 2 0 0 1 -2 2 h-{sc(9)} l-{sc(4)} {sc(4)} v-{sc(4)} h-{sc(3)} a2 2 0 0 1 -2 -2 v-{sc(7)} a2 2 0 0 1 2 -2 Z" {st}/>'
    if name == "heart":
        return (f'<path d="M{cx} {cy+sc(6)} C{cx-sc(9)} {cy-sc(3)},{cx-sc(7)} {cy-sc(9)},{cx} {cy-sc(4)} '
                f'C{cx+sc(7)} {cy-sc(9)},{cx+sc(9)} {cy-sc(3)},{cx} {cy+sc(6)} Z" {p}/>')
    if name == "lock":
        return (f'<rect x="{cx-sc(6)}" y="{cy-sc(2)}" width="{sc(12)}" height="{sc(9)}" rx="2" {st}/>'
                f'<path d="M{cx-sc(3.5)} {cy-sc(2)} v-{sc(3)} a{sc(3.5)} {sc(3.5)} 0 0 1 {sc(7)} 0 v{sc(3)}" {st}/>'
                f'<circle cx="{cx}" cy="{cy+sc(2.5)}" r="{sc(1.2)}" {p}/>')
    if name == "shield":
        return f'<path d="M{cx} {cy-sc(8)} l{sc(7)} {sc(3)} v{sc(5)} c0 {sc(5)} -{sc(3)} {sc(7)} -{sc(7)} {sc(9)} c-{sc(4)} -{sc(2)} -{sc(7)} -{sc(4)} -{sc(7)} -{sc(9)} v-{sc(5)} Z" {st}/>'
    if name == "shieldok":
        return (f'<path d="M{cx} {cy-sc(8)} l{sc(7)} {sc(3)} v{sc(5)} c0 {sc(5)} -{sc(3)} {sc(7)} -{sc(7)} {sc(9)} c-{sc(4)} -{sc(2)} -{sc(7)} -{sc(4)} -{sc(7)} -{sc(9)} v-{sc(5)} Z" {st}/>'
                f'<path d="M{cx-sc(3)} {cy} l{sc(2)} {sc(2.4)} {sc(4)} -{sc(4.5)}" {st}/>')
    if name == "eye":
        return (f'<path d="M{cx-sc(8)} {cy} c{sc(4)} -{sc(6)} {sc(12)} -{sc(6)} {sc(16)} 0 c-{sc(4)} {sc(6)} -{sc(12)} {sc(6)} -{sc(16)} 0 Z" {st}/>'
                f'<circle cx="{cx}" cy="{cy}" r="{sc(2.4)}" {p}/>')
    if name == "chart":
        return "".join(f'<rect x="{cx-sc(7)+i*sc(5)}" y="{cy+sc(6)-sc([5,9,4,11][i])}" width="{sc(3.2)}" height="{sc([5,9,4,11][i])}" rx="1" {p}/>' for i in range(4))
    if name == "gear":
        teeth = "".join(f'<rect x="{cx-sc(1.3)}" y="{cy-sc(9)}" width="{sc(2.6)}" height="{sc(4)}" rx="1" transform="rotate({a} {cx} {cy})" {p}/>' for a in range(0, 360, 45))
        return teeth + f'<circle cx="{cx}" cy="{cy}" r="{sc(4.6)}" {st}/>'
    if name == "target":
        return (f'<circle cx="{cx}" cy="{cy}" r="{sc(7.5)}" {st}/>'
                f'<circle cx="{cx}" cy="{cy}" r="{sc(3.5)}" {st}/>'
                f'<circle cx="{cx}" cy="{cy}" r="{sc(0.9)}" {p}/>')
    if name == "search":
        return (f'<circle cx="{cx-sc(2)}" cy="{cy-sc(2)}" r="{sc(6)}" {st}/>'
                f'<path d="M{cx+sc(3)} {cy+sc(3)} l{sc(4)} {sc(4)}" {st}/>')
    if name == "clock":
        return (f'<circle cx="{cx}" cy="{cy}" r="{sc(7.5)}" {st}/>'
                f'<path d="M{cx} {cy-sc(4)} v{sc(4)} l{sc(3)} {sc(2)}" {st}/>')
    if name == "grid":
        return "".join(f'<rect x="{cx-sc(7)+j*sc(8)}" y="{cy-sc(7)+i*sc(8)}" width="{sc(6)}" height="{sc(6)}" rx="1.4" {st}/>' for i in range(2) for j in range(2))
    if name == "list":
        return (f'<path d="M{cx-sc(6)} {cy-sc(5)} h{sc(12)} M{cx-sc(6)} {cy} h{sc(12)} M{cx-sc(6)} {cy+sc(5)} h{sc(12)}" {st}/>')
    if name == "doc":
        return (f'<path d="M{cx-sc(6)} {cy-sc(8)} h{sc(8)} l{sc(4)} {sc(4)} v{sc(12)} h-{sc(12)} Z" {st}/>'
                f'<path d="M{cx-sc(3)} {cy-sc(1)} h{sc(6)} M{cx-sc(3)} {cy+sc(3)} h{sc(6)}" {st}/>')
    if name == "coin":
        return (f'<circle cx="{cx}" cy="{cy}" r="{sc(7.5)}" {st}/>'
                f'<path d="M{cx} {cy-sc(4)} v{sc(8)} M{cx-sc(2.4)} {cy-sc(2)} h{sc(4)} a{sc(2)} {sc(2)} 0 0 1 0 {sc(4)} h-{sc(4.8)}" {st}/>')
    if name == "gift":
        return (f'<rect x="{cx-sc(7)}" y="{cy-sc(3)}" width="{sc(14)}" height="{sc(9)}" rx="1.5" {st}/>'
                f'<path d="M{cx-sc(8)} {cy-sc(3)} h{sc(16)} M{cx} {cy-sc(3)} v{sc(9)} '
                f'M{cx} {cy-sc(3)} c-{sc(4)} 0 -{sc(5)} -{sc(5)} 0 -{sc(4)} c{sc(4)} -{sc(1)} {sc(4)} {sc(4)} 0 {sc(4)}" {st}/>')
    if name == "info":
        return (f'<circle cx="{cx}" cy="{cy}" r="{sc(7.5)}" {st}/>'
                f'<circle cx="{cx}" cy="{cy-sc(3.5)}" r="{sc(0.9)}" {p}/><path d="M{cx} {cy-sc(1)} v{sc(4.5)}" {st}/>')
    if name == "compass":
        return (f'<circle cx="{cx}" cy="{cy}" r="{sc(7.5)}" {st}/>'
                f'<path d="M{cx+sc(3.5)} {cy-sc(3.5)} l-{sc(2.2)} {sc(5)} -{sc(5)} {sc(2.2)} {sc(2.2)} -{sc(5)} Z" {p}/>')
    if name == "net":
        return (f'<circle cx="{cx}" cy="{cy-sc(5)}" r="{sc(2.4)}" {st}/>'
                f'<circle cx="{cx-sc(6)}" cy="{cy+sc(4)}" r="{sc(2.4)}" {st}/>'
                f'<circle cx="{cx+sc(6)}" cy="{cy+sc(4)}" r="{sc(2.4)}" {st}/>'
                f'<path d="M{cx} {cy-sc(3)} l-{sc(5)} {sc(6)} M{cx} {cy-sc(3)} l{sc(5)} {sc(6)} M{cx-sc(4)} {cy+sc(4)} h{sc(8)}" {st}/>')
    if name == "sliders":
        return (f'<path d="M{cx-sc(7)} {cy-sc(5)} h{sc(14)} M{cx-sc(7)} {cy} h{sc(14)} M{cx-sc(7)} {cy+sc(5)} h{sc(14)}" {st}/>'
                f'<circle cx="{cx+sc(2)}" cy="{cy-sc(5)}" r="{sc(2)}" {p}/><circle cx="{cx-sc(3)}" cy="{cy}" r="{sc(2)}" {p}/><circle cx="{cx+sc(4)}" cy="{cy+sc(5)}" r="{sc(2)}" {p}/>')
    if name == "watch":
        return (f'<rect x="{cx-sc(5)}" y="{cy-sc(5)}" width="{sc(10)}" height="{sc(10)}" rx="2.5" {st}/>'
                f'<path d="M{cx-sc(2.5)} {cy-sc(5)} v-{sc(3)} h{sc(5)} v{sc(3)} M{cx-sc(2.5)} {cy+sc(5)} v{sc(3)} h{sc(5)} v-{sc(3)}" {st}/>')
    if name == "phone":
        return (f'<rect x="{cx-sc(5)}" y="{cy-sc(8)}" width="{sc(10)}" height="{sc(16)}" rx="2.4" {st}/>'
                f'<path d="M{cx-sc(1.6)} {cy+sc(5)} h{sc(3.2)}" {st}/>')
    if name == "headset":
        return (f'<path d="M{cx-sc(8)} {cy+sc(1)} v-{sc(1)} a{sc(8)} {sc(8)} 0 0 1 {sc(16)} 0 v{sc(1)}" {st}/>'
                f'<rect x="{cx-sc(9)}" y="{cy+sc(1)}" width="{sc(4)}" height="{sc(7)}" rx="1.6" {st}/>'
                f'<rect x="{cx+sc(5)}" y="{cy+sc(1)}" width="{sc(4)}" height="{sc(7)}" rx="1.6" {st}/>')
    if name == "robot":
        return (f'<rect x="{cx-sc(7)}" y="{cy-sc(4)}" width="{sc(14)}" height="{sc(11)}" rx="3" {st}/>'
                f'<path d="M{cx} {cy-sc(4)} v-{sc(3)}" {st}/><circle cx="{cx}" cy="{cy-sc(8)}" r="{sc(1.4)}" {p}/>'
                f'<circle cx="{cx-sc(3)}" cy="{cy+sc(1)}" r="{sc(1.5)}" {p}/><circle cx="{cx+sc(3)}" cy="{cy+sc(1)}" r="{sc(1.5)}" {p}/>')
    if name == "speaker":
        return (f'<rect x="{cx-sc(6)}" y="{cy-sc(8)}" width="{sc(12)}" height="{sc(16)}" rx="3" {st}/>'
                f'<circle cx="{cx}" cy="{cy+sc(2)}" r="{sc(3.4)}" {st}/><circle cx="{cx}" cy="{cy-sc(5)}" r="{sc(1)}" {p}/>')
    if name == "cloud":
        return f'<path d="M{cx-sc(6)} {cy+sc(4)} a{sc(4)} {sc(4)} 0 0 1 {sc(1)} -{sc(8)} a{sc(5)} {sc(5)} 0 0 1 {sc(10)} {sc(1)} a{sc(3.5)} {sc(3.5)} 0 0 1 -{sc(1)} {sc(7)} Z" {st}/>'
    if name == "finger":
        return (f'<path d="M{cx-sc(6)} {cy+sc(2)} c0 -{sc(7)} {sc(3)} -{sc(9)} {sc(6)} -{sc(9)} c{sc(3)} 0 {sc(6)} {sc(2)} {sc(6)} {sc(7)}" {st}/>'
                f'<path d="M{cx-sc(3)} {cy+sc(4)} c0 -{sc(6)} {sc(2)} -{sc(7)} {sc(3)} -{sc(7)} c{sc(2)} 0 {sc(3)} {sc(2)} {sc(3)} {sc(5)}" {st}/>'
                f'<path d="M{cx} {cy+sc(6)} v-{sc(6)}" {st}/>')
    if name == "brain":
        return (f'<circle cx="{cx-sc(3)}" cy="{cy}" r="{sc(5)}" {st}/>'
                f'<circle cx="{cx+sc(3)}" cy="{cy}" r="{sc(5)}" {st}/>')
    if name == "bolt":
        return f'<path d="M{cx+sc(2)} {cy-sc(8)} L{cx-sc(6)} {cy+sc(1)} L{cx} {cy+sc(1)} L{cx-sc(2)} {cy+sc(8)} L{cx+sc(6)} {cy-sc(1)} L{cx} {cy-sc(1)} Z" {p}/>'
    if name == "leaf":
        return f'<path d="M{cx-sc(6)} {cy+sc(6)} c0 -{sc(9)} {sc(6)} -{sc(13)} {sc(12)} -{sc(12)} c{sc(1)} {sc(6)} -{sc(3)} {sc(12)} -{sc(12)} {sc(12)} Z M{cx-sc(3)} {cy+sc(3)} l{sc(6)} -{sc(6)}" {st}/>'
    if name == "link":
        return f'<path d="M{cx-sc(2)} {cy+sc(2)} l-{sc(3)} {sc(3)} a{sc(3)} {sc(3)} 0 0 1 -{sc(4)} -{sc(4)} l{sc(3)} -{sc(3)} m{sc(6)} -{sc(2)} l{sc(3)} -{sc(3)} a{sc(3)} {sc(3)} 0 0 1 {sc(4)} {sc(4)} l-{sc(3)} {sc(3)} M{cx-sc(3)} {cy+sc(3)} l{sc(6)} -{sc(6)}" {st}/>'
    if name == "warn":
        return (f'<path d="M{cx} {cy-sc(8)} L{cx+sc(8)} {cy+sc(6)} H{cx-sc(8)} Z" {st}/>'
                f'<path d="M{cx} {cy-sc(3)} v{sc(4)}" {st}/><circle cx="{cx}" cy="{cy+sc(4)}" r="{sc(0.9)}" {p}/>')
    if name == "plus":
        return f'<path d="M{cx} {cy-sc(7)} v{sc(14)} M{cx-sc(7)} {cy} h{sc(14)}" fill="none" stroke="{col}" stroke-width="{2.4*s:.2f}" stroke-linecap="round"/>'
    if name == "cross":  # medical
        return f'<path d="M{cx} {cy-sc(7)} v{sc(14)} M{cx-sc(7)} {cy} h{sc(14)}" fill="none" stroke="{col}" stroke-width="{3*s:.2f}" stroke-linecap="round"/>'
    if name == "book":
        return (f'<rect x="{cx-sc(7)}" y="{cy-sc(7)}" width="{sc(14)}" height="{sc(14)}" rx="2" {st}/>'
                f'<path d="M{cx} {cy-sc(7)} v{sc(14)}" {st}/>')
    if name == "flag":
        return (f'<path d="M{cx-sc(6)} {cy+sc(8)} v-{sc(16)}" {st}/>'
                f'<path d="M{cx-sc(6)} {cy-sc(7)} h{sc(11)} l-{sc(2.5)} {sc(3.5)} {sc(2.5)} {sc(3.5)} h-{sc(11)} Z" {st}/>')
    if name == "dove":  # memorial / departure
        return (f'<path d="M{cx-sc(8)} {cy+sc(2)} c{sc(3)} -{sc(5)} {sc(8)} -{sc(6)} {sc(11)} -{sc(3)} '
                f'c{sc(2)} -{sc(4)} {sc(5)} -{sc(4)} {sc(5)} -{sc(4)} c-{sc(1)} {sc(3)} -{sc(2)} {sc(4)} -{sc(4)} {sc(5)} '
                f'c-{sc(1)} {sc(4)} -{sc(5)} {sc(6)} -{sc(9)} {sc(5)} l{sc(2)} {sc(3)} h-{sc(5)} Z" {st}/>')
    # fallback dot
    return f'<circle cx="{cx}" cy="{cy}" r="{sc(4)}" {p}/>'


def stars(x, y, rating, col, s=1.0):
    """Row of 5 stars, `rating` (0..5) filled; returns svg + label handled by caller."""
    out = []
    for i in range(5):
        cx = x + i * 12 * s
        full = i < math.floor(rating)
        fill = col if full else "none"
        out.append(f'<path d="M{cx} {y-4*s} l{1.3*s} {2.7*s} {2.9*s} {0.3*s} -{2.1*s} {2*s} {0.6*s} {2.9*s} '
                   f'-{2.6*s} -{1.5*s} -{2.6*s} {1.5*s} {0.6*s} -{2.9*s} -{2.1*s} -{2*s} {2.9*s} -{0.3*s} Z" '
                   f'fill="{fill}" stroke="{col}" stroke-width="{0.9*s}" stroke-linejoin="round"/>')
    return "".join(out)


# --------------------------------------------------------------------------- #
# primitives
# --------------------------------------------------------------------------- #
def rrect(x, y, w, h, r, fill, stroke=None, sw=1):
    s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r}" fill="{fill}"{s}/>'


def text(x, y, s, size, fill, weight=400, anchor="start", spacing=0, mono=False):
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    fam = "ui-monospace,Menlo,monospace" if mono else FONT
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{ls}>{esc(s)}</text>')


def chip(x, y, ic, col):
    return (rrect(x, y, 34, 34, 11, A(col, 0.16)) + icon(ic, x + 17, y + 17, col, 0.92))


def pill(x, y, label, tone):
    col = {"good": C["green"], "warn": C["amber"], "crit": C["red"],
           "info": C["cyan"], "brand": C["brandA"], "gold": C["gold"]}[tone]
    w = 12 + len(label) * 6.2
    return (rrect(x - w, y - 11, w, 17, 8, A(col, 0.16))
            + text(x - w / 2, y + 1, label, 9.5, col, 700, "middle", 0.4))


def meter(x, y, w, pct, grad):
    return (rrect(x, y, w, 7, 4, "#0d0a24", C["line"], 1)
            + rrect(x, y, max(6, w * pct), 7, 4, f"url(#{grad})"))


def spark(x, y, w, h, pts, col):
    n = len(pts)
    lo, hi = min(pts), max(pts)
    rng = (hi - lo) or 1
    coords = []
    for i, v in enumerate(pts):
        px = x + w * i / (n - 1)
        py = y + h - (v - lo) / rng * h
        coords.append(f"{px:.1f},{py:.1f}")
    endx, endy = coords[-1].split(",")
    return (f'<polyline points="{" ".join(coords)}" fill="none" stroke="{col}" '
            f'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<circle cx="{endx}" cy="{endy}" r="3.2" fill="{col}"/>')


def button(x, y, w, label, kind="brand", h=42):
    if kind == "brand":
        fill, tcol, st = "url(#gBrand)", "#fff", None
    elif kind == "danger":
        fill, tcol, st = A(C["red"], 0.16), C["red"], C["red"]
    elif kind == "amber":
        fill, tcol, st = "url(#gAmber)", "#20160a", None
    else:  # ghost
        fill, tcol, st = "rgba(255,255,255,0.06)", C["txt"], C["line"]
    return (rrect(x, y, w, h, 13, fill, st, 1)
            + text(x + w / 2, y + h / 2 + 4.5, label, 13, tcol, 700, "middle"))


def toggle(x, y, on):
    bg = C["green"] if on else "#2a2450"
    kx = x + 16 if on else x + 2
    return (rrect(x, y, 34, 20, 10, bg)
            + f'<circle cx="{kx+8}" cy="{y+10}" r="8" fill="#fff"/>')


def status_dot(x, y, label, tone):
    col = {"on": C["green"], "off": C["t3"], "avail": C["amber"], "crit": C["red"]}[tone]
    w = 14 + len(label) * 6.0
    return (rrect(x - w, y - 9, w, 16, 8, A(col, 0.14))
            + f'<circle cx="{x-w+9}" cy="{y-1}" r="3" fill="{col}"/>'
            + text(x - w + 16, y + 3, label, 9, col, 700, "start", 0.5))


# --------------------------------------------------------------------------- #
# frame
# --------------------------------------------------------------------------- #
PLATFORM = "ios"          # "ios" | "android"


def _status_icons(xr, y, col):
    o = []
    if PLATFORM == "android":
        o.append(rrect(xr - 9, y - 7, 8, 12, 1.5, "none", col, 1.2))
        o.append(rrect(xr - 7.5, y - 3, 5, 7, 1, col))
        o.append(f'<path d="M{xr-20} {y+5} L{xr-15} {y-4} L{xr-10} {y+5} Z" fill="{col}"/>')
        o.append(f'<path d="M{xr-33} {y+5} L{xr-33} {y-2} L{xr-25} {y+5} Z" fill="{col}"/>')
    else:
        o.append(rrect(xr - 22, y - 6, 20, 11, 3, "none", col, 1.1))
        o.append(rrect(xr - 20, y - 4, 14, 7, 2, col))
        o.append(rrect(xr - 1.4, y - 2.5, 2, 5, 1, col))
        o.append(f'<path d="M{xr-35} {y-1} a6 6 0 0 1 11 0" fill="none" stroke="{col}" stroke-width="1.3"/>')
        o.append(f'<circle cx="{xr-29.5}" cy="{y+3}" r="1.2" fill="{col}"/>')
        for i in range(4):
            o.append(rrect(xr - 52 + i * 4, y + 4 - (i + 1) * 1.9, 2.6, (i + 1) * 1.9, 0.8, col))
    return "".join(o)


def statusbar():
    tcol = C["silver"] if "silver" in C else C["t2"]
    notch = "#05070d"
    o = []
    if PLATFORM == "android":
        o.append(f'<circle cx="{W/2}" cy="{SY+12}" r="4.5" fill="{notch}"/>')
        o.append(f'<circle cx="{W/2}" cy="{SY+12}" r="4.5" fill="none" stroke="{C["line"]}" stroke-width="1"/>')
    else:
        o.append(rrect(W / 2 - 30, SY + 5, 60, 15, 7.5, notch))
    o.append(text(SX + 14, SY + 34, "9:41", 11, tcol, 600))
    o.append(_status_icons(SX + SW - 14, SY + 34, tcol))
    return o


def navbar():
    o = []
    yb = SY + SH - 6
    if PLATFORM == "android":
        cx = W / 2
        o.append(f'<path d="M{cx-34+5} {yb-4.5} L{cx-34-5} {yb} L{cx-34+5} {yb+4.5} Z" fill="none" stroke="rgba(255,255,255,0.5)" stroke-width="1.3" stroke-linejoin="round"/>')
        o.append(f'<circle cx="{cx}" cy="{yb}" r="4.6" fill="none" stroke="rgba(255,255,255,0.5)" stroke-width="1.3"/>')
        o.append(rrect(cx + 34 - 4.6, yb - 4.6, 9.2, 9.2, 1.6, "none", "rgba(255,255,255,0.5)", 1.3))
    else:
        o.append(rrect(W / 2 - 42, yb - 1, 84, 4, 2, "rgba(255,255,255,0.6)"))
    return o


def head(num, title, sub, accent="brand", locked=False):
    ac = ACCENT.get(accent, C["brandA"])
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
           f'viewBox="0 0 {W} {H}" role="img" aria-label="{esc(title)} screen">']
    out.append(f'''<defs>
      <linearGradient id="gScr" x1="0" y1="0" x2="0.6" y2="1">
        <stop offset="0" stop-color="{C['scrA']}"/><stop offset="1" stop-color="{C['scrB']}"/></linearGradient>
      <linearGradient id="gFrame" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stop-color="{C['frameA']}"/><stop offset="1" stop-color="{C['frameB']}"/></linearGradient>
      <linearGradient id="gCard" x1="0" y1="0" x2="0.4" y2="1">
        <stop offset="0" stop-color="{C['card']}"/><stop offset="1" stop-color="{C['card2']}"/></linearGradient>
      <linearGradient id="gBrand" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0" stop-color="{C['brandA']}"/><stop offset="1" stop-color="{C['brandB']}"/></linearGradient>
      <linearGradient id="gAmber" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0" stop-color="{C['amber']}"/><stop offset="1" stop-color="#ffd27a"/></linearGradient>
      <linearGradient id="mV" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{C['brandA']}"/><stop offset="1" stop-color="{C['brandB']}"/></linearGradient>
      <linearGradient id="mA" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{C['amber']}"/><stop offset="1" stop-color="#ff9f45"/></linearGradient>
      <linearGradient id="mG" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#5fb87a"/><stop offset="1" stop-color="{C['green']}"/></linearGradient>
      <linearGradient id="mC" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#6bb6d6"/><stop offset="1" stop-color="{C['cyan']}"/></linearGradient>
      <radialGradient id="orb" cx="36%" cy="30%" r="78%">
        <stop offset="0" stop-color="#cbeeff"/><stop offset="38%" stop-color="{C['brandA']}"/>
        <stop offset="78%" stop-color="#1f6fb2"/><stop offset="100%" stop-color="#0b2438"/></radialGradient>
      <radialGradient id="glow" cx="50%" cy="50%" r="50%">
        <stop offset="0" stop-color="{ac}" stop-opacity="0.5"/><stop offset="1" stop-color="{ac}" stop-opacity="0"/></radialGradient>
    </defs>''')
    out.append(rrect(PX, PY, PW, PH, 40, "url(#gFrame)"))
    out.append(rrect(SX, SY, SW, SH, 31, "url(#gScr)"))
    out += statusbar()
    lockmark = "  🔒" if locked else ""
    out.append(text(CX, SY + 66, title, 20, C["txt"], 700, spacing=-0.4))
    if locked:
        lx = CX + len(title) * 11.2 + 18
        out.append(icon("lock", lx, SY + 60, C["amber"], 0.66))
    if sub:
        out.append(text(CX, SY + 84, sub, 11.5, C["t2"], 400))
    return out


def tabbar(tabs, active):
    out = [rrect(SX, SY + SH - 52, SW, 52, 0, C["tab"])]
    out.append(f'<rect x="{SX}" y="{SY+SH-52}" width="{SW}" height="1" fill="{C["line"]}"/>')
    step = SW / len(tabs)
    for i, (ic, lbl) in enumerate(tabs):
        cx = SX + step * i + step / 2
        on = (i == active)
        col = C["brandA"] if on else C["t3"]
        out.append(icon(ic, cx, SY + SH - 34, col, 0.72))
        out.append(text(cx, SY + SH - 12, lbl, 8.2, col, 600, "middle"))
    return out


MAIN = [("grid", "Overview"), ("lock", "Vault"), ("shieldok", "Audit"), ("gear", "More")]
TENANTS = [("people", "Tenants"), ("doc", "Tokens"), ("cloud", "Intake"), ("gear", "More")]
AUDIT = [("shieldok", "Audit"), ("search", "Verify"), ("clock", "Log"), ("gear", "More")]
OPS = [("building", "Deploy"), ("db", "Backup"), ("chart", "Health"), ("gear", "More")]


def close():
    return ['</svg>']


# --------------------------------------------------------------------------- #
# building blocks
# --------------------------------------------------------------------------- #
def card_block(y, c):
    h = c.get("h", 52)
    extra = c.get("extra")
    if extra and extra[0] in ("meter", "spark"):
        h = 66
    out = [rrect(CX, y, CW, h, 16, "url(#gCard)", C["line"], 1)]
    tx = CX + 14
    if c.get("icon"):
        out.append(chip(CX + 12, y + (h - 34) / 2 if not extra else y + 9, c["icon"], ACCENT[c["color"]]))
        tx = CX + 56
    ty = y + (26 if extra else h / 2 - 6)
    out.append(text(tx, ty, c["k"], 13, C["txt"], 600))
    if c.get("s"):
        out.append(text(tx, ty + 15, c["s"], 11, C["t2"]))
    if c.get("metric"):
        out.append(text(CX + CW - 14, y + h / 2 + 7, c["metric"], 20, C["txt"], 750, "end"))
    if c.get("pill"):
        out.append(pill(CX + CW - 14, y + 20, c["pill"][0], c["pill"][1]))
    if c.get("stat"):
        out.append(status_dot(CX + CW - 14, y + h / 2, c["stat"][0], c["stat"][1]))
    if extra:
        if extra[0] == "meter":
            out.append(meter(tx, y + h - 16, CW - (tx - CX) - 14, extra[1], extra[2]))
        elif extra[0] == "spark":
            out.append(spark(tx, y + h - 30, CW - (tx - CX) - 16, 22, extra[1], ACCENT[extra[2]]))
    return "".join(out), y + h + 10


def check_row(y, ic, col, k, s, count, on=True):
    out = [rrect(CX, y, CW, 46, 14, "url(#gCard)", C["line"], 1)]
    out.append(chip(CX + 10, y + 6, ic, ACCENT[col]))
    out.append(text(CX + 54, y + 20, k, 12.5, C["txt"], 600))
    out.append(text(CX + 54, y + 34, s, 10.5, C["t2"]))
    if count:
        out.append(text(CX + CW - 40, y + 27, count, 11, C["t2"], 500, "end"))
    if on:
        out.append(f'<circle cx="{CX+CW-20}" cy="{y+23}" r="9" fill="{A(C["green"],0.18)}" stroke="{C["green"]}" stroke-width="1"/>')
        out.append(icon("shieldok", CX + CW - 20, y + 23, C["green"], 0.42) if False else
                   f'<path d="M{CX+CW-24} {y+23} l{2.6} {3} {5} -{5.5}" fill="none" stroke="{C["green"]}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>')
    else:
        out.append(f'<circle cx="{CX+CW-20}" cy="{y+23}" r="9" fill="none" stroke="{C["t3"]}" stroke-width="1.4"/>')
    return "".join(out), y + 54


def person_row(y, initial, col, name, rel, tone_label, tone):
    out = [rrect(CX, y, CW, 50, 14, "url(#gCard)", C["line"], 1)]
    out.append(f'<circle cx="{CX+26}" cy="{y+25}" r="15" fill="{A(col,0.20)}" stroke="{col}" stroke-width="1.2"/>')
    out.append(text(CX + 26, y + 30, initial, 14, col, 800, "middle"))
    out.append(text(CX + 52, y + 22, name, 12.5, C["txt"], 650))
    out.append(text(CX + 52, y + 37, rel, 10.5, C["t2"]))
    out.append(pill(CX + CW - 14, y + 25, tone_label, tone))
    return "".join(out), y + 58


def orb(cx, cy, r, head_profile=False):
    out = [f'<circle cx="{cx}" cy="{cy}" r="{r*1.5:.1f}" fill="url(#glow)"/>',
           f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#orb)"/>',
           f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="rgba(255,255,255,0.20)" stroke-width="1"/>',
           f'<ellipse cx="{cx-r*0.28:.1f}" cy="{cy-r*0.34:.1f}" rx="{r*0.30:.1f}" ry="{r*0.18:.1f}" fill="rgba(255,255,255,0.40)"/>']
    if head_profile:
        # simple facing-left head/brain profile line, echoing the launch mockup
        out.append(f'<path d="M{cx+r*0.5:.1f} {cy+r*0.55:.1f} '
                   f'C{cx-r*0.1:.1f} {cy+r*0.62:.1f},{cx-r*0.62:.1f} {cy+r*0.34:.1f},{cx-r*0.6:.1f} {cy-r*0.06:.1f} '
                   f'C{cx-r*0.58:.1f} {cy-r*0.5:.1f},{cx-r*0.2:.1f} {cy-r*0.66:.1f},{cx+r*0.16:.1f} {cy-r*0.6:.1f} '
                   f'C{cx+r*0.5:.1f} {cy-r*0.54:.1f},{cx+r*0.6:.1f} {cy-r*0.2:.1f},{cx+r*0.4:.1f} {cy+r*0.05:.1f}" '
                   f'fill="none" stroke="rgba(255,255,255,0.85)" stroke-width="1.6" stroke-linecap="round"/>')
        for dx, dy in [(-0.18, -0.18), (0.02, -0.28), (0.16, -0.06), (-0.1, 0.12), (0.22, 0.14)]:
            out.append(f'<circle cx="{cx+r*dx:.1f}" cy="{cy+r*dy:.1f}" r="1.5" fill="rgba(255,255,255,0.9)"/>')
    return "".join(out)


def ring(cx, cy, r, pct, col, sw=9):
    circ = 2 * math.pi * r
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{A(col,0.16)}" stroke-width="{sw}"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{col}" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-dasharray="{circ*pct:.1f} {circ:.1f}" '
            f'transform="rotate(-90 {cx} {cy})"/>')


def statbar(y, label, pct, val, col):
    out = [text(CX, y, label, 12, C["txt"], 600),
           text(CX + CW, y, val, 12, col, 750, "end"),
           rrect(CX, y + 8, CW, 7, 4, "#0d0a24", C["line"], 1),
           rrect(CX, y + 8, max(8, CW * pct), 7, 4, col)]
    return "".join(out), y + 30


def qr(qx, qy, qs, seed=7):
    import random
    random.seed(seed)
    out = [rrect(qx, qy, qs, qs, 14, "#ffffff")]
    cell = (qs - 20) / 21

    def finder(r, c):
        res = []
        for i in range(7):
            for j in range(7):
                on = i in (0, 6) or j in (0, 6) or (2 <= i <= 4 and 2 <= j <= 4)
                if on:
                    res.append(rrect(qx + 10 + (c + j) * cell, qy + 10 + (r + i) * cell, cell, cell, 0, "#140f34"))
        return "".join(res)
    grid = []
    for r in range(21):
        for c in range(21):
            if (r < 8 and c < 8) or (r < 8 and c > 12) or (r > 12 and c < 8):
                continue
            if random.random() > 0.5:
                grid.append(rrect(qx + 10 + c * cell, qy + 10 + r * cell, cell, cell, 0, "#140f34"))
    out.append("".join(grid) + finder(0, 0) + finder(0, 14) + finder(14, 0))
    return "".join(out)


# --------------------------------------------------------------------------- #
# screen renderer
# --------------------------------------------------------------------------- #
def render(spec):
    num = spec["num"]
    out = head(f"{num:02d}", spec["title"], spec.get("sub", ""),
               spec.get("accent", "brand"), spec.get("locked", False))
    y = SY + 100
    hero = spec.get("hero")

    if hero == "overview":
        cx0 = W / 2
        out.append(orb(cx0, y + 40, 34))
        out.append(icon("lock", cx0, y + 40, "rgba(255,255,255,0.95)", 1.5))
        y += 100
        out.append(f'<circle cx="{cx0-46}" cy="{y-4}" r="3" fill="{C["green"]}"/>')
        out.append(text(cx0, y, "Vault online", 14, "#fff", 700, "middle"))
        out.append(text(cx0, y + 17, "AES-256-GCM · tamper-evident audit", 10, C["t2"], 500, "middle"))
        y += 38
        gw = (CW - 10) / 2
        cells = [("Tenants", "2", "qrme · jim", C["brandA"]),
                 ("Records", "1,842", "sealed", C["amber"]),
                 ("Audit chain", "OK", "verified", C["green"]),
                 ("Deployment", "Tier III+", "", C["cyan"])]
        for i, (k, v, sfx, col) in enumerate(cells):
            gx = CX + (i % 2) * (gw + 10)
            gy = y + (i // 2) * 62
            out.append(rrect(gx, gy, gw, 54, 14, "url(#gCard)", C["line"], 1))
            out.append(text(gx + 12, gy + 20, k, 10, C["t2"], 500))
            small = v in ("OK", "Tier III+")
            out.append(text(gx + 12, gy + (40 if small else 42), v, 15 if small else 19, col, 800))
            out.append(text(gx + gw - 12, gy + (40 if small else 42), sfx, 9, C["t2"], 500, "end"))
        y += 132
        out.append(rrect(CX, y, CW, 44, 13, A(C["green"], 0.09), C["green"], 1))
        out.append(icon("shieldok", CX + 24, y + 22, C["green"], 0.85))
        out.append(text(CX + 46, y + 19, "Hash-chain verified", 11.5, C["txt"], 650))
        out.append(text(CX + 46, y + 34, "no record was retroactively edited", 9.5, C["t2"]))

    elif hero == "storerec":
        out.append(rrect(CX, y, CW, 58, 15, "url(#gCard)", C["line"], 1))
        out.append(text(CX + 14, y + 22, "VALUE", 9, C["t3"], 700, "start", 0.6))
        out.append(text(CX + 14, y + 40, "“Maria Bianchi · +1 415…”", 11.5, C["txt"], 500))
        out.append(text(CX + CW - 14, y + 22, "plaintext", 9.5, C["amber"], 600, "end"))
        y += 68
        out.append(f'<circle cx="{W/2}" cy="{y+4}" r="15" fill="{A(C["brandA"], 0.16)}" stroke="{C["brandA"]}" stroke-width="1.4"/>')
        out.append(icon("lock", W / 2, y + 4, C["brandA"], 0.9))
        out.append(text(W / 2, y + 32, "AES-256-GCM", 9.5, C["brandA"], 700, "middle", 0.4))
        y += 46
        out.append(rrect(CX, y, CW, 58, 15, "url(#gCard)", C["line"], 1))
        out.append(text(CX + 14, y + 22, "AT REST", 9, C["t3"], 700, "start", 0.6))
        out.append(text(CX + 14, y + 40, "9f2a c4e1 … e71b", 11, C["cyan"], 500, "start", 0.5, True))
        out.append(text(CX + CW - 14, y + 22, "sealed", 9.5, C["green"], 600, "end"))
        y += 70
        for ic, col, k, ss in [("finger", "brand", "AAD-bound", "to this tenant + key"),
                               ("eye", "green", "Only ciphertext on disk", "plaintext never persisted")]:
            s2, y = card_block(y, {"icon": ic, "color": col, "k": k, "s": ss, "h": 48})
            out.append(s2)
        out.append(button(CX, y, CW, "Seal record", "brand", 42))

    elif hero == "encryption":
        bw = (CW - 40) / 2
        out.append(rrect(CX, y, bw, 46, 12, A(C["amber"], 0.10), C["amber"], 1.2))
        out.append(text(CX + bw / 2, y + 22, "Plaintext", 11, C["amber"], 700, "middle"))
        out.append(text(CX + bw / 2, y + 36, "in memory", 8.5, C["t2"], 500, "middle"))
        out.append(f'<circle cx="{CX+bw+20}" cy="{y+23}" r="12" fill="{A(C["brandA"], 0.16)}" stroke="{C["brandA"]}" stroke-width="1.3"/>')
        out.append(icon("lock", CX + bw + 20, y + 23, C["brandA"], 0.66))
        out.append(rrect(CX + CW - bw, y, bw, 46, 12, A(C["cyan"], 0.10), C["cyan"], 1.2))
        out.append(text(CX + CW - bw / 2, y + 22, "Ciphertext", 11, C["cyan"], 700, "middle"))
        out.append(text(CX + CW - bw / 2, y + 36, "on disk", 8.5, C["t2"], 500, "middle"))
        y += 62
        for ic, col, k, ss in [("lock", "brand", "AES-256-GCM", "authenticated encryption"),
                               ("finger", "cyan", "AAD binds tenant + key", "ciphertext can't be relocated"),
                               ("shieldok", "green", "Master key in KMS / HSM", "your hardware, your walls"),
                               ("eye", "amber", "Only ciphertext on disk", "the database holds nothing readable")]:
            s2, y = card_block(y, {"icon": ic, "color": col, "k": k, "s": ss, "h": 50})
            out.append(s2)

    elif hero == "chain":
        entries = [("STORE", "green", "records/med/contact", "#1842"),
                   ("READ", "cyan", "records/med/contact", "#1843"),
                   ("STORE", "green", "contributions/qrme", "#1844"),
                   ("ERASE", "red", "records/med/old", "#1845")]
        lx = CX + 16
        out.append(f'<line x1="{lx}" y1="{y+8}" x2="{lx}" y2="{y+8+len(entries)*64-42}" stroke="{C["line"]}" stroke-width="2"/>')
        for op, col, key, blk in entries:
            c = ACCENT[col]
            out.append(f'<circle cx="{lx}" cy="{y+12}" r="9" fill="{C["scrB"]}" stroke="{c}" stroke-width="2"/>')
            out.append(f'<circle cx="{lx}" cy="{y+12}" r="3" fill="{c}"/>')
            out.append(rrect(lx + 22, y - 6, CW - 38, 46, 12, "url(#gCard)", C["line"], 1))
            out.append(text(lx + 36, y + 11, op, 10.5, c, 800, "start", 0.6))
            out.append(pill(lx + 22 + (CW - 38) - 8, y + 11, blk, "info"))
            out.append(text(lx + 36, y + 26, key, 9.5, C["t2"], 500, "start", 0, True))
            out.append(text(lx + 36, y + 37, "sha256 3f9a… ↳ links prev", 8.5, C["t3"], 500, "start", 0, True))
            y += 64

    elif hero == "verify":
        cx0, cy0, r = W / 2, y + 52, 46
        out.append(ring(cx0, cy0, r, 1.0, C["green"], 9))
        out.append(icon("shieldok", cx0, cy0 - 4, C["green"], 1.5))
        out.append(text(cx0, cy0 + 22, "INTACT", 11, C["green"], 800, "middle", 1))
        y = cy0 + r + 26
        for ic, col, k, ss, pt in [("list", "cyan", "1,845 entries", "every access, in order", ("100%", "good")),
                                   ("shieldok", "green", "No retroactive edit", "the hash-chain is unbroken", None),
                                   ("clock", "brand", "Last verified", "just now · GET /audit/verify", None)]:
            c = {"icon": ic, "color": col, "k": k, "s": ss, "h": 48}
            if pt:
                c["pill"] = pt
            s2, y = card_block(y, c)
            out.append(s2)

    elif hero == "token":
        out.append(rrect(CX, y, CW, 60, 15, A(C["amber"], 0.09), C["amber"], 1))
        out.append(icon("warn", CX + 24, y + 22, C["amber"], 0.85))
        out.append(text(CX + 44, y + 20, "Shown once — copy it now", 11.5, C["txt"], 650))
        out.append(text(CX + 44, y + 36, "only its SHA-256 hash is stored", 9.5, C["t2"]))
        y += 70
        out.append(rrect(CX, y, CW, 42, 12, "#0d0a24", C["line"], 1))
        out.append(text(CX + 14, y + 26, "pdi_live_k7Q2••••••••3f9a", 12, C["cyan"], 600, "start", 0.4, True))
        out.append(icon("doc", CX + CW - 20, y + 21, C["t2"], 0.7))
        y += 54
        seg = ["read", "write"]
        out.append(rrect(CX, y, CW, 36, 11, "#0d0a24", C["line"], 1))
        sw = (CW - 8) / 2
        for i, lbl in enumerate(seg):
            on = (i == 1)
            if on:
                out.append(rrect(CX + 4 + i * sw, y + 4, sw, 28, 8, "url(#gBrand)"))
            out.append(text(CX + 4 + i * sw + sw / 2, y + 23, lbl, 11.5, "#fff" if on else C["t2"], 700, "middle"))
        y += 48
        for ic, col, k, ss in [("shieldok", "green", "Scoped access", "read tokens can't write or delete"),
                               ("warn", "red", "Revoke instantly", "DELETE /tokens/{token}")]:
            s2, y = card_block(y, {"icon": ic, "color": col, "k": k, "s": ss, "h": 48})
            out.append(s2)

    elif hero == "snapshot":
        bw = (CW - 12) / 2
        out.append(rrect(CX, y, bw, 76, 16, A(C["brandA"], 0.10), C["brandA"], 1.4))
        out.append(icon("db", CX + bw / 2, y + 28, C["brandA"], 1.2))
        out.append(text(CX + bw / 2, y + 54, "Snapshot", 12, C["brandA"], 700, "middle"))
        out.append(text(CX + bw / 2, y + 68, "export", 9, C["t2"], 500, "middle"))
        out.append(rrect(CX + bw + 12, y, bw, 76, 16, A(C["green"], 0.10), C["green"], 1.4))
        out.append(icon("shieldok", CX + bw + 12 + bw / 2, y + 28, C["green"], 1.2))
        out.append(text(CX + bw + 12 + bw / 2, y + 54, "Restore", 12, C["green"], 700, "middle"))
        out.append(text(CX + bw + 12 + bw / 2, y + 68, "reinsert", 9, C["t2"], 500, "middle"))
        y += 90
        for ic, col, k, ss in [("lock", "cyan", "Ciphertext only", "no plaintext ever leaves"),
                               ("finger", "brand", "AAD still binds", "tenant + key survive restore"),
                               ("clock", "amber", "Disaster recovery", "rebuild after a loss")]:
            s2, y = card_block(y, {"icon": ic, "color": col, "k": k, "s": ss, "h": 48})
            out.append(s2)

    elif hero == "deployment":
        opts = [("building", "brand", "On-premises", "in your own facility", True),
                ("shieldok", "cyan", "Colocation · Tier III+", "carrier-grade, your keys", False)]
        for ic, col, k, ss, on in opts:
            hgt = 58
            out.append(rrect(CX, y, CW, hgt, 15, A(ACCENT[col], 0.10) if on else "url(#gCard)",
                             ACCENT[col] if on else C["line"], 1.4 if on else 1))
            out.append(chip(CX + 12, y + 12, ic, ACCENT[col]))
            out.append(text(CX + 56, y + 26, k, 12.5, C["txt"], 700))
            out.append(text(CX + 56, y + 42, ss, 10, C["t2"]))
            if on:
                out.append(f'<circle cx="{CX+CW-22}" cy="{y+hgt/2}" r="9" fill="{A(ACCENT[col],0.2)}" stroke="{ACCENT[col]}" stroke-width="1.2"/>')
                out.append(f'<path d="M{CX+CW-27} {y+hgt/2} l{2.6} {3} {5} -{5.5}" fill="none" stroke="{ACCENT[col]}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>')
            y += hgt + 12
        for ic, col, k, ss in [("finger", "green", "Your hardware, your keys", "PDI_MASTER_KEY in your KMS/HSM"),
                               ("doc", "amber", "Deployment record", "models the proposal's tiers")]:
            s2, y = card_block(y, {"icon": ic, "color": col, "k": k, "s": ss, "h": 50})
            out.append(s2)

    elif hero == "design":
        out.append(text(CX, y, "Colors", 12, C["txt"], 700))
        y += 12
        cols = [("#38BDF8", "Vault Cyan"), ("#9FD8E8", "Soft Cyan"),
                ("#1A1333", "Deep Indigo"), ("#C7C9D9", "Soft Silver")]
        for i, (hexc, name) in enumerate(cols):
            gx = CX + (i % 2) * (CW / 2 + 6)
            gy = y + (i // 2) * 44
            out.append(rrect(gx, gy, CW / 2 - 6, 36, 10, "url(#gCard)", C["line"], 1))
            out.append(rrect(gx + 8, gy + 8, 20, 20, 6, hexc, C["line"], 1))
            out.append(text(gx + 36, gy + 17, name, 9.5, C["txt"], 600))
            out.append(text(gx + 36, gy + 29, hexc, 8.5, C["t2"], 500, "start", 0, True))
        y += 100
        out.append(text(CX, y, "Principles", 12, C["txt"], 700))
        y += 12
        for lbl, ic in [("Encrypted at rest · AES-256-GCM", "lock"),
                        ("Tamper-evident audit chain", "shieldok"),
                        ("Tenant-isolated · AAD-bound", "finger"),
                        ("On-prem or colocation", "building")]:
            out.append(rrect(CX, y, CW, 38, 10, "url(#gCard)", C["line"], 1))
            out.append(icon(ic, CX + 20, y + 19, C["brandA"], 0.62))
            out.append(text(CX + 38, y + 23, lbl, 11, C["txt"], 550))
            y += 46

    else:  # generic stacked cards

        for c in spec["cards"]:
            s, y = card_block(y, c)
            out.append(s)
        if spec.get("button"):
            out.append(button(CX, y, CW, spec["button"][0], spec["button"][1], 42))

    out += tabbar(spec.get("tabs", MAIN), spec.get("tab", 0))
    out += navbar()
    out += close()
    return "".join(out)


# --------------------------------------------------------------------------- #
# screen definitions — a screen for every capability
# --------------------------------------------------------------------------- #
SCREENS = [
    # ---- the vault ----
    dict(num=1, title="Overview", sub="Your encrypted vault, live", hero="overview", accent="brand", tab=0),
    dict(num=2, title="Vault", sub="Records, sealed at rest", accent="cyan", tab=1, cards=[
        dict(icon="lock", color="brand", k="records/med", s="tenant: jim-mini", pill=("SEALED", "good")),
        dict(icon="lock", color="cyan", k="profiles/src", s="tenant: qrme", pill=("SEALED", "good")),
        dict(icon="lock", color="amber", k="contribs/qrme", s="anonymized intake", pill=("SEALED", "good")),
        dict(icon="db", color="green", k="1,842 records", s="all ciphertext on disk"),
    ]),
    dict(num=3, title="Store a Record", sub="Sealed the moment it lands", hero="storerec", accent="brand", tab=1),
    dict(num=4, title="Encryption", sub="AES-256-GCM, AAD-bound", hero="encryption", accent="brand", tab=1),
    # ---- tenants & access ----
    dict(num=5, title="Tenants", sub="One per integrating system", accent="cyan", tabs=TENANTS, tab=0, cards=[
        dict(icon="people", color="brand", k="qrme", s="profile source material", stat=("ACTIVE", "on")),
        dict(icon="people", color="cyan", k="jim-mini", s="medical & context payloads", stat=("ACTIVE", "on")),
        dict(icon="finger", color="green", k="Strictly namespaced", s="no cross-tenant reads"),
        dict(icon="plus", color="amber", k="Create tenant", s="admin · returns a token once"),
    ]),
    dict(num=6, title="Create Tenant", sub="Token shown once", hero="token", accent="amber", tabs=TENANTS, tab=1),
    dict(num=7, title="Access Control", sub="Scoped read / write", accent="brand", tabs=TENANTS, tab=1, cards=[
        dict(icon="doc", color="green", k="Read token", s="cannot write or delete", pill=("READ", "good")),
        dict(icon="pen", color="amber", k="Write token", s="store, read, delete", pill=("WRITE", "warn")),
        dict(icon="finger", color="cyan", k="Hashed at rest", s="only the SHA-256 hash is stored"),
        dict(icon="warn", color="red", k="Revoke instantly", s="DELETE /tokens/{token}"),
    ]),
    # ---- audit ----
    dict(num=8, title="Audit Log", sub="Append-only, hash-chained", hero="chain", accent="cyan", tabs=AUDIT, tab=0),
    dict(num=9, title="Verify Chain", sub="Prove nothing was edited", hero="verify", accent="green", tabs=AUDIT, tab=1),
    dict(num=10, title="Contributions", sub="Anonymized intake, sealed", accent="brand", tabs=TENANTS, tab=2, cards=[
        dict(icon="cloud", color="brand", k="contribs/qrme", s="model-improvement data", pill=("SEALED", "good")),
        dict(icon="eye", color="cyan", k="Anonymized by the source", s="ids stripped before intake"),
        dict(icon="shieldok", color="green", k="Encrypted & audit-chained", s="same vault, same proof"),
        dict(icon="warn", color="red", k="Revocable by ref", s="deleted at the gateway on revoke"),
    ]),
    # ---- operations ----
    dict(num=11, title="Snapshot & Restore", sub="Disaster recovery", hero="snapshot", accent="brand", tabs=OPS, tab=1),
    dict(num=12, title="Deployment", sub="On-prem or colocation", hero="deployment", accent="brand", tabs=OPS, tab=0),
    dict(num=13, title="Key Management", sub="Your keys, your walls", accent="cyan", tabs=OPS, tab=0, cards=[
        dict(icon="lock", color="brand", k="PDI_MASTER_KEY", s="base64 · 32-byte AES-256", pill=("SET", "good")),
        dict(icon="building", color="cyan", k="KMS / HSM", s="inside your private facility"),
        dict(icon="warn", color="amber", k="Ephemeral if unset", s="dev only — never production"),
        dict(icon="finger", color="green", k="AAD per record", s="binds tenant + key"),
    ]),
    dict(num=14, title="Tenant Isolation", sub="Walls between systems", accent="green", tabs=TENANTS, tab=0, cards=[
        dict(icon="finger", color="brand", k="AAD-bound ciphertext", s="can't be relocated across tenants"),
        dict(icon="eye", color="cyan", k="Namespaced keys", s="one tenant never reads another"),
        dict(icon="shieldok", color="green", k="Enforced on every op", s="store, read, list, delete"),
    ]),
    # ---- the promise ----
    dict(num=15, title="Data Promise", sub="Deletion is real", accent="green", tabs=OPS, tab=0, cards=[
        dict(icon="lock", color="brand", k="Only ciphertext on disk", s="nothing readable at rest", pill=("GCM", "good")),
        dict(icon="clock", color="amber", k="Soft recovery window", s="then a permanent wipe"),
        dict(icon="warn", color="red", k="No orphaned ciphertext", s="the owning app purges its keys"),
        dict(icon="shieldok", color="cyan", k="Audit proves it", s="erase lands in the chain"),
    ]),
    dict(num=16, title="Your Data", sub="The per-user audit view", accent="cyan", tab=2, cards=[
        dict(icon="lock", color="green", k="Stored", s="3 records sealed for you", pill=("GCM", "good")),
        dict(icon="eye", color="cyan", k="Read", s="last access 2m ago"),
        dict(icon="warn", color="red", k="Erased", s="1 record wiped · in the chain"),
        dict(icon="shieldok", color="brand", k="Chain verified", s="surfaced by QRME & JIM-mini"),
    ]),
    dict(num=17, title="System Health", sub="Liveness & integrity", accent="green", tabs=OPS, tab=2, cards=[
        dict(icon="bolt", color="green", k="GET /health", s="live", metric="200"),
        dict(icon="shieldok", color="cyan", k="Audit chain", s="verified continuously", pill=("OK", "good")),
        dict(icon="db", color="brand", k="Records", s="ciphertext only", metric="1,842"),
        dict(icon="people", color="amber", k="Tenants", s="qrme · jim-mini", metric="2"),
    ]),
    dict(num=18, title="Tandem", sub="Both AI systems, one vault", accent="brand", tab=0, cards=[
        dict(icon="people", color="cyan", k="QRME", s="seals profile source material", stat=("VAULTED", "on")),
        dict(icon="cross", color="green", k="JIM-mini", s="vaults medical & context", stat=("VAULTED", "on")),
        dict(icon="link", color="brand", k="Only over HTTP", s="they never import PDI internals"),
        dict(icon="shieldok", color="amber", k="Each its own tenant", s="its own token, its own walls"),
    ]),
    dict(num=19, title="Design System", sub="One world, vault cyan", hero="design", accent="brand", tab=3),
]


def main():
    global PLATFORM
    total = 0
    for plat, sub in (("ios", ""), ("android", "android")):
        PLATFORM = plat
        outdir = OUT if not sub else os.path.join(OUT, sub)
        os.makedirs(outdir, exist_ok=True)
        for s in SCREENS:
            n = s["num"]
            slug = s["title"].lower().replace(" & ", "-").replace(" ", "-").replace("é", "e")
            fn = f'{n:02d}-{slug}.svg'
            with open(os.path.join(outdir, fn), "w") as f:
                f.write(render(s))
            total += 1
    PLATFORM = "ios"
    print(f"generated {total} screens ({total // 2} × 2 platforms)")
    return []


if __name__ == "__main__":
    main()
