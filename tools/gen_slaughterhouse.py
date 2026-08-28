#!/usr/bin/env python3
"""Slaughterhouse hero art — the horned skull with RUN in both sockets.

Drawn from the level's own most-screenshotted frame: a vast ram-horned skull
in red neon on black, RUN burned into each eye, jagged cave teeth closing in
from top and bottom, a magenta strike down the left, and the small white
blocks that sit in the real level.

Usage: python3 tools/gen_slaughterhouse.py
"""

import math
import pathlib
import random
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "art" / "slaughterhouse.svg"

W, H = 1600, 900
CX, CY = 800, 430

RED = "#ff1a1a"
HOT = "#ff6a4a"
DEEP = "#8f0000"


def jag(x1, y1, x2, y2, amp, steps, rng):
    """A ragged line from a to b — used for ribs, cracks and lightning."""
    pts = []
    for i in range(steps + 1):
        t = i / steps
        x = x1 + (x2 - x1) * t
        y = y1 + (y2 - y1) * t
        if 0 < i < steps:
            nx, ny = -(y2 - y1), (x2 - x1)
            n = math.hypot(nx, ny) or 1
            off = rng.uniform(-amp, amp)
            x += nx / n * off
            y += ny / n * off
        pts.append(f"{x:.1f} {y:.1f}")
    return "M" + " L".join(pts)


def horn(rng):
    """One curling ram horn: the dark body and the red linework, separately.

    They have to be separate. Blurring a group that also carries the dark
    fill just blurs the dark over the strokes and there is no glow left."""
    outer = ("M712 292 C604 104 340 62 186 176 C32 290 34 476 198 540 "
             "C312 584 436 530 476 444")
    inner = ("M476 444 C444 512 330 552 234 508 C104 448 104 306 234 244 "
             "C378 176 596 232 692 356")
    shape = f"{outer} {inner[1:]} Z"
    fill = f'<path d="{shape}" fill="#0b0102"/>'
    lines = [f'<path d="{shape}" fill="none" stroke="{RED}" '
             'stroke-width="17" stroke-linejoin="round"/>']
    for i in range(11):
        t = i / 10
        a = math.pi * (0.86 + 0.92 * t)
        ox = 288 + math.cos(a) * 256
        oy = 340 + math.sin(a) * 256 * 0.9
        ix = 296 + math.cos(a) * 156
        iy = 348 + math.sin(a) * 156 * 0.9
        lines.append(f'<path d="{jag(ox, oy, ix, iy, 9, 4, rng)}" fill="none" '
                     f'stroke="{RED}" stroke-width="7" opacity="0.92"/>')
    return fill, "".join(lines)


def cave_teeth(y, height, count, down, rng, fill="#000000"):
    """Stalactites or stalagmites as one jagged polygon across the frame."""
    pts = []
    step = W / count
    for i in range(count + 1):
        x = i * step + rng.uniform(-step * 0.28, step * 0.28)
        depth = rng.uniform(0.35, 1.0) * height
        pts.append(f"{x:.0f},{y + (depth if down else -depth):.0f}")
        pts.append(f"{x + step * 0.5:.0f},{y:.0f}")
    edge = y - height * 1.2 if down else y + height * 1.2
    pts = [f"-40,{edge:.0f}"] + pts + [f"{W + 40},{edge:.0f}"]
    return (f'<polygon points="{" ".join(pts)}" fill="{fill}" '
            f'stroke="{RED}" stroke-width="3" stroke-opacity="0.55"/>')


