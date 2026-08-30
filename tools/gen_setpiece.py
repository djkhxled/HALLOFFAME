#!/usr/bin/env python3
"""Generate the pinned set-piece for the themed tier, ranks 11-25.

Every one of those fifteen levels already declares a theme.signature, and
every signature function in scroll.js opens with

    var stage = document.querySelector("[data-sig='orbit']");
    if (!stage) return;

Only the ten bespoke fragments ever contained a [data-sig] element, so all
fifteen signatures were bailing on their first line. The declared signature
drove no markup, no motion and no CSS. This writes the missing stage.

The markup honours each signature's existing data-attribute contract, so the
timelines in scroll.js drive these pages with no special casing: a themed
level pins, scrubs and parallaxes exactly like a bespoke one. Layers are
plain elements positioned from this script and painted by src/css/stage.css
out of the level's own palette tokens, so nothing here hardcodes a colour.

The copy is split deliberately. The eyebrow and the headline are editorial --
Baylor's reading of the level, in the register of the bespoke set-pieces. The
sub is assembled from the level's own record by fact_sub(), so it cannot
state anything the JSON has not sourced; a null simply drops out of the
sentence.

Usage: python3 tools/gen_setpiece.py [slug ...]
Writes: bespoke/<slug>.html
"""

import json
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "bespoke"
LEVELS_DIR = ROOT / "data" / "levels"


