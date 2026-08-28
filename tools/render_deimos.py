#!/usr/bin/env python3
"""Render the Deimos cover as a raster image.

The SVG version reads as illustration because vector fills are flat. This
renders instead: fractal cloud, volumetric haze between depth planes, bloom
around the light source, backlit rims, and sensor grain. Follows the "Ashfall"
philosophy in notes/design/deimos-philosophy.md.

Pillow only — no numpy on this machine.

Usage: python3 tools/render_deimos.py [--scale 1.0]
Writes: src/art/deimos.png
"""

import argparse
import math
import pathlib
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "art" / "deimos.png"

W, H = 2400, 1350

# One hot family, one cold, and a great deal of near-black between them.
NEAR_BLACK = (10, 6, 8)
EMBER = (255, 96, 48)
CORE = (255, 176, 132)
BONE = (232, 214, 206)

ORB = (0.735, 0.20)   # eclipse centre, as a fraction of the frame
ORB_R = 0.152         # eclipse radius, fraction of width


# --------------------------------------------------------------------------
# noise and gradients
# --------------------------------------------------------------------------

def value_noise(w, h, cells, seed):
    """One octave: random lattice scaled up with bicubic smoothing."""
    rng = random.Random(seed)
    small = Image.new("L", (max(cells, 2), max(int(cells * h / w), 2)))
    small.putdata([rng.randrange(256) for _ in range(small.width * small.height)])
    return small.resize((w, h), Image.BICUBIC)


def fractal_noise(w, h, octaves=6, seed=0, base=3, persistence=0.55):
    """Cloud, grown rather than drawn: many frequencies folded together.

    Accumulated as a running weighted average via Image.blend — ImageChops.add
    refuses F-mode, and staying in L keeps every octave 8-bit and fast.
    """
    acc = None
    running = 0.0
    amp = 1.0
    for i in range(octaves):
        layer = value_noise(w, h, base * (2 ** i), seed + i * 977)
        running += amp
        acc = layer if acc is None else Image.blend(acc, layer, amp / running)
        amp *= persistence
    return acc


def vgrad(w, h, stops):
    """Vertical gradient from (position, rgb) stops."""
    strip = Image.new("RGB", (1, h))
    px = strip.load()
    stops = sorted(stops)
    for y in range(h):
        t = y / max(h - 1, 1)
        lo = stops[0]
        hi = stops[-1]
        for i in range(len(stops) - 1):
            if stops[i][0] <= t <= stops[i + 1][0]:
                lo, hi = stops[i], stops[i + 1]
                break
        span = (hi[0] - lo[0]) or 1
        f = (t - lo[0]) / span
        px[0, y] = tuple(int(lo[1][c] + (hi[1][c] - lo[1][c]) * f) for c in range(3))
    return strip.resize((w, h), Image.BILINEAR)


def _lerp_stops(stops, t):
    stops = sorted(stops)
    lo, hi = stops[0], stops[-1]
    for i in range(len(stops) - 1):
        if stops[i][0] <= t <= stops[i + 1][0]:
            lo, hi = stops[i], stops[i + 1]
            break
    span = (hi[0] - lo[0]) or 1
    f = (t - lo[0]) / span
    return tuple(int(lo[1][c] + (hi[1][c] - lo[1][c]) * f) for c in range(3))


def radial_ramp(size, cx, cy, r, stops, steps=110):
    """A true radial gradient. A disc lit vertically reads as a dome, not a
    sphere — the falloff has to run from the centre outward."""
    img = Image.new("RGB", size, stops[-1][1])
    d = ImageDraw.Draw(img)
    for i in range(steps, 0, -1):
        t = i / steps
        rr = r * t
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
                  fill=_lerp_stops(stops, t))
    return img.filter(ImageFilter.GaussianBlur(max(size[0] / 1400, 1)))


def radial_mask(w, h, cx, cy, radius, falloff=1.0):
    """Soft radial falloff as an L mask, built at low res then smoothed."""
    dw, dh = w // 6, h // 6
    m = Image.new("L", (dw, dh), 0)
    px = m.load()
    rx, ry = cx * dw, cy * dh
    r = radius * dw
    for y in range(dh):
        for x in range(dw):
            d = math.hypot(x - rx, y - ry) / r
            v = max(0.0, 1.0 - d) ** falloff
            px[x, y] = int(v * 255)
    return m.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(w / 220))


