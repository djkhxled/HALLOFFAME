#!/usr/bin/env python3
"""Generate the Deimos hero art from the level's thumbnail composition.

Cinematic, not geometric: a blood eclipse burning behind a ruined gothic
cathedral, organic rock terrain, a leaning grave marker with its plaque, bone,
bats, fog banks and heavy grain. Everything is silhouette, light and texture —
no decorative primitives.

Original artwork following the thumbnail's composition; nothing is traced or
embedded from the source image.

Usage: python3 tools/gen_deimos.py
Writes: src/art/deimos.svg
"""

import math
import pathlib
import random

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "art" / "deimos.svg"

W, H = 1600, 900
ORB = (1010, 178, 182)          # cx, cy, r
rng = random.Random(1969)


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


# ---------------------------------------------------------------- terrain

def ridge(y0, amp, seed, n=110, jag=0.55, x0=-60, x1=W + 60):
    """An organic rock silhouette: layered waves plus per-point jitter, so the
    edge never reads as a row of triangles."""
    r = random.Random(seed)
    pts = []
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        y = y0
        y += math.sin(t * math.pi * 2.1 + seed * 0.7) * amp * 0.5
        y += math.sin(t * math.pi * 5.3 + seed) * amp * 0.28
        y += math.sin(t * math.pi * 11.7 + seed * 1.9) * amp * 0.14
        y += r.uniform(-1, 1) * amp * jag * 0.4
        pts.append((x, y))
    d = f"M{f(x0)} {H + 60} L{f(pts[0][0])} {f(pts[0][1])}"
    for x, y in pts[1:]:
        d += f" L{f(x)} {f(y)}"
    d += f" L{f(x1)} {H + 60} Z"
    return d, pts


def boulder(cx, cy, rx, ry, seed, n=26):
    """A single mass of rock — irregular, closed, no straight runs."""
    r = random.Random(seed)
    pts = []
    for i in range(n):
        a = i / n * math.tau
        k = 1 + r.uniform(-0.22, 0.22) + math.sin(a * 3 + seed) * 0.1
        pts.append((cx + math.cos(a) * rx * k, cy + math.sin(a) * ry * k))
    return "M" + " L".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"


# ---------------------------------------------------------------- lighting

def bolt(x, y, segs, spread, drop, seed):
    r = random.Random(seed)
    d = f"M{f(x)} {f(y)}"
    for _ in range(segs):
        x += r.uniform(-spread, spread)
        y += drop * r.uniform(0.6, 1.4)
        d += f" L{f(x)} {f(y)}"
    return d


# ---------------------------------------------------------------- cathedral

def spire(x, base, w, top, extra=""):
    """A tower: tapered body, pointed roof, rim light down the lit side."""
    h = w / 2
    body = (f'<path d="M{f(x - h)} {f(base)} L{f(x - h * 0.86)} {f(top + w * 0.9)} '
            f'L{f(x)} {f(top)} L{f(x + h * 0.86)} {f(top + w * 0.9)} '
            f'L{f(x + h)} {f(base)} Z" fill="url(#dm-stone)"/>')
    rim = (f'<path d="M{f(x)} {f(top)} L{f(x + h * 0.86)} {f(top + w * 0.9)} '
           f'L{f(x + h)} {f(base)}" fill="none" stroke="#ff8a5c" '
           f'stroke-width="2.4" opacity="0.7"/>')
    return body + rim + extra


def windows(x, y0, y1, w, cols, rows, op=0.8):
    out = []
    for c in range(cols):
        for rw in range(rows):
            wx = x - w / 2 + (c + 0.5) * (w / cols)
            wy = y0 + (rw + 0.5) * ((y1 - y0) / rows)
            out.append(f'<path d="M{f(wx - 4)} {f(wy + 11)} '
                       f'a4.6 4.6 0 0 1 8 0 v-11 h-8 Z" '
                       f'fill="#ffb27a" opacity="{op}"/>')
    return "".join(out)


