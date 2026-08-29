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


def m_motes(p, rng, c, n=110, twinkle=0.0):
    """twinkle is the fraction that animates. Deliberately a fraction and not
    all of them: a field where every point pulses reads as noise, and these
    are opacity animations on individual SVG children, which the compositor
    does not accelerate. A third of them moving is the effect; all of them
    moving is a cost."""
    p.append(f'<g fill="{c["hi"]}">')
    for _ in range(n):
        base = f'cx="{f(rng.uniform(0, W))}" cy="{f(rng.uniform(0.02, 0.98) * H)}" '\
               f'r="{rng.uniform(1, 2.8):.1f}"'
        if rng.random() < twinkle:
            p.append(f'<circle {base} class="mo-twinkle" style="'
                     f'--dur:{rng.uniform(1.8, 6.5):.1f}s;'
                     f'--delay:-{rng.uniform(0, 6):.1f}s"/>')
        else:
            p.append(f'<circle {base} opacity="{rng.uniform(0.2, 0.85):.2f}"/>')
    p.append("</g>")



# --------------------------------------------------- motifs from the writing
# Each of these exists because Baylor's commentary named something specific
# that the generic motif library could not draw.

def m_tornado(p, rng, c, cx=0.5, w=0.3, turns=17):
    """Black Blizzard: a minimalist funnel, drawn only as its edges."""
    x = cx * W
    for i in range(turns):
        t = i / (turns - 1)
        y = H * (0.06 + 0.92 * t)
        rx = w * W * (0.16 + 0.84 * (1 - t) ** 1.7)
        ry = rx * 0.22
        off = math.sin(t * 7.0) * rx * 0.22
        p.append(f'<ellipse cx="{f(x + off)}" cy="{f(y)}" rx="{f(rx)}" '
                 f'ry="{f(ry)}" fill="none" stroke="{c["hi"]}" '
                 f'stroke-width="{f(1.4 + 3.4 * (1 - t))}" '
                 f'opacity="{f(0.3 + 0.62 * (1 - t))}"/>')
    # debris caught in the draught
    for _ in range(70):
        t = rng.random()
        y = H * (0.06 + 0.92 * t)
        rx = w * W * (0.16 + 0.84 * (1 - t) ** 1.7)
        x2 = x + math.sin(t * 7.0) * rx * 0.22 + rng.uniform(-rx, rx)
        p.append(f'<rect x="{f(x2)}" y="{f(y + rng.uniform(-14, 14))}" '
                 f'width="{f(rng.uniform(2, 7))}" height="{f(rng.uniform(1, 3))}" '
                 f'fill="{c["hi"]}" opacity="{f(rng.uniform(0.15, 0.7))}" '
                 f'transform="rotate({rng.uniform(-30, 30):.0f} {f(x2)} {f(y)})"/>')


def m_glitch(p, rng, c, rows=26):
    """Killbot: torn scanline displacement, warning bars, false pathways."""
    for _ in range(rows):
        y = rng.uniform(0, H)
        h = rng.uniform(3, 26)
        x = rng.uniform(-100, W * 0.5)
        w = rng.uniform(W * 0.25, W * 1.1)
        col = rng.choice([c["a1"], c["a2"], c["hi"]])
        p.append(f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" '
                 f'fill="{col}" opacity="{f(rng.uniform(0.06, 0.3))}"/>')
    for _ in range(7):  # hazard chevrons
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        s = rng.uniform(26, 70)
        p.append(f'<path d="M{f(x)} {f(y)} l{f(s)} {f(s * 0.6)} l{f(-s)} '
                 f'{f(s * 0.6)}" fill="none" stroke="{c["hi"]}" '
                 f'stroke-width="4" opacity="{f(rng.uniform(0.25, 0.6))}"/>')


