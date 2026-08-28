#!/usr/bin/env python3
"""Generate art for the themed tier, ranks 11-25.

The bespoke tier gets a generator each. This tier shares one, driven by a
per-level config: a palette plus a list of motifs drawn from a common
library. Each config is taken from that level's own reference, so the pages
still read as themselves without ten more bespoke scripts.

Usage: python3 tools/gen_themed.py [slug ...]
Writes: src/art/<slug>.svg
"""

import math
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ART = ROOT / "src" / "art"
W, H = 1600, 900


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


# ---------------------------------------------------------------- motifs

def m_orb(p, rng, c, cx=0.68, cy=0.4, r=0.19, ring=True):
    """A large lit body: planet, sun, blast core."""
    x, y, rr = cx * W, cy * H, r * W
    p.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(rr * 2.6)}" '
             'fill="url(#g-halo)"/>')
    p.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(rr)}" fill="url(#g-orb)"/>')
    if ring:
        p.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(rr)}" fill="none" '
                 f'stroke="{c["hi"]}" stroke-width="3" opacity="0.8"/>')
        p.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(rr * 1.16)}" fill="none" '
                 f'stroke="{c["a1"]}" stroke-width="1.6" opacity="0.4"/>')


def m_burst(p, rng, c, cx=0.5, cy=0.42, n=24, r=0.6):
    """Radial blades from a point."""
    x, y = cx * W, cy * H
    p.append(f'<g transform="translate({f(x)} {f(y)})" opacity="0.5">')
    for i in range(n):
        a0 = i * math.tau / n
        a1 = a0 + math.tau / n * 0.34
        rr = r * W * (0.7 + 0.3 * (i % 3) / 2)
        p.append(f'<path d="M0 0 L{f(math.cos(a0)*rr)} {f(math.sin(a0)*rr)} '
                 f'L{f(math.cos(a1)*rr)} {f(math.sin(a1)*rr)} Z" '
                 f'fill="url(#g-blade)"/>')
    p.append("</g>")


def m_wheel(p, rng, c, cx=0.5, cy=0.3, r=0.34, marks=12):
    """A ringed dial with tick marks — zodiac wheel, gauge, orbit."""
    x, y, rr = cx * W, cy * H, r * W
    p.append(f'<g transform="translate({f(x)} {f(y)})" fill="none" '
             f'stroke="{c["a1"]}" filter="url(#g-glow)">')
    for k, sw in ((1.0, 5), (0.86, 2.4), (0.7, 3.4)):
        p.append(f'<circle r="{f(rr * k)}" stroke-width="{sw}" opacity="0.8"/>')
    p.append("</g>")
    p.append(f'<g transform="translate({f(x)} {f(y)})" stroke="{c["hi"]}" '
             'stroke-width="2.4" opacity="0.6">')
    for i in range(marks):
        a = i * math.tau / marks
        p.append(f'<path d="M{f(math.cos(a)*rr*0.86)} {f(math.sin(a)*rr*0.86)} '
                 f'L{f(math.cos(a)*rr)} {f(math.sin(a)*rr)}"/>')
    p.append("</g>")


def m_gears(p, rng, c, n=4, teeth=12):
    for _ in range(n):
        x, y = rng.uniform(0.05, 0.95) * W, rng.uniform(0.1, 0.9) * H
        r = rng.uniform(28, 62)
        p.append(f'<g transform="translate({f(x)} {f(y)})" fill="none" '
                 f'stroke="{c["a1"]}" opacity="{rng.uniform(0.25, 0.6):.2f}">')
        p.append(f'<circle r="{f(r)}" stroke-width="{f(r*0.26)}"/>')
        p.append(f'<circle r="{f(r*0.36)}" stroke-width="{f(r*0.13)}"/>')
        for i in range(teeth):
            a = i * math.tau / teeth
            p.append(f'<path d="M{f(math.cos(a)*r*1.05)} {f(math.sin(a)*r*1.05)} '
                     f'L{f(math.cos(a)*r*1.3)} {f(math.sin(a)*r*1.3)}" '
                     f'stroke-width="{f(r*0.22)}"/>')
        p.append("</g>")