def build():
    rng = random.Random(1912)  # verified 19 December
    p = []
    a = p.append

    a(f'<svg class="art art--slaughterhouse" viewBox="0 0 {W} {H}" '
      'xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice" '
      'role="img" aria-label="A vast horned skull in red neon on black, the '
      'word RUN burning in each eye socket, jagged cave teeth closing in from '
      'above and below">')

    a("<defs>")
    a('<radialGradient id="sh-glow" cx="50%" cy="46%" r="62%">'
      '<stop offset="0%" stop-color="#e01414" stop-opacity="0.5"/>'
      f'<stop offset="30%" stop-color="{DEEP}" stop-opacity="0.62"/>'
      '<stop offset="66%" stop-color="#4a0006" stop-opacity="0.5"/>'
      '<stop offset="100%" stop-color="#000000" stop-opacity="0"/>'
      "</radialGradient>")
    a('<radialGradient id="sh-maw" cx="50%" cy="40%" r="60%">'
      '<stop offset="0%" stop-color="#ffd0b0"/>'
      f'<stop offset="34%" stop-color="{HOT}"/>'
      f'<stop offset="100%" stop-color="{DEEP}" stop-opacity="0.1"/>'
      "</radialGradient>")
    a('<linearGradient id="sh-vig" x1="0" y1="0" x2="0" y2="1">'
      '<stop offset="0%" stop-color="#000000" stop-opacity="0.55"/>'
      '<stop offset="40%" stop-color="#000000" stop-opacity="0"/>'
      '<stop offset="100%" stop-color="#050101" stop-opacity="0.8"/>'
      "</linearGradient>")
    # The neon look is one blurred copy under a crisp one.
    a('<filter id="sh-neon" x="-30%" y="-30%" width="160%" height="160%">'
      '<feGaussianBlur stdDeviation="13"/></filter>')
    a('<filter id="sh-bloom" x="-40%" y="-40%" width="180%" height="180%">'
      '<feGaussianBlur stdDeviation="30"/></filter>')
    a('<filter id="sh-fine"><feGaussianBlur stdDeviation="3"/></filter>')
    a("</defs>")

    a(f'<rect width="{W}" height="{H}" fill="#050101"/>')
    a(f'<rect width="{W}" height="{H}" fill="url(#sh-glow)"/>')

    # ------------------------------------------------- heat haze up the walls
    a('<g opacity="0.5" filter="url(#sh-bloom)">')
    for _ in range(14):
        x = rng.uniform(0, W)
        h = rng.uniform(160, 420)
        a(f'<ellipse cx="{x:.0f}" cy="{rng.uniform(120, 780):.0f}" '
          f'rx="{rng.uniform(30, 90):.0f}" ry="{h / 2:.0f}" fill="{DEEP}" '
          f'opacity="{rng.uniform(0.12, 0.35):.2f}"/>')
    a("</g>")

    # ---------------------------------------------------------- the skull
    fills, lines = [], []

    left_fill, left_line = horn(rng)
    right_fill, right_line = horn(rng)  # its own noise, so it isn't a mirror
    fills.append(left_fill)
    lines.append(left_line)
    fills.append(f'<g transform="translate({W},0) scale(-1,1)">{right_fill}</g>')
    lines.append(f'<g transform="translate({W},0) scale(-1,1)">{right_line}</g>')

    CRANIUM = ("M800 214 C672 214 596 282 582 380 C572 448 590 500 612 540 "
               "C632 576 640 614 634 650 C692 678 740 692 800 692 "
               "C860 692 908 678 966 650 C960 614 968 576 988 540 "
               "C1010 500 1028 448 1018 380 C1004 282 928 214 800 214 Z")
    fills.append(f'<path d="{CRANIUM}" fill="#0b0102"/>')
    lines.append(f'<path d="{CRANIUM}" fill="none" stroke="{RED}" '
                 'stroke-width="17" stroke-linejoin="round"/>')

    for ex in (716, 884):
        sock = (f"M{ex - 74} 396 L{ex + 74} 382 L{ex + 66} 480 "
                f"L{ex - 66} 486 Z")
        fills.append(f'<path d="{sock}" fill="#050000"/>')
        lines.append(f'<path d="{sock}" fill="none" stroke="{RED}" '
                     'stroke-width="12"/>')

    lines.append(f'<path d="M612 386 L700 356 M988 386 L900 356" '
                 f'stroke="{RED}" stroke-width="10" fill="none" '
                 'stroke-linecap="round"/>')

    nose = "M800 508 L768 570 L800 584 L832 570 Z"
    fills.append(f'<path d="{nose}" fill="#050000"/>')
    lines.append(f'<path d="{nose}" fill="none" stroke="{RED}" '
                 'stroke-width="8"/>')

    for x0, x1 in ((606, 676), (994, 924)):
        lines.append(f'<path d="{jag(x0, 520, x1, 606, 12, 5, rng)}" '
                     f'fill="none" stroke="{RED}" stroke-width="5" '
                     'opacity="0.85"/>')

    maw = ("M676 622 C730 610 870 610 924 622 C908 674 866 702 800 702 "
           "C734 702 692 674 676 622 Z")
    fills.append(f'<path d="{maw}" fill="url(#sh-maw)" opacity="0.95"/>')
    teeth = " ".join(f"M{676 + i * 28} 622 L{690 + i * 28} 656 "
                     f"L{704 + i * 28} 622" for i in range(9))
    lines.append(f'<path d="{teeth}" fill="none" stroke="#1a0000" '
                 'stroke-width="9" stroke-linejoin="round"/>')

    ink = "".join(lines)
    # The figure is drawn at a comfortable size and then blown up to fill the
    # frame; the reference is edge to edge, not a medallion in the middle.
    up = f'<g transform="translate({CX},{CY}) scale(1.05) translate({-CX},{-CY})">'
    a(f'{up}{"".join(fills)}</g>')
    a(f'{up}<g filter="url(#sh-bloom)" opacity="0.7">{ink}</g></g>')
    a(f'{up}<g filter="url(#sh-neon)" opacity="0.95">{ink}</g></g>')
    a(f"{up}{ink}</g>")

    # ------------------------------------------------------------- RUN, RUN
    for ex in (716, 884):
        a(up)
        a(f'<text x="{ex}" y="{460}" text-anchor="middle" '
          'font-family="Metal Mania, Impact, sans-serif" font-size="66" '
          f'fill="{RED}" filter="url(#sh-neon)" opacity="0.95">RUN</text>')
        a(f'<text x="{ex}" y="{460}" text-anchor="middle" '
          'font-family="Metal Mania, Impact, sans-serif" font-size="66" '
          f'fill="#ffd0c0" letter-spacing="2">RUN</text>')
        a("</g>")

    # ------------------------------------------------------------ cave teeth
    top = cave_teeth(92, 124, 24, True, rng)
    bottom = cave_teeth(816, 132, 20, False, rng)
    a(f'<g filter="url(#sh-bloom)" opacity="0.75">{top}{bottom}</g>')
    a(top)
    a(bottom)

    # ------------------------------------------------------------- lightning
    a(f'<g stroke="#ff4de0" fill="none" opacity="0.75">'
      f'<path d="{jag(120, 40, 210, 330, 26, 9, rng)}" stroke-width="2.4"/>'
      f'<path d="{jag(1470, 90, 1392, 300, 20, 8, rng)}" '
      'stroke-width="1.8" opacity="0.6"/></g>')

    # -------------------------------------------------------- level blocks
    a('<g fill="#ffffff">')
    for _ in range(11):
        x, y = rng.uniform(60, W - 60), rng.uniform(80, H - 120)
        sz = rng.uniform(9, 17)
        a(f'<rect x="{x:.0f}" y="{y:.0f}" width="{sz:.0f}" height="{sz:.0f}" '
          f'opacity="{rng.uniform(0.55, 0.95):.2f}" '
          f'transform="rotate({rng.uniform(-20, 20):.0f} {x:.0f} {y:.0f})"/>')
    a("</g>")

    # ---------------------------------------------------------------- embers
    a("<g>")
    for _ in range(150):
        x, y = rng.uniform(0, W), rng.uniform(60, H)
        r = rng.uniform(0.8, 2.6)
        col = rng.choice([RED, HOT, "#ffb066"])
        a(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="{col}" '
          f'opacity="{rng.uniform(0.25, 0.9):.2f}"/>')
    a("</g>")

    a(f'<rect width="{W}" height="{H}" fill="url(#sh-vig)"/>')
    a("</svg>")
    return "\n".join(p)