def cathedral():
    p = []
    base = 470
    # rear towers, lower and dimmer, to give the mass depth
    p.append('<g opacity="0.75">')
    p.append(spire(872, base, 46, 236))
    p.append(spire(1152, base, 44, 250))
    p.append("</g>")

    # main body
    p.append(f'<path d="M912 {base} L912 300 L1108 300 L1108 {base} Z" '
             'fill="url(#dm-stone)"/>')
    # crenellations along the body
    cren = []
    x = 912
    up = True
    while x < 1108:
        cren.append(f"L{f(x)} {f(288 if up else 300)}")
        x += 14
        cren.append(f"L{f(x)} {f(288 if up else 300)}")
        up = not up
    p.append(f'<path d="M912 306 {" ".join(cren)} L1108 306 Z" fill="url(#dm-stone)"/>')

    # flanking towers
    p.append(spire(936, base, 62, 186))
    p.append(spire(1084, base, 60, 196))
    # central keep and steeple
    p.append(spire(1010, base, 88, 96))
    # cross on the steeple
    p.append('<g fill="#2a1012"><rect x="1006" y="34" width="8" height="46"/>'
             '<rect x="991" y="46" width="38" height="7"/></g>'
             '<g fill="none" stroke="#ff8a5c" stroke-width="1.8" opacity="0.75">'
             '<path d="M1010 34 v46 M991 49 h38"/></g>')

    # rose window
    p.append('<circle cx="1010" cy="356" r="27" fill="url(#dm-rose)"/>'
             '<g fill="none" stroke="#2a1012" stroke-width="3">'
             '<circle cx="1010" cy="356" r="27"/>'
             '<circle cx="1010" cy="356" r="11"/>'
             '<path d="M1010 329 v54 M983 356 h54 M991 337 l38 38 M1029 337 l-38 38"/></g>'
             '<circle cx="1010" cy="356" r="42" fill="#ff6a36" opacity="0.2" '
             'filter="url(#dm-blur)"/>')

    # windows across the body and towers
    p.append(windows(1010, 392, 452, 150, 6, 2))
    p.append(windows(936, 240, 430, 34, 1, 4, 0.7))
    p.append(windows(1084, 250, 430, 34, 1, 4, 0.7))
    p.append(windows(872, 300, 440, 26, 1, 3, 0.55))
    p.append(windows(1152, 310, 440, 26, 1, 3, 0.55))

    # buttresses
    p.append('<g fill="none" stroke="#241012" stroke-width="11">'
             '<path d="M898 430 Q 908 384 918 392"/>'
             '<path d="M1122 430 Q 1112 384 1102 392"/></g>')

    # a broken shoulder, so the ruin reads
    p.append('<path d="M1084 196 l9 22 -14 18 15 17 -11 24 h-3 V196 Z" fill="#0b0607"/>')
    return "".join(p)


# ---------------------------------------------------------------- marker

def marker():
    p = []
    # angled plaque board, upper left
    p.append('<path d="M92 176 L326 122 L372 258 L138 314 Z" fill="#221415"/>')
    p.append('<g stroke="#000" stroke-width="1" opacity="0.55" fill="none">'
             '<path d="M112 186 L332 132 M124 224 L346 170 M134 264 L356 210"/></g>')
    p.append('<path d="M326 122 L372 258" fill="none" stroke="#c8705a" '
             'stroke-width="2.8" opacity="0.55"/>')
    p.append('<path d="M92 176 L326 122" fill="none" stroke="#8a4a3c" '
             'stroke-width="1.6" opacity="0.35"/>')
    # shield board with its pointer
    p.append('<path d="M392 182 L514 154 L558 238 L522 328 L406 302 Z" fill="#221415"/>')
    p.append('<path d="M514 154 L558 238 L522 328" fill="none" stroke="#c8705a" '
             'stroke-width="2.6" opacity="0.55"/>')
    p.append('<path d="M438 256 L512 242 L496 268 L522 274 L434 292 Z" '
             'fill="#ff4a22" opacity="0.65"/>')
    # leaning post and crossbar
    p.append('<path d="M246 668 L288 292 l38 5 -42 376 Z" fill="#221415"/>')
    p.append('<path d="M188 362 l208 28 -6 40 -208-28 Z" fill="#221415"/>')
    p.append('<g stroke="#000" stroke-width="1" opacity="0.5" fill="none">'
             '<path d="M258 664 L298 298 M272 666 L312 300"/>'
             '<path d="M190 376 l206 28 M192 390 l206 28"/></g>')
    p.append('<g fill="none" stroke="#c8705a" stroke-width="2.4" opacity="0.55">'
             '<path d="M326 297 L284 668" /><path d="M396 390 l-6 40"/></g>')
    # small nailed cross
    p.append('<g fill="#c8705a" opacity="0.6"><rect x="302" y="410" width="6" '
             'height="30"/><rect x="291" y="418" width="28" height="6"/></g>')
    return "".join(p)


