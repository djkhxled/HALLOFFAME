#!/usr/bin/env python3
"""Build Baylor's Hall of Extremes into docs/.

Usage: python3 build.py
Exit 0 on success, 1 if validation fails (nothing is written on failure).
"""

import hashlib
import json
import pathlib
import re
import shutil
import sys

from hall import render
from hall.data import load_levels, validate_levels, voice_progress

ROOT = pathlib.Path(__file__).resolve().parent
DOCS = ROOT / "docs"
TEMPLATES = ROOT / "templates"


def asset_stamp() -> str:
    """A short hash over every CSS and JS file.

    Browsers cache /assets/... aggressively, so a rebuilt stylesheet can keep
    showing the old page and look like a bug in the change rather than in the
    cache. Stamping the URLs makes a rebuild always win, and the stamp only
    moves when the assets actually do.
    """
    h = hashlib.sha256()
    for sub in ("css", "js"):
        for f in sorted((ROOT / "src" / sub).rglob("*")):
            if f.is_file():
                h.update(f.name.encode())
                h.update(f.read_bytes())
    return h.hexdigest()[:10]


def read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def meta_pair(level: dict) -> tuple[str, str]:
    facts = level.get("facts") or {}
    creators = facts.get("creators") or []
    left = ", ".join(str(c) for c in creators) if creators else "—"
    verifier = facts.get("verifier")
    date = facts.get("verifiedDate") or ""
    year = date[:4] if date else ""
    right = f"Verified by {verifier}" if verifier else "—"
    if year:
        right += f" · {year}"
    return left, right


def build_level(level: dict, site: dict, prev, nxt, base_tpl: str, level_tpl: str) -> str:
    slug = level["slug"]
    theme = level.get("theme") or {}
    media = level.get("media") or {}

    # SVG is inlined so level CSS can reach into it; raster art ships as an
    # <img> and is served from the copied asset tree.
    art_html = ""
    art_rel = media.get("art")
    if art_rel:
        if art_rel.endswith(".svg"):
            art_html = read(ROOT / art_rel)
        else:
            name = pathlib.Path(art_rel).name
            art_html = (
                f'<img class="hero__img" src="/assets/art/{name}" alt="" '
                f'fetchpriority="high" decoding="async">'
            )

    bespoke_path = ROOT / "bespoke" / f"{slug}.html"
    bespoke_html = read(bespoke_path) if bespoke_path.exists() else ""

    left, right = meta_pair(level)

    body = render.fill(
        level_tpl,
        {
            "rank": level["rank"],
            "name": level["name"],
            "native_html": (
                f'<p class="hero__native" lang="{theme.get("nativeLang", "ja")}">'
                f'{render.esc(theme["nativeName"])}</p>'
                if theme.get("nativeName") else ""
            ),
            "tagline": level.get("tagline", ""),
            "art_html": art_html,
            "meta_left": left,
            "meta_right": right,
            "bespoke_html": bespoke_html,
            "statblock_html": render.statblock_html(level.get("facts")),
            "voice_html": render.voice_html(level.get("voice")),
            "video_html": render.video_html(media, level["name"]),
            "player_html": render.player_html(level.get("facts")),
            "ranknav_html": render.ranknav_html(prev, nxt),
            "sources_html": render.sources_html(level.get("facts")),
        },
    )

    css_path = ROOT / "src" / "css" / "levels" / f"{slug}.css"

    # The level's palette must reach the page before anything paints, or the
    # page renders in the neutral defaults. Level CSS uses [data-level=...],
    # which outranks :root, so it can still override any of these.
    head_extra = ""
    palette = render.palette_style(level)
    if palette:
        head_extra += f"<style>:root{{{palette}}}</style>"

    # A level may bring its own typefaces when the shared stack cannot carry
    # its identity. Loaded before the level stylesheet so it can use them.
    families = theme.get("googleFonts") or []
    if families:
        query = "&".join(f"family={f}" for f in families)
        head_extra += (
            f'<link href="https://fonts.googleapis.com/css2?{query}'
            f'&display=swap" rel="stylesheet">'
        )

    # A themed level owns no stylesheet, so its display face is declared
    # here; bespoke levels can still override it in their own CSS.
    face = theme.get("displayFont")
    face_rule = f"--font-display:{face};" if face else ""

    head_extra += (
        f"<style>[data-level=\"{slug}\"]{{{face_rule}}}"
        f"[data-level=\"{slug}\"] .hero__title{{font-size:"
        f"{render.hero_size(level['name'])}}}</style>"
    )
    if css_path.exists():
        head_extra += f'<link rel="stylesheet" href="/assets/css/levels/{slug}.css">'

    return render.fill(
        base_tpl,
        {
            "slug": slug,
            "signature": theme.get("signature") or "static",
            "texture": theme.get("texture") or "none",
            "title": f'{level["name"]} — #{level["rank"]} · {site["title"]}',
            "description": level.get("tagline", ""),
            "head_extra_html": head_extra,
            "body_html": body,
            "disclaimer": site["disclaimer"],
            "colophon": site["colophon"],
        },
    )