def m_slabs(p, rng, c, n=5):
    """Rimmed rectangles with an inner frame — the game's basic block."""
    for _ in range(n):
        x, y = rng.uniform(0.06, 0.94) * W, rng.uniform(0.08, 0.92) * H
        w, h = rng.uniform(130, 300), rng.uniform(90, 190)
        rot = rng.uniform(-14, 14)
        p.append(f'<g transform="translate({f(x)} {f(y)}) rotate({f(rot)})" '
                 f'opacity="{rng.uniform(0.55, 0.95):.2f}">')
        p.append(f'<rect x="{f(-w/2)}" y="{f(-h/2)}" width="{f(w)}" '
                 f'height="{f(h)}" fill="url(#g-slab)"/>')
        p.append(f'<rect x="{f(-w/2)}" y="{f(-h/2)}" width="{f(w)}" '
                 f'height="{f(h)}" fill="none" stroke="{c["a1"]}" '
                 'stroke-width="6" filter="url(#g-glow)"/>')
        p.append(f'<rect x="{f(-w/2+13)}" y="{f(-h/2+13)}" width="{f(w-26)}" '
                 f'height="{f(h-26)}" fill="none" stroke="{c["hi"]}" '
                 'stroke-width="2" opacity="0.7"/>')
        p.append("</g>")


def m_tris(p, rng, c, n=18, size=(18, 54)):
    for _ in range(n):
        x, y = rng.uniform(0, W), rng.uniform(0.05, 0.95) * H
        s = rng.uniform(*size)
        col = c["a1"] if rng.random() < 0.6 else c["a2"]
        p.append(f'<path d="M{f(x)} {f(y-s)} L{f(x+s*0.85)} {f(y+s*0.6)} '
                 f'L{f(x-s*0.85)} {f(y+s*0.6)} Z" fill="none" stroke="{col}" '
                 f'stroke-width="3" opacity="{rng.uniform(0.3, 0.8):.2f}"/>')


def m_net(p, rng, c, n=26):
    """A thin polygon net — cold, sparse, structural."""
    pts = [(rng.uniform(-40, W + 40), rng.uniform(-40, H + 40)) for _ in range(n)]
    p.append(f'<g stroke="{c["hi"]}" fill="none" stroke-width="1.4">')
    for i, (x, y) in enumerate(pts):
        for x2, y2 in pts[i + 1:]:
            if math.hypot(x2 - x, y2 - y) < 260:
                p.append(f'<path d="M{f(x)} {f(y)} L{f(x2)} {f(y2)}" '
                         f'opacity="{rng.uniform(0.1, 0.45):.2f}"/>')
    p.append("</g>")


def m_chains(p, rng, c, n=5):
    for _ in range(n):
        x = rng.uniform(0.05, 0.95) * W
        links = rng.randint(4, 9)
        p.append(f'<g transform="translate({f(x)} 0)" fill="none" '
                 f'stroke="{c["hi"]}" stroke-width="6" '
                 f'opacity="{rng.uniform(0.2, 0.5):.2f}">')
        for i in range(links):
            p.append(f'<ellipse cy="{f(24 + i * 46)}" rx="12" ry="22"/>')
        p.append("</g>")


def m_beam(p, rng, c, y=0.5, h=0.02):
    """A horizontal bar of light across the frame."""
    yy, hh = y * H, h * H
    p.append(f'<rect x="0" y="{f(yy - hh * 3)}" width="{W}" height="{f(hh * 6)}" '
             f'fill="{c["a1"]}" opacity="0.16" filter="url(#g-soft)"/>')
    p.append(f'<rect x="0" y="{f(yy - hh / 2)}" width="{W}" height="{f(hh)}" '
             f'fill="url(#g-beam)" filter="url(#g-glow)"/>')


