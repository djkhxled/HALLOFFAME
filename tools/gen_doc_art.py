#!/usr/bin/env python3
"""Art for the three policy pages.

Terms, Privacy and Credits were the only pages on the site with no artwork
at all, which made them read as a different website. They also should not
compete with a level page: nobody is here for the mood, and a set-piece
behind a liability clause is a joke at the reader's expense.

So this is deliberately the quietest thing in src/art — a ruled grid on a
slow diagonal, a few faint rules, and nothing that moves on its own. It
carries the site's structure without carrying its volume.

Usage: python3 tools/gen_doc_art.py
Writes: src/art/doc.svg
"""

import math
import pathlib
import random

ROOT = pathlib.Path(__file__).resolve().parent.parent
ART = ROOT / "src" / "art"
W, H = 1600, 900


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def build():
    rng = random.Random(7)
    p = []
    a = p.append

    a(f'<svg class="art art--doc" viewBox="0 0 {W} {H}" '
      'xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice" '
      'role="img" aria-label="A faint ruled grid on a slow diagonal">')

    a("<defs>")
    a('<linearGradient id="dc-bg" x1="0" y1="0" x2="0.4" y2="1">'
      '<stop offset="0%" stop-color="#141726"/>'
      '<stop offset="60%" stop-color="#0a0c14"/>'
      '<stop offset="100%" stop-color="#06070b"/></linearGradient>')
    a('<linearGradient id="dc-fade" x1="0" y1="0" x2="0" y2="1">'
      '<stop offset="0%" stop-color="#06070b" stop-opacity="0.1"/>'
      '<stop offset="55%" stop-color="#06070b" stop-opacity="0.55"/>'
      '<stop offset="100%" stop-color="#06070b" stop-opacity="1"/>'
      "</linearGradient>")
    a('<filter id="dc-soft" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="26"/></filter>')
    a('<filter id="dc-grain">'
      '<feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="4"/>'
      '<feColorMatrix type="saturate" values="0"/></filter>')
    a("</defs>")

    a(f'<rect width="{W}" height="{H}" fill="url(#dc-bg)"/>')

    # One soft bloom, off to one side, so the frame is not evenly lit.
    a('<g filter="url(#dc-soft)">')
    a(f'<ellipse cx="{W * 0.22:.0f}" cy="{H * 0.3:.0f}" rx="360" ry="200" '
      'fill="#2b3350" opacity="0.5"/>')
    a(f'<ellipse cx="{W * 0.82:.0f}" cy="{H * 0.7:.0f}" rx="300" ry="170" '
      'fill="#1e2438" opacity="0.45"/>')
    a("</g>")

    # The grid, sheared. A straight grid on a legal page reads as a table;
    # the shear is the only thing here with any attitude.
    a('<g transform="rotate(-9 800 450)" stroke="#9b9ba6" fill="none">')
    for i in range(-6, 30):
        x = i * 78
        a(f'<path d="M{f(x)} -200 L{f(x)} {H + 200}" stroke-width="1" '
          f'opacity="{rng.uniform(0.03, 0.09):.3f}"/>')
    for i in range(-4, 18):
        y = i * 74
        a(f'<path d="M-200 {f(y)} L{W + 200} {f(y)}" stroke-width="1" '
          f'opacity="{rng.uniform(0.03, 0.08):.3f}"/>')
    a("</g>")

    # A handful of brighter rules, to stop it reading as graph paper.
    a('<g stroke="#d8d8e0" fill="none">')
    for _ in range(7):
        y = rng.uniform(0.08, 0.92) * H
        x0 = rng.uniform(-100, W * 0.5)
        a(f'<path d="M{f(x0)} {f(y)} L{f(x0 + rng.uniform(240, 900))} {f(y)}" '
          f'stroke-width="1.4" opacity="{rng.uniform(0.06, 0.16):.2f}"/>')
    a("</g>")

    # Marks at a few intersections: the same 24px glyph language as the
    # countdown, at rest.
    a('<g stroke="#9b9ba6" fill="none" stroke-width="1.4" opacity="0.2">')
    for _ in range(9):
        x, y = rng.uniform(0.05, 0.95) * W, rng.uniform(0.08, 0.92) * H
        s = rng.uniform(9, 22)
        if rng.random() < 0.5:
            a(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(s)}"/>')
        else:
            a(f'<path d="M{f(x - s)} {f(y)} L{f(x)} {f(y - s)} '
              f'L{f(x + s)} {f(y)} L{f(x)} {f(y + s)} Z"/>')
    a("</g>")

    a(f'<rect width="{W}" height="{H}" fill="url(#dc-fade)"/>')
    a(f'<rect width="{W}" height="{H}" filter="url(#dc-grain)" opacity="0.1"/>')
    a("</svg>")
    return "\n".join(p) + "\n"


if __name__ == "__main__":
    ART.mkdir(parents=True, exist_ok=True)
    out = ART / "doc.svg"
    out.write_text(build(), encoding="utf-8")
    print(f"wrote {out}  ({out.stat().st_size:,} bytes)")