def m_eye(p, rng, c, cx=0.5, cy=0.44, r=0.2):
    """Ocular Miracle: an iris, ringed and lashed with light."""
    x, y, rr = cx * W, cy * H, r * W
    p.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(rr * 2.4)}" fill="url(#g-halo)"/>')
    p.append(f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(rr * 1.9)}" ry="{f(rr)}" '
             f'fill="none" stroke="{c["a1"]}" stroke-width="5" opacity="0.75"/>')
    p.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(rr * 0.72)}" fill="url(#g-orb)"/>')
    for i in range(56):  # iris fibres
        ang = i / 56 * math.tau
        r0, r1 = rr * 0.3, rr * 0.72 * rng.uniform(0.8, 1.0)
        p.append(f'<line x1="{f(x + math.cos(ang) * r0)}" '
                 f'y1="{f(y + math.sin(ang) * r0)}" '
                 f'x2="{f(x + math.cos(ang) * r1)}" '
                 f'y2="{f(y + math.sin(ang) * r1)}" stroke="{c["hi"]}" '
                 f'stroke-width="1.3" opacity="{f(rng.uniform(0.15, 0.6))}"/>')
    p.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(rr * 0.26)}" fill="{c["deep"]}"/>')


def m_vines(p, rng, c, n=22):
    """The Golden: overgrowth closing in from every edge.

    Baylor's line is "suffocating, deeply overgrown", so this frames the
    centre rather than scattering. Spawning points walk the perimeter in
    order instead of picking a side at random, which left one seed with
    almost every vine on the left and two-thirds of the frame empty.
    """
    for i in range(n):
        t = i / n
        edge = i % 4
        if edge == 0:                       # top
            x0, y0, ang = rng.uniform(0, W), -40, math.pi / 2
        elif edge == 1:                     # right
            x0, y0, ang = W + 40, rng.uniform(0, H), math.pi
        elif edge == 2:                     # bottom
            x0, y0, ang = rng.uniform(0, W), H + 40, -math.pi / 2
        else:                               # left
            x0, y0, ang = -40, rng.uniform(0, H), 0.0
        ang += rng.uniform(-0.5, 0.5)

        x, y = x0, y0
        d = [f"M{f(x)} {f(y)}"]
        pts = [(x, y)]
        for _ in range(rng.randint(4, 7)):
            step = rng.uniform(80, 190)
            ang += rng.uniform(-0.55, 0.55)
            x += math.cos(ang) * step
            y += math.sin(ang) * step
            d.append(f"L{f(x)} {f(y)}")
            pts.append((x, y))
        p.append(f'<path d="{" ".join(d)}" fill="none" stroke="{c["a1"]}" '
                 f'stroke-width="{f(rng.uniform(2.0, 5.5))}" '
                 f'stroke-linecap="round" stroke-linejoin="round" '
                 f'opacity="{f(rng.uniform(0.28, 0.7))}"/>')

        for (lx, ly) in pts[1:]:            # leaves along the run
            for _ in range(rng.randint(1, 3)):
                ox, oy = lx + rng.uniform(-26, 26), ly + rng.uniform(-26, 26)
                p.append(f'<ellipse cx="{f(ox)}" cy="{f(oy)}" '
                         f'rx="{f(rng.uniform(7, 20))}" '
                         f'ry="{f(rng.uniform(3, 8))}" '
                         f'fill="{rng.choice([c["a1"], c["a2"]])}" '
                         f'opacity="{f(rng.uniform(0.18, 0.5))}" '
                         f'transform="rotate({rng.uniform(0, 180):.0f} '
                         f'{f(ox)} {f(oy)})"/>')