def main():
    svg = build()
    ET.fromstring(svg)
    OUT.write_text(svg + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}  ({len(svg):,} bytes)")


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# The set-piece scene.
#
# This generator owns bespoke/slaughterhouse.html as well as the hero art: the
# thorn is recursive and the chains are repetitive, so both want a loop rather
# than hand-written markup. The prose lives here too, so the file has one
# source rather than being half generated and half edited by hand.
# ---------------------------------------------------------------------------

SETPIECE = ROOT / "bespoke" / "slaughterhouse.html"


def thorn(rng, x, y, ang, length, depth, out):
    """A branching bramble. Each limb throws barbs and forks twice."""
    if depth == 0 or length < 14:
        return
    x2 = x + math.cos(ang) * length
    y2 = y + math.sin(ang) * length
    out.append(f'<path d="{jag(x, y, x2, y2, length * 0.14, 3, rng)}" '
               f'stroke-width="{max(1.2, depth * 0.9):.1f}"/>')
    for side in (-1, 1):  # barbs
        ba = ang + side * rng.uniform(1.0, 1.5)
        bl = length * rng.uniform(0.18, 0.34)
        out.append(f'<path d="M{x2:.1f} {y2:.1f} '
                   f"L{x2 + math.cos(ba) * bl:.1f} "
                   f'{y2 + math.sin(ba) * bl:.1f}" stroke-width="1.4"/>')
    for _ in range(2):
        thorn(rng, x2, y2, ang + rng.uniform(-0.72, 0.72),
              length * rng.uniform(0.6, 0.82), depth - 1, out)


