#!/usr/bin/env python3
"""Antarctic Lights hero art.

Drawn from the level's own thumbnail rather than a generic polar scene: a
full-width aurora fringe of hanging rays in mint, cyan, violet and magenta
with a few warm amber strands, dark cloud streaks cutting across it, a hard
starfield behind, and a bright ice plain below — not the near-black ground
the first pass used.

Usage: python3 tools/gen_antarctic_lights.py
"""

import pathlib
import random
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "art" / "antarctic-lights.svg"

W, H = 1600, 900
HORIZON = 596

# Curtain colours, sampled off the thumbnail. Amber is deliberately rare —
# in the reference it reads as two or three strands, not a band.
RAY_COLOURS = (
    [("#7dffca", 15), ("#5cf0e0", 12), ("#4fd4ff", 12), ("#63b4ff", 9)]
    + [("#8f6cff", 9), ("#a95cff", 8), ("#c95cf0", 6)]
    + [("#ffc36b", 2), ("#ff9f5c", 1)]
)
WEIGHTED = [c for c, n in RAY_COLOURS for _ in range(n)]


def esc(v):
    return str(v)


def ray(rng, x, top, height, width, colour, opacity):
    """One hanging strand: wide and soft at the top, tapering to a point."""
    spread = width * rng.uniform(1.15, 1.7)
    drift = rng.uniform(-38, 38)
    tip_x = x + drift
    return (
        f'<path d="M{x - spread / 2:.1f} {top:.1f} '
        f"L{x + spread / 2:.1f} {top:.1f} "
        f"L{tip_x + width * 0.16:.1f} {top + height:.1f} "
        f'L{tip_x - width * 0.16:.1f} {top + height:.1f} Z" '
        f'fill="{colour}" opacity="{opacity:.2f}"/>'
    )