def m_duals(p, rng, c, n=9):
    """Codependence: paired icons, always two, never quite symmetrical."""
    for i in range(n):
        t = (i + 0.5) / n
        x = t * W
        yt = H * (0.3 + 0.12 * math.sin(t * 6))
        yb = H * (0.7 - 0.12 * math.sin(t * 6 + 1.3))
        s = rng.uniform(14, 26)
        for y, col in ((yt, c["a1"]), (yb, c["a2"])):
            p.append(f'<rect x="{f(x - s / 2)}" y="{f(y - s / 2)}" width="{f(s)}" '
                     f'height="{f(s)}" fill="none" stroke="{col}" stroke-width="3" '
                     f'opacity="0.85" transform="rotate(45 {f(x)} {f(y)})"/>')
        p.append(f'<line x1="{f(x)}" y1="{f(yt)}" x2="{f(x)}" y2="{f(yb)}" '
                 f'stroke="{c["hi"]}" stroke-width="1.2" opacity="0.2" '
                 'stroke-dasharray="4 7"/>')


def m_speedlines(p, rng, c, n=60):
    """Subsonic: everything smeared by velocity."""
    for _ in range(n):
        y = rng.uniform(0, H)
        w = rng.uniform(90, 620)
        x = rng.uniform(-200, W)
        p.append(f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" '
                 f'height="{f(rng.uniform(1, 4))}" '
                 f'fill="{rng.choice([c["a1"], c["a2"], c["hi"]])}" '
                 f'opacity="{f(rng.uniform(0.1, 0.55))}"/>')


def m_nebula(p, rng, c, n=9):
    """Andromeda: gas, not geometry."""
    for _ in range(n):
        cx, cy = rng.uniform(0, W), rng.uniform(0, H * 0.85)
        p.append(f'<ellipse cx="{f(cx)}" cy="{f(cy)}" rx="{f(rng.uniform(120, 380))}" '
                 f'ry="{f(rng.uniform(60, 190))}" '
                 f'fill="{rng.choice([c["a1"], c["a2"]])}" '
                 f'opacity="{f(rng.uniform(0.05, 0.16))}" filter="url(#g-soft)" '
                 f'transform="rotate({rng.uniform(-40, 40):.0f} {f(cx)} {f(cy)})"/>')


def m_blade(p, rng, c, n=5):
    """Edge of Destiny: long light blades sweeping the frame."""
    for i in range(n):
        x = W * (0.1 + 0.2 * i) + rng.uniform(-60, 60)
        ln = rng.uniform(H * 0.5, H * 1.15)
        wd = rng.uniform(10, 34)
        ang = rng.uniform(-26, 26)
        p.append(f'<g transform="rotate({ang:.1f} {f(x)} {f(H/2)})">'
                 f'<rect x="{f(x - wd/2)}" y="{f(H/2 - ln/2)}" width="{f(wd)}" '
                 f'height="{f(ln)}" fill="url(#g-blade)" opacity="0.75"/>'
                 f'<rect x="{f(x - 1)}" y="{f(H/2 - ln/2)}" width="2" '
                 f'height="{f(ln)}" fill="{c["hi"]}" opacity="0.6"/></g>')



# ------------------------------------------------------------- atmosphere
# Applied to every level in this tier. The motifs were reading as flat
# shapes pasted on a gradient; these three passes give the frame depth
# behind, light through, and grit in front of the subject.

def haze(p, rng, c, n=8):
    """Soft coloured fog behind the subject, so the background has volume."""
    p.append('<g filter="url(#g-soft)">')
    for _ in range(n):
        cx, cy = rng.uniform(-100, W + 100), rng.uniform(0, H)
        p.append(f'<ellipse cx="{f(cx)}" cy="{f(cy)}" '
                 f'rx="{f(rng.uniform(160, 460))}" ry="{f(rng.uniform(80, 240))}" '
                 f'fill="{rng.choice([c["a1"], c["a2"], c["bg1"]])}" '
                 f'opacity="{f(rng.uniform(0.05, 0.15))}"/>')
    p.append("</g>")