def screen(base, layer):
    return ImageChops.screen(base, layer)


def tinted(mask, colour, size):
    """An L mask painted a single colour, as an RGB layer."""
    out = Image.new("RGB", size, colour)
    black = Image.new("RGB", size, (0, 0, 0))
    return Image.composite(out, black, mask)


# --------------------------------------------------------------------------
# scene geometry
# --------------------------------------------------------------------------

def cathedral_polys(s):
    """Silhouette parts. Coordinates in the 1600x900 space, scaled by s."""
    def P(pts):
        return [(x * s, y * s) for x, y in pts]

    base = 520
    parts = []
    # outer towers, flanking towers, central keep
    for x0, x1, apex, top in (
        (958, 1002, 980, 266), (1300, 1344, 1322, 254),
        (1004, 1064, 1034, 214), (1244, 1304, 1274, 202),
    ):
        parts.append(P([(x0, top), (apex, top - 62), (x1, top),
                        (x1, base), (x0, base)]))
    parts.append(P([(1096, 150), (1138, 42), (1180, 150),
                    (1180, base), (1096, base)]))
    # main hall with crenellated top
    cren = [(1064, 330)]
    x = 1064
    up = True
    while x < 1244:
        cren.append((x, 308 if up else 330))
        x += 18
        cren.append((x, 308 if up else 330))
        up = not up
    cren += [(1244, 330), (1244, base), (1064, base)]
    parts.append(P(cren))
    return parts


ISLANDS = [
    # (points in 1600x900 space, depth 0=near .. 2=far)
    ([(918, 512), (988, 498), (1064, 508), (1140, 494), (1216, 506),
      (1292, 496), (1372, 510), (1350, 558), (1362, 600), (1306, 618),
      (1290, 672), (1240, 650), (1216, 714), (1168, 664), (1128, 706),
      (1086, 654), (1042, 694), (1004, 642), (964, 666), (940, 606),
      (914, 556)], 1),
    ([(548, 592), (628, 576), (708, 588), (790, 572), (872, 586), (936, 576),
      (918, 626), (930, 670), (878, 690), (862, 746), (812, 724), (788, 790),
      (740, 738), (700, 774), (658, 720), (616, 756), (580, 700),
      (552, 644)], 0),
    ([(40, 640), (118, 624), (200, 634), (282, 620), (364, 632), (446, 622),
      (520, 638), (500, 686), (512, 728), (458, 748), (440, 804), (390, 780),
      (358, 842), (314, 790), (276, 818), (234, 766), (192, 794), (152, 740),
      (114, 758), (82, 704), (46, 682)], 0),
    ([(1420, 520), (1478, 506), (1546, 514), (1600, 504), (1600, 640),
      (1580, 660), (1566, 714), (1524, 688), (1500, 744), (1462, 692),
      (1430, 720), (1408, 656)], 2),
    ([(624, 452), (668, 442), (706, 452), (692, 480), (664, 496),
      (636, 478)], 2),
    ([(842, 470), (876, 462), (900, 472), (888, 494), (862, 502),
      (844, 488)], 2),
    ([(400, 502), (436, 494), (462, 504), (448, 526), (420, 532),
      (404, 518)], 2),
]

MARKER = [
    [(96, 168), (326, 118), (372, 250), (142, 306)],
    [(392, 176), (512, 150), (556, 232), (520, 320), (406, 296)],
    [(244, 660), (286, 286), (324, 291), (282, 660)],
    [(186, 356), (394, 384), (388, 424), (180, 396)],
]


def scaled(pts, s):
    return [(x * s, y * s) for x, y in pts]


# --------------------------------------------------------------------------
# render
# --------------------------------------------------------------------------

