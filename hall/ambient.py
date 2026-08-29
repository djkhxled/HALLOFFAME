"""Ambient motion spliced into any hero artwork at build time.

The themed tier's motion is authored inside tools/gen_themed.py, because it
attaches to specific motifs — the wheel that turns is that level's wheel.
This module is for motion that attaches to nothing: shooting stars, a bar of
light crossing the frame, a scanline tearing. That kind of layer does not
need to know what it is over, so it does not need to live in a generator,
and putting it here means the ten hand-written bespoke pieces and the
landing page get it too without ten more edits.

A level opts in through theme.artAmbient in its own record. build.py splices
the result in immediately before the artwork's closing </svg>, so the layer
sits above the composition and under nothing.

Every canvas on the site is 1600x900, which is what lets one set of
coordinates serve all of them. The classes are driven by src/css/art.css.

The layer carries its own <defs>. It cannot reach the gradients declared by
whichever generator drew the art underneath it, and ids are global within a
document once the SVG is inlined, so every id here is prefixed to make a
collision impossible.
"""

import math
import random

W, H = 1600, 900


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def _shooting(out, rng, c, n=7):
    """Shooting stars. The trail is drawn pointing back along the travel
    vector, so it trails rather than leads whichever way the star is
    thrown."""
    for _ in range(n):
        # Mostly left-to-right, the direction the eye reads in; a quarter go
        # the other way so it does not read as a pattern.
        rightward = rng.random() > 0.25
        dx = rng.uniform(520, 1250) * (1 if rightward else -1)
        dy = rng.uniform(180, 520)
        x0 = (rng.uniform(-160, W * 0.55) if rightward
              else rng.uniform(W * 0.45, W + 160))
        y0 = rng.uniform(-120, H * 0.5)
        mag = math.hypot(dx, dy)
        length = rng.uniform(40, 130)
        tx, ty = -dx / mag * length, -dy / mag * length
        out.append(
            f'<g class="mo-shoot" style="--dur:{rng.uniform(5.5, 15):.1f}s;'
            f'--delay:-{rng.uniform(0, 14):.1f}s;--dx:{dx:.0f};--dy:{dy:.0f}">'
            f'<line x1="{f(x0)}" y1="{f(y0)}" x2="{f(x0 + tx)}" '
            f'y2="{f(y0 + ty)}" stroke="{c["hi"]}" '
            f'stroke-width="{rng.uniform(1.2, 2.6):.1f}" stroke-linecap="round" '
            f'opacity="0.55"/>'
            f'<circle cx="{f(x0)}" cy="{f(y0)}" '
            f'r="{rng.uniform(1.8, 3.4):.1f}" fill="{c["hi"]}"/></g>'
        )


def _sweeps(out, rng, c, n=2):
    """A soft raking bar of light crossing the whole frame.

    The skew is on a wrapper, never on the animated rect: a CSS transform
    property replaces a transform attribute outright, and the bar would
    cross bolt upright.
    """
    for _ in range(n):
        out.append(
            f'<g transform="skewX({rng.uniform(-16, 16):.0f})">'
            f'<rect class="mo-sweep" style="--dur:{rng.uniform(9, 20):.1f}s;'
            f'--delay:-{rng.uniform(0, 16):.1f}s" '
            f'x="{f(rng.uniform(0, W))}" y="-120" '
            f'width="{f(rng.uniform(90, 260))}" height="{f(H + 240)}" '
            f'fill="url(#amb-sweep)" opacity="0"/></g>'
        )


def _tears(out, rng, c, n=10):
    """Rows that jump sideways and snap back. A signal fault, not a pulse."""
    for _ in range(n):
        out.append(
            f'<rect class="mo-tear" style="--dur:{rng.uniform(2.4, 7):.1f}s;'
            f'--delay:-{rng.uniform(0, 6):.1f}s;'
            f'--sx:{rng.uniform(18, 90):.0f}" '
            f'x="{f(rng.uniform(-120, W * 0.4))}" y="{f(rng.uniform(0, H))}" '
            f'width="{f(rng.uniform(W * 0.3, W * 1.15))}" '
            f'height="{f(rng.uniform(4, 30))}" '
            f'fill="{rng.choice([c["a1"], c["a2"], c["hi"]])}" '
            f'opacity="{f(rng.uniform(0.08, 0.32))}"/>'
        )


def _rips(out, rng, c, n=2):
    """A bright band that travels down the frame and resets."""
    for _ in range(n):
        out.append(
            f'<rect class="mo-rip" style="--dur:{rng.uniform(5, 11):.1f}s;'
            f'--delay:-{rng.uniform(0, 9):.1f}s" x="0" '
            f'y="{f(rng.uniform(-40, 60))}" width="{W}" '
            f'height="{f(rng.uniform(3, 14))}" fill="{c["hi"]}" opacity="0"/>'
        )