def shafts(p, rng, c, n=5):
    """Volumetric light falling through the frame."""
    p.append('<g filter="url(#g-soft)" opacity="0.5">')
    for _ in range(n):
        x = rng.uniform(0, W)
        top = rng.uniform(-120, 60)
        wtop = rng.uniform(30, 110)
        wbot = wtop * rng.uniform(1.6, 3.4)
        drift = rng.uniform(-160, 160)
        p.append(f'<path d="M{f(x - wtop/2)} {f(top)} L{f(x + wtop/2)} {f(top)} '
                 f'L{f(x + drift + wbot/2)} {f(H + 60)} '
                 f'L{f(x + drift - wbot/2)} {f(H + 60)} Z" '
                 f'fill="{c["hi"]}" opacity="{f(rng.uniform(0.04, 0.11))}"/>')
    p.append("</g>")


def dust(p, rng, c, n=90):
    """Foreground particles, larger and softer than the mid-ground motes so
    the frame reads as having a near plane."""
    for _ in range(n):
        r = rng.uniform(1.2, 5.5)
        near = r > 3.6
        p.append(f'<circle cx="{f(rng.uniform(0, W))}" cy="{f(rng.uniform(0, H))}" '
                 f'r="{f(r)}" fill="{rng.choice([c["hi"], c["a1"], c["a2"]])}" '
                 f'opacity="{f(rng.uniform(0.06, 0.2) if near else rng.uniform(0.2, 0.6))}"'
                 f'{" filter=\"url(#g-soft)\"" if near else ""}/>')



# ----------------------------------------------------------------- motion
# The hero SVG is inlined into the page, so the artwork can be animated as
# elements rather than as a picture. These emit the .mo-* hooks that
# src/css/art.css drives; the timing rides along in a style attribute so one
# keyframe serves every instance at its own speed and phase.


def wrap(p, start, motion):
    """Wrap everything appended since index `start` in an animated group.

    The wrapper is bare on purpose. Almost every motif emits
    <g transform="translate(x y)">, and a CSS transform property beats a
    presentation attribute outright -- animating those groups directly threw
    them to the origin. Wrapping leaves the positioning attribute untouched
    and animates a parent that has none.
    """
    cls = motion["cls"]
    style = ";".join(f"--{k}:{v}" for k, v in motion.items() if k != "cls")
    p.insert(start, f'<g class="{cls}"{f" style={style!r}" if style else ""}>')
    p.append("</g>")



def page_field(slug, fallback):
    """The --field the page will actually render on.

    The band has to be painted in this, not in the art's own deep colour.
    They are usually close, but Freedom08 has pale cream art on a dark navy
    page, and a band in the art's colour left its title at 1.78:1."""
    import json
    for jf in (ROOT / "data" / "levels").glob("*.json"):
        rec = json.loads(jf.read_text(encoding="utf-8"))
        if rec["slug"] == slug:
            return rec["theme"]["palette"].get("field") or fallback
    return fallback


def band(p, rng, c, strength=0.62, colour=None):
    """A soft full-width haze across the middle of the frame.

    The hero title sits here. This used to be a CSS scrim painted over the
    finished art, which read as a dark ellipse stuck on top of the picture.
    Baked into the art instead, edge to edge and fading out over most of the
    frame height, it reads as depth rather than as an overlay -- and it is
    part of the composition, so nothing has to sit above the artwork.
    """
    col = colour or c["deep"]
    top = H * 0.24
    height = H * 0.52
    p.append(f'<linearGradient id="g-band" x1="0" y1="0" x2="0" y2="1">'
             f'<stop offset="0%" stop-color="{col}" stop-opacity="0"/>'
             f'<stop offset="34%" stop-color="{col}" '
             f'stop-opacity="{strength:.2f}"/>'
             f'<stop offset="66%" stop-color="{col}" '
             f'stop-opacity="{strength:.2f}"/>'
             f'<stop offset="100%" stop-color="{col}" stop-opacity="0"/>'
             "</linearGradient>")
    p.append(f'<rect x="0" y="{f(top)}" width="{W}" height="{f(height)}" '
             'fill="url(#g-band)"/>')


