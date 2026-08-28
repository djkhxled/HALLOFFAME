#!/usr/bin/env python3
"""One-off: seed the 23 not-yet-published level records.

Ranks 1 and 2 (Deimos, Nhelv) are hand-authored and are NOT touched here.
Taglines and palettes are provisional placeholders for the countdown; they get
replaced with researched content when each level is built out in M2/M3.

Usage: python3 tools/seed_levels.py
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "levels"

# rank, slug, name, creators, tagline, field, ink, muted, accent, texture, signature
STUBS = [
    (3, "the-yandere", "The Yandere", ["Dorami", "and more"],
     "Sweetness and menace wearing the same face.",
     "#12060c", "#fbeef4", "#c99bb2", "#ff4f9a", "grain", "pulse"),
    (4, "cold-sweat", "Cold Sweat", ["Para", "and more"],
     "The panic that arrives a half-second before the drop does.",
     "#050d12", "#e9f6fb", "#8fb4c4", "#38d6f5", "grain", "flood"),
    (5, "acheron", "Acheron", ["ryamu", "Riot", "and more"],
     "The middle chapter of Riot's descent into hell.",
     "#0d0503", "#ffeee4", "#c39684", "#ff5c1a", "ember", "descend"),
    (6, "tidal-wave", "Tidal Wave", ["OniLink"],
     "Three minutes of wave, and nowhere to hide.",
     "#02080f", "#e6f4ff", "#7fa8c4", "#22a7ff", "caustics", "surge"),
    (7, "solar-flare", "Solar Flare", ["Linear", "Swiborg", "Rynoxious"],
     "Light loud enough to hear.",
     "#100702", "#fff2df", "#cfa06a", "#ffa528", "ember", "ignite"),
    (8, "slaughterhouse", "Slaughterhouse", ["icedcave", "and more"],
     "It was the hardest level in the game, and it looked the part.",
     "#0c0303", "#ffe9e9", "#c08585", "#ff2d2d", "grain", "pulse"),
    (9, "kyouki", "Kyouki", ["Demishio"],
     "Madness, arranged neatly.",
     "#0a0507", "#fdeef0", "#c294a0", "#ff3b5c", "scanline", "fracture"),
    (10, "titan-complex", "Titan Complex", ["TCTeam"],
     "Built like a machine that was never meant to be entered.",
     "#05090d", "#e8f1f8", "#8ea4b8", "#4dc3ff", "chrome", "fracture"),
    (11, "freedom08", "Freedom08", ["Pennutoh", "and more"],
     "Joy at an unreasonable speed.",
     "#060a10", "#eef3ff", "#94a2c0", "#7aa8ff", "grain", "static"),
    (12, "idols", "Idols", ["Zafkiel7", "and more"],
     "Worship, rendered in neon.",
     "#0e0710", "#f8eeff", "#b697c4", "#c56bff", "scanline", "static"),
    (13, "subsonic", "Subsonic", ["Viprin", "and more"],
     "A Viprin collab from when collabs were still being invented.",
     "#04070f", "#e9f0ff", "#8b9bc0", "#5f8cff", "grain", "static"),
    (14, "codependence", "Codependence", ["TCTeam"],
     "Two halves that cannot function apart.",
     "#040c0c", "#e6f7f6", "#86b3b0", "#2fd9c9", "grain", "static"),
    (15, "zodiac", "Zodiac", ["BIANOX", "and more"],
     "Star charts drawn by somebody with something to prove.",
     "#080614", "#f0eeff", "#9c96c6", "#9d7bff", "starfield", "static"),
    (16, "bloodlust", "Bloodlust", ["Manix648", "and more"],
     "The one that taught a generation what an extreme demon was.",
     "#0a0202", "#ffe7e7", "#bd8080", "#ff1f1f", "ember", "static"),
    (17, "black-blizzard", "Black Blizzard", ["KrmaL"],
     "A whiteout with teeth.",
     "#070809", "#f4f6f8", "#a3a9b0", "#dfe6ee", "snow", "static"),
    (18, "maniacal-chains", "Maniacal Chains", ["LordDivinity"],
     "Restraint as a design principle, then abandoned.",
     "#08070a", "#f1eef4", "#a096ac", "#b06bff", "grain", "static"),
    (19, "antarctic-lights", "Antarctic Lights", ["Declan", "SkyJax", "Tolstyh", "Arcturus"],
     "Cold, and quietly spectacular.",
     "#03090e", "#e8f6fb", "#8ab3c2", "#5ff0c8", "snow", "static"),
    (20, "firework", "Firework", ["cherryteam"],
     "Bright, brief, and gone before you've understood it.",
     "#0b0610", "#fdeef6", "#bd94ac", "#ff6bd6", "grain", "static"),
    (21, "andromeda", "Andromeda", ["Insxne"],
     "A galaxy you are asked to cross on foot.",
     "#06081a", "#eceeff", "#9295c4", "#7c7dff", "starfield", "static"),
    (22, "the-golden", "The Golden", ["BoBoBoBoBoBoBo", "and more"],
     "Gilded, and heavier than it looks.",
     "#0d0a03", "#fff6e2", "#c7ab77", "#ffc44d", "chrome", "static"),
    (23, "ocular-miracle", "Ocular Miracle", ["Davphla", "and more"],
     "Something is watching, and it is beautiful about it.",
     "#040a0c", "#e8f8fb", "#89b6bf", "#3fe0f0", "caustics", "static"),
    (24, "killbot", "Killbot", ["Lithifusion"],
     "Industrial, unfeeling, extremely good at its job.",
     "#08090b", "#eef1f5", "#99a1ac", "#ff5a3c", "chrome", "static"),
    (25, "edge-of-destiny", "Edge of Destiny", ["CDMusic", "and more"],
     "Where the list begins, and the climb starts.",
     "#050810", "#eaeeff", "#8f97b8", "#6f8cff", "starfield", "static"),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for (rank, slug, name, creators, tagline, field, ink, muted, accent,
         texture, signature) in STUBS:
        record = {
            "rank": rank,
            "slug": slug,
            "name": name,
            "tagline": tagline,
            "published": False,
            "facts": {
                "creators": creators,
                "host": None,
                "verifier": None,
                "verifiedDate": None,
                "ratedDate": None,
                "attempts": None,
                "levelId": None,
                "objects": None,
                "length": None,
                "gdVersion": None,
                "song": {"name": None, "artist": None, "newgroundsId": None},
                "peakRank": None,
                "sources": [],
            },
            "theme": {
                "tier": "themed",
                "palette": {
                    "field": field,
                    "ink": ink,
                    "muted": muted,
                    "accent": accent,
                },
                "texture": texture,
                "signature": signature,
                "mood": None,
            },
            "voice": {"hook": None, "why": None, "draftedByClaude": True},
            "media": {"video": {}, "art": None, "images": []},
        }
        path = OUT / f"{rank:02d}-{slug}.json"
        path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {path.name}")


if __name__ == "__main__":
    main()