def _embers(out, rng, c, n=26):
    """Motes that rise and fade. Reads as heat over a dark frame and as dust
    over a light one, which is why it is not called either."""
    for _ in range(n):
        out.append(
            f'<circle class="mo-rise" style="--dur:{rng.uniform(6, 17):.1f}s;'
            f'--delay:-{rng.uniform(0, 16):.1f}s;'
            f'--dx:{rng.uniform(-90, 90):.0f}" '
            f'cx="{f(rng.uniform(0, W))}" cy="{f(rng.uniform(H * 0.55, H + 40))}" '
            f'r="{rng.uniform(1.4, 4.2):.1f}" '
            f'fill="{rng.choice([c["hi"], c["a1"]])}" opacity="0"/>'
        )


def _drops(out, rng, c, n=30):
    """Falling flecks. Snow, ash, rain — whatever the palette makes them."""
    for _ in range(n):
        out.append(
            f'<circle class="mo-fall" style="--dur:{rng.uniform(7, 20):.1f}s;'
            f'--delay:-{rng.uniform(0, 19):.1f}s;'
            f'--dx:{rng.uniform(-140, 140):.0f}" '
            f'cx="{f(rng.uniform(0, W))}" cy="{f(rng.uniform(-80, H * 0.3))}" '
            f'r="{rng.uniform(1, 3.4):.1f}" fill="{c["hi"]}" opacity="0"/>'
        )


def _pulses(out, rng, c, n=3):
    """Rings that expand out of a point and fade — a sonar ping."""
    for _ in range(n):
        cx, cy = rng.uniform(W * 0.2, W * 0.8), rng.uniform(H * 0.2, H * 0.7)
        out.append(
            f'<circle class="mo-ping" style="--dur:{rng.uniform(5, 11):.1f}s;'
            f'--delay:-{rng.uniform(0, 10):.1f}s" '
            f'cx="{f(cx)}" cy="{f(cy)}" r="40" fill="none" '
            f'stroke="{c["a1"]}" stroke-width="2" opacity="0"/>'
        )


def _flickers(out, rng, c, n=5):
    """Panels that cut out and back. Never a fade — a fade reads as a pulse,
    and this has to read as a fault."""
    for _ in range(n):
        s = rng.uniform(60, 200)
        out.append(
            f'<rect class="mo-flicker" style="--dur:{rng.uniform(1.6, 5):.1f}s;'
            f'--delay:-{rng.uniform(0, 4):.1f}s;'
            f'--hi:{rng.uniform(0.3, 0.7):.2f};--lo:0.02" '
            f'x="{f(rng.uniform(0, W - s))}" '
            f'y="{f(rng.uniform(0, H - s * 0.5))}" width="{f(s)}" '
            f'height="{f(s * rng.uniform(0.2, 0.6))}" fill="{c["a2"]}"/>'
        )


EFFECTS = {
    "shooting": _shooting, "sweeps": _sweeps, "tears": _tears,
    "rips": _rips, "embers": _embers, "drops": _drops, "pulses": _pulses,
    "flickers": _flickers,
}


def ambient_svg(effects, palette: dict, seed: int) -> str:
    """SVG for the requested effects, ready to splice before </svg>.

    effects is a list of names, or of [name, count] pairs. Returns "" when
    nothing is asked for, so a level with no artAmbient is untouched.
    """
    if not effects:
        return ""

    c = {
        "hi": palette.get("ink") or "#ffffff",
        "a1": palette.get("accent") or palette.get("ink") or "#ffffff",
        "a2": palette.get("accent2") or palette.get("muted") or "#888888",
    }
    rng = random.Random(seed)
    out = []
    for entry in effects:
        name, count = (entry, None) if isinstance(entry, str) else entry
        if name not in EFFECTS:
            raise KeyError(f"unknown ambient effect {name!r}, "
                           f"expected one of {sorted(EFFECTS)}")
        EFFECTS[name](out, rng, c, **({"n": count} if count else {}))

    if not out:
        return ""

    defs = (
        '<defs><linearGradient id="amb-sweep" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0%" stop-color="{c["hi"]}" stop-opacity="0"/>'
        f'<stop offset="50%" stop-color="{c["hi"]}" stop-opacity="0.5"/>'
        f'<stop offset="100%" stop-color="{c["hi"]}" stop-opacity="0"/>'
        "</linearGradient></defs>"
    )
    return f'<g class="ambient" aria-hidden="true">{defs}{"".join(out)}</g>'