def bones():
    p = ['<g fill="#1c1213">']
    for cx, cy, r in ((128, 596, 31), (196, 618, 25), (66, 626, 23)):
        p.append(f'<path d="M{f(cx - r)} {f(cy - r * 0.3)} '
                 f'a{f(r)} {f(r)} 0 0 1 {f(r * 1.9)} {f(r * 0.45)} '
                 f'q2 {f(r * 0.72)} -{f(r * 0.46)} {f(r * 0.85)} '
                 f'q-{f(r * 0.62)} {f(r * 0.1)} -{f(r * 1.1)} -{f(r * 0.2)} '
                 f'q-{f(r * 0.42)} -{f(r * 0.46)} -{f(r * 0.34)} -{f(r * 1.1)} Z"/>')
    for x, y, w_, rot in ((222, 646, 82, -8), (198, 682, 64, 6), (152, 664, 56, -15)):
        p.append(f'<rect x="{x}" y="{y}" width="{w_}" height="9" rx="4.5" '
                 f'transform="rotate({rot} {x} {y})"/>')
    p.append("</g>")
    # sockets, only slightly darker than the bone
    p.append('<g fill="#100a0b">')
    for ex, ey, er in ((116, 592, 6.4), (140, 595, 6.4), (186, 614, 5.2),
                       (205, 617, 5.2), (58, 622, 4.8), (75, 624, 4.8)):
        p.append(f'<ellipse cx="{ex}" cy="{ey}" rx="{er}" ry="{er * 1.15}"/>')
    p.append("</g>")
    return "".join(p)


# ---------------------------------------------------------------- assemble

