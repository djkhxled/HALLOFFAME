#!/usr/bin/env python3
"""Fill in the themed tier, ranks 11-25, and publish them.

Palettes mirror tools/gen_themed.py so the page and its art agree. Facts are
only what could be sourced; everything else stays null and renders as an em
dash rather than a guess.

Usage: python3 tools/seed_themed_records.py
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
LV = ROOT / "data" / "levels"

WIKI = "https://geometrydash.wiki.gg/wiki/"
FAN = "https://geometry-dash-fan.fandom.com/wiki/"

# slug: palette, texture, signature, tagline, hook, why, facts overrides
DATA = {
    "freedom08": dict(
        pal=("#161a3a", "#eef0ff", "#a4abd8", "#b9a6e8", "#7fb4ee"),
        tex="grain", sig="flood", fonts=["Poppins:wght@300;600"],
        tag="Pale marble, hanging chains and colour — the brightest level on this list.",
        hook="Joy at an unreasonable speed.",
        why="<p>Freedom08 is the one that doesn't look like a demon at all. Cream columns, "
            "soft pastels, open light &mdash; and then it plays like everything else here. "
            "That contrast is the whole appeal.</p><p>It's a reminder that this difficulty "
            "tier doesn't have to mean darkness and red. Somebody decided extreme demons "
            "could be pretty and just did it.</p>",
        wiki="Freedom08"),
    "idols": dict(
        pal=("#12042c", "#fdefff", "#c49ad8", "#ff3ce0", "#3cf0ff"),
        tex="grain", sig="ignite", fonts=["Bungee"],
        tag="Every colour at once, and somehow it works.",
        hook="Maximum saturation, zero restraint.",
        why="<p>Idols is loud in a way almost nothing else manages without turning to mud. "
            "Magenta, yellow, cyan and green all fighting in the same frame, and it still "
            "reads cleanly.</p><p>It shouldn't work. It absolutely works.</p>",
        wiki="Idols"),
    "subsonic": dict(
        pal=("#0a0420", "#f4ecff", "#a9a0c8", "#ff4de0", "#4de0ff"),
        tex="scanline", sig="prism", fonts=["Kaushan+Script"],
        tag="A Viprin collab from back when collabs were still being invented.",
        hook="The template for everything after it.",
        why="<p>Subsonic is on this list partly for what it started. Viprin's collabs set the "
            "shape that mega-collaborations still follow, and you can see the whole grammar "
            "here already.</p><p>The magenta-and-cyan look has been copied endlessly since. "
            "This is where a lot of people saw it first.</p>",
        wiki="Subsonic"),
    "codependence": dict(
        pal=("#050b12", "#eef6ff", "#8fa6b8", "#ff2a3c", "#2ae0ff"),
        tex="scanline", sig="fracture", fonts=["Chakra+Petch:wght@500;700"],
        tag="Two halves that cannot function apart — red above, cyan below.",
        hook="A level built as an argument with itself.",
        why="<p>Codependence splits itself down the middle and makes the split the point. Red "
            "on top, cyan underneath, and the whole level lives on that tension.</p>"
            "<p>Committing to one visual idea that hard is rare, and it's why this one sticks.</p>",
        wiki="Codependence"),
    "zodiac": dict(
        pal=("#0d0620", "#f0ecff", "#a099c8", "#6b7cff", "#ff6bd0"),
        tex="starfield", sig="orbit", fonts=["Cinzel:wght@600"],
        tag="A twenty-creator collab built around the astrological wheel.",
        hook="Twenty names on one chart.",
        why="<p>Zodiac earns its place on scale and coherence at once. Twenty-odd creators, and "
            "it still holds a single idea from end to end.</p><p>The wheel motif gives every "
            "part somewhere to belong, which is exactly what enormous collabs usually lack.</p>",
        wiki="Zodiac"),
    "bloodlust": dict(
        pal=("#120102", "#ffe6e6", "#bd8080", "#ff1414", "#ff5a2a"),
        tex="ember", sig="pulse", fonts=["Cinzel:wght@600;800"],
        tag="The rebirth of Bloodbath — and the level that taught a generation what an extreme demon was.",
        hook="Bloodbath, reborn and sharpened.",
        why="<p>Bloodlust is here for what it meant. It took Bloodbath &mdash; already the most "
            "famous level in the game &mdash; and rebuilt it harder, then sat at #1.</p>"
            "<p>knobbelboy verified it himself after 121,296 attempts, having picked it up "
            "when the previous verifier stepped away. That number still stops me.</p>",
        wiki="Bloodlust",
        facts=dict(host="Manix648", verifier="knobbelboy", verifiedDate="2018-02-20",
                   attempts="121,296", objects="170,739", length="2m 51s",
                   gdVersion="2.0/2.1", peakRank="#1 on the Demonlist",
                   note="A buffed and extended remake of Bloodbath. Taken over by "
                        "knobbelboy after the previous verifier stepped away.")),
    "black-blizzard": dict(
        pal=("#050506", "#f4f6f8", "#9aa0a8", "#c9cdd4", "#8f959e"),
        tex="snow", sig="static", fonts=["Saira:wght@300;600"],
        tag="Pure black and white, and four months to verify.",
        hook="No colour at all, and it doesn't need any.",
        why="<p>Black Blizzard is the most restrained level on this list by a mile. White line "
            "on black, nothing else, and it still has more presence than levels doing ten "
            "times as much.</p><p>KrmaL made it, verified it and published it alone, over four "
            "months. He also used to ban people from his stream for revealing the song, which "
            "I find very funny.</p>",
        wiki="Black_Blizzard",
        facts=dict(host="KrmaL", verifier="KrmaL", verifiedDate="2017-05-21",
                   levelId="34057654", gdVersion="2.0/2.1",
                   song=dict(name="Dimension", artist="hyperdemented",
                             newgroundsId="709578"),
                   note="Created, verified and published solo by KrmaL; verification "
                        "took about four months.")),
    "maniacal-chains": dict(
        pal=("#010708", "#e8fffe", "#7fb8b4", "#25e8e0", "#8ff5f0"),
        tex="chrome", sig="descend", fonts=["Saira:wght@300;700"],
        tag="A single cyan beam through mirrored chains and teeth.",
        hook="Symmetry used as a threat.",
        why="<p>Maniacal Chains builds almost everything around one horizontal axis and mirrors "
            "it. The result is unnervingly clean for something this aggressive.</p>"
            "<p>That teal is doing an enormous amount of work against all the black.</p>",
        wiki="Maniacal_Chains"),
    "titan-complex": dict(
        pal=("#160205", "#ffe6ec", "#c48a97", "#ff2d5a", "#ff7a95"),
        tex="grain", sig="fracture", fonts=["Kaushan+Script"],
        tag="Built like a machine that was never meant to be entered.",
        hook="Industrial, and completely airless.",
        why="<p>Titan Complex is oppressive in a way I like. Deep red on black, saw shapes "
            "everywhere, structures that look load-bearing rather than decorative.</p>"
            "<p>The script logo against all that machinery is a genuinely strange choice and "
            "it works.</p>",
        wiki="Titan_Complex"),
    "firework": dict(
        pal=("#0c0508", "#fdecef", "#c08f97", "#ff2f45", "#7ad4e8"),
        tex="ember", sig="ignite", fonts=["Cinzel:wght@600"],
        tag="Chrome and crimson, bright and gone before you've understood it.",
        hook="Brief, and very loud about it.",
        why="<p>Firework is all edge and shine &mdash; chrome letters, red light, small tech "
            "detail scattered everywhere. It looks expensive.</p><p>It also doesn't outstay "
            "its welcome, which on this list is almost a novelty.</p>",
        wiki="Firework"),
    "andromeda": dict(
        pal=("#080326", "#efeaff", "#a099cc", "#7c5cff", "#3ccfff"),
        tex="starfield", sig="orbit", fonts=["Saira:wght@300;600"],
        tag="A galaxy you are asked to cross on foot.",
        hook="Violet tubing and one white core.",
        why="<p>Andromeda gets the hardest thing about space themes right: it feels big. Most "
            "levels that try this end up looking like a screensaver.</p><p>The maze tubing "
            "winding through the dark gives it structure, and then that white burst in the "
            "middle gives it a centre.</p>",
        wiki="Andromeda"),
    "the-golden": dict(
        pal=("#050f06", "#f2ffe6", "#9dbf8f", "#b6ff2a", "#ffe14d"),
        tex="grain", sig="ignite", fonts=["Cinzel:wght@600;800"],
        tag="Not gold at all — acid green, and heavier than it looks.",
        hook="The most misleading title on the list.",
        why="<p>The Golden isn't gold. It's a hard acid green over near-black, and that "
            "misdirection is half of why I like it.</p><p>Green is the hardest colour to make "
            "look good in this game &mdash; it goes muddy or radioactive almost every time. "
            "This one lands it.</p>",
        wiki="The_Golden"),
    "ocular-miracle": dict(
        pal=("#05061a", "#eef2ff", "#95a0c8", "#ff2f4a", "#4a8bff"),
        tex="starfield", sig="orbit", fonts=["Saira:wght@200;500"],
        tag="A planet, a red nebula, and the calmest art on this list.",
        hook="Something is watching, and it is beautiful about it.",
        why="<p>Ocular Miracle is the one that looks least like a Geometry Dash level. It looks "
            "like a book cover &mdash; a real painted planet, red nebula arcs, thin elegant "
            "type.</p><p>Everything else on this list shouts. This one doesn't, and it's "
            "still unmistakable.</p>",
        wiki="Ocular_Miracle"),
    "killbot": dict(
        pal=("#0a0f06", "#ffeaea", "#b09090", "#ff2020", "#3cff3c"),
        tex="grain", sig="slash", fonts=["Bungee"],
        tag="Red against green, painted rather than built.",
        hook="Industrial, unfeeling, extremely good at its job.",
        why="<p>Killbot goes for a colour pairing that should be unusable &mdash; saturated red "
            "against saturated green &mdash; and makes it feel violent instead of festive.</p>"
            "<p>The art is painterly and messy in a game full of clean geometry, which is "
            "exactly why it stands out.</p>",
        wiki="Killbot"),
    "edge-of-destiny": dict(
        pal=("#040a28", "#eafaff", "#8fa8d0", "#2ad4ff", "#6b8cff"),
        tex="caustics", sig="surge", fonts=["Saira:wght@300;700"],
        tag="Where the list begins — a blazing cyan core and a lot of blue.",
        hook="Number twenty-five, and still on the list.",
        why="<p>Edge of Destiny closes out the list, and that's not a slight. Everything here "
            "beat out hundreds of levels to be on it at all.</p><p>That cyan blast against "
            "layered dark blue platforms is a genuinely great piece of composition, and it's "
            "the level I'd point at to explain what I mean by atmosphere.</p>",
        wiki="Edge_of_Destiny"),
}


def main():
    for path in sorted(LV.glob("*.json")):
        rec = json.loads(path.read_text(encoding="utf-8"))
        slug = rec["slug"]
        if slug not in DATA:
            continue
        d = DATA[slug]
        field, ink, muted, a1, a2 = d["pal"]

        rec["published"] = True
        rec["tagline"] = d["tag"]
        t = rec["theme"]
        t["tier"] = "themed"
        t["palette"] = {"field": field, "ink": ink, "muted": muted,
                        "accent": a1, "accent2": a2}
        t["texture"] = d["tex"]
        t["signature"] = d["sig"]
        t["googleFonts"] = d["fonts"]

        fa = rec.setdefault("facts", {})
        for k, v in (d.get("facts") or {}).items():
            fa[k] = v
        fa.setdefault("song", {"name": None, "artist": None, "newgroundsId": None})
        fa["sources"] = [WIKI + d["wiki"], FAN + d["wiki"]]

        rec["voice"] = {"hook": d["hook"], "why": d["why"], "draftedByClaude": True}
        rec["media"]["art"] = f"src/art/{slug}.svg"

        path.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
        print(f"  {slug}")


if __name__ == "__main__":
    main()
