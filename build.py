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


def relativize(text: str, depth: int) -> str:
    """Turn site-internal absolute URLs into relative ones.

    The site has to work at three addresses: localhost at the root,
    djkhxled.github.io/HALLOFFAME/ under a project path, and b4ylor.com at
    the apex. A hardcoded prefix is right for exactly one of them and silently
    breaks the others, which is what left the pages unstyled. Relative URLs
    are correct at all three with nothing to configure and nothing to flip
    when the domain goes live.

    depth is how many directories deep the page sits below the site root:
    index.html is 0, privacy/index.html is 1, levels/deimos/index.html is 2.
    """
    prefix = "../" * depth if depth else ""

    def fix(m):
        return f'{m.group(1)}="{prefix}{m.group(2)}'

    # href="/x" and src="/x", but never "//host" (protocol-relative)
    text = re.sub(r'\b(href|src)="/(?!/)([^"]*)', fix, text)
    # a bare href="/" becomes "./" rather than an empty attribute
    text = text.replace('href=""', 'href="./"').replace('src=""', 'src="./"')
    return text


def relativize_css(text: str, depth: int) -> str:
    """Same, for url(/assets/...) inside a stylesheet. depth is measured from
    the stylesheet's own directory, since CSS URLs resolve against it."""
    prefix = "../" * depth if depth else ""
    return re.sub(r'url\(/(?!/)', f"url({prefix}", text)


def texture_class(theme: dict) -> str:
    """The texture layer's classes. A level may layer one modifier over a
    shared texture -- Slaughterhouse takes ember and swaps its glyphs for
    inverted pentagrams."""
    parts = ["texture", f"texture--{theme.get('texture') or 'none'}"]
    mod = theme.get("textureMod")
    if mod:
        parts.append(f"texture--{mod}")
    return " ".join(parts)


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
            "spotlight_html": render.spotlight_html(theme),
            "statblock_html": render.statblock_html(level.get("facts")),
            "roster_html": render.roster_html(level.get("facts")),
            "arc_html": render.arc_html(level.get("voice")),
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

    # googleFonts stays in the data as the record of which faces a level
    # uses, but nothing is requested from Google: tools/fetch_vendor.py has
    # pulled every face into src/fonts and fonts.css declares them all.

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
            "texture_class": texture_class(theme),
            "title": f'{level["name"]} — #{level["rank"]} · {site["title"]}',
            "description": level.get("tagline", ""),
            "head_extra_html": head_extra,
            "body_html": body,
            "disclaimer": site["disclaimer"],
            "colophon": site["colophon"],
            "footer_links_html": render.footer_links_html(site["docs"]),
        },
    )


def build_doc(doc: dict, site: dict, base_tpl: str, page_tpl: str) -> str:
    body = read(ROOT / "pages" / f"{doc['slug']}.html")
    body += render.doc_footer_html(site.get("contact"), site.get("updated", ""))
    inner = render.fill(
        page_tpl,
        {
            "eyebrow": doc["eyebrow"],
            "heading": doc["heading"],
            "lede": doc["lede"],
            "meta_left": site["title"],
            "meta_right": f"Updated {site.get('updated', '')}",
            "body_html": body,
            "docnav_html": render.docnav_html(site["docs"], doc["slug"]),
        },
    )
    return render.fill(
        base_tpl,
        {
            "slug": f"doc-{doc['slug']}",
            "signature": "static",
            "texture_class": "texture texture--grain",
            "title": f"{strip_tags(doc['heading'])} · {site['title']}",
            "description": doc["lede"],
            "head_extra_html": (
                f'<style>[data-level="doc-{doc["slug"]}"] .hero__title'
                f'{{font-size:{render.hero_size(strip_tags(doc["heading"]))}}}'
                "</style>"
            ),
            "body_html": inner,
            "disclaimer": site["disclaimer"],
            "colophon": site["colophon"],
            "footer_links_html": render.footer_links_html(site["docs"]),
        },
    )


def strip_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).replace("&amp;", "&")


def build_index(levels: list[dict], site: dict, base_tpl: str, index_tpl: str) -> str:
    body = render.fill(
        index_tpl,
        {
            "eyebrow": site["eyebrow"],
            "title_line_html": site["titleHtml"],
            "meta_left": site["metaLeft"],
            "meta_right": site["metaRight"],
            "lede": site["lede"],
            "art_html": read(ROOT / "src" / "art" / "index.svg")
            if (ROOT / "src" / "art" / "index.svg").exists() else "",
            "countdown_html": render.countdown_html(levels),
            "about_html": site["aboutHtml"],
        },
    )
    return render.fill(
        base_tpl,
        {
            "slug": "index",
            "signature": "static",
            "texture_class": "texture texture--starfield",
            "title": site["title"],
            "description": site["description"],
            "head_extra_html": (
                "<style>[data-level=\"index\"] .hero__title{font-size:"
                f"{render.hero_size(site['heroLongestLine'])}}}</style>"
            ),
            "body_html": body,
            "disclaimer": site["disclaimer"],
            "colophon": site["colophon"],
            "footer_links_html": render.footer_links_html(site["docs"]),
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

    # docs/ is wiped and rebuilt every run, so a CNAME committed by hand
    # disappears on the next build. Set site.domain and it is written here
    # instead, which is the only way it survives.
    domain = site.get("domain")
    if domain:
        write(DOCS / "CNAME", domain + "\n")

    for sub in ("css", "js", "art", "fonts"):
        src = ROOT / "src" / sub
        if src.exists():
            shutil.copytree(src, DOCS / "assets" / sub)

    for css in (DOCS / "assets" / "css").rglob("*.css"):
        depth = len(css.relative_to(DOCS).parts) - 1
        css.write_text(relativize_css(css.read_text(encoding="utf-8"), depth),
                       encoding="utf-8")

    base_tpl = read(TEMPLATES / "base.html")
    index_tpl = read(TEMPLATES / "index.html")
    level_tpl = read(TEMPLATES / "level.html")

    stamp = asset_stamp()

    def stamped(html: str, depth: int = 0) -> str:
        html = re.sub(r'(/assets/(?:css|js)/[^"\']+?\.(?:css|js))',
                      lambda m: f"{m.group(1)}?v={stamp}", html)
        return relativize(html, depth)

    write(DOCS / "index.html",
          stamped(build_index(levels, site, base_tpl, index_tpl)))
    pages = 1

    page_tpl = read(TEMPLATES / "page.html")
    for doc in site.get("docs", []):
        write(DOCS / doc["slug"] / "index.html",
              stamped(build_doc(doc, site, base_tpl, page_tpl), 1))
        pages += 1
    if not site.get("contact"):
        print("  ! no site.contact set — the policy pages say so in place "
              "of an address", file=sys.stderr)

    published = [lv for lv in levels if lv.get("published")]
    by_rank = {lv["rank"]: lv for lv in levels}
    for level in published:
        prev = by_rank.get(level["rank"] - 1)
        nxt = by_rank.get(level["rank"] + 1)
        prev = prev if prev and prev.get("published") else None
        nxt = nxt if nxt and nxt.get("published") else None
        html = stamped(
            build_level(level, site, prev, nxt, base_tpl, level_tpl), 2)
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
