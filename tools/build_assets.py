#!/usr/bin/env python3
"""Generate the README's hero art — GENERATED, do not hand-edit the output.

    python3 tools/build_assets.py

These three were hand-built one-offs and aged the way hand-built one-offs do:
drawn before BYOK, compliance transfers and intakes, the executed-BAA gate,
custody beacons and the gate agent existed, and still showing an early vault
several releases later. The cover also used amber as its key colour, while
every screen in `docs/screens/` is night-indigo with vault cyan.

They are generated now, from the same palette constants the screens use, for
the same reason the screens are: a picture of the product that cannot be
regenerated is a picture that will be wrong soon, and nobody will notice.

Dependency-free — stdlib only.
"""

from __future__ import annotations

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets")

# Straight from docs/screens/build.py, so the art cannot drift from the screens.
C = {
    "scrA": "#181235", "scrB": "#0c0920",
    "card": "#201a48", "card2": "#181240", "line": "#302a60",
    "txt": "#f2effc", "t2": "#9a93c6", "t3": "#6a6399",
    "brandA": "#38bdf8", "brandB": "#7dd3fc",     # vault cyan
    "amber": "#ffb84d", "green": "#7bc47f", "cyan": "#9fd8e8", "red": "#e0687a",
}

W, H = 1280, 640


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, size=14, fill=None, weight=400, anchor="start", spacing=0):
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill or C["txt"]}"'
            f' font-weight="{weight}" text-anchor="{anchor}"{ls}>{esc(s)}</text>')


def rrect(x, y, w, h, r, fill, stroke=None, sw=1, dash=None):
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}"'
            f' fill="{fill}"{st}{da}/>')


def circle(cx, cy, r, fill="none", stroke=None, sw=1, dash=None):
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"{st}{da}/>'


def arrow(x1, y1, x2, y2, tint=None, sw=1.8, dash=None):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<path d="M{x1} {y1} L{x2} {y2}" stroke="{tint or C["t3"]}"'
            f' stroke-width="{sw}" fill="none" marker-end="url(#ah)"{da}/>')


def panel(x, y, w, h, title, lines, tint, badge=None):
    o = [rrect(x, y, w, h, 16, C["card"], C["line"], 1.2),
         rrect(x, y, 4, h, 2, tint),
         text(x + 20, y + 30, title, 15, C["txt"], 700)]
    for i, ln in enumerate(lines):
        o.append(text(x + 20, y + 54 + i * 20, ln, 12.5, C["t2"]))
    if badge:
        bw = 18 + len(badge) * 6.4
        o.append(rrect(x + w - bw - 14, y + 14, bw, 22, 11,
                       "rgba(255,255,255,0.05)", tint, 1))
        o.append(text(x + w - bw / 2 - 14, y + 29.5, badge, 10.5, tint, 700,
                      "middle"))
    return "".join(o)


def head(title, desc):
    return (
        f'<svg role="img" aria-labelledby="t d" xmlns="http://www.w3.org/2000/svg"'
        f' viewBox="0 0 {W} {H}" width="{W}" height="{H}"'
        f' font-family="Helvetica, Arial, sans-serif">'
        f'<title id="t">{esc(title)}</title><desc id="d">{esc(desc)}</desc>'
        f'<defs>'
        f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{C["scrA"]}"/>'
        f'<stop offset="1" stop-color="{C["scrB"]}"/></linearGradient>'
        f'<linearGradient id="brand" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{C["brandA"]}"/>'
        f'<stop offset="1" stop-color="{C["brandB"]}"/></linearGradient>'
        f'<radialGradient id="glow" cx="50%" cy="50%" r="50%">'
        f'<stop offset="0" stop-color="{C["brandA"]}" stop-opacity="0.34"/>'
        f'<stop offset="1" stop-color="{C["brandA"]}" stop-opacity="0"/>'
        f'</radialGradient>'
        f'<marker id="ah" viewBox="0 0 10 10" refX="9" refY="5"'
        f' markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M0 0 L10 5 L0 10 z" fill="{C["t3"]}"/></marker>'
        f'</defs>'
        f'<rect width="{W}" height="{H}" fill="url(#bg)"/>')


def wordmark(x, y, name, tagline, sub=None):
    o = [text(x, y, name, 50, C["txt"], 800, spacing=5),
         rrect(x + 3, y + 16, 92, 4, 2, "url(#brand)"),
         text(x, y + 46, tagline, 16, C["t2"])]
    if sub:
        o.append(text(x, y + 70, sub, 13, C["t3"]))
    return "".join(o)


