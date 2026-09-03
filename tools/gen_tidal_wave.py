#!/usr/bin/env python3
"""Generate the Tidal Wave hero art as a level screenshot, not an impression.

The level's vocabulary, taken from in-game reference:
  - large rotated square blocks with thick white glowing outlines
  - dense rows of small triangles packed along their inner edges
  - nested chevron arrows in the block centres
  - black spiked saw stars with a glowing core
  - jagged teeth along ceiling and floor
  - fine particulate everywhere

Usage: python3 tools/gen_tidal_wave.py
Writes: src/art/tidal-wave.svg
"""

import math
import pathlib
import random

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "art" / "tidal-wave.svg"

W, H = 1600, 900
rng = random.Random(24)


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def star(points=12, r_out=76, r_in=44, rot=-8):
    """A saw blade: alternating long and short spikes."""
    pts = []
    for i in range(points * 2):
        a = math.radians(rot + i * (360 / (points * 2)))
        r = r_out if i % 2 == 0 else r_in
        pts.append(f"{f(math.cos(a) * r)} {f(math.sin(a) * r)}")
    return "M" + " L".join(pts) + " Z"


def tri(cx, cy, w, h, rot=0):
    """A small triangle, point up, rotated about its own centre."""
    pts = [(0, -h * 0.5), (w * 0.5, h * 0.5), (-w * 0.5, h * 0.5)]
    a = math.radians(rot)
    out = []
    for x, y in pts:
        out.append(f"{f(cx + x * math.cos(a) - y * math.sin(a))} "
                   f"{f(cy + x * math.sin(a) + y * math.cos(a))}")
    return "M" + " L".join(out) + " Z"


def tri_row(x0, y0, x1, y1, n, size, flip=False):
    """A run of nested triangles along an edge — the level's densest motif."""
    out = []
    ang = math.degrees(math.atan2(y1 - y0, x1 - x0)) + (180 if flip else 0)
    for i in range(n):
        t = (i + 0.5) / n
        cx = x0 + (x1 - x0) * t
        cy = y0 + (y1 - y0) * t
        out.append(f'<path d="{tri(cx, cy, size, size * 1.15, ang + 90)}" '
                   f'fill="#5fd6ff" opacity="1"/>')
        out.append(f'<path d="{tri(cx, cy, size * 0.62, size * 0.72, ang + 90)}" '
                   f'fill="#ffffff" opacity="0.95"/>')
    return "".join(out)


def chevrons(cx, cy, n, w, gap, rot):
    """Nested arrow heads, as stacked inside the blocks."""
    out = []
    for i in range(n):
        s = w - i * gap
        if s <= 8:
            break
        op = 0.85 - i * 0.16
        out.append(
            f'<path d="M{f(-s)} {f(s * 0.55)} L0 {f(-s * 0.55)} L{f(s)} {f(s * 0.55)}" '
            f'fill="none" stroke="#bfeaff" stroke-width="{f(max(2.4, 7 - i))}" '
            f'opacity="{op:.2f}" stroke-linejoin="round"/>'
        )
    return (f'<g transform="translate({f(cx)} {f(cy)}) rotate({f(rot)})">'
            + "".join(out) + "</g>")


def block(cx, cy, size, rot, dim=1.0):
    """A rotated square block: thick white rim, packed interior."""
    h = size / 2
    inner = h - 26
    parts = [f'<g transform="translate({f(cx)} {f(cy)}) rotate({f(rot)})" '
             f'opacity="{dim:.2f}">']
    # body
    parts.append(f'<rect x="{f(-h)}" y="{f(-h)}" width="{f(size)}" '
                 f'height="{f(size)}" fill="url(#tw-blockfill)"/>')
    # triangle runs along all four inner edges
    n = max(3, int(size / 52))
    for (ax, ay, bx, by) in (
        (-inner, -inner, inner, -inner),
        (inner, -inner, inner, inner),
        (inner, inner, -inner, inner),
        (-inner, inner, -inner, -inner),
    ):
        parts.append(tri_row(ax, ay, bx, by, n, size * 0.098))
    # nested arrows in the middle
    parts.append(chevrons(0, size * 0.06, 4, size * 0.2, size * 0.045, 0))
    # small square studs
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(
                f'<rect x="{f(sx * inner * 0.52 - 7)}" y="{f(sy * inner * 0.52 - 7)}" '
                f'width="14" height="14" fill="#cdeeff" opacity="0.5" '
                f'transform="rotate(45 {f(sx * inner * 0.52)} {f(sy * inner * 0.52)})"/>'
            )
    # the rim, drawn last so nothing crosses it
    parts.append(f'<rect x="{f(-h)}" y="{f(-h)}" width="{f(size)}" '
                 f'height="{f(size)}" fill="none" stroke="#8fe6ff" '
                 f'stroke-width="16" filter="url(#tw-rim)" opacity="0.9"/>')
    parts.append(f'<rect x="{f(-h)}" y="{f(-h)}" width="{f(size)}" '
                 f'height="{f(size)}" fill="none" stroke="#ffffff" '
                 f'stroke-width="8"/>')
    parts.append(f'<rect x="{f(-h + 15)}" y="{f(-h + 15)}" width="{f(size - 30)}" '
                 f'height="{f(size - 30)}" fill="none" stroke="#9fe8ff" '
                 f'stroke-width="3" opacity="0.9"/>')
    parts.append("</g>")
    return "".join(parts)