def render(scale=1.0):
    w, h = int(W * scale), int(H * scale)
    s = w / 1600.0
    size = (w, h)

    # --- sky: near-black is the ground state, ember only near the source --
    img = vgrad(w, h, [
        (0.00, (7, 4, 6)),
        (0.30, (14, 8, 9)),
        (0.58, (20, 10, 10)),
        (1.00, (5, 3, 4)),
    ])

    # --- weather: fractal cloud, tinted and screened in -------------------
    cloud = fractal_noise(w // 2, h // 2, octaves=6, seed=11, base=3)
    cloud = cloud.resize(size, Image.BICUBIC).filter(ImageFilter.GaussianBlur(w / 400))
    cloud = cloud.point(lambda v: max(0, v - 120) * 2)
    band = radial_mask(w, h, 0.66, 0.16, 0.72, falloff=1.8)
    cloud = ImageChops.multiply(cloud, band)
    img = screen(img, tinted(cloud, (74, 24, 20), size).point(lambda v: int(v * 0.5)))

    # --- the eclipse ------------------------------------------------------
    halo = radial_mask(w, h, ORB[0], ORB[1], ORB_R * 3.2, falloff=3.0)
    img = screen(img, tinted(halo, (118, 20, 12), size).point(lambda v: int(v * 0.8)))

    cx, cy, r = ORB[0] * w, ORB[1] * h, ORB_R * w
    orb = Image.new("L", size, 0)
    ImageDraw.Draw(orb).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    orb = orb.filter(ImageFilter.GaussianBlur(w / 1100))

    disc = radial_ramp(size, cx, cy, r, [
        (0.00, (255, 208, 168)),
        (0.30, (255, 122, 70)),
        (0.62, (222, 40, 18)),
        (0.86, (140, 14, 8)),
        (1.00, (255, 128, 74)),   # limb brightening at the very edge
    ])
    img = Image.composite(disc, img, orb)

    # a hot filament right on the rim
    ring = Image.new("L", size, 0)
    ImageDraw.Draw(ring).ellipse([cx - r, cy - r, cx + r, cy + r],
                                 outline=255, width=max(int(w / 500), 2))
    img = screen(img, tinted(ring.filter(ImageFilter.GaussianBlur(w / 900)),
                             CORE, size))

    # --- lightning clawing across the disc -------------------------------
    bolt = Image.new("L", size, 0)
    bd = ImageDraw.Draw(bolt)
    for path in (
        [(1002, 84), (1032, 124), (1008, 136), (1042, 182), (1024, 190)],
        [(1372, 118), (1342, 154), (1368, 168), (1340, 218)],
        [(1300, 30), (1320, 62), (1302, 72), (1326, 108)],
    ):
        bd.line([(x * s, y * s) for x, y in path],
                fill=255, width=max(int(2.4 * s), 2), joint="curve")
    img = screen(img, tinted(bolt, (255, 226, 204), size))
    img = screen(img, tinted(bolt.filter(ImageFilter.GaussianBlur(w / 220)),
                             (170, 52, 26), size))

    # --- distant ranges: each plane hazier than the one in front ---------
    for idx, (top, tint, haze) in enumerate((
        (0.60, (30, 17, 17), 0.46),
        (0.68, (20, 11, 12), 0.30),
    )):
        ridge = Image.new("L", size, 0)
        rd = ImageDraw.Draw(ridge)
        rng = random.Random(2200 + idx * 31)
        pts = [(0, h)]
        x = 0.0
        y = top * h
        while x < w:
            x += rng.uniform(0.018, 0.055) * w
            y = top * h + rng.uniform(-0.075, 0.055) * h
            pts.append((x, y))
        pts.append((w, h))
        rd.polygon(pts, fill=255)
        ridge = ridge.filter(ImageFilter.GaussianBlur(w / 900 + idx * w / 700))

        rock = Image.new("RGB", size, tint)
        tex = fractal_noise(w // 4, h // 4, octaves=4, seed=511 + idx * 17,
                            base=6).resize(size, Image.BICUBIC)
        rock = ImageChops.multiply(rock, Image.merge("RGB", (tex, tex, tex))
                                   .point(lambda v: 150 + v // 2))
        img = Image.composite(rock, img, ridge)

        crest = ImageChops.subtract(
            ridge.filter(ImageFilter.GaussianBlur(w / 700)), ridge)
        crest = ImageChops.multiply(crest, radial_mask(w, h, ORB[0], ORB[1],
                                                       ORB_R * 5.5, 0.8))
        img = screen(img, tinted(crest, (172, 74, 46), size))
        img = screen(img, tinted(ridge.filter(ImageFilter.GaussianBlur(w / 70)),
                                 (46, 20, 18), size)
                     .point(lambda v, a=haze: int(v * a)))

    # --- cathedral, backlit ----------------------------------------------
    mass = Image.new("L", size, 0)
    md = ImageDraw.Draw(mass)
    for poly in cathedral_polys(s):
        md.polygon(poly, fill=255)
    mass = mass.filter(ImageFilter.GaussianBlur(w / 2400))

    # Backlit stone is not pure black: it catches a little bounce from the
    # disc, and that residual detail is what separates a rendered mass from
    # a cut-out silhouette.
    stone = vgrad(w, h, [(0.0, (62, 32, 30)), (0.5, (34, 18, 18)), (1.0, (14, 8, 10))])
    grain = fractal_noise(w // 3, h // 3, octaves=5, seed=41, base=6)
    grain = grain.resize(size, Image.BICUBIC)
    stone = ImageChops.multiply(stone, Image.merge("RGB", (grain, grain, grain))
                                .point(lambda v: 110 + int(v * 0.66)))
    # bounce falls off with distance from the source
    stone = screen(stone, tinted(
        radial_mask(w, h, ORB[0], ORB[1], ORB_R * 3.4, 1.6),
        (52, 20, 14), size).point(lambda v: int(v * 0.55)))
    img = Image.composite(stone, img, mass)

    # rim: the edge of the mass, lit only where it interrupts the disc.
    # Two widths — a tight hot filament and a wider soft falloff.
    for radius, colour, gain in ((w / 900, CORE, 1.0), (w / 260, EMBER, 0.65)):
        rim = ImageChops.subtract(
            mass.filter(ImageFilter.GaussianBlur(radius)), mass)
        rim = ImageChops.multiply(
            rim, radial_mask(w, h, ORB[0], ORB[1], ORB_R * 3.0, 0.9))
        img = screen(img, tinted(rim, colour, size)
                     .point(lambda v, g=gain: int(v * g)))

    # lit windows and the rose
    glow = Image.new("L", size, 0)
    gd = ImageDraw.Draw(glow)
    for x, y, rr in ((1154, 392, 34),):
        gd.ellipse([(x - rr) * s, (y - rr) * s, (x + rr) * s, (y + rr) * s], fill=210)
    for x, y in ((1082, 452), (1116, 452), (1174, 452), (1208, 452),
                 (1024, 300), (1024, 384), (1266, 288), (1266, 372),
                 (1130, 246), (970, 360), (1312, 348)):
        gd.rounded_rectangle([x * s, y * s, (x + 18) * s, (y + 34) * s],
                             radius=9 * s, fill=190)
    img = screen(img, tinted(glow.filter(ImageFilter.GaussianBlur(w / 1400)),
                             (255, 150, 96), size))
    img = screen(img, tinted(glow.filter(ImageFilter.GaussianBlur(w / 180)),
                             (150, 60, 30), size))

    # --- floating islands, far planes hazier -----------------------------
    for pts, depth in sorted(ISLANDS, key=lambda p: -p[1]):
        m = Image.new("L", size, 0)
        ImageDraw.Draw(m).polygon(scaled(pts, s), fill=255)
        m = m.filter(ImageFilter.GaussianBlur(w / 2200 + depth * w / 1400))

        # Bright enough that its texture survives the vignette. Flat black
        # rock is the difference between a silhouette and a rendered mass.
        rock = vgrad(w, h, [(0.0, (78, 44, 40)), (0.42, (40, 22, 22)),
                            (1.0, (12, 7, 9))])
        tex = fractal_noise(w // 3, h // 3, octaves=5, seed=97 + depth * 13, base=5)
        tex = tex.resize(size, Image.BICUBIC)
        rock = ImageChops.multiply(rock, Image.merge("RGB", (tex, tex, tex))
                                   .point(lambda v: 96 + int(v * 0.72)))
        img = Image.composite(rock, img, m)

        for radius, colour, gain in ((w / 1000, (255, 170, 128), 1.0),
                                     (w / 300, (198, 84, 52), 0.6)):
            edge = ImageChops.subtract(
                m.filter(ImageFilter.GaussianBlur(radius)), m)
            edge = ImageChops.multiply(edge, radial_mask(w, h, ORB[0], ORB[1],
                                                         ORB_R * 4.6, 0.9))
            img = screen(img, tinted(edge, colour, size)
                         .point(lambda v, g=gain: int(v * g * (1 - depth * 0.24))))

        # atmosphere sits in front of every distant plane
        if depth:
            img = screen(img, tinted(
                m.filter(ImageFilter.GaussianBlur(w / 90)),
                (44, 18, 16), size).point(lambda v: int(v * 0.26 * depth)))

    # --- marker ----------------------------------------------------------
    mm = Image.new("L", size, 0)
    for poly in MARKER:
        ImageDraw.Draw(mm).polygon(scaled(poly, s), fill=255)
    mm = mm.filter(ImageFilter.GaussianBlur(w / 2400))
    timber = vgrad(w, h, [(0.0, (34, 18, 18)), (1.0, (10, 6, 8))])
    wt = fractal_noise(w // 4, h // 4, octaves=4, seed=303, base=8).resize(size, Image.BICUBIC)
    timber = ImageChops.multiply(timber, Image.merge("RGB", (wt, wt, wt))
                                 .point(lambda v: 130 + v // 3))
    img = Image.composite(timber, img, mm)
    medge = ImageChops.subtract(mm.filter(ImageFilter.GaussianBlur(w / 1100)), mm)
    medge = ImageChops.multiply(medge, radial_mask(w, h, ORB[0], ORB[1], ORB_R * 5.0, 0.9))
    img = screen(img, tinted(medge, (172, 84, 60), size).point(lambda v: int(v * 0.7)))

    # --- embers, with bloom ----------------------------------------------
    em = Image.new("L", size, 0)
    ed = ImageDraw.Draw(em)
    rng = random.Random(7)
    for _ in range(46):
        x = rng.uniform(0.04, 0.98) * w
        y = rng.uniform(0.30, 0.92) * h
        rr = rng.uniform(1.0, 2.9) * scale
        ed.ellipse([x - rr, y - rr, x + rr, y + rr],
                   fill=rng.randrange(120, 235))
    img = screen(img, tinted(em, (255, 150, 92), size))
    img = screen(img, tinted(em.filter(ImageFilter.GaussianBlur(w / 260)),
                             (120, 44, 24), size))

    # --- drifting haze in front of the middle distance -------------------
    for seed, y0, y1, strength, blur in ((71, 0.44, 0.70, 0.34, 60),
                                         (83, 0.62, 0.94, 0.26, 44)):
        fog = fractal_noise(w // 3, h // 3, octaves=5, seed=seed, base=4)
        fog = fog.resize(size, Image.BICUBIC).point(lambda v: max(0, v - 118) * 2)
        band = vgrad(w, h, [(0.0, (0, 0, 0)), (y0, (0, 0, 0)),
                            ((y0 + y1) / 2, (255, 255, 255)),
                            (y1, (0, 0, 0)), (1.0, (0, 0, 0))]).convert("L")
        fog = ImageChops.multiply(fog, band)
        fog = fog.filter(ImageFilter.GaussianBlur(w / blur))
        img = screen(img, tinted(fog, (72, 32, 26), size)
                     .point(lambda v, a=strength: int(v * a)))

    # --- global: bloom, vignette, grain ----------------------------------
    bright = img.convert("L").point(lambda v: max(0, v - 128) * 2)
    img = screen(img, tinted(bright.filter(ImageFilter.GaussianBlur(w / 120)),
                             (108, 38, 22), size))

    vig = radial_mask(w, h, 0.5, 0.46, 0.92, falloff=1.1)
    vig = vig.point(lambda v: 70 + int(v * 0.72))
    img = ImageChops.multiply(img, Image.merge("RGB", (vig, vig, vig)))

    g = value_noise(w // 2, h // 2, w // 2, 5150).resize(size, Image.NEAREST)
    g = g.point(lambda v: 118 + (v - 128) // 5)
    img = ImageChops.multiply(img, Image.merge("RGB", (g, g, g)) \
                              .point(lambda v: min(255, v + 132)))

    return img


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=float, default=1.0)
    args = ap.parse_args()
    out = render(args.scale)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.save(OUT, "PNG", optimize=True)
    print(f"wrote {OUT.relative_to(ROOT)}  {out.size[0]}x{out.size[1]}  "
          f"{OUT.stat().st_size // 1024} KB")