def _chain(x, y, w, tint, n=4):
    """The hash chain, as a row of linked blocks. It is the product's proof."""
    o, step = [], w / n
    for i in range(n):
        bx = x + i * step
        o.append(rrect(bx, y, step - 26, 34, 8, C["card2"], tint, 1.1))
        o.append(text(bx + (step - 26) / 2, y + 22,
                      ("genesis" if i == 0 else f"{'3f9a b21c e07d'.split()[i-1]}…"),
                      11.5, C["t2"], 600, "middle"))
        if i < n - 1:
            o.append(arrow(bx + step - 24, y + 17, bx + step - 2, y + 17, tint,
                           1.4))
    return "".join(o)


def cover():
    """The vault, who can open it, and the proof that nothing was edited."""
    o = [head("PDI — Private Data Infrastructure",
              "PDI: encrypted at rest, isolated per tenant, audited by hash "
              "chain, with BYOK. Generated by tools/build_assets.py.")]
    o.append(wordmark(86, 96, "PDI",
                      "Encrypted at rest · isolated per tenant · hash-chained",
                      "…and a key the operator may not hold"))

    cx, cy = 880, 320
    o.append(f'<circle cx="{cx}" cy="{cy}" r="196" fill="url(#glow)"/>')
    o.append(circle(cx, cy, 132, "none", C["line"], 1.4))
    o.append(circle(cx, cy, 158, "none", C["line"], 1, "3 7"))
    o.append(text(cx, cy - 172, "A E S · 2 5 6 · G C M", 12, C["t3"], 600,
                  "middle", spacing=1))
    # The vault door.
    o.append(circle(cx, cy, 96, C["card2"], C["brandA"], 2))
    for a in (0, 90, 180, 270):
        import math
        r1, r2 = 26, 92
        rad = math.radians(a + 45)
        o.append(f'<path d="M{cx + r1 * math.cos(rad)} {cy + r1 * math.sin(rad)}'
                 f' L{cx + r2 * math.cos(rad)} {cy + r2 * math.sin(rad)}"'
                 f' stroke="{C["line"]}" stroke-width="7"/>')
    o.append(circle(cx, cy, 34, C["scrB"], C["brandB"], 2))
    o.append(rrect(cx - 9, cy - 4, 18, 16, 3, C["brandB"]))
    o.append(f'<path d="M{cx - 6} {cy - 4} v-6 a6 6 0 0 1 12 0 v6"'
             f' fill="none" stroke="{C["brandB"]}" stroke-width="2.4"/>')
    o.append(text(cx, cy + 178, "n o n c e · a a d · t a g", 11.5, C["t3"],
                  400, "middle"))

    # Who is inside, and who holds the key.
    o.append(panel(86, 230, 330, 96, "Per-tenant isolation",
                   ["AAD binds ciphertext to tenant + key,",
                    "so a record cannot be relocated."], C["brandA"]))
    o.append(panel(86, 344, 330, 96, "Customer-held keys",
                   ["Under BYOK the operator's own",
                    "database cannot open the records."], C["green"], "BYOK"))
    o.append(panel(86, 458, 330, 76, "Compliance carriage",
                   ["HIPAA · OSHA · CPNI, with the BAA",
                    "enforced in code before any PHI."], C["amber"]))

    o.append(_chain(470, 556, 720, C["brandB"]))
    o.append(text(470, 604, "append-only, hash-chained — any retroactive edit "
                  "breaks the link and GET /audit/verify says so", 12,
                  C["t3"]))
    o.append("</svg>")
    return "".join(o)


