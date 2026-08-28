#!/usr/bin/env python3
"""Generate the Kyouki hero art from in-game reference.

The level's vocabulary:
  - slabs carved with orthogonal maze/circuit line work
  - nested diamonds with gradient rims running pink -> violet -> cyan
  - segmented discs, like a wheel cut into wedges
  - stacked downward chevrons
  - small square particles: black ones tumbling, green and yellow in clusters
  - organic dark silhouettes crowding the edges
  - deep blue ground, neon green, blue and violet on top of it

Usage: python3 tools/gen_kyouki.py
Writes: src/art/kyouki.svg
"""

import math
import pathlib
import random

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "art" / "kyouki.svg"

W, H = 1600, 900
rng = random.Random(112313819)          # the level id, for a stable scatter


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


# ------------------------------------------------------------------ maze

def maze(w, h, cell, seed, runs=5):
    """Orthogonal circuit line work — the level's most distinctive fill.

    A constrained random walk on a grid: always axis-aligned, never
    backtracking, so it reads as etched channels rather than scribble.
    """
    r = random.Random(seed)
    cols, rows = max(2, int(w // cell)), max(2, int(h // cell))
    out = []
    for _ in range(runs):
        cx, cy = r.randrange(cols), r.randrange(rows)
        d = f"M{f(cx * cell)} {f(cy * cell)}"
        last = None
        for _ in range(r.randint(5, 10)):
            opts = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            if last:
                opts.remove((-last[0], -last[1]))
            dx, dy = r.choice(opts)
            n = r.randint(1, 3)
            nx = min(max(cx + dx * n, 0), cols)
            ny = min(max(cy + dy * n, 0), rows)
            if (nx, ny) == (cx, cy):
                continue
            cx, cy = nx, ny
            last = (dx, dy)
            d += f" L{f(cx * cell)} {f(cy * cell)}"
        out.append(d)
    return out


def slab(cx, cy, w, h, rot, seed, hue="a", dim=1.0):
    """A rectangular block, rimmed in neon and carved with circuit lines."""
    p = [f'<g transform="translate({f(cx)} {f(cy)}) rotate({f(rot)})" '
         f'opacity="{dim:.2f}">']
    p.append(f'<rect x="{f(-w/2)}" y="{f(-h/2)}" width="{f(w)}" height="{f(h)}" '
             'fill="url(#ky-slab)"/>')
    p.append(f'<g transform="translate({f(-w/2 + 14)} {f(-h/2 + 14)})" '
             f'clip-path="url(#ky-clip-{"a" if w > 200 else "b"})">')
    for d in maze(w - 28, h - 28, 22, seed):
        p.append(f'<path d="{d}" fill="none" stroke="#bfe4ff" stroke-width="3" '
                 'opacity="0.5" stroke-linecap="square"/>')
        p.append(f'<path d="{d}" fill="none" stroke="#eaf6ff" stroke-width="1.2" '
                 'opacity="0.8" stroke-linecap="square"/>')
    p.append("</g>")
    # neon rim, gradient down its length
    p.append(f'<rect x="{f(-w/2)}" y="{f(-h/2)}" width="{f(w)}" height="{f(h)}" '
             f'fill="none" stroke="url(#ky-rim-{hue})" stroke-width="7" '
             'filter="url(#ky-glow)"/>')
    p.append(f'<rect x="{f(-w/2)}" y="{f(-h/2)}" width="{f(w)}" height="{f(h)}" '
             f'fill="none" stroke="#f2f8ff" stroke-width="2.2" opacity="0.85"/>')
    p.append("</g>")
    return "".join(p)


def diamond(cx, cy, size, seed, hue="b", dim=1.0):
    """Nested diamonds with a gradient rim."""
    p = [f'<g transform="translate({f(cx)} {f(cy)}) rotate(45)" '
         f'opacity="{dim:.2f}">']
    for i, (s, sw, op) in enumerate(((size, 6, 1.0), (size * 0.72, 4, 0.8),
                                     (size * 0.46, 3, 0.6),
                                     (size * 0.24, 2.4, 0.45))):
        col = f"url(#ky-rim-{hue})" if i == 0 else ("#8fd8ff" if i % 2 else "#c58fff")
        fil = ' filter="url(#ky-glow)"' if i == 0 else ""
        p.append(f'<rect x="{f(-s/2)}" y="{f(-s/2)}" width="{f(s)}" '
                 f'height="{f(s)}" fill="none" stroke="{col}" '
                 f'stroke-width="{sw}" opacity="{op}"{fil}/>')
    p.append(f'<rect x="{f(-size*0.12)}" y="{f(-size*0.12)}" '
             f'width="{f(size*0.24)}" height="{f(size*0.24)}" fill="#eaf6ff" '
             'opacity="0.55"/>')
    p.append("</g>")
    return "".join(p)


def disc(cx, cy, r, seed, wedges=8, dim=1.0):
    """A wheel cut into wedges, half of them lit."""
    p = [f'<g transform="translate({f(cx)} {f(cy)})" opacity="{dim:.2f}">']
    p.append(f'<circle r="{f(r)}" fill="#0a1440" opacity="0.85"/>')
    rr = random.Random(seed)
    for i in range(wedges):
        a0 = i * math.tau / wedges
        a1 = (i + 1) * math.tau / wedges
        if rr.random() < 0.45:
            continue
        x0, y0 = math.cos(a0) * r, math.sin(a0) * r
        x1, y1 = math.cos(a1) * r, math.sin(a1) * r
        col = "#4fe0ff" if i % 2 else "#a45cff"
        p.append(f'<path d="M0 0 L{f(x0)} {f(y0)} A{f(r)} {f(r)} 0 0 1 '
                 f'{f(x1)} {f(y1)} Z" fill="{col}" opacity="0.62"/>')
    p.append(f'<circle r="{f(r)}" fill="none" stroke="#eaf6ff" stroke-width="4" '
             'filter="url(#ky-glow)"/>')
    p.append(f'<circle r="{f(r * 0.3)}" fill="none" stroke="#eaf6ff" '
             'stroke-width="2.4" opacity="0.7"/>')
    p.append("</g>")
    return "".join(p)


def chevrons(cx, cy, n, w, gap, col, dim=1.0):
    p = [f'<g transform="translate({f(cx)} {f(cy)})" opacity="{dim:.2f}">']
    for i in range(n):
        y = i * gap
        p.append(f'<path d="M{f(-w)} {f(y)} L0 {f(y + w * 0.62)} L{f(w)} {f(y)}" '
                 f'fill="none" stroke="{col}" stroke-width="{f(max(2.4, 7 - i))}" '
                 f'opacity="{0.9 - i * 0.16:.2f}" stroke-linejoin="round"/>')
    p.append("</g>")
    return "".join(p)


def canopy(y0, amp, seed, fill, spikes=64):
    """Dark organic growth crowding the frame, as the level's backdrop does."""
    r = random.Random(seed)
    d = [f"M-60 {H + 60}", f"L-60 {f(y0)}"]
    x = -60
    while x < W + 60:
        w = r.uniform(18, 46)
        h = r.uniform(0.4, 1.5) * amp
        d.append(f"L{f(x + w / 2)} {f(y0 - h)}")
        d.append(f"L{f(x + w)} {f(y0 + r.uniform(-8, 12))}")
        x += w
    d.append(f"L{f(W + 60)} {H + 60} Z")
    return f'<path d="{" ".join(d)}" fill="{fill}"/>'


def build():
    p = []
    a = p.append

    a(f'<svg class="art art--kyouki" viewBox="0 0 {W} {H}" '
      'xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice" '
      'role="img" aria-label="Neon blue, green and violet slabs carved with '
      'circuit patterns, nested diamonds and segmented discs over a deep blue '
      'field">')

    a("<defs>")
    a('<linearGradient id="ky-bg" x1="0" y1="0" x2="0.3" y2="1">'
      '<stop offset="0%" stop-color="#122a8c"/>'
      '<stop offset="46%" stop-color="#0b1652"/>'
      '<stop offset="100%" stop-color="#050a2c"/></linearGradient>')
    a('<linearGradient id="ky-slab" x1="0" y1="0" x2="0.4" y2="1">'
      '<stop offset="0%" stop-color="#3f6ff0" stop-opacity="0.82"/>'
      '<stop offset="55%" stop-color="#1d3aa8" stop-opacity="0.78"/>'
      '<stop offset="100%" stop-color="#0a1450" stop-opacity="0.78"/></linearGradient>')
    # the rims run through the level's three colours
    a('<linearGradient id="ky-rim-a" x1="0" y1="0" x2="1" y2="1">'
      '<stop offset="0%" stop-color="#ff5ce0"/>'
      '<stop offset="42%" stop-color="#a45cff"/>'
      '<stop offset="78%" stop-color="#4fe0ff"/>'
      '<stop offset="100%" stop-color="#5cff9d"/></linearGradient>')
    a('<linearGradient id="ky-rim-b" x1="0" y1="1" x2="1" y2="0">'
      '<stop offset="0%" stop-color="#5cff9d"/>'
      '<stop offset="40%" stop-color="#4fe0ff"/>'
      '<stop offset="76%" stop-color="#a45cff"/>'
      '<stop offset="100%" stop-color="#ff5ce0"/></linearGradient>')
    a('<radialGradient id="ky-amb" cx="50%" cy="50%" r="50%">'
      '<stop offset="0%" stop-color="#4a7bff" stop-opacity="0.6"/>'
      '<stop offset="55%" stop-color="#8a4cff" stop-opacity="0.3"/>'
      '<stop offset="100%" stop-color="#7a3cff" stop-opacity="0"/></radialGradient>')
    a('<linearGradient id="ky-vig" x1="0" y1="0" x2="0" y2="1">'
      '<stop offset="0%" stop-color="#04081f" stop-opacity="0.42"/>'
      '<stop offset="26%" stop-color="#04081f" stop-opacity="0.02"/>'
      '<stop offset="100%" stop-color="#04081f" stop-opacity="0.5"/></linearGradient>')
    a('<filter id="ky-glow" x="-70%" y="-70%" width="240%" height="240%">'
      '<feGaussianBlur stdDeviation="9" result="b"/>'
      '<feFlood flood-color="#7ad4ff" result="c"/>'
      '<feComposite in="c" in2="b" operator="in" result="g"/>'
      '<feMerge><feMergeNode in="g"/><feMergeNode in="g"/>'
      '<feMergeNode in="SourceGraphic"/></feMerge></filter>')
    a('<filter id="ky-soft"><feGaussianBlur stdDeviation="16"/></filter>')
    a('<filter id="ky-grain">'
      '<feTurbulence type="fractalNoise" baseFrequency="0.84" numOctaves="4"/>'
      '<feColorMatrix type="saturate" values="0"/></filter>')
    a('<clipPath id="ky-clip-a"><rect width="600" height="400"/></clipPath>')
    a('<clipPath id="ky-clip-b"><rect width="300" height="300"/></clipPath>')
    a("</defs>")

    a(f'<rect width="{W}" height="{H}" fill="url(#ky-bg)"/>')
    a(f'<ellipse cx="800" cy="420" rx="900" ry="520" fill="url(#ky-amb)"/>')

    # soft blooms behind everything
    a('<g filter="url(#ky-soft)">')
    for bx, by, r_, col, op in ((300, 300, 210, "#3a6bff", 0.45),
                                (1250, 380, 240, "#a45cff", 0.4),
                                (760, 700, 270, "#2ad4ff", 0.32),
                                (1450, 750, 190, "#5cff9d", 0.24)):
        a(f'<circle cx="{bx}" cy="{by}" r="{r_}" fill="{col}" opacity="{op}"/>')
    a("</g>")

    # organic growth top and bottom
    a(canopy(150, 120, 5, "#050a26"))
    a(f'<g transform="translate(0 {H}) scale(1 -1)">{canopy(210, 150, 9, "#04081f")}</g>')

    # slabs
    for cx, cy, w_, h_, rot, seed, hue, dim in (
        (250, 300, 300, 190, -8, 11, "a", 0.95),
        (700, 190, 340, 150, 4, 22, "b", 1.0),
        (1230, 250, 280, 200, -6, 33, "a", 0.95),
        (1470, 520, 240, 170, 7, 44, "b", 0.85),
        (420, 700, 320, 180, 5, 55, "b", 0.9),
        (980, 760, 300, 165, -5, 66, "a", 0.9),
    ):
        a(slab(cx, cy, w_, h_, rot, seed, hue, dim))

    # diamonds
    for cx, cy, s, seed, hue, dim in (
        (560, 420, 150, 7, "b", 1.0), (1080, 470, 120, 8, "a", 0.9),
        (140, 600, 100, 9, "a", 0.8), (1370, 130, 96, 10, "b", 0.75),
        (830, 300, 78, 12, "a", 0.7),
    ):
        a(diamond(cx, cy, s, seed, hue, dim))

    # discs
    for cx, cy, r_, seed, wedges, dim in ((950, 430, 62, 3, 8, 1.0),
                                          (330, 470, 44, 4, 8, 0.85),
                                          (1300, 690, 52, 5, 10, 0.8)):
        a(disc(cx, cy, r_, seed, wedges, dim))

    # chevron stacks
    for cx, cy, n, w_, gap, col, dim in ((640, 560, 4, 46, 26, "#8fd8ff", 0.8),
                                         (1160, 610, 3, 38, 22, "#c58fff", 0.7),
                                         (200, 180, 3, 34, 20, "#5cff9d", 0.6)):
        a(chevrons(cx, cy, n, w_, gap, col, dim))

    # particulate: black squares tumbling, green and yellow in clusters
    a('<g fill="#04061a">')
    for _ in range(70):
        x, y = rng.uniform(0, W), rng.uniform(40, 870)
        s = rng.uniform(9, 26)
        a(f'<rect x="{f(x)}" y="{f(y)}" width="{f(s)}" height="{f(s)}" '
          f'transform="rotate({f(rng.uniform(0, 90))} {f(x)} {f(y)})" '
          f'opacity="{rng.uniform(0.5, 0.95):.2f}"/>')
    a("</g>")
    for gx, gy, col, n in ((470, 350, "#5cff9d", 26), (1140, 330, "#ffe14d", 20),
                           (880, 640, "#5cff9d", 18), (240, 760, "#ffe14d", 14)):
        a(f'<g fill="{col}">')
        for _ in range(n):
            x = gx + rng.gauss(0, 46)
            y = gy + rng.gauss(0, 34)
            s = rng.uniform(5, 12)
            a(f'<rect x="{f(x)}" y="{f(y)}" width="{f(s)}" height="{f(s)}" '
              f'opacity="{rng.uniform(0.45, 0.95):.2f}"/>')
        a("</g>")

    # fine motes
    a('<g fill="#dfeaff">')
    for _ in range(90):
        a(f'<circle cx="{f(rng.uniform(0, W))}" cy="{f(rng.uniform(40, 870))}" '
          f'r="{rng.uniform(1, 2.6):.1f}" opacity="{rng.uniform(0.25, 0.8):.2f}"/>')
    a("</g>")

    a(f'<rect width="{W}" height="{H}" fill="url(#ky-vig)"/>')
    a(f'<rect width="{W}" height="{H}" filter="url(#ky-grain)" opacity="0.11"/>')
    a("</svg>")
    return "\n".join(p) + "\n"


if __name__ == "__main__":
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}  {OUT.stat().st_size // 1024} KB")