def f(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def esc(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


# --------------------------------------------------------------- fact copy

MONTHS = ("January February March April May June July August September "
          "October November December").split()


def pretty_date(iso):
    """2020-04-17 -> 17 April 2020. Returns None for anything else, so a
    partial or malformed date drops out of the sentence rather than
    appearing half-rendered."""
    if not iso:
        return None
    parts = iso.split("-")
    if len(parts) != 3:
        return None
    y, m, d = parts
    try:
        return f"{int(d)} {MONTHS[int(m) - 1]} {y}"
    except (ValueError, IndexError):
        return None


def fact_sub(facts):
    """A sourced sentence about who made it and what it costs to play.

    Assembled clause by clause from whatever the record actually holds. The
    rule for the whole site is that an unknown is never guessed at, so every
    clause here is conditional and an absent fact leaves no trace -- no em
    dash, no 'unknown', just a shorter sentence.
    """
    facts = facts or {}
    creators = facts.get("creators") or []
    host = facts.get("host")
    verifier = facts.get("verifier")
    date = pretty_date(facts.get("verifiedDate"))

    made = ""
    if len(creators) == 1:
        made = f"Built by {creators[0]}"
    elif host and len(creators) > 1:
        made = f"Hosted by {host} with {len(creators) - 1} others"
    elif len(creators) > 1:
        made = f"Built by {len(creators)} creators"
    elif host:
        made = f"Hosted by {host}"

    if verifier:
        clause = f"verified by {verifier}"
        if date:
            clause += f" on {date}"
        made = f"{made}, {clause}" if made else clause[0].upper() + clause[1:]
    elif date:
        made = f"{made}, verified {date}" if made else f"Verified {date}"

    first = f"{made}." if made else ""

    # Second sentence: the shape of the thing. Objects and length only read
    # as a pair; either alone still says something worth saying.
    objects, length = facts.get("objects"), facts.get("length")
    if objects and length:
        second = f"{objects} objects in {length}."
    elif objects:
        second = f"{objects} objects."
    elif length:
        second = f"{length} long."
    else:
        second = ""

    attempts = facts.get("attempts")
    third = f"{attempts} attempts to verify." if attempts else ""

    peak = facts.get("peakRank")
    fourth = f"Peaked at {peak}." if peak else ""

    return " ".join(part for part in (first, second, third, fourth) if part)


# ------------------------------------------------------------ layer helpers
# Scattered elements carry their geometry inline, because the alternative is
# fifteen hand-written stylesheets. The shared stylesheet owns how a layer
# looks; this owns where its pieces are.

def sty(**kw):
    return " ".join(f"{k.replace('_', '-')}:{v};" for k, v in kw.items())


def specks(rng, n, cls="stage__speck", extra="", size=(1.5, 4.5),
           opacity=(0.15, 0.8), rows=(0, 100)):
    out = []
    for _ in range(n):
        s = rng.uniform(*size)
        out.append(
            f'<span class="{cls}" {extra} aria-hidden="true" style="'
            + sty(left=f"{rng.uniform(0, 100):.1f}%",
                  top=f"{rng.uniform(*rows):.1f}%",
                  width=f"{s:.1f}px", height=f"{s:.1f}px",
                  opacity=f"{rng.uniform(*opacity):.2f}",
                  **{"--dur": f"{rng.uniform(2.4, 7.5):.1f}s",
                     "--delay": f"-{rng.uniform(0, 6):.1f}s"})
            + '"></span>'
        )
    return out


def copy_block(sig, hook, eyebrow, big, sub):
    """The three lines every stage ends on. hook is the data attribute the
    signature's timeline staggers, which differs per signature -- prism
    animates letter-spacing on [data-split], fracture fades [data-frac-line]."""
    return [
        '  <div class="stage__copy page">',
        f'    <p class="eyebrow stage__eyebrow" {hook} data-motion>{esc(eyebrow)}</p>',
        f'    <p class="stage__line" {hook} data-motion>{big}</p>',
        f'    <p class="stage__sub measure" {hook} data-motion>{esc(sub)}</p>',
        "  </div>",
    ]


# ------------------------------------------------------------------ stages
# One builder per signature. Each returns the layers that sit behind the
# copy, in paint order, and each satisfies the data attributes its timeline
# in scroll.js already reaches for.

def s_ascend(rng, cfg):
    """Aerial Gleam: the mirror of descend. There, the world rushes up past
    a falling camera; here the ground drops away and the light opens above.
    [data-lift=far|mid|near] [data-cloud] [data-sky]"""
    out = ['  <div class="as__sky" data-sky data-motion aria-hidden="true"></div>']
    for depth, y, h in (("far", 62, 26), ("mid", 76, 22), ("near", 90, 20)):
        out.append(
            f'  <div class="as__ridge as__ridge--{depth}" data-lift="{depth}" '
            'data-motion aria-hidden="true" style="'
            + sty(top=f"{y}%", height=f"{h}vmin")
            + '"></div>'
        )
    for i in range(8):
        out.append(
            '  <span class="as__cloud" data-cloud data-motion aria-hidden="true" style="'
            + sty(left=f"{rng.uniform(-8, 92):.1f}%",
                  top=f"{rng.uniform(8, 78):.1f}%",
                  width=f"{rng.uniform(22, 62):.0f}vmin",
                  height=f"{rng.uniform(4, 12):.0f}vmin",
                  opacity=f"{rng.uniform(0.12, 0.4):.2f}",
                  **{"--dur": f"{rng.uniform(9, 22):.1f}s",
                     "--delay": f"-{rng.uniform(0, 18):.1f}s"})
            + '"></span>'
        )
    for i in range(5):
        out.append(
            '  <span class="as__shaft" data-motion aria-hidden="true" style="'
            + sty(left=f"{rng.uniform(4, 92):.1f}%",
                  width=f"{rng.uniform(4, 16):.1f}vmin",
                  **{"--dur": f"{rng.uniform(6, 13):.1f}s",
                     "--delay": f"-{rng.uniform(0, 11):.1f}s"})
            + '"></span>'
        )
    out += specks(rng, 48, cls="stage__speck stage__speck--rise")
    return out


def s_ignite(rng, cfg):
    """Exposure ramps and the corona opens. [data-rays] [data-core]
    [data-cog] [data-cog-rev]"""
    out = [
        '  <div class="ig__rays" data-rays data-motion aria-hidden="true"></div>',
        '  <div class="ig__halo" aria-hidden="true"></div>',
        '  <div class="ig__core" data-core data-motion aria-hidden="true"></div>',
    ]
    for i in range(6):
        spin = "data-cog-rev" if i % 2 else "data-cog"
        size = rng.uniform(9, 26)
        out.append(
            f'  <div class="ig__cog" {spin} data-motion aria-hidden="true" style="'
            + sty(left=f"{rng.uniform(4, 92):.1f}%",
                  top=f"{rng.uniform(6, 86):.1f}%",
                  width=f"{size:.1f}vmin", height=f"{size:.1f}vmin",
                  **{"--teeth": f"{rng.randint(9, 16)}"})
            + '"></div>'
        )
    for i in range(5):
        out.append(
            '  <span class="ig__lick" data-motion aria-hidden="true" style="'
            + sty(left=f"{rng.uniform(2, 94):.1f}%",
                  height=f"{rng.uniform(18, 46):.0f}vmin",
                  **{"--dur": f"{rng.uniform(3.2, 6.4):.1f}s",
                     "--delay": f"-{rng.uniform(0, 5):.1f}s"})
            + '"></span>'
        )
    out += specks(rng, 46, cls="stage__speck stage__speck--rise")
    return out


def s_orbit(rng, cfg):
    """Layered bodies drift at different rates. [data-depth=far|mid|near]"""
    out = ['  <div class="orb__void" data-depth="far" data-motion aria-hidden="true"></div>']
    for i, (depth, size, op) in enumerate(
            (("far", 78, 0.28), ("mid", 52, 0.42), ("near", 30, 0.6))):
        out.append(
            f'  <div class="orb__ring" data-depth="{depth}" data-motion '
            'aria-hidden="true" style="'
            + sty(width=f"{size}vmin", height=f"{size}vmin",
                  opacity=f"{op}",
                  **{"--spin": f"{40 + i * 26}s",
                     "--tilt": f"{rng.uniform(-24, 24):.0f}deg"})
            + '"></div>'
        )
    out.append('  <div class="orb__body" data-depth="mid" data-motion '
               'aria-hidden="true"></div>')
    for i in range(9):
        out.append(
            '  <span class="orb__moon" data-depth="near" data-motion '
            'aria-hidden="true" style="'
            + sty(left=f"{rng.uniform(3, 95):.1f}%",
                  top=f"{rng.uniform(6, 90):.1f}%",
                  width=f"{rng.uniform(0.6, 2.6):.1f}vmin",
                  height=f"{rng.uniform(0.6, 2.6):.1f}vmin",
                  **{"--dur": f"{rng.uniform(3, 8):.1f}s",
                     "--delay": f"-{rng.uniform(0, 6):.1f}s"})
            + '"></span>'
        )
    out += specks(rng, 90, cls="stage__speck stage__speck--twinkle",
                  extra='data-depth="far" data-motion', size=(1, 2.6))
    return out


def s_pulse(rng, cfg):
    """The frame breathes on beat. [data-loom] [data-beat]"""
    out = [
        '  <div class="pl__loom" data-loom data-motion aria-hidden="true"></div>',
        '  <div class="pl__ribs" data-motion aria-hidden="true"></div>',
    ]
    for i in range(4):
        out.append(
            f'  <div class="pl__ring" data-beat data-motion aria-hidden="true" style="'
            + sty(width=f"{26 + i * 15}vmin", height=f"{26 + i * 15}vmin",
                  opacity=f"{0.5 - i * 0.09:.2f}")
            + '"></div>'
        )
    for i in range(7):
        out.append(
            '  <span class="pl__drip" data-motion aria-hidden="true" style="'
            + sty(left=f"{rng.uniform(3, 95):.1f}%",
                  height=f"{rng.uniform(8, 30):.0f}vmin",
                  **{"--dur": f"{rng.uniform(4, 9):.1f}s",
                     "--delay": f"-{rng.uniform(0, 7):.1f}s"})
            + '"></span>'
        )
    out += specks(rng, 40, cls="stage__speck stage__speck--rise")
    return out


def s_fracture(rng, cfg):
    """The frame shatters and reassembles. [data-shard]"""
    out = ['  <div class="fr__field" aria-hidden="true">']
    for i in range(14):
        w = rng.uniform(9, 30)
        out.append(
            '    <div class="fr__shard" data-shard data-motion style="'
            + sty(left=f"{rng.uniform(-4, 92):.1f}%",
                  top=f"{rng.uniform(-4, 88):.1f}%",
                  width=f"{w:.1f}vmin",
                  height=f"{w * rng.uniform(0.5, 2.1):.1f}vmin",
                  transform=f"rotate({rng.uniform(-40, 40):.0f}deg)",
                  opacity=f"{rng.uniform(0.24, 0.72):.2f}")
            + '"></div>'
        )
    for i in range(6):
        out.append(
            '    <span class="fr__crack" aria-hidden="true" style="'
            + sty(left=f"{rng.uniform(2, 96):.1f}%",
                  top=f"{rng.uniform(-10, 60):.1f}%",
                  height=f"{rng.uniform(30, 90):.0f}vmin",
                  transform=f"rotate({rng.uniform(-26, 26):.0f}deg)")
            + '"></span>'
        )
    out.append("  </div>")
    out += specks(rng, 34)
    return out


def s_descend(rng, cfg):
    """The camera falls and the world rises past it.
    [data-fall=far|mid|near] [data-chain] [data-dark]"""
    out = []
    for depth in ("far", "mid", "near"):
        out.append(f'  <div class="ds__wall ds__wall--{depth}" '
                   f'data-fall="{depth}" data-motion aria-hidden="true"></div>')
    for i in range(9):
        out.append(
            '  <span class="ds__chain" data-chain data-motion aria-hidden="true" style="'
            + sty(left=f"{rng.uniform(1, 97):.1f}%",
                  top=f"{rng.uniform(-30, 40):.1f}%",
                  height=f"{rng.uniform(40, 130):.0f}vmin",
                  opacity=f"{rng.uniform(0.3, 0.85):.2f}",
                  **{"--link": f"{rng.uniform(1.1, 2.2):.1f}vmin"})
            + '"></span>'
        )
    for i in range(6):
        out.append(
            '  <span class="ds__tooth" data-fall="mid" data-motion '
            'aria-hidden="true" style="'
            + sty(left=f"{rng.uniform(2, 94):.1f}%",
                  top=f"{rng.uniform(4, 84):.1f}%",
                  width=f"{rng.uniform(4, 12):.1f}vmin",
                  transform=f"rotate({rng.choice([0, 180])}deg)")
            + '"></span>'
        )
    out += specks(rng, 40, cls="stage__speck stage__speck--rise")
    out.append('  <div class="ds__dark" data-dark data-motion aria-hidden="true"></div>')
    return out


def s_surge(rng, cfg):
    """The wave rears and the water pans past.
    [data-swell] [data-current=a|b] [data-foam]"""
    out = [
        '  <div class="sg__sky" aria-hidden="true"></div>',
        '  <div class="sg__swell" data-swell data-motion aria-hidden="true"></div>',
    ]
    for i in range(5):
        lane = "a" if i % 2 == 0 else "b"
        out.append(
            f'  <div class="sg__current" data-current="{lane}" data-motion '
            'aria-hidden="true" style="'
            + sty(top=f"{rng.uniform(18, 88):.1f}%",
                  height=f"{rng.uniform(2, 9):.1f}vmin",
                  opacity=f"{rng.uniform(0.2, 0.6):.2f}")
            + '"></div>'
        )
    # exactly two tiles: the timeline travels -50%, so any other count seams
    out.append('  <div class="sg__foam" data-foam data-motion aria-hidden="true">'
               '<i></i><i></i></div>')
    for i in range(7):
        out.append(
            '  <span class="sg__spray" data-motion aria-hidden="true" style="'
            + sty(left=f"{rng.uniform(2, 95):.1f}%",
                  bottom=f"{rng.uniform(2, 40):.1f}%",
                  width=f"{rng.uniform(2, 7):.1f}vmin",
                  **{"--dur": f"{rng.uniform(3.4, 7):.1f}s",
                     "--delay": f"-{rng.uniform(0, 6):.1f}s"})
            + '"></span>'
        )
    out += specks(rng, 36, cls="stage__speck stage__speck--rise")
    return out


def s_prism(rng, cfg):
    """The beam sweeps and the lattice drifts apart.
    [data-beam] [data-drift=a|b]"""
    out = ['  <div class="pr__lattice" aria-hidden="true">']
    for i in range(12):
        lane = "a" if i % 2 == 0 else "b"
        w = rng.uniform(7, 22)
        out.append(
            f'    <div class="pr__cell" data-drift="{lane}" data-motion style="'
            + sty(left=f"{rng.uniform(-2, 90):.1f}%",
                  top=f"{rng.uniform(-2, 86):.1f}%",
                  width=f"{w:.1f}vmin", height=f"{w * rng.uniform(0.6, 1.6):.1f}vmin",
                  transform=f"rotate({rng.uniform(-18, 18):.0f}deg)",
                  opacity=f"{rng.uniform(0.2, 0.6):.2f}")
            + '"></div>'
        )
    for i in range(8):
        lane = "b" if i % 2 else "a"
        out.append(
            f'    <span class="pr__tri" data-drift="{lane}" data-motion style="'
            + sty(left=f"{rng.uniform(2, 94):.1f}%",
                  top=f"{rng.uniform(4, 88):.1f}%",
                  **{"--s": f"{rng.uniform(2.4, 7):.1f}vmin"})
            + '"></span>'
        )
    out.append("  </div>")
    out.append('  <div class="pr__beam" data-beam data-motion aria-hidden="true"></div>')
    out.append('  <div class="pr__scan" aria-hidden="true"></div>')
    out += specks(rng, 30)
    return out


# ----------------------------------------------------- signatures written here
# Five levels wanted something the existing vocabulary could not say. Their
# timelines are new in scroll.js and the contracts are defined by these
# builders.

def s_flood(rng, cfg):
    """Freedom08: four and a quarter minutes of holding a line. Pillars stand
    while the tide climbs them. [data-pillar] [data-tide] [data-banner]"""
    out = ['  <div class="fl__hall" aria-hidden="true">']
    for i in range(9):
        x = 3 + i * 11.4
        out.append(
            '    <div class="fl__pillar" data-pillar data-motion style="'
            + sty(left=f"{x:.1f}%",
                  width=f"{rng.uniform(3.4, 6.2):.1f}vmin",
                  height=f"{rng.uniform(58, 96):.0f}%",
                  opacity=f"{rng.uniform(0.3, 0.85):.2f}")
            + '"></div>'
        )
    out.append("  </div>")
    for i in range(6):
        out.append(
            '  <span class="fl__banner" data-banner data-motion aria-hidden="true" style="'
            + sty(left=f"{rng.uniform(4, 92):.1f}%",
                  top=f"{rng.uniform(-6, 22):.1f}%",
                  width=f"{rng.uniform(3, 7):.1f}vmin",
                  height=f"{rng.uniform(24, 52):.0f}vmin",
                  **{"--dur": f"{rng.uniform(4, 9):.1f}s",
                     "--delay": f"-{rng.uniform(0, 8):.1f}s"})
            + '"></span>'
        )
    out += specks(rng, 60, cls="stage__speck stage__speck--rise", size=(2, 6))
    out.append('  <div class="fl__tide" data-tide data-motion aria-hidden="true"></div>')
    return out


def s_twin(rng, cfg):
    """Codependence: two players, one brain. Halves converge on the seam.
    [data-twin=a|b] [data-seam] [data-link]"""
    out = [
        '  <div class="tw__half tw__half--a" data-twin="a" data-motion aria-hidden="true"></div>',
        '  <div class="tw__half tw__half--b" data-twin="b" data-motion aria-hidden="true"></div>',
    ]
    for i in range(11):
        x = 4 + i * 9.0
        drop = rng.uniform(9, 26)
        out.append(
            f'  <span class="tw__icon tw__icon--up" data-twin="a" data-motion '
            'aria-hidden="true" style="'
            + sty(left=f"{x:.1f}%", top=f"{28 - drop * 0.3:.1f}%",
                  **{"--s": f"{rng.uniform(1.8, 3.4):.1f}vmin"})
            + '"></span>'
        )
        out.append(
            f'  <span class="tw__icon tw__icon--dn" data-twin="b" data-motion '
            'aria-hidden="true" style="'
            + sty(left=f"{x:.1f}%", top=f"{66 + drop * 0.3:.1f}%",
                  **{"--s": f"{rng.uniform(1.8, 3.4):.1f}vmin"})
            + '"></span>'
        )
        out.append(
            '  <span class="tw__link" data-link data-motion aria-hidden="true" style="'
            + sty(left=f"{x + 0.9:.1f}%", top=f"{28 - drop * 0.3:.1f}%",
                  height=f"{38 + drop * 0.6:.1f}%")
            + '"></span>'
        )
    out.append('  <div class="tw__seam" data-seam data-motion aria-hidden="true"></div>')
    out += specks(rng, 30)
    return out


def s_whiteout(rng, cfg):
    """Black Blizzard: a funnel of debris against pure black, no colour in it
    at all. [data-funnel] [data-debris] [data-gust]"""
    out = ['  <div class="wo__funnel" data-funnel data-motion aria-hidden="true">']
    for i in range(22):
        t = i / 21
        width = 8 + t * 54
        out.append(
            '    <span class="wo__turn" style="'
            + sty(top=f"{t * 100:.1f}%", width=f"{width:.1f}%",
                  opacity=f"{0.14 + t * 0.4:.2f}",
                  **{"--dur": f"{rng.uniform(1.6, 4.2):.1f}s",
                     "--delay": f"-{rng.uniform(0, 4):.1f}s"})
            + '"></span>'
        )
    out.append("  </div>")
    for i in range(9):
        out.append(
            '  <span class="wo__gust" data-gust data-motion aria-hidden="true" style="'
            + sty(top=f"{rng.uniform(2, 94):.1f}%",
                  width=f"{rng.uniform(18, 62):.0f}%",
                  opacity=f"{rng.uniform(0.1, 0.4):.2f}")
            + '"></span>'
        )
    out += specks(rng, 110, cls="stage__speck stage__speck--blow",
                  extra="data-debris data-motion", size=(1, 4))
    return out


def s_overgrow(rng, cfg):
    """The Golden: the clutter is the difficulty. Growth closes in from every
    edge until the centre is all that is left. [data-creep=a|b] [data-frond]"""
    out = []
    for i in range(16):
        side = "a" if i % 2 == 0 else "b"
        out.append(
            f'  <span class="og__vine og__vine--{side}" data-creep="{side}" '
            'data-motion aria-hidden="true" style="'
            + sty(left=f"{rng.uniform(-6, 96):.1f}%",
                  top=f"{rng.uniform(-8, 92):.1f}%",
                  width=f"{rng.uniform(14, 48):.0f}vmin",
                  transform=f"rotate({rng.uniform(-70, 70):.0f}deg)",
                  opacity=f"{rng.uniform(0.25, 0.8):.2f}")
            + '"></span>'
        )
    for i in range(26):
        out.append(
            '  <span class="og__frond" data-frond data-motion aria-hidden="true" style="'
            + sty(left=f"{rng.uniform(-2, 100):.1f}%",
                  top=f"{rng.uniform(-2, 100):.1f}%",
                  width=f"{rng.uniform(2.4, 8):.1f}vmin",
                  transform=f"rotate({rng.uniform(0, 360):.0f}deg)",
                  **{"--dur": f"{rng.uniform(3.6, 8):.1f}s",
                     "--delay": f"-{rng.uniform(0, 7):.1f}s"})
            + '"></span>'
        )
    out.append('  <div class="og__gloom" aria-hidden="true"></div>')
    out += specks(rng, 44, cls="stage__speck stage__speck--rise")
    return out


def s_iris(rng, cfg):
    """Ocular Miracle: 548,393 objects, and the eye opens on all of them.
    [data-lid=t|b] [data-pupil] [data-iris] [data-lash]"""
    out = ['  <div class="ir__white" aria-hidden="true"></div>',
           '  <div class="ir__iris" data-iris data-motion aria-hidden="true">']
    for i in range(48):
        out.append(
            '    <span class="ir__fibre" style="'
            + sty(transform=f"rotate({i * 7.5:.1f}deg)",
                  opacity=f"{rng.uniform(0.2, 0.9):.2f}",
                  **{"--len": f"{rng.uniform(34, 50):.0f}%"})
            + '"></span>'
        )
    out.append("  </div>")
    out.append('  <div class="ir__pupil" data-pupil data-motion aria-hidden="true"></div>')
    for i in range(3):
        out.append(
            f'  <div class="ir__halo" aria-hidden="true" style="'
            + sty(width=f"{40 + i * 18}vmin", height=f"{40 + i * 18}vmin",
                  opacity=f"{0.3 - i * 0.08:.2f}",
                  **{"--dur": f"{6 + i * 2}s"})
            + '"></div>'
        )
    out += specks(rng, 70, cls="stage__speck stage__speck--twinkle", size=(1, 2.8))
    out.append('  <div class="ir__lid ir__lid--t" data-lid="t" data-motion aria-hidden="true"></div>')
    out.append('  <div class="ir__lid ir__lid--b" data-lid="b" data-motion aria-hidden="true"></div>')
    return out


def s_corrupt(rng, cfg):
    """Killbot: the screen is actively lying to you. Channels separate, rows
    tear, hazard plates flash. [data-chan=r|g] [data-tear] [data-flicker]"""
    out = ['  <div class="cr__chan cr__chan--r" data-chan="r" data-motion aria-hidden="true"></div>',
           '  <div class="cr__chan cr__chan--g" data-chan="g" data-motion aria-hidden="true"></div>',
           '  <div class="cr__rows" aria-hidden="true">']
    for i in range(30):
        out.append(
            '    <span class="cr__row" data-tear data-motion style="'
            + sty(top=f"{rng.uniform(0, 99):.1f}%",
                  height=f"{rng.uniform(0.5, 4.5):.1f}%",
                  width=f"{rng.uniform(20, 100):.0f}%",
                  left=f"{rng.uniform(-8, 20):.1f}%",
                  opacity=f"{rng.uniform(0.1, 0.55):.2f}")
            + '"></span>'
        )
    out.append("  </div>")
    for i in range(7):
        out.append(
            '  <span class="cr__plate" data-flicker aria-hidden="true" style="'
            + sty(left=f"{rng.uniform(2, 88):.1f}%",
                  top=f"{rng.uniform(4, 86):.1f}%",
                  width=f"{rng.uniform(8, 22):.0f}vmin",
                  height=f"{rng.uniform(3, 9):.0f}vmin",
                  transform=f"rotate({rng.uniform(-8, 8):.0f}deg)")
            + '"></span>'
        )
    out.append('  <div class="cr__grid" aria-hidden="true"></div>')
    out += specks(rng, 40)
    return out


STAGES = {
    "ascend": s_ascend, "ignite": s_ignite, "orbit": s_orbit, "pulse": s_pulse,
    "fracture": s_fracture, "descend": s_descend, "surge": s_surge,
    "prism": s_prism,
    "flood": s_flood, "twin": s_twin, "whiteout": s_whiteout,
    "overgrow": s_overgrow, "iris": s_iris, "corrupt": s_corrupt,
}

# The attribute each signature's timeline staggers the copy on. These are
# not interchangeable: prism animates letter-spacing on [data-split] and
# slash skews [data-cut], so using the wrong one leaves the copy at its
# entrance state.
HOOKS = {
    "ascend": "data-asc-line", "ignite": "data-ignite-line", "orbit": "data-orbit-line",
    "pulse": "data-pulse-line", "fracture": "data-frac-line",
    "descend": "data-desc-line", "surge": "data-surge-line",
    "prism": "data-split",
    "flood": "data-flood-line", "twin": "data-twin-line",
    "whiteout": "data-white-line", "overgrow": "data-grow-line",
    "iris": "data-iris-line", "corrupt": "data-corrupt-line",
}


# ---------------------------------------------------------------- the levels
# sig is authoritative: build.py writes it to data-signature and scroll.js
# dispatches on it, so it must match the record's theme.signature.

COPY = {
    "freedom08": dict(
        sig="flood", seed=111, title="the long hall",
        eyebrow="Four minutes and sixteen seconds",
        big="Hold the<br>rhythm"),
    "idols": dict(
        sig="ignite", seed=112, title="the colour",
        eyebrow="No hell theme, no red, no skulls",
        big="All of<br>the colour"),
    "subsonic": dict(
        sig="prism", seed=113, title="the speed",
        eyebrow="Supersonic, Hypersonic, and then this",
        big="Speed as a<br>difficulty"),
    "codependence": dict(
        sig="twin", seed=114, title="the pair",
        eyebrow="Two icons, two hands",
        big="One brain"),
    "zodiac": dict(
        sig="orbit", seed=115, title="the wheel",
        eyebrow="Twelve signs, twenty-two builders",
        big="Three minutes<br>of sky"),
    "bloodlust": dict(
        sig="pulse", seed=116, title="the heartbeat",
        eyebrow="Bloodbath, extended past its own ending",
        big="The apocalypse<br>version"),
    "black-blizzard": dict(
        sig="whiteout", seed=117, title="the storm",
        eyebrow="No glow, no palette, no mercy",
        big="White<br>on black"),
    "maniacal-chains": dict(
        sig="descend", seed=118, title="the descent",
        eyebrow="Industrial, mechanical, hostile",
        big="Nowhere<br>to breathe"),
    "titan-complex": dict(
        sig="fracture", seed=119, title="the fortress",
        eyebrow="Every game mode, no weak one to hide behind",
        big="A fortress,<br>dismantled"),
    "firework": dict(
        sig="ignite", seed=120, title="the greyscale",
        eyebrow="Monochrome, in a genre built on neon",
        big="A silent<br>film"),
    "andromeda": dict(
        sig="orbit", seed=121, title="the drift",
        eyebrow="Seventy-six seconds of deep space",
        big="Zero<br>gravity"),
    "the-golden": dict(
        sig="overgrow", seed=122, title="the overgrowth",
        eyebrow="The clutter is the difficulty",
        big="A living<br>environment"),
    "ocular-miracle": dict(
        sig="iris", seed=123, title="the eye",
        eyebrow="Half a million objects in one level",
        big="The editor,<br>at its limit"),
    "killbot": dict(
        sig="corrupt", seed=124, title="the noise",
        eyebrow="The screen is lying to you on purpose",
        big="Read the<br>real path"),
    "aerial-gleam": dict(
        sig="ascend", seed=126, title="the climb",
        eyebrow="Two point two, spent entirely in the air",
        big="The ground<br>drops away"),
    "nullscapes": dict(
        sig="fracture", seed=127, title="the void",
        eyebrow="Its own description, in full",
        big="Get out of<br>my head"),
    "atomic-cannon-mk-ii": dict(
        sig="ignite", seed=128, title="the blast",
        eyebrow="Second of four, and the series is the point",
        big="Ordnance,<br>not architecture"),
    "wow": dict(
        sig="orbit", seed=129, title="the battle",
        eyebrow="Eight builders, 2.1, and F-777",
        big="Loud, and<br>unembarrassed"),
    "digital-descent": dict(
        sig="descend", seed=130, title="the collapse",
        eyebrow="Revolution is not always made by the ones who rule",
        big="The digital era,<br>going down"),
    "edge-of-destiny": dict(
        sig="surge", seed=125, title="the climax",
        eyebrow="Blade of Justice, rebuilt and optimised",
        big="The<br>climax"),
}


def record(slug):
    for path in LEVELS_DIR.glob("*.json"):
        rec = json.loads(path.read_text(encoding="utf-8"))
        if rec["slug"] == slug:
            return rec
    raise KeyError(slug)


def build(slug, cfg):
    rec = record(slug)
    sig = cfg["sig"]
    declared = (rec.get("theme") or {}).get("signature")
    if declared != sig:
        raise SystemExit(
            f"{slug}: this script builds a {sig!r} stage but the record "
            f"declares {declared!r}. scroll.js dispatches on the record, so "
            "the stage would never animate. Fix one of them."
        )

    rng = random.Random(cfg["seed"])
    hook = HOOKS[sig]
    ident = f"stage-{slug}"

    lines = [
        f'<section class="stage stage--{sig}" data-sig="{sig}" '
        f'aria-labelledby="{ident}">',
        f'  <h2 id="{ident}" class="visually-hidden">'
        f'{esc(rec["name"])} &mdash; {esc(cfg["title"])}</h2>',
        '  <div class="stage__wash" aria-hidden="true"></div>',
    ]
    lines += STAGES[sig](rng, cfg)
    lines += copy_block(sig, hook, cfg["eyebrow"], cfg["big"],
                        fact_sub(rec.get("facts")))
    lines.append('  <div class="stage__vig" aria-hidden="true"></div>')
    lines.append("</section>")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    want = sys.argv[1:] or list(COPY)
    OUT.mkdir(parents=True, exist_ok=True)
    for slug in want:
        html = build(slug, COPY[slug])
        (OUT / f"{slug}.html").write_text(html, encoding="utf-8")
        print(f"  {slug:18} {COPY[slug]['sig']:<9} "
              f"{len(html.splitlines()):>3} lines")