def chain(x, top, bottom, rx=13, ry=22):
    """A hanging chain, as alternating link ellipses."""
    links = []
    y = top
    i = 0
    while y < bottom:
        a, b = (rx, ry) if i % 2 == 0 else (rx * 0.45, ry)
        links.append(f'<ellipse cx="{x}" cy="{y:.0f}" rx="{a:.0f}" '
                     f'ry="{b}" fill="none" stroke="#a8161b" '
                     'stroke-width="5" opacity="0.9"/>')
        y += ry * 1.5
        i += 1
    return "".join(links)


def scene():
    rng = random.Random(2110)  # the October claim
    p = []
    a = p.append
    a('<svg class="pulse__scene" viewBox="0 0 1600 900" '
      'xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice" '
      'aria-hidden="true">')
    a("<defs>")
    a('<radialGradient id="sp-orb" cx="42%" cy="38%" r="58%">'
      '<stop offset="0%" stop-color="#ffffff"/>'
      '<stop offset="26%" stop-color="#ffd6f2"/>'
      '<stop offset="58%" stop-color="#ff2fc8" stop-opacity="0.8"/>'
      '<stop offset="100%" stop-color="#ff2fc8" stop-opacity="0"/>'
      "</radialGradient>")
    a('<radialGradient id="sp-halo" cx="50%" cy="50%" r="50%">'
      '<stop offset="0%" stop-color="#2bff9d" stop-opacity="0.5"/>'
      '<stop offset="100%" stop-color="#2bff9d" stop-opacity="0"/>'
      "</radialGradient>")
    a('<filter id="sp-neon" x="-40%" y="-40%" width="180%" height="180%">'
      '<feGaussianBlur stdDeviation="9"/></filter>')
    a("</defs>")

    # chains down the right, as in the THE END frame
    a(f'<g opacity="0.8">{chain(86, -40, 900)}{chain(1436, -20, 940)}'
      f'{chain(1546, -60, 900)}</g>')

    # neon guide lines, magenta and green
    a('<g fill="none" opacity="0.85">')
    a(f'<path d="{jag(980, -20, 1040, 300, 34, 8, rng)}" stroke="#ff2fc8" '
      'stroke-width="3"/>')
    a(f'<path d="{jag(1090, -30, 1030, 260, 30, 7, rng)}" stroke="#2bff9d" '
      'stroke-width="3"/>')
    a("</g>")

    # the bramble
    limbs = []
    for base_ang, ln in ((-2.6, 132), (-2.0, 150), (2.6, 122), (2.1, 106)):
        thorn(rng, 1210, 400, base_ang, ln, 5, limbs)
    bramble = "".join(limbs)
    a(f'<g stroke="{RED}" fill="none" stroke-linecap="round" '
      f'filter="url(#sp-neon)" opacity="0.6">{bramble}</g>')
    a(f'<g stroke="{RED}" fill="none" stroke-linecap="round">{bramble}</g>')

    # the orb the bramble reaches into
    a('<circle cx="980" cy="404" r="168" fill="url(#sp-halo)"/>')
    a('<circle cx="980" cy="404" r="104" fill="url(#sp-orb)" data-beat/>')

    # the blocky face: square sockets, crossed out, dripping, jagged jaw
    face = []
    face.append('<rect x="176" y="516" width="470" height="212" fill="none" '
                f'stroke="{RED}" stroke-width="6"/>')
    for ex in (286, 466):
        face.append(f'<rect x="{ex}" y="576" width="94" height="80" '
                    f'fill="none" stroke="{RED}" stroke-width="5"/>')
        face.append(f'<path d="M{ex} 576 L{ex + 94} 656 M{ex + 94} 576 '
                    f'L{ex} 656" stroke="{RED}" stroke-width="4" '
                    'opacity="0.85"/>')
        for k in range(4):  # drips
            dx = ex + 14 + k * 22
            face.append(f'<path d="M{dx} 656 L{dx} {656 + rng.randint(18, 52)}"'
                        f' stroke="{RED}" stroke-width="2.4" opacity="0.7"/>')
    jawpts = []
    for i in range(11):
        tx = 186 + i * 44
        jawpts.append(f"M{tx} 728 L{tx + 22} 790 L{tx + 44} 728")
    face.append(f'<path d="{" ".join(jawpts)}" fill="none" stroke="{RED}" '
                'stroke-width="5" stroke-linejoin="round"/>')
    blocky = "".join(face)
    a(f'<g filter="url(#sp-neon)" opacity="0.55" data-beat>{blocky}</g>')
    a(f"<g>{blocky}</g>")

    # loose level blocks
    a('<g fill="#ffffff">')
    for _ in range(9):
        x, y = rng.uniform(120, 1500), rng.uniform(100, 820)
        s = rng.uniform(8, 15)
        a(f'<rect x="{x:.0f}" y="{y:.0f}" width="{s:.0f}" height="{s:.0f}" '
          f'opacity="{rng.uniform(0.5, 0.9):.2f}"/>')
    a("</g>")
    a("</svg>")
    return "".join(p)