MOTIFS = {
    "orb": m_orb, "burst": m_burst, "wheel": m_wheel, "gears": m_gears,
    "slabs": m_slabs, "tris": m_tris, "net": m_net, "chains": m_chains,
    "beam": m_beam, "zigzag": m_zigzag, "peaks": m_peaks,
    "columns": m_columns, "swirl": m_swirl, "skull": m_skull,
    "sigils": m_sigils, "sparks": m_sparks, "confetti": m_confetti,
    "motes": m_motes,
    # drawn for what the commentary actually describes
    "tornado": m_tornado, "glitch": m_glitch, "eye": m_eye, "vines": m_vines,
    "duals": m_duals, "speedlines": m_speedlines, "nebula": m_nebula,
    "blade": m_blade,
}


# ---------------------------------------------------------------- configs
# c: bg deep/mid, a1/a2 accents, hi highlight. Motifs run in order given.

LEVELS = {
    "freedom08": dict(
        # The palest art on the site sits on a dark navy page, so its haze
        # has to work harder than anyone else's to carry a light title.
        seed=11, band=0.88, label="Pale columns, chained banners and drifting petals in cream and lavender",
        c=dict(bg1="#e9e6f5", bg2="#cfd3ee", deep="#8f93c8", a1="#b9a6e8",
               a2="#7fb4ee", hi="#fffdf2"), light=True,
        motifs=[("columns", {}), ("tris", dict(n=12)),
                ("sparks", dict(n=5), dict(cls="mo-breathe", dur="6.5s")),
                ("motes", dict(n=70, twinkle=0.34))]),
    "idols": dict(
        seed=12, label="Saturated rainbow burst with gears and neon shards",
        c=dict(bg1="#3a0a5e", bg2="#12042c", deep="#0a0220", a1="#ff3ce0",
               a2="#3cf0ff", hi="#ffe94d"),
        motifs=[("burst", dict(cx=0.55, cy=0.36, n=26),
                 dict(cls="mo-spin", dur="150s")),
                ("slabs", dict(n=4)),
                ("gears", dict(n=3), dict(cls="mo-spin-r", dur="70s")),
                ("tris", dict(n=18)), ("motes", dict(twinkle=0.4))]),
    "subsonic": dict(
        seed=13, label="Magenta and cyan light smeared into speed lines over wireframe boxes",
        c=dict(bg1="#1b0a3e", bg2="#0a0420", deep="#050213", a1="#ff4de0",
               a2="#4de0ff", hi="#f0e6ff"),
        motifs=[("speedlines", dict(n=70),
                 dict(cls="mo-drift", dur="7s", dx=190, dy=0)),
                ("slabs", dict(n=5)),
                ("gears", dict(n=3), dict(cls="mo-spin", dur="26s")),
                ("tris", dict(n=10)), ("motes", dict(twinkle=0.3))]),
    "codependence": dict(
        seed=14, label="A frame split red above and cyan below, with paired icons strung between",
        c=dict(bg1="#4a0510", bg2="#02181f", deep="#050b12", a1="#ff2a3c",
               a2="#2ae0ff", hi="#ffffff"), split=True,
        motifs=[("duals", dict(n=9), dict(cls="mo-bob", dur="7s", dy=22)),
                ("gears", dict(n=4), dict(cls="mo-spin", dur="60s")),
                ("tris", dict(n=14)), ("motes", dict(twinkle=0.3))]),
    "zodiac": dict(
        seed=15, label="A neon astrological wheel over a deep violet starfield",
        c=dict(bg1="#241243", bg2="#0d0620", deep="#070313", a1="#6b7cff",
               a2="#ff6bd0", hi="#eae6ff"),
        motifs=[("wheel", dict(cx=0.5, cy=0.24, r=0.38, marks=12),
                 dict(cls="mo-spin", dur="110s")),
                ("wheel", dict(cx=0.5, cy=0.92, r=0.34, marks=12),
                 dict(cls="mo-spin-r", dur="76s")),
                ("motes", dict(n=150, twinkle=0.42))]),
    "bloodlust": dict(
        seed=16, label="A pixelated blood orb behind horned skulls and pentagram sigils",
        c=dict(bg1="#3a0304", bg2="#120102", deep="#0a0001", a1="#ff1414",
               a2="#ff5a2a", hi="#ffd6d6"),
        motifs=[("orb", dict(cx=0.5, cy=0.42, r=0.28),
                 dict(cls="mo-breathe", dur="2.6s", **{"from": 0.97, "to": 1.04})),
                ("sigils", dict(n=4), dict(cls="mo-spin-r", dur="180s")),
                ("skull", dict(cx=0.12, cy=0.78, s=0.7)),
                ("skull", dict(cx=0.88, cy=0.78, s=0.7)),
                ("motes", dict(n=60, twinkle=0.3))]),
    "black-blizzard": dict(
        seed=17, haze=0, shafts=0, dust=40, label="A white funnel of debris turning against pure black",
        c=dict(bg1="#131417", bg2="#050506", deep="#000000", a1="#c9cdd4",
               a2="#8f959e", hi="#ffffff"),
        motifs=[("tornado", dict(cx=0.52, w=0.34),
                 dict(cls="mo-spin", dur="34s")),
                ("net", dict(n=16), dict(cls="mo-drift", dur="24s", dx=40, dy=-18)),
                ("motes", dict(n=70, twinkle=0.5))]),
    "maniacal-chains": dict(
        seed=18, label="A cyan beam through mirrored zigzags and hanging chains",
        c=dict(bg1="#04181c", bg2="#010708", deep="#000203", a1="#25e8e0",
               a2="#8ff5f0", hi="#e8fffe"),
        motifs=[("chains", dict(n=7), dict(cls="mo-bob", dur="5.5s", dy=16)),
                ("zigzag", dict(y=0.5, amp=80, rows=3),
                 dict(cls="mo-drift", dur="18s", dx=-70, dy=0)),
                ("beam", dict(y=0.5)), ("motes", dict(n=70, twinkle=0.35))]),
    "titan-complex": dict(
        seed=19, label="Crimson structures and black saw gears on deep red",
        c=dict(bg1="#4d0512", bg2="#160205", deep="#080102", a1="#ff2d5a",
               a2="#ff7a95", hi="#ffd9e2"),
        motifs=[("slabs", dict(n=5)),
                ("gears", dict(n=5, teeth=14), dict(cls="mo-spin", dur="88s")),
                ("tris", dict(n=14), dict(cls="mo-bob", dur="9s", dy=10)),
                ("motes", dict(n=60, twinkle=0.28))]),
    "firework": dict(
        seed=20, haze=3, shafts=2, dust=55, label="Chrome and crimson shards with small tech rings and sparks",
        c=dict(bg1="#2a1016", bg2="#0c0508", deep="#050203", a1="#ff2f45",
               a2="#7ad4e8", hi="#f4f6f8"),
        motifs=[("burst", dict(cx=0.5, cy=0.44, n=18, r=0.4),
                 dict(cls="mo-spin-r", dur="120s")),
                ("gears", dict(n=4), dict(cls="mo-spin", dur="54s")),
                ("tris", dict(n=16)),
                ("sparks", dict(n=6), dict(cls="mo-breathe", dur="3.4s")),
                ("motes", dict(twinkle=0.45))]),
    "andromeda": dict(
        seed=21, label="Violet and cyan gas clouds around a lit core in deep space",
        c=dict(bg1="#1a0b46", bg2="#080326", deep="#040115", a1="#7c5cff",
               a2="#3ccfff", hi="#eae6ff"),
        motifs=[("nebula", dict(n=10),
                 dict(cls="mo-drift", dur="46s", dx=70, dy=-34)),
                ("orb", dict(cx=0.66, cy=0.4, r=0.15),
                 dict(cls="mo-breathe", dur="9s")),
                ("swirl", dict(n=4), dict(cls="mo-spin", dur="200s")),
                ("motes", dict(n=170, twinkle=0.5))]),
    "the-golden": dict(
        seed=22, label="Acid-green overgrowth creeping over dark gold ridges",
        c=dict(bg1="#123312", bg2="#050f06", deep="#020703", a1="#b6ff2a",
               a2="#ffe14d", hi="#f4ffe0"),
        motifs=[("vines", dict(n=26), dict(cls="mo-bob", dur="11s", dy=9)),
                ("peaks", dict(y=0.8, amp=140)),
                ("sparks", dict(n=6), dict(cls="mo-breathe", dur="5s")),
                ("motes", dict(n=70, twinkle=0.35))]),
    "ocular-miracle": dict(
        seed=23, label="A vast lit iris ringed with light against a red starfield",
        c=dict(bg1="#0d1038", bg2="#05061a", deep="#02030c", a1="#ff2f4a",
               a2="#4a8bff", hi="#eef2ff"),
        motifs=[("eye", dict(cx=0.5, cy=0.44, r=0.2),
                 dict(cls="mo-breathe", dur="8s", **{"from": 0.97, "to": 1.03})),
                ("swirl", dict(n=5), dict(cls="mo-spin", dur="240s")),
                ("motes", dict(n=180, twinkle=0.55))]),
    "killbot": dict(
        seed=24, label="Torn scanlines and hazard chevrons breaking up a red and green frame",
        c=dict(bg1="#2a0d0d", bg2="#0a1a08", deep="#050b04", a1="#ff2020",
               a2="#3cff3c", hi="#ffe8e8"),
        motifs=[("glitch", dict(rows=30)),
                ("skull", dict(cx=0.5, cy=0.46, s=1.1),
                 dict(cls="mo-tear", dur="6.5s", sx=14)),
                ("tris", dict(n=14), dict(cls="mo-flicker", dur="4.2s")),
                ("motes", dict(n=60, twinkle=0.3))]),
    "edge-of-destiny": dict(
        seed=25, label="Blades of cyan light sweeping past a blazing core",
        c=dict(bg1="#0a1f52", bg2="#040a28", deep="#020616", a1="#2ad4ff",
               a2="#6b8cff", hi="#eafaff"),
        motifs=[("blade", dict(n=5), dict(cls="mo-drift", dur="16s", dx=90, dy=0)),
                ("orb", dict(cx=0.5, cy=0.42, r=0.16),
                 dict(cls="mo-breathe", dur="4.5s")),
                ("slabs", dict(n=4)), ("motes", dict(n=110, twinkle=0.42))]),
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
    a(f'<radialGradient id="g-corner" cx="50%" cy="46%" r="72%">'
      f'<stop offset="55%" stop-color="{c["deep"]}" stop-opacity="0"/>'
      f'<stop offset="100%" stop-color="{c["deep"]}" stop-opacity="0.72"/>'
      "</radialGradient>")
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

    haze(p, rng, c, n=cfg.get("haze", 8))
    shafts(p, rng, c, n=cfg.get("shafts", 5))

    for entry in cfg["motifs"]:
        name, kw = entry[0], entry[1]
        start = len(p)
        MOTIFS[name](p, rng, c, **kw)
        if len(entry) > 2 and entry[2]:
            wrap(p, start, entry[2])

    dust(p, rng, c, n=cfg.get("dust", 90))

    band(p, rng, c, cfg.get("band", 0.62),
         colour=page_field(slug, c["deep"]))
    a(f'<rect width="{W}" height="{H}" fill="url(#g-corner)"/>')
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