def build_index(levels: list[dict], site: dict, base_tpl: str, index_tpl: str) -> str:
    body = render.fill(
        index_tpl,
        {
            "eyebrow": site["eyebrow"],
            "title_line_html": site["titleHtml"],
            "meta_left": site["metaLeft"],
            "meta_right": site["metaRight"],
            "lede": site["lede"],
            "countdown_html": render.countdown_html(levels),
            "about_html": site["aboutHtml"],
        },
    )
    return render.fill(
        base_tpl,
        {
            "slug": "index",
            "signature": "static",
            "texture": "starfield",
            "title": site["title"],
            "description": site["description"],
            "head_extra_html": (
                "<style>[data-level=\"index\"] .hero__title{font-size:"
                f"{render.hero_size(site['heroLongestLine'])}}}</style>"
            ),
            "body_html": body,
            "disclaimer": site["disclaimer"],
            "colophon": site["colophon"],
        },
    )


def main() -> int:
    site = json.loads(read(ROOT / "data" / "site.json"))
    levels = load_levels(ROOT / "data" / "levels")

    errors = validate_levels(levels, ROOT)
    if errors:
        print("build failed — validation errors:\n", file=sys.stderr)
        for err in errors:
            print(f"  ✗ {err}", file=sys.stderr)
        return 1

    if DOCS.exists():
        shutil.rmtree(DOCS)
    DOCS.mkdir(parents=True)

    for sub in ("css", "js", "art"):
        src = ROOT / "src" / sub
        if src.exists():
            shutil.copytree(src, DOCS / "assets" / sub)

    base_tpl = read(TEMPLATES / "base.html")
    index_tpl = read(TEMPLATES / "index.html")
    level_tpl = read(TEMPLATES / "level.html")

    stamp = asset_stamp()

    def stamped(html: str) -> str:
        return re.sub(r'(/assets/(?:css|js)/[^"\']+?\.(?:css|js))',
                      lambda m: f"{m.group(1)}?v={stamp}", html)

    write(DOCS / "index.html",
          stamped(build_index(levels, site, base_tpl, index_tpl)))
    pages = 1

    published = [lv for lv in levels if lv.get("published")]
    by_rank = {lv["rank"]: lv for lv in levels}
    for level in published:
        prev = by_rank.get(level["rank"] - 1)
        nxt = by_rank.get(level["rank"] + 1)
        prev = prev if prev and prev.get("published") else None
        nxt = nxt if nxt and nxt.get("published") else None
        html = stamped(build_level(level, site, prev, nxt, base_tpl, level_tpl))
        write(DOCS / "levels" / level["slug"] / "index.html", html)
        pages += 1

    (DOCS / ".nojekyll").write_text("", encoding="utf-8")

    own, total = voice_progress(levels)
    print("Hall of Extremes — build")
    print(f"  levels:  {len(levels)} records, {len(published)} published")
    print(f"  pages:   {pages} written")
    print(f"  voice:   {own}/{total} in your words")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
