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

    def test_no_youtube_iframe_ships_in_the_html(self):
        for slug in ("deimos", "nhelv"):
            html = (DOCS / "levels" / slug / "index.html").read_text(encoding="utf-8")
            self.assertNotIn("<iframe", html, f"{slug} ships an iframe on load")

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

    def test_level_fonts_are_requested_when_declared(self):
        html = (DOCS / "levels" / "nhelv" / "index.html").read_text(encoding="utf-8")
        self.assertIn("Bodoni+Moda", html)
        self.assertIn("Cutive+Mono", html)

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

    def test_notes_are_not_published(self):
        self.assertFalse((DOCS / "superpowers").exists())
        self.assertFalse((DOCS / "specs").exists())


if __name__ == "__main__":
    unittest.main()
