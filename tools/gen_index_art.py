#!/usr/bin/env python3
"""Hero art for the landing page.

The index was the only page on the site with no art behind its title. This
draws one, and draws it out of the list itself: twenty-five shafts of light,
one per level, left to right in countdown order, each carrying that level's
own accent and second accent. Rank 1 stands furthest right and burns
brightest. Change a palette in data/levels and this changes with it.

Usage: python3 tools/gen_index_art.py
"""

import json
import math
import pathlib
import random
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "art" / "index.svg"
W, H = 1600, 900
FLOOR = 690


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def levels():
    out = []
    for p in sorted((ROOT / "data" / "levels").glob("*.json")):
        r = json.loads(p.read_text(encoding="utf-8"))
        pal = r["theme"]["palette"]
        out.append((r["rank"], pal.get("accent", "#888"),
                    pal.get("accent2", "#555")))
    out.sort(key=lambda t: -t[0])          # 25 on the left, 1 on the right
    return out


def build():
    rng = random.Random(25)
    lv = levels()
    n = len(lv)
    p = []
    a = p.append

    a(f'<svg class="art art--index" viewBox="0 0 {W} {H}" '
      'xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice" '
      'role="img" aria-label="Twenty-five shafts of coloured light, one for '
      'each level on the list, rising from a dark floor">')

    a("<defs>")
    a('<linearGradient id="ix-sky" x1="0" y1="0" x2="0.2" y2="1">'
      '<stop offset="0%" stop-color="#0a0b14"/>'
      '<stop offset="62%" stop-color="#06070b"/>'
      '<stop offset="100%" stop-color="#040407"/></linearGradient>')
    for i, (rank, a1, a2) in enumerate(lv):
        # Fades out at the bottom as well as the top. These used to end fully
        # opaque and were cut off by a hard floor line, which read as the
        # image being clipped rather than the light running out.
        a(f'<linearGradient id="ix-g{i}" x1="0" y1="0" x2="0" y2="1">'
          f'<stop offset="0%" stop-color="{a2}" stop-opacity="0"/>'
          f'<stop offset="34%" stop-color="{a2}" stop-opacity="0.5"/>'
          f'<stop offset="62%" stop-color="{a1}" stop-opacity="0.9"/>'
          f'<stop offset="84%" stop-color="{a1}" stop-opacity="0.5"/>'
          f'<stop offset="100%" stop-color="{a1}" stop-opacity="0"/>'
          "</linearGradient>")
    a('<linearGradient id="ix-vig" x1="0" y1="0" x2="0" y2="1">'
      '<stop offset="0%" stop-color="#040407" stop-opacity="0.62"/>'
      '<stop offset="34%" stop-color="#040407" stop-opacity="0"/>'
      '<stop offset="100%" stop-color="#040407" stop-opacity="0.9"/>'
      "</linearGradient>")
    a('<radialGradient id="ix-corner" cx="50%" cy="52%" r="70%">'
      '<stop offset="52%" stop-color="#040407" stop-opacity="0"/>'
      '<stop offset="100%" stop-color="#040407" stop-opacity="0.8"/>'
      "</radialGradient>")
    a('<filter id="ix-wide" x="-120%" y="-120%" width="340%" height="340%"><feGaussianBlur stdDeviation="46"/></filter>')
    a('<filter id="ix-soft" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="16"/></filter>')
    a('<filter id="ix-fine" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="4"/></filter>')
    a("</defs>")

    a(f'<rect width="{W}" height="{H}" fill="url(#ix-sky)"/>')

    # a faint star field, so the upper frame is not empty
    a('<g fill="#dfe3f2">')
    for _ in range(150):
        a(f'<circle cx="{f(rng.uniform(0, W))}" cy="{f(rng.uniform(0, FLOOR))}" '
          f'r="{f(rng.uniform(0.4, 1.4))}" '
          f'opacity="{f(rng.uniform(0.12, 0.6))}"/>')
    a("</g>")

    step = W / n
    # Rank 1 tallest on the right; the list rises as you read toward it.
    for pass_no, (blur, alpha, wide) in enumerate(
            ((("url(#ix-wide)"), 0.5, 2.6),
             (("url(#ix-soft)"), 0.75, 1.35),
             ((None), 1.0, 0.62))):
        a(f'<g opacity="{alpha}"'
          + (f' filter="{blur}"' if blur else "") + ">")
        for i, (rank, a1, a2) in enumerate(lv):
            t = i / (n - 1)                      # 0 at rank 25, 1 at rank 1
            x = step * (i + 0.5)
            height = H * (0.42 + 0.58 * t ** 1.4)
            top = H * 0.98 - height
            half = step * 0.34 * wide
            a(f'<path d="M{f(x - half * 0.42)} {f(top)} '
              f'L{f(x + half * 0.42)} {f(top)} '
              f'L{f(x + half)} {f(FLOOR)} L{f(x - half)} {f(FLOOR)} Z" '
              f'fill="url(#ix-g{i})"/>')
        a("</g>")

    a(f'<rect width="{W}" height="{H}" fill="url(#ix-corner)"/>')
    a(f'<rect width="{W}" height="{H}" fill="url(#ix-vig)"/>')
    a("</svg>")
    return "\n".join(p)


def main():
    svg = build()
    ET.fromstring(svg)
    OUT.write_text(svg + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}  ({len(svg):,} bytes)")


if __name__ == "__main__":
    main()