def m_zigzag(p, rng, c, y=0.5, amp=90, period=150, rows=3):
    for r_ in range(rows):
        yy = y * H + (r_ - rows / 2) * amp * 1.5
        d, x = [f"M-40 {f(yy)}"], -40
        while x < W + 60:
            d.append(f"L{f(x + period/2)} {f(yy - amp)}")
            d.append(f"L{f(x + period)} {f(yy)}")
            x += period
        p.append(f'<path d="{" ".join(d)}" fill="none" stroke="{c["a1"]}" '
                 f'stroke-width="{f(5 - r_)}" '
                 f'opacity="{0.5 - r_ * 0.13:.2f}" filter="url(#g-glow)"/>')


def m_peaks(p, rng, c, y=0.78, amp=150, fill=None, n=9):
    fill = fill or c["deep"]
    d, x = [f"M-60 {H + 60}", f"L-60 {f(y * H)}"], -60
    step = (W + 120) / n
    for i in range(n):
        d.append(f"L{f(x + step/2)} {f(y * H - amp * rng.uniform(0.5, 1.3))}")
        d.append(f"L{f(x + step)} {f(y * H + rng.uniform(-20, 30))}")
        x += step
    d.append(f"L{f(W + 60)} {H + 60} Z")
    p.append(f'<path d="{" ".join(d)}" fill="{fill}"/>')


def m_columns(p, rng, c, n=4):
    """Pale vertical pillars with capitals — Freedom08's architecture."""
    for i in range(n):
        x = (i + 0.5) / n * W + rng.uniform(-40, 40)
        w = rng.uniform(46, 74)
        p.append(f'<g opacity="0.9">')
        p.append(f'<rect x="{f(x - w/2)}" y="-20" width="{f(w)}" '
                 f'height="{H + 40}" fill="url(#g-slab)"/>')
        for yy in (0.22, 0.62):
            p.append(f'<rect x="{f(x - w*0.78)}" y="{f(yy * H)}" '
                     f'width="{f(w*1.56)}" height="26" rx="9" fill="{c["hi"]}" '
                     'opacity="0.85"/>')
        p.append(f'<g stroke="{c["a1"]}" stroke-width="2" opacity="0.5">')
        for k in range(6):
            p.append(f'<path d="M{f(x - w/2 + 8 + k*(w-16)/5)} 0 '
                     f'V{H}"/>')
        p.append("</g></g>")


def m_swirl(p, rng, c, cx=0.6, cy=0.45, n=5):
    """Nebula arcs sweeping around a point."""
    x, y = cx * W, cy * H
    for i in range(n):
        r = (0.2 + i * 0.11) * W
        a0 = rng.uniform(0, math.tau)
        sweep = rng.uniform(1.4, 2.6)
        x0, y0 = x + math.cos(a0) * r, y + math.sin(a0) * r
        x1, y1 = x + math.cos(a0 + sweep) * r, y + math.sin(a0 + sweep) * r
        col = c["a1"] if i % 2 else c["a2"]
        p.append(f'<path d="M{f(x0)} {f(y0)} A{f(r)} {f(r)} 0 0 1 {f(x1)} {f(y1)}" '
                 f'fill="none" stroke="{col}" stroke-width="{f(rng.uniform(14, 44))}" '
                 f'opacity="{rng.uniform(0.12, 0.3):.2f}" filter="url(#g-soft)"/>')


def m_skull(p, rng, c, cx=0.5, cy=0.46, s=1.0):
    """A horned skull silhouette."""
    x, y = cx * W, cy * H
    p.append(f'<g transform="translate({f(x)} {f(y)}) scale({s})" '
             f'fill="{c["deep"]}">')
    p.append('<path d="M-150 -40 a150 150 0 0 1 300 0 q6 110 -70 130 l0 60 '
             'q-80 30 -160 0 l0 -60 q-76 -20 -70 -130 Z"/>')
    p.append('<path d="M-150 -50 q-70 -110 -20 -170 q10 84 60 130 Z"/>')
    p.append('<path d="M150 -50 q70 -110 20 -170 q-10 84 -60 130 Z"/>')
    p.append("</g>")
    p.append(f'<g transform="translate({f(x)} {f(y)}) scale({s})" '
             f'fill="{c["a1"]}" opacity="0.85">')
    p.append('<ellipse cx="-64" cy="10" rx="42" ry="50"/>')
    p.append('<ellipse cx="64" cy="10" rx="42" ry="50"/>')
    p.append('<path d="M0 46 l26 54 -52 0 Z"/>')
    p.append("</g>")