def teeth(baseline, amp, period, down=True, fill="#03080f"):
    """Jagged spikes along an edge."""
    pts = [f"M-40 {f(baseline)}"]
    x = -40
    i = 0
    while x < W + 60:
        x2 = x + period / 2
        y = baseline + (amp if down else -amp) * (1 if i % 2 == 0 else 0.66)
        pts.append(f"L{f(x2)} {f(y)}")
        x2 += period / 2
        pts.append(f"L{f(x2)} {f(baseline)}")
        x = x2
        i += 1
    edge = -60 if down else H + 60
    pts.append(f"L{f(W + 60)} {f(edge)} L-40 {f(edge)} Z")
    return f'<path d="{" ".join(pts)}" fill="{fill}"/>'


def build():
    p = []
    a = p.append

    a(f'<svg class="art art--tidalwave" viewBox="0 0 {W} {H}" '
      'xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice" '
      'role="img" aria-label="A corridor of glowing blue blocks packed with '
      'triangle patterns, spiked saw blades and a player trail, in the style '
      'of the level itself">')

    # ---- defs ----
    a("<defs>")
    a('<linearGradient id="tw-bg" x1="0" y1="0" x2="0.2" y2="1">'
      '<stop offset="0%" stop-color="#061c34"/>'
      '<stop offset="52%" stop-color="#04121f"/>'
      '<stop offset="100%" stop-color="#020a12"/></linearGradient>')
    a('<linearGradient id="tw-blockfill" x1="0" y1="0" x2="0.4" y2="1">'
      '<stop offset="0%" stop-color="#2f9ff0" stop-opacity="0.88"/>'
      '<stop offset="52%" stop-color="#1560b8" stop-opacity="0.82"/>'
      '<stop offset="100%" stop-color="#0a2f66" stop-opacity="0.88"/></linearGradient>')
    a('<radialGradient id="tw-core" cx="50%" cy="50%" r="50%">'
      '<stop offset="0%" stop-color="#ffffff"/>'
      '<stop offset="40%" stop-color="#4fd8ff"/>'
      '<stop offset="100%" stop-color="#0b5f9e"/></radialGradient>')
    a('<radialGradient id="tw-amb" cx="50%" cy="50%" r="50%">'
      '<stop offset="0%" stop-color="#2ac9ff" stop-opacity="0.5"/>'
      '<stop offset="100%" stop-color="#2ac9ff" stop-opacity="0"/></radialGradient>')
    a('<linearGradient id="tw-foam" x1="0" y1="0" x2="0" y2="1">'
      '<stop offset="0%" stop-color="#eafdff"/>'
      '<stop offset="46%" stop-color="#7fe4ff"/>'
      '<stop offset="100%" stop-color="#1a86c8"/></linearGradient>')
    a('<linearGradient id="tw-vig" x1="0" y1="0" x2="0" y2="1">'
      '<stop offset="0%" stop-color="#020a12" stop-opacity="0.42"/>'
      '<stop offset="26%" stop-color="#020a12" stop-opacity="0.02"/>'
      '<stop offset="100%" stop-color="#020a12" stop-opacity="0.55"/></linearGradient>')
    # the white rim glow is the level's single most recognisable feature
    a('<filter id="tw-rim" x="-70%" y="-70%" width="240%" height="240%">'
      '<feGaussianBlur stdDeviation="10" result="b"/>'
      '<feFlood flood-color="#5fd6ff" result="c"/>'
      '<feComposite in="c" in2="b" operator="in" result="g"/>'
      '<feMerge><feMergeNode in="g"/><feMergeNode in="g"/>'
      '<feMergeNode in="SourceGraphic"/></feMerge></filter>')
    a('<filter id="tw-soft" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="14"/></filter>')
    a('<linearGradient id="tw-foamfade" x1="0" y1="0" x2="0" y2="1">'
      '<stop offset="0%" stop-color="#000"/>'
      '<stop offset="38%" stop-color="#888"/>'
      '<stop offset="78%" stop-color="#fff"/>'
      '<stop offset="100%" stop-color="#fff"/></linearGradient>')
    a(f'<mask id="tw-foammask"><rect x="0" y="812" width="{W}" '
      'height="88" fill="url(#tw-foamfade)"/></mask>')
    a('<filter id="tw-grain">'
      '<feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="4"/>'
      '<feColorMatrix type="saturate" values="0"/></filter>')
    a(f'<g id="tw-saw"><path d="{star()}" fill="#03080f"/>'
      f'<path d="{star(12, 62, 36, -8)}" fill="#0a2b4a"/>'
      '<circle r="30" fill="url(#tw-core)"/>'
      '<circle r="30" fill="#4fd8ff" opacity="0.4" filter="url(#tw-soft)"/>'
      '<circle r="13" fill="#ffffff"/></g>')
    a("</defs>")

    # ---- ground ----
    a(f'<rect width="{W}" height="{H}" fill="url(#tw-bg)"/>')
    a(f'<ellipse cx="820" cy="430" rx="900" ry="520" fill="url(#tw-amb)"/>')

    # vertical light shafts in the background
    for x, w_, op in ((250, 26, 0.16), (612, 16, 0.12), (1042, 30, 0.15),
                      (1360, 18, 0.1)):
        a(f'<rect x="{x}" y="0" width="{w_}" height="{H}" fill="#2ac9ff" '
          f'opacity="{op}" filter="url(#tw-soft)"/>')

    # ---- blocks: a zigzag corridor, as the level reads on screen ----
    a('<g>')
    for cx, cy, size, rot, dim in (
        (150, 250, 330, 45, 0.95),
        (560, 150, 300, 45, 1.0),
        (980, 235, 340, 45, 0.95),
        (1420, 165, 320, 45, 0.9),
        (330, 745, 300, 45, 0.9),
        (760, 800, 330, 45, 0.95),
        (1230, 730, 310, 45, 0.9),
        (1560, 560, 260, 45, 0.75),
    ):
        a(block(cx, cy, size, rot, dim))
    a('</g>')

    # ---- saw blades ----
    for x, y, s in ((392, 300, 1.0), (1120, 520, 0.86), (1490, 860, 1.1),
                    (250, 560, 0.66)):
        a(f'<use href="#tw-saw" transform="translate({x} {y}) scale({s})"/>')

    # ---- small stepped pixel decorations ----
    for bx, by, st in ((880, 470, 1), (1268, 388, -1), (520, 560, 1)):
        for i in range(4):
            a(f'<rect x="{bx + i * 19 * st}" y="{by - i * 19}" width="15" '
              f'height="15" fill="#eafcff" opacity="{0.85 - i * 0.14:.2f}"/>')

    # ---- ceiling and floor ----
    a(teeth(96, 46, 118, down=True))
    a(teeth(66, 30, 74, down=True, fill="#061c34"))
    a(teeth(818, 44, 126, down=False))

    # ---- particulate ----
    a('<g fill="#eafcff">')
    for _ in range(150):
        x = rng.uniform(0, W)
        y = rng.uniform(60, 850)
        r = rng.choice([1.0, 1.4, 1.8, 2.4])
        a(f'<circle cx="{f(x)}" cy="{f(y)}" r="{r}" '
          f'opacity="{rng.uniform(0.25, 0.9):.2f}"/>')
    a("</g>")
    a('<g fill="#7fe4ff">')
    for _ in range(46):
        x = rng.uniform(0, W)
        y = rng.uniform(80, 840)
        a(f'<rect x="{f(x)}" y="{f(y)}" width="5" height="5" '
          f'opacity="{rng.uniform(0.3, 0.8):.2f}"/>')
    a("</g>")

    a(f'<rect width="{W}" height="{H}" fill="url(#tw-vig)"/>')
    # Foam last: it is lit ground, not sky, so the vignette must not sit on
    # top of it. Masked so it dissolves upward instead of ending in a band,
    # and kept low enough that the corner metadata never lands on it.
    a('<g mask="url(#tw-foammask)">')
    a(f'<rect x="0" y="862" width="{W}" height="38" fill="url(#tw-foam)" '
      'opacity="0.92"/>')
    for i in range(0, W + 40, 38):
        r = 13 + (i // 38 % 4) * 5
        cy = 866 + ((i // 38 % 3) - 1) * 4
        a(f'<circle cx="{i}" cy="{cy}" r="{r}" fill="url(#tw-foam)" '
          'opacity="0.9"/>')
    for i in range(19, W + 40, 76):
        a(f'<circle cx="{i}" cy="856" r="7" fill="#ffffff" opacity="0.8"/>')
    a('</g>')

    a(f'<rect width="{W}" height="{H}" filter="url(#tw-grain)" opacity="0.1"/>')
    a("</svg>")
    return "\n".join(p) + "\n"


if __name__ == "__main__":
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}  {OUT.stat().st_size // 1024} KB")