def build():
    rng = random.Random(1407)  # verified 14 July
    p = []
    a = p.append

    a(f'<svg class="art art--antarctic" viewBox="0 0 {W} {H}" '
      'xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice" '
      'role="img" aria-label="Aurora curtains in mint, violet and magenta '
      'hanging over a bright ice plain under a dense starfield">')

    # ---------------------------------------------------------------- defs
    a("<defs>")
    a('<linearGradient id="al-sky" x1="0" y1="0" x2="0.15" y2="1">'
      '<stop offset="0%" stop-color="#0b0733"/>'
      '<stop offset="30%" stop-color="#101c4d"/>'
      '<stop offset="62%" stop-color="#0d3a5e"/>'
      '<stop offset="100%" stop-color="#0a2c46"/>'
      "</linearGradient>")
    a('<linearGradient id="al-fringe" x1="0" y1="0" x2="0" y2="1">'
      '<stop offset="0%" stop-color="#7dffca" stop-opacity="0.55"/>'
      '<stop offset="55%" stop-color="#5cc8ff" stop-opacity="0.28"/>'
      '<stop offset="100%" stop-color="#8f6cff" stop-opacity="0"/>'
      "</linearGradient>")
    a('<linearGradient id="al-ice" x1="0.25" y1="0" x2="0.6" y2="1">'
      '<stop offset="0%" stop-color="#e8fbff"/>'
      '<stop offset="22%" stop-color="#bfe8f5"/>'
      '<stop offset="55%" stop-color="#7ab8d6"/>'
      '<stop offset="100%" stop-color="#2b6285"/>'
      "</linearGradient>")
    a('<linearGradient id="al-glow" x1="0" y1="0" x2="0" y2="1">'
      '<stop offset="0%" stop-color="#7dffca" stop-opacity="0.34"/>'
      '<stop offset="100%" stop-color="#7dffca" stop-opacity="0"/>'
      "</linearGradient>")
    a('<linearGradient id="al-vig" x1="0" y1="0" x2="0" y2="1">'
      '<stop offset="0%" stop-color="#050a20" stop-opacity="0.42"/>'
      '<stop offset="34%" stop-color="#050a20" stop-opacity="0"/>'
      '<stop offset="100%" stop-color="#030b16" stop-opacity="0.72"/>'
      "</linearGradient>")
    a('<filter id="al-wide"><feGaussianBlur stdDeviation="42"/></filter>')
    a('<filter id="al-soft"><feGaussianBlur stdDeviation="13"/></filter>')
    a('<filter id="al-fine"><feGaussianBlur stdDeviation="5"/></filter>')
    a('<filter id="al-cloud"><feGaussianBlur stdDeviation="22"/></filter>')
    a("</defs>")

    a(f'<rect width="{W}" height="{H}" fill="url(#al-sky)"/>')

    # ------------------------------------------------------------ starfield
    a('<g fill="#eafaff">')
    for _ in range(230):
        x = rng.uniform(0, W)
        y = rng.uniform(0, HORIZON - 30)
        # Thin the stars out where the curtains are brightest.
        r = rng.uniform(0.5, 1.5)
        op = rng.uniform(0.25, 0.95) * (0.45 + 0.55 * (y / HORIZON))
        a(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" '
          f'opacity="{op:.2f}"/>')
    a("</g>")
    for _ in range(9):  # a handful of brighter ones with a cross flare
        x, y = rng.uniform(40, W - 40), rng.uniform(20, 300)
        a(f'<g opacity="{rng.uniform(0.55, 0.9):.2f}" filter="url(#al-fine)">'
          f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.4" fill="#ffffff"/></g>')

    # ------------------------------------------------------- the wide glow
    a(f'<rect x="-60" y="-120" width="{W + 120}" height="560" '
      'fill="url(#al-fringe)" filter="url(#al-wide)" opacity="0.85"/>')

    # ---------------------------------------------------------- the fringe
    # Three passes: a soft back layer, the main strands, then a few crisp
    # ones in front so the curtain has depth rather than reading as one blur.
    a('<g filter="url(#al-soft)" opacity="0.62">')
    for _ in range(46):
        x = rng.uniform(-40, W + 40)
        a(ray(rng, x, rng.uniform(-90, -10), rng.uniform(300, 620),
              rng.uniform(26, 74), rng.choice(WEIGHTED),
              rng.uniform(0.22, 0.5)))
    a("</g>")

    a('<g filter="url(#al-fine)" opacity="0.86">')
    for _ in range(64):
        x = rng.uniform(-30, W + 30)
        a(ray(rng, x, rng.uniform(-70, 20), rng.uniform(220, 540),
              rng.uniform(9, 34), rng.choice(WEIGHTED),
              rng.uniform(0.3, 0.72)))
    a("</g>")

    a('<g opacity="0.7">')
    for _ in range(22):
        x = rng.uniform(0, W)
        a(ray(rng, x, rng.uniform(-50, 10), rng.uniform(180, 420),
              rng.uniform(3, 11), rng.choice(WEIGHTED),
              rng.uniform(0.35, 0.8)))
    a("</g>")

    # ------------------------------------------------------- cloud streaks
    # Dark wisps cutting across the curtains, as in the reference.
    a('<g filter="url(#al-cloud)" fill="#0a1226">')
    for _ in range(11):
        cx, cy = rng.uniform(0, W), rng.uniform(90, 470)
        rx, ry = rng.uniform(90, 300), rng.uniform(7, 20)
        rot = rng.uniform(-13, 13)
        a(f'<ellipse cx="{cx:.0f}" cy="{cy:.0f}" rx="{rx:.0f}" ry="{ry:.0f}" '
          f'opacity="{rng.uniform(0.3, 0.62):.2f}" '
          f'transform="rotate({rot:.1f} {cx:.0f} {cy:.0f})"/>')
    a("</g>")

    # ----------------------------------------------------- horizon + light
    a(f'<rect x="0" y="{HORIZON - 190}" width="{W}" height="190" '
      'fill="url(#al-glow)" opacity="0.75"/>')

    # far ridge, and the little station from the thumbnail
    ridge = [f"{-20},{HORIZON + 6}"]
    x = -20
    while x < W + 20:
        x += rng.uniform(34, 96)
        ridge.append(f"{x:.0f},{HORIZON - rng.uniform(2, 20):.0f}")
    ridge.append(f"{W + 20},{HORIZON + 30}")
    ridge.append(f"{W + 20},{HORIZON + 40}")
    ridge.append(f"-20,{HORIZON + 40}")
    a(f'<polygon points="{" ".join(ridge)}" fill="#16405e" opacity="0.75"/>')

    a(f'<g fill="#16405e" opacity="0.8">'
      f'<rect x="1082" y="{HORIZON - 22}" width="7" height="22"/>'
      f'<rect x="1120" y="{HORIZON - 15}" width="26" height="15"/>'
      f'<rect x="1168" y="{HORIZON - 19}" width="18" height="19"/>'
      f'<circle cx="1086" cy="{HORIZON - 26}" r="9"/></g>')

    # ------------------------------------------------------------- the ice
    a(f'<rect x="0" y="{HORIZON}" width="{W}" height="{H - HORIZON}" '
      'fill="url(#al-ice)"/>')

    # Slabs: flat-topped shards, lighter on top, catching the sky.
    a("<g>")
    for _ in range(120):
        y = rng.uniform(HORIZON + 6, H - 10)
        depth = (y - HORIZON) / (H - HORIZON)
        w = rng.uniform(28, 150) * (0.5 + depth)
        h = rng.uniform(5, 20) * (0.5 + depth)
        x = rng.uniform(-40, W)
        skew = rng.uniform(-16, 16)
        light = 0.55 - 0.4 * depth
        a(f'<path d="M{x:.0f} {y:.0f} L{x + w:.0f} {y - h * 0.35:.0f} '
          f"L{x + w + skew:.0f} {y + h:.0f} L{x + skew * 0.4:.0f} "
          f'{y + h * 1.25:.0f} Z" fill="#eafaff" '
          f'opacity="{max(light, 0.05):.2f}"/>')
        a(f'<path d="M{x:.0f} {y:.0f} L{x + w:.0f} {y - h * 0.35:.0f}" '
          f'stroke="#ffffff" stroke-width="1.4" fill="none" '
          f'opacity="{max(0.7 - depth * 0.55, 0.06):.2f}"/>')
    a("</g>")

    # Crevices running toward the viewer.
    a('<g stroke="#1d5578" fill="none">')
    for _ in range(26):
        x0 = rng.uniform(0, W)
        y0 = rng.uniform(HORIZON + 20, H)
        a(f'<path d="M{x0:.0f} {y0:.0f} q {rng.uniform(-70, 70):.0f} '
          f"{rng.uniform(30, 90):.0f} {rng.uniform(-130, 130):.0f} "
          f'{rng.uniform(70, 170):.0f}" stroke-width="{rng.uniform(1, 3):.1f}" '
          f'opacity="{rng.uniform(0.12, 0.34):.2f}"/>')
    a("</g>")

    # Snow sparkle on the plain.
    a('<g fill="#ffffff">')
    for _ in range(180):
        x = rng.uniform(0, W)
        y = rng.uniform(HORIZON + 8, H)
        a(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rng.uniform(0.5, 1.7):.2f}" '
          f'opacity="{rng.uniform(0.2, 0.8):.2f}"/>')
    a("</g>")

    a(f'<rect width="{W}" height="{H}" fill="url(#al-vig)"/>')
    a("</svg>")
    return "\n".join(p)


def main():
    svg = build()
    ET.fromstring(svg)  # well-formedness gate; a broken glyph fails here
    OUT.write_text(svg + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}  ({len(svg):,} bytes)")


if __name__ == "__main__":
    main()