def m_sigils(p, rng, c, n=3):
    """Pentagram sigils in circles."""
    for _ in range(n):
        x, y = rng.uniform(0.05, 0.95) * W, rng.uniform(0.08, 0.92) * H
        r = rng.uniform(50, 110)
        p.append(f'<g transform="translate({f(x)} {f(y)})" fill="none" '
                 f'stroke="{c["a1"]}" stroke-width="3" '
                 f'opacity="{rng.uniform(0.16, 0.4):.2f}">')
        p.append(f'<circle r="{f(r)}"/><circle r="{f(r*0.8)}" stroke-width="1.6"/>')
        pts = []
        for i in range(5):
            a = -math.pi / 2 + i * 2 * math.tau / 5
            pts.append(f"{f(math.cos(a)*r*0.8)} {f(math.sin(a)*r*0.8)}")
        p.append(f'<path d="M{" L".join(pts)} Z" stroke-linejoin="round"/>')
        p.append("</g>")


def m_sparks(p, rng, c, n=5):
    """Four-point star sparkles."""
    for _ in range(n):
        x, y = rng.uniform(0.05, 0.95) * W, rng.uniform(0.08, 0.92) * H
        s = rng.uniform(24, 60)
        p.append(f'<path d="M{f(x)} {f(y-s)} Q{f(x)} {f(y)} {f(x+s*0.42)} {f(y)} '
                 f'Q{f(x)} {f(y)} {f(x)} {f(y+s)} Q{f(x)} {f(y)} {f(x-s*0.42)} {f(y)} '
                 f'Q{f(x)} {f(y)} {f(x)} {f(y-s)} Z" fill="{c["hi"]}" '
                 f'opacity="{rng.uniform(0.5, 0.95):.2f}"/>')


def m_confetti(p, rng, c, n=70):
    """Loose blocks tumbling through the frame."""
    p.append(f'<g fill="{c["deep"]}">')
    for _ in range(n):
        x, y = rng.uniform(0, W), rng.uniform(0.03, 0.97) * H
        s = rng.uniform(7, 22)
        p.append(f'<rect x="{f(x)}" y="{f(y)}" width="{f(s)}" height="{f(s)}" '
                 f'transform="rotate({f(rng.uniform(0, 90))} {f(x)} {f(y)})" '
                 f'opacity="{rng.uniform(0.4, 0.9):.2f}"/>')
    p.append("</g>")


def m_motes(p, rng, c, n=110):
    p.append(f'<g fill="{c["hi"]}">')
    for _ in range(n):
        p.append(f'<circle cx="{f(rng.uniform(0, W))}" '
                 f'cy="{f(rng.uniform(0.02, 0.98) * H)}" '
                 f'r="{rng.uniform(1, 2.8):.1f}" '
                 f'opacity="{rng.uniform(0.2, 0.85):.2f}"/>')
    p.append("</g>")


MOTIFS = {
    "orb": m_orb, "burst": m_burst, "wheel": m_wheel, "gears": m_gears,
    "slabs": m_slabs, "tris": m_tris, "net": m_net, "chains": m_chains,
    "beam": m_beam, "zigzag": m_zigzag, "peaks": m_peaks,
    "columns": m_columns, "swirl": m_swirl, "skull": m_skull,
    "sigils": m_sigils, "sparks": m_sparks, "confetti": m_confetti,
    "motes": m_motes,
}


# ---------------------------------------------------------------- configs
# c: bg deep/mid, a1/a2 accents, hi highlight. Motifs run in order given.

