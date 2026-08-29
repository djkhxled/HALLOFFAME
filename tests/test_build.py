import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"


class TestBuild(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(
            ["python3", "build.py"], cwd=ROOT, check=True, capture_output=True
        )

    def test_emits_the_landing_page(self):
        self.assertTrue((DOCS / "index.html").is_file())

    def test_emits_both_published_levels(self):
        self.assertTrue((DOCS / "levels" / "deimos" / "index.html").is_file())
        self.assertTrue((DOCS / "levels" / "nhelv" / "index.html").is_file())

    def test_pages_exist_for_exactly_the_published_levels(self):
        """Named slugs go stale as levels ship; check the rule instead."""
        import json
        published = set()
        for jf in (ROOT / "data" / "levels").glob("*.json"):
            rec = json.loads(jf.read_text(encoding="utf-8"))
            if rec.get("published"):
                published.add(rec["slug"])
        built = {d.name for d in (DOCS / "levels").iterdir() if d.is_dir()}
        self.assertEqual(built, published)

    def test_index_lists_all_25_ranks(self):
        html = (DOCS / "index.html").read_text(encoding="utf-8")
        self.assertEqual(html.count('class="countdown__entry'), 25)

    def test_content_is_server_rendered_not_js_injected(self):
        html = (DOCS / "levels" / "nhelv" / "index.html").read_text(encoding="utf-8")
        self.assertIn("SrGuillester", html)
        self.assertIn("Silentroom", html)
        self.assertIn("Why", html)

    def test_no_youtube_iframe_ships_on_any_page(self):
        """Footage is click-to-load on every page, so nothing is requested
        from YouTube until a reader asks for it. The privacy page says so."""
        for f in sorted(DOCS.rglob("index.html")):
            html = f.read_text(encoding="utf-8")
            self.assertNotIn("<iframe", html,
                             f"{f.relative_to(DOCS)} ships an iframe on load")

    def test_footage_links_are_real_video_ids(self):
        import json
        import re
        bad = []
        for jf in sorted((ROOT / "data" / "levels").glob("*.json")):
            rec = json.loads(jf.read_text(encoding="utf-8"))
            vid = (rec["media"].get("video") or {}).get("youtubeId")
            if vid and not re.fullmatch(r"[A-Za-z0-9_-]{11}", vid):
                bad.append(f"{rec['slug']}: {vid!r}")
        self.assertEqual(bad, [])

    def test_unknown_facts_render_as_a_dash(self):
        html = (DOCS / "levels" / "nhelv" / "index.html").read_text(encoding="utf-8")
        self.assertIn("mdash", html)
        self.assertNotIn(">None<", html)

    def test_sources_are_cited_on_published_pages(self):
        html = (DOCS / "levels" / "deimos" / "index.html").read_text(encoding="utf-8")
        self.assertIn("geometrydash.wiki.gg", html)

    def test_level_pages_ship_their_own_palette(self):
        """A level page must carry its palette, not fall back to the neutral
        defaults — a light-field level renders unreadable without it."""
        html = (DOCS / "levels" / "nhelv" / "index.html").read_text(encoding="utf-8")
        self.assertIn("--field:#eeedea", html)
        self.assertIn("--ink:#1b1b1e", html)

    def test_declared_faces_are_available_locally(self):
        """Fonts used to arrive via a Google Fonts <link> per level. They are
        self-hosted now, so the check is that every declared family has real
        @font-face rules in the one stylesheet every page loads."""
        import json
        html = (DOCS / "levels" / "nhelv" / "index.html").read_text(encoding="utf-8")
        self.assertIn("/assets/css/fonts.css", html)
        css = (DOCS / "assets" / "css" / "fonts.css").read_text(encoding="utf-8")
        for jf in (ROOT / "data" / "levels").glob("*.json"):
            rec = json.loads(jf.read_text(encoding="utf-8"))
            for spec in rec["theme"].get("googleFonts") or []:
                family = spec.split(":")[0].replace("+", " ")
                self.assertIn(f"font-family: '{family}'", css,
                              f"{rec['slug']} declares {family}, not hosted")

    def test_font_files_are_served_from_this_origin(self):
        css = (DOCS / "assets" / "css" / "fonts.css").read_text(encoding="utf-8")
        self.assertIn("/assets/fonts/", css)
        self.assertNotIn("fonts.gstatic.com", css)
        self.assertTrue(list((DOCS / "assets" / "fonts").glob("*.woff2")))

    def test_nojekyll_is_written(self):
        self.assertTrue((DOCS / ".nojekyll").is_file())

    def test_a_large_collab_shows_a_count_and_a_full_roster(self):
        """29 names would wreck the stat grid, so the cell carries the count
        and every name appears in the roster below it."""
        html = (DOCS / "levels" / "deimos" / "index.html").read_text(encoding="utf-8")
        self.assertIn("29 creators", html)
        self.assertIn('class="roster__list"', html)
        for name in ("ItsHybrid", "Yonaka", "GrenadeofTacos", "ryamu"):
            self.assertIn(f"<li>{name}</li>", html)

    def test_the_arc_states_only_the_markers_it_has(self):
        """Two stops carry a stated percentage; the other three must render an
        empty marker rather than an invented timing."""
        html = (DOCS / "levels" / "deimos" / "index.html").read_text(encoding="utf-8")
        self.assertIn('class="arc__at">30%', html)
        self.assertEqual(html.count('class="arc__at arc__at--none"'), 3)

    def test_an_arc_with_no_stated_timings_drops_the_marker_row(self):
        """Nhelv's arc states no percentages, so five empty slots would be
        five rows of nothing."""
        html = (DOCS / "levels" / "nhelv" / "index.html").read_text(encoding="utf-8")
        self.assertIn('class="arc__stop"', html)
        self.assertNotIn('class="arc__at', html)

    def test_a_nong_track_is_named_instead_of_linked(self):
        """Nhelv's in-game song ID points at a different track; linking it
        would hand the reader the wrong music."""
        html = (DOCS / "levels" / "nhelv" / "index.html").read_text(encoding="utf-8")
        self.assertIn("Silentroom", html)
        self.assertIn("player__nong", html)
        self.assertNotIn("newgrounds.com/audio", html)

    def test_cold_sweat_carries_its_own_level_id(self):
        """76543324 is Verdant Landscape by ItzNisha, and its song came across
        with it."""
        html = (DOCS / "levels" / "cold-sweat" / "index.html").read_text(encoding="utf-8")
        self.assertIn("63996127", html)
        self.assertNotIn("76543324", html)
        self.assertIn("False Noise", html)
        self.assertNotIn("Xomu", html)

    def test_kyouki_carries_its_own_level_id(self):
        """112313819 is Anathema by nikroplays, and its song and object count
        came across with it."""
        html = (DOCS / "levels" / "kyouki" / "index.html").read_text(encoding="utf-8")
        self.assertIn("86018142", html)
        self.assertNotIn("112313819", html)
        self.assertIn("Creo", html)
        self.assertNotIn("Living Tombstone", html)
        self.assertNotIn("287,445", html)

    def test_deimos_is_no_longer_a_drafted_placeholder(self):
        html = (DOCS / "levels" / "deimos" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("voice__drafted", html)
        self.assertIn("voice__body--long", html)

    def test_snow_flakes_render_at_the_size_they_were_drawn(self):
        """The flake tile must be painted 1:1. Setting background-size larger
        than the SVG canvas scales every flake up to fill the tile, which is
        how they ended up ~190px across and swamping the page."""
        import re
        css = (ROOT / "src" / "css" / "components.css").read_text(encoding="utf-8")
        block = css[css.index(".texture--snow::after {"):]
        block = block[: block.index("}")]
        canvases = [int(w) for w in re.findall(r"svg[^)]*?width='(\d+)'", block)]
        sizes = re.search(r"background-size:([^;]+);", block).group(1)
        tiles = [int(t) for t in re.findall(r"(\d+)px \d+px", sizes)]
        self.assertEqual(len(canvases), 2, "expected two flake layers")
        self.assertEqual(canvases, tiles, "flake tiles are being scaled")

    def test_pentagrams_render_at_the_size_they_were_drawn(self):
        """Same invariant as the snow flakes: tile painted 1:1."""
        import re
        css = (ROOT / "src" / "css" / "components.css").read_text(encoding="utf-8")
        block = css[css.index(".texture--ember.texture--pentagram::after {"):]
        block = block[: block.index("}")]
        canvases = [int(w) for w in re.findall(r"svg[^)]*?width='(\d+)'", block)]
        sizes = re.search(r"background-size:([^;]+);", block).group(1)
        tiles = [int(t) for t in re.findall(r"(\d+)px \d+px", sizes)]
        self.assertEqual(canvases, tiles, "pentagram tiles are being scaled")

    def test_every_declared_texture_is_implemented(self):
        """snow, ember, caustics and chrome were all declared by levels and
        rendered nothing, which is why those pages looked bare."""
        import json
        css = (ROOT / "src" / "css" / "components.css").read_text(encoding="utf-8")
        declared = set()
        for jf in (ROOT / "data" / "levels").glob("*.json"):
            rec = json.loads(jf.read_text(encoding="utf-8"))
            tex = rec["theme"].get("texture")
            if tex and tex != "none":
                declared.add(tex)
        missing = sorted(t for t in declared if f".texture--{t}" not in css)
        self.assertEqual(missing, [], f"textures with no CSS: {missing}")

    def test_internal_urls_are_relative_so_the_site_can_move(self):
        """The site has to work at localhost root, under a GitHub Pages
        project path, and later at b4ylor.com. A leading slash is correct for
        exactly one of those and leaves the others unstyled."""
        import re
        bad = []
        for f in sorted(DOCS.rglob("index.html")):
            page = str(f.relative_to(DOCS))
            html = f.read_text(encoding="utf-8")
            for m in re.finditer(r'\b(?:href|src)="(/[^/][^"]*)"', html):
                bad.append(f"{page}: {m.group(1)}")
        self.assertEqual(bad[:6], [], f"{len(bad)} root-absolute internal URLs")

    def test_relative_depth_matches_where_the_page_sits(self):
        deep = (DOCS / "levels" / "deimos" / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="../../assets/css/base.css', deep)
        self.assertIn('href="../../"', deep)
        mid = (DOCS / "privacy" / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="../assets/css/base.css', mid)
        top = (DOCS / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="assets/css/base.css', top)

    def test_stylesheet_urls_resolve_from_the_stylesheet(self):
        css = (DOCS / "assets" / "css" / "fonts.css").read_text(encoding="utf-8")
        self.assertNotIn("url(/", css)
        self.assertIn("url(../../assets/fonts/", css)
        first = css.split("url(../../assets/fonts/")[1].split(")")[0]
        self.assertTrue((DOCS / "assets" / "fonts" / first).is_file(),
                        f"fonts.css points at a file that is not there: {first}")

    def test_the_index_art_is_built_from_the_current_palettes(self):
        """The landing hero draws one shaft per level in that level's own
        accent. It is generated separately from the build, so a palette edit
        would silently leave it stale; this catches the drift."""
        import json
        svg = (DOCS / "assets" / "art" / "index.svg").read_text(encoding="utf-8")
        missing = []
        for jf in sorted((ROOT / "data" / "levels").glob("*.json")):
            rec = json.loads(jf.read_text(encoding="utf-8"))
            accent = rec["theme"]["palette"].get("accent")
            if accent and accent.lower() not in svg.lower():
                missing.append(f"{rec['slug']} ({accent})")
        self.assertEqual(missing, [],
                         "run tools/gen_index_art.py — these palettes changed")

    def test_notes_are_not_published(self):
        self.assertFalse((DOCS / "superpowers").exists())
        self.assertFalse((DOCS / "specs").exists())


if __name__ == "__main__":
    unittest.main()