def architecture():
    """Tenants, the vault, and the two things that make it more than a database."""
    o = [head("PDI architecture — tenants, encrypted vault, tamper-evident audit",
              "How a record enters, who can read it, and what proves it was "
              "not edited. Generated by tools/build_assets.py.")]
    o.append(text(86, 76, "PDI architecture", 30, C["txt"], 800))
    o.append(text(86, 106, "Every record arrives through a tenant, leaves as "
                  "ciphertext, and lands on the chain.", 14, C["t2"]))

    # Four equal panels across the full width. The first draft squeezed the
    # last one to 130px and its title ran straight into its own badge.
    cols = [
        ("Integrating systems",
         ["qrme — profile source material", "jim-mini — medical & context",
          "robots — what a body recorded", "", "each its own tenant + token"],
         C["brandA"], None),
        ("The vault",
         ["AES-256-GCM at rest", "AAD-bound to tenant + key",
          "envelope keys, rotatable", "", "only ciphertext on disk"],
         C["green"], None),
        ("The audit chain",
         ["every put / get / delete", "SHA-256 over the previous hash",
          "verify() walks the whole chain", "", "append-only, kept forever"],
         C["amber"], None),
        ("Physical custody",
         ["beacons on carriers and gates", "a scan is a link in the chain",
          "the agent may never grant entry", "", "reveals a seal, not contents"],
         C["red"], "NEW"),
    ]
    pw, step = 257, 283
    for i, (title, lines, tint, badge) in enumerate(cols):
        x = 86 + i * step
        o.append(panel(x, 164, pw, 158, title, lines, tint, badge))
        if i < 3:
            o.append(arrow(x + pw + 4, 243, x + step - 4, 243))

    o.append(rrect(86, 372, 1108, 96, 16, C["card2"], C["line"], 1.2))
    o.append(rrect(86, 372, 4, 96, 2, C["brandB"]))
    o.append(text(108, 402, "The question that decides everything: who holds "
                 "the key", 15, C["txt"], 700))
    o.append(text(108, 428, "Under deployment custody the operator can decrypt. "
                  "Under BYOK they cannot — and the same rack, the same",
                  12.5, C["t2"]))
    o.append(text(108, 448, "colocation contract and the same audit chain look "
                  "identical from outside. It is not whose rack it is.",
                  12.5, C["t2"]))

    o.append(_chain(86, 508, 700, C["amber"]))
    o.append(text(86, 566, "A physical carrier gets a beacon: its scans and "
                  "hand-ins land on this same chain, so a gap in custody "
                  "becomes a finding.", 12.5, C["t3"]))
    o.append("</svg>")
    return "".join(o)


def encryption_flow():
    """Seal, store, audit — and what each step refuses to do."""
    o = [head("PDI encryption flow — seal, store, audit",
              "What happens to a value between the request and the disk. "
              "Generated by tools/build_assets.py.")]
    o.append(text(86, 76, "Seal · store · audit", 30, C["txt"], 800))
    o.append(text(86, 106, "What happens to a value between the request and "
                  "the disk — and what never happens.", 14, C["t2"]))

    steps = [
        ("1 · Resolve the key", ["Deployment key, or the customer's",
                                 "own — presented per request and",
                                 "never stored."], C["brandA"]),
        ("2 · Seal", ["AES-256-GCM, with AAD bound to",
                      "tenant + key so a blob cannot be",
                      "moved between either."], C["green"]),
        ("3 · Store", ["Only \"<version>:nonce||ciphertext\"",
                       "reaches disk. The plaintext is not",
                       "written anywhere."], C["brandB"]),
        ("4 · Record", ["The action lands on the chain —",
                        "the key and the value do not.",
                        "The chain proves, it does not hold."], C["amber"]),
    ]
    for i, (title, lines, tint) in enumerate(steps):
        x = 86 + i * 282
        o.append(panel(x, 164, 258, 158, title, lines, tint))
        if i < 3:
            o.append(arrow(x + 264, 243, x + 276, 243))

    o.append(rrect(86, 380, 1108, 108, 16, C["card2"], C["red"], 1.3))
    o.append(rrect(86, 380, 4, 108, 2, C["red"]))
    o.append(text(108, 412, "What a wrong key does — before it does damage",
                  15, C["txt"], 700))
    o.append(text(108, 438, "A presented key is checked against a stored check "
                  "value first, so a wrong one is refused rather than used.",
                  12.5, C["t2"]))
    o.append(text(108, 458, "Sealing under it would write records that nothing "
                  "could ever open again — a silent, permanent loss.",
                  12.5, C["t2"]))

    o.append(text(86, 542, "Rotation adds a key version and re-seals; "
                  "retirement removes the old one only once nothing is left "
                  "on it.", 12.5, C["t3"]))
    o.append(text(86, 566, "Adoption of a customer key is all-or-nothing: a "
                  "half-migrated tenant is the worst state to be in.",
                  12.5, C["t3"]))
    o.append("</svg>")
    return "".join(o)


ASSETS = {
    "cover.svg": cover,
    "architecture.svg": architecture,
    "encryption-flow.svg": encryption_flow,
}


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    for name, fn in ASSETS.items():
        with open(os.path.join(OUT, name), "w") as f:
            f.write(fn())
        print(f"wrote assets/{name}")


if __name__ == "__main__":
    main()