LEVELS = {
    "freedom08": dict(
        seed=11, label="Pale columns, chained banners and drifting petals in cream and lavender",
        c=dict(bg1="#e9e6f5", bg2="#cfd3ee", deep="#8f93c8", a1="#b9a6e8",
               a2="#7fb4ee", hi="#fffdf2"), light=True,
        motifs=[("columns", {}), ("tris", dict(n=12)), ("sparks", dict(n=5)),
                ("motes", dict(n=70))]),
    "idols": dict(
        seed=12, label="Saturated rainbow burst with gears and neon shards",
        c=dict(bg1="#3a0a5e", bg2="#12042c", deep="#0a0220", a1="#ff3ce0",
               a2="#3cf0ff", hi="#ffe94d"),
        motifs=[("burst", dict(cx=0.55, cy=0.36, n=26)), ("slabs", dict(n=4)),
                ("gears", dict(n=3)), ("tris", dict(n=18)), ("motes", {})]),
    "subsonic": dict(
        seed=13, label="Magenta and cyan neon over wireframe boxes and gears",
        c=dict(bg1="#1b0a3e", bg2="#0a0420", deep="#050213", a1="#ff4de0",
               a2="#4de0ff", hi="#f0e6ff"),
        motifs=[("slabs", dict(n=6)), ("gears", dict(n=4)), ("tris", dict(n=14)),
                ("motes", {})]),
    "codependence": dict(
        seed=14, label="A frame split between red above and cyan below, with gears and triangles",
        c=dict(bg1="#4a0510", bg2="#02181f", deep="#050b12", a1="#ff2a3c",
               a2="#2ae0ff", hi="#ffffff"), split=True,
        motifs=[("gears", dict(n=5)), ("tris", dict(n=20)), ("slabs", dict(n=3)),
                ("motes", {})]),
    "zodiac": dict(
        seed=15, label="A neon astrological wheel over a deep violet starfield",
        c=dict(bg1="#241243", bg2="#0d0620", deep="#070313", a1="#6b7cff",
               a2="#ff6bd0", hi="#eae6ff"),
        motifs=[("wheel", dict(cx=0.5, cy=0.24, r=0.38, marks=12)),
                ("wheel", dict(cx=0.5, cy=0.92, r=0.34, marks=12)),
                ("motes", dict(n=150))]),
    "bloodlust": dict(
        seed=16, label="A pixelated blood orb behind horned skulls and pentagram sigils",
        c=dict(bg1="#3a0304", bg2="#120102", deep="#0a0001", a1="#ff1414",
               a2="#ff5a2a", hi="#ffd6d6"),
        motifs=[("orb", dict(cx=0.5, cy=0.42, r=0.28)), ("sigils", dict(n=4)),
                ("skull", dict(cx=0.12, cy=0.78, s=0.7)),
                ("skull", dict(cx=0.88, cy=0.78, s=0.7)), ("motes", dict(n=60))]),
    "black-blizzard": dict(
        seed=17, label="A thin white polygon net scattered across pure black",
        c=dict(bg1="#131417", bg2="#050506", deep="#000000", a1="#c9cdd4",
               a2="#8f959e", hi="#ffffff"),
        motifs=[("net", dict(n=30)), ("tris", dict(n=10)), ("motes", dict(n=60))]),
    "maniacal-chains": dict(
        seed=18, label="A cyan beam through mirrored zigzags and hanging chains",
        c=dict(bg1="#04181c", bg2="#010708", deep="#000203", a1="#25e8e0",
               a2="#8ff5f0", hi="#e8fffe"),
        motifs=[("chains", dict(n=7)), ("zigzag", dict(y=0.5, amp=80, rows=3)),
                ("beam", dict(y=0.5)), ("motes", dict(n=70))]),
    "titan-complex": dict(
        seed=19, label="Crimson structures and black saw gears on deep red",
        c=dict(bg1="#4d0512", bg2="#160205", deep="#080102", a1="#ff2d5a",
               a2="#ff7a95", hi="#ffd9e2"),
        motifs=[("slabs", dict(n=5)), ("gears", dict(n=5, teeth=14)),
                ("tris", dict(n=14)), ("motes", dict(n=60))]),
    "firework": dict(
        seed=20, label="Chrome and crimson shards with small tech rings and sparks",
        c=dict(bg1="#2a1016", bg2="#0c0508", deep="#050203", a1="#ff2f45",
               a2="#7ad4e8", hi="#f4f6f8"),
        motifs=[("burst", dict(cx=0.5, cy=0.44, n=18, r=0.4)),
                ("gears", dict(n=4)), ("tris", dict(n=16)), ("sparks", dict(n=6)),
                ("motes", {})]),
    "andromeda": dict(
        seed=21, label="Violet maze tubing around a white core burst in deep space",
        c=dict(bg1="#1a0b46", bg2="#080326", deep="#040115", a1="#7c5cff",
               a2="#3ccfff", hi="#eae6ff"),
        motifs=[("slabs", dict(n=5)), ("orb", dict(cx=0.52, cy=0.44, r=0.09)),
                ("burst", dict(cx=0.52, cy=0.44, n=16, r=0.28)),
                ("gears", dict(n=4)), ("motes", dict(n=120))]),
    "the-golden": dict(
        seed=22, label="Gold-green light over dark ridges with sharp star sparkles",
        c=dict(bg1="#123312", bg2="#050f06", deep="#020703", a1="#b6ff2a",
               a2="#ffe14d", hi="#f4ffe0"),
        motifs=[("peaks", dict(y=0.62, amp=210, n=7)),
                ("peaks", dict(y=0.82, amp=150, n=9)),
                ("sparks", dict(n=6)), ("tris", dict(n=12)), ("motes", dict(n=70))]),
    "ocular-miracle": dict(
        seed=23, label="A banded planet and red nebula arcs across a starfield",
        c=dict(bg1="#0d1038", bg2="#05061a", deep="#02030c", a1="#ff2f4a",
               a2="#4a8bff", hi="#eef2ff"),
        motifs=[("swirl", dict(cx=0.56, cy=0.44, n=6)),
                ("orb", dict(cx=0.44, cy=0.46, r=0.22)),
                ("motes", dict(n=200))]),
    "killbot": dict(
        seed=24, label="Clashing red and green with halftone blocks and hard shards",
        c=dict(bg1="#2a0d0d", bg2="#0a1a08", deep="#050b04", a1="#ff2020",
               a2="#3cff3c", hi="#ffe8e8"),
        motifs=[("tris", dict(n=24, size=(24, 80))), ("slabs", dict(n=4)),
                ("confetti", dict(n=90)), ("motes", dict(n=60))]),
    "edge-of-destiny": dict(
        seed=25, label="A blazing cyan core beside layered blue platforms",
        c=dict(bg1="#0a1f52", bg2="#040a28", deep="#020616", a1="#2ad4ff",
               a2="#6b8cff", hi="#eafaff"),
        motifs=[("orb", dict(cx=0.78, cy=0.46, r=0.26)),
                ("slabs", dict(n=5)), ("tris", dict(n=14)),
                ("confetti", dict(n=40)), ("motes", dict(n=90))]),
}