def build():
    p = []
    a = p.append
    cx, cy, r = ORB

    a(f'<svg class="art art--deimos" viewBox="0 0 {W} {H}" '
      'xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice" '
      'role="img" aria-label="A blood eclipse burning behind a ruined gothic '
      'cathedral, above dark rock, with a leaning grave marker and bone">')

    a("<defs>")
    a('<radialGradient id="dm-orb" cx="50%" cy="46%" r="52%">'
      '<stop offset="0%" stop-color="#fff0e0"/>'
      '<stop offset="20%" stop-color="#ff8e5c"/>'
      '<stop offset="50%" stop-color="#ff3a18"/>'
      '<stop offset="82%" stop-color="#a50f06"/>'
      '<stop offset="95%" stop-color="#ff7038"/>'
      '<stop offset="100%" stop-color="#480503"/></radialGradient>')
    a('<radialGradient id="dm-halo" cx="50%" cy="50%" r="50%">'
      '<stop offset="0%" stop-color="#ff3a1c" stop-opacity="0.55"/>'
      '<stop offset="34%" stop-color="#c4140f" stop-opacity="0.26"/>'
      '<stop offset="100%" stop-color="#c4140f" stop-opacity="0"/></radialGradient>')
    a('<linearGradient id="dm-stone" x1="0" y1="0" x2="0.35" y2="1">'
      '<stop offset="0%" stop-color="#40201d"/>'
      '<stop offset="46%" stop-color="#20100f"/>'
      '<stop offset="100%" stop-color="#0b0607"/></linearGradient>')
    a('<radialGradient id="dm-rose" cx="50%" cy="50%" r="50%">'
      '<stop offset="0%" stop-color="#ffd6ad"/>'
      '<stop offset="55%" stop-color="#ff6a36"/>'
      '<stop offset="100%" stop-color="#8c1c0a"/></radialGradient>')
    a('<linearGradient id="dm-fog" x1="0" y1="0" x2="0" y2="1">'
      '<stop offset="0%" stop-color="#0a0506" stop-opacity="0"/>'
      '<stop offset="72%" stop-color="#0a0506" stop-opacity="0.34"/>'
      '<stop offset="100%" stop-color="#0a0506" stop-opacity="0.72"/></linearGradient>')
    a('<radialGradient id="dm-vig" cx="50%" cy="44%" r="72%">'
      '<stop offset="54%" stop-color="#0a0506" stop-opacity="0"/>'
      '<stop offset="100%" stop-color="#000" stop-opacity="0.78"/></radialGradient>')
    a('<filter id="dm-blur"><feGaussianBlur stdDeviation="10"/></filter>')
    a('<filter id="dm-fogblur"><feGaussianBlur stdDeviation="34"/></filter>')
    a('<filter id="dm-soft"><feGaussianBlur stdDeviation="4"/></filter>')
    a('<filter id="dm-grain">'
      '<feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="5"/>'
      '<feColorMatrix type="saturate" values="0"/></filter>')
    a("</defs>")

    a(f'<rect width="{W}" height="{H}" fill="#0a0506"/>')

    # cloud banks catching the light
    a('<g filter="url(#dm-fogblur)">')
    for bx, by, rx, ry, op in ((1010, 96, 470, 74, 0.5), (700, 232, 380, 54, 0.4),
                               (1420, 300, 300, 48, 0.34), (330, 150, 340, 62, 0.34)):
        a(f'<ellipse cx="{bx}" cy="{by}" rx="{rx}" ry="{ry}" fill="#3a1618" '
          f'opacity="{op}"/>')
    a("</g>")

    # The eclipse group sits right of centre: the hero's centred rank line
    # is unreadable over the disc, and moving light beats fighting it.
    a('<g transform="translate(150 26)">')
    # the eclipse
    a(f'<circle cx="{cx}" cy="{cy}" r="{r * 2.6}" fill="url(#dm-halo)"/>')
    a(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#dm-orb)"/>')
    a(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#ffc19c" '
      'stroke-width="3" opacity="0.8"/>')
    a(f'<circle cx="{cx}" cy="{cy}" r="{r + 20}" fill="none" stroke="#ff5a2e" '
      'stroke-width="1.6" opacity="0.4"/>')

    # lightning clawing across the disc
    for i, (bx, by) in enumerate(((880, 90), (1156, 74), (1120, 300), (836, 210))):
        d = bolt(bx, by, 5, 26, 34, 40 + i)
        a(f'<path d="{d}" fill="none" stroke="#ff5a2e" stroke-width="9" '
          f'opacity="0.3" filter="url(#dm-soft)"/>')
        a(f'<path d="{d}" fill="none" stroke="#ffe4d2" stroke-width="2.3" '
          'stroke-linejoin="round" opacity="0.92"/>')

    a(cathedral())

    # bats
    a('<g fill="#0a0506" opacity="0.94">')
    for bx, by, s in ((1116, 118, 1.0), (884, 168, 0.75), (1206, 262, 0.9),
                      (940, 88, 0.6), (1264, 150, 0.7), (1042, 250, 0.55)):
        a(f'<path transform="translate({bx} {by}) scale({s})" '
          'd="M0 0 q9-10 18 0 q9-10 18 0 q-9 8-18 3 q-9 5-18-3Z"/>')
    a("</g>")
    a("</g>")

    # terrain: three organic ranges, each hazier than the one in front
    for i, (y0, amp, seed, fill) in enumerate((
        (588, 96, 3, "#2b1a19"), (704, 84, 8, "#1d1213"), (812, 66, 15, "#120b0c"),
    )):
        d, pts = ridge(y0, amp, seed)
        a(f'<path d="{d}" fill="{fill}"/>')
        # a thin catch of eclipse light along each crest
        crest = "M" + " L".join(f"{f(x)} {f(y)}" for x, y in pts)
        a(f'<path d="{crest}" fill="none" stroke="#c0503a" stroke-width="1.6" '
          f'opacity="{0.34 - i * 0.08:.2f}"/>')

    # boulders sitting on the ranges
    for bx, by, rx, ry, seed, fill in (
        (470, 700, 120, 54, 21, "#241615"), (760, 764, 150, 60, 33, "#1a1011"),
        (1240, 726, 130, 56, 44, "#241615"), (180, 762, 96, 44, 55, "#1a1011"),
        (1480, 790, 110, 48, 66, "#160d0e"),
    ):
        a(f'<path d="{boulder(bx, by, rx, ry, seed)}" fill="{fill}"/>')

    # ember pools between the rocks
    a('<g filter="url(#dm-blur)">')
    for ex, ey, rx in ((300, 700, 150), (760, 754, 170), (1230, 716, 150)):
        a(f'<ellipse cx="{ex}" cy="{ey}" rx="{rx}" ry="15" fill="#ff3b1e" '
          'opacity="0.32"/>')
    a("</g>")

    # a ground strike, as in the thumbnail
    d = bolt(612, 520, 4, 22, 30, 91)
    a(f'<path d="{d}" fill="none" stroke="#ff3b1e" stroke-width="11" '
      'opacity="0.28" filter="url(#dm-soft)"/>')
    a(f'<path d="{d}" fill="none" stroke="#ff7a52" stroke-width="2.6" '
      'stroke-linejoin="round" opacity="0.9"/>')

    a(marker())
    a(bones())

    # drifting fog in front of the middle distance
    a('<g filter="url(#dm-fogblur)">')
    for fx, fy, rx, ry, op in ((520, 640, 360, 46, 0.3), (1150, 690, 320, 40, 0.26),
                               (830, 780, 420, 44, 0.24)):
        a(f'<ellipse cx="{fx}" cy="{fy}" rx="{rx}" ry="{ry}" fill="#3a1618" '
          f'opacity="{op}"/>')
    a("</g>")

    # rising embers
    a('<g fill="#ff9d6a">')
    for _ in range(60):
        x = rng.uniform(0, W)
        y = rng.uniform(300, 860)
        a(f'<circle cx="{f(x)}" cy="{f(y)}" r="{rng.uniform(1.0, 2.8):.1f}" '
          f'opacity="{rng.uniform(0.25, 0.8):.2f}"/>')
    a("</g>")

    a(f'<rect width="{W}" height="{H}" fill="url(#dm-fog)"/>')
    a(f'<rect width="{W}" height="{H}" fill="url(#dm-vig)"/>')
    a(f'<rect width="{W}" height="{H}" filter="url(#dm-grain)" opacity="0.2"/>')
    a("</svg>")
    return "\n".join(p) + "\n"


if __name__ == "__main__":
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}  {OUT.stat().st_size // 1024} KB")