BAT = ("M0 0 c14 -13 30 -20 44 -9 c6 -12 16 -12 22 0 c14 -11 30 -4 44 9 "
       "c-12 -3 -22 2 -26 12 c-8 -8 -16 -7 -18 3 c-4 -8 -14 -9 -22 -2 "
       "c-4 -11 -14 -16 -26 -13 Z")


def build_setpiece():
    return f'''<section class="sig sig--pulse" data-sig="pulse" aria-labelledby="pulse-h">
  <h2 id="pulse-h" class="visually-hidden">Slaughterhouse &mdash; the end of the world</h2>

  <div class="pulse__loom" data-loom aria-hidden="true">
    {scene()}
  </div>

  <p class="pulse__end" aria-hidden="true">
    <span class="pulse__end-text">THE END</span>
    <svg class="pulse__bat" viewBox="0 0 110 30" aria-hidden="true" focusable="false"><path d="{BAT}" fill="currentColor"/></svg>
  </p>

  <div class="pulse__copy page">
    <p class="eyebrow" data-pulse-line data-motion>Welcome to the End of the World</p>
    <p class="pulse__line" data-pulse-line data-motion>Never supposed<br>to be possible</p>
    <p class="pulse__sub measure" data-pulse-line data-motion>
      Hosted by icedcave over his own 2015 impossible level. spaceuk claimed
      the verification on 24 October 2021 and had hacked it; Doggie took the
      title legitimately on 19 December. River&rsquo;s wave at 49-58% is the
      part everyone quotes.
    </p>
  </div>
</section>
'''


if __name__ == "__main__":
    SETPIECE.write_text(build_setpiece(), encoding="utf-8")
    print(f"wrote {SETPIECE.relative_to(ROOT)}")