def build(slug, cfg):
    rng = random.Random(cfg["seed"])
    c = cfg["c"]
    p = []
    a = p.append

    a(f'<svg class="art art--{slug}" viewBox="0 0 {W} {H}" '
      'xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice" '
      f'role="img" aria-label="{cfg["label"]}">')

    a("<defs>")
    a(f'<linearGradient id="g-bg" x1="0" y1="0" x2="0.3" y2="1">'
      f'<stop offset="0%" stop-color="{c["bg1"]}"/>'
      f'<stop offset="58%" stop-color="{c["bg2"]}"/>'
      f'<stop offset="100%" stop-color="{c["deep"]}"/></linearGradient>')
    a(f'<linearGradient id="g-slab" x1="0" y1="0" x2="0.4" y2="1">'
      f'<stop offset="0%" stop-color="{c["a1"]}" stop-opacity="0.42"/>'
      f'<stop offset="100%" stop-color="{c["deep"]}" stop-opacity="0.72"/>'
      "</linearGradient>")
    a(f'<linearGradient id="g-blade" x1="0" y1="0" x2="1" y2="1">'
      f'<stop offset="0%" stop-color="{c["hi"]}" stop-opacity="0.7"/>'
      f'<stop offset="60%" stop-color="{c["a1"]}" stop-opacity="0.28"/>'
      f'<stop offset="100%" stop-color="{c["a2"]}" stop-opacity="0"/>'
      "</linearGradient>")
    a(f'<linearGradient id="g-beam" x1="0" y1="0" x2="1" y2="0">'
      f'<stop offset="0%" stop-color="{c["a1"]}" stop-opacity="0"/>'
      f'<stop offset="30%" stop-color="{c["hi"]}"/>'
      f'<stop offset="70%" stop-color="{c["a1"]}"/>'
      f'<stop offset="100%" stop-color="{c["a1"]}" stop-opacity="0"/>'
      "</linearGradient>")
    a(f'<radialGradient id="g-orb" cx="42%" cy="38%" r="62%">'
      f'<stop offset="0%" stop-color="{c["hi"]}"/>'
      f'<stop offset="38%" stop-color="{c["a1"]}"/>'
      f'<stop offset="78%" stop-color="{c["a2"]}" stop-opacity="0.7"/>'
      f'<stop offset="100%" stop-color="{c["deep"]}"/></radialGradient>')
    a(f'<radialGradient id="g-halo" cx="50%" cy="50%" r="50%">'
      f'<stop offset="0%" stop-color="{c["a1"]}" stop-opacity="0.42"/>'
      f'<stop offset="100%" stop-color="{c["a1"]}" stop-opacity="0"/>'
      "</radialGradient>")
    a(f'<linearGradient id="g-vig" x1="0" y1="0" x2="0" y2="1">'
      f'<stop offset="0%" stop-color="{c["deep"]}" stop-opacity="0.42"/>'
      f'<stop offset="26%" stop-color="{c["deep"]}" stop-opacity="0.02"/>'
      f'<stop offset="100%" stop-color="{c["deep"]}" stop-opacity="0.5"/>'
      "</linearGradient>")
    a(f'<filter id="g-glow" x="-70%" y="-70%" width="240%" height="240%">'
      '<feGaussianBlur stdDeviation="8" result="b"/>'
      f'<feFlood flood-color="{c["a1"]}" result="fc"/>'
      '<feComposite in="fc" in2="b" operator="in" result="g"/>'
      '<feMerge><feMergeNode in="g"/><feMergeNode in="g"/>'
      '<feMergeNode in="SourceGraphic"/></feMerge></filter>')
    a('<filter id="g-soft"><feGaussianBlur stdDeviation="20"/></filter>')
    a('<filter id="g-grain">'
      '<feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="4"/>'
      '<feColorMatrix type="saturate" values="0"/></filter>')
    a("</defs>")

    a(f'<rect width="{W}" height="{H}" fill="url(#g-bg)"/>')
    if cfg.get("split"):
        # Codependence is literally two halves; the art says so.
        a(f'<rect width="{W}" height="{f(H*0.52)}" fill="{c["bg1"]}" '
          'opacity="0.85"/>')
        a(f'<rect y="{f(H*0.52)}" width="{W}" height="{f(H*0.48)}" '
          f'fill="{c["bg2"]}" opacity="0.9"/>')
        a(f'<rect y="{f(H*0.5)}" width="{W}" height="{f(H*0.04)}" '
          f'fill="{c["hi"]}" opacity="0.18" filter="url(#g-soft)"/>')

    for name, kw in cfg["motifs"]:
        MOTIFS[name](p, rng, c, **kw)

    a(f'<rect width="{W}" height="{H}" fill="url(#g-vig)"/>')
    a(f'<rect width="{W}" height="{H}" filter="url(#g-grain)" '
      f'opacity="{0.08 if cfg.get("light") else 0.12}"/>')
    a("</svg>")
    return "\n".join(p) + "\n"


if __name__ == "__main__":
    want = sys.argv[1:] or list(LEVELS)
    ART.mkdir(parents=True, exist_ok=True)
    for slug in want:
        out = ART / f"{slug}.svg"
        out.write_text(build(slug, LEVELS[slug]), encoding="utf-8")
        print(f"  {slug:18} {out.stat().st_size // 1024:>3} KB")
