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

    def test_unpublished_levels_get_no_page(self):
        self.assertFalse((DOCS / "levels" / "killbot").exists())

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

    def test_nojekyll_is_written(self):
        self.assertTrue((DOCS / ".nojekyll").is_file())

    def test_notes_are_not_published(self):
        self.assertFalse((DOCS / "superpowers").exists())
        self.assertFalse((DOCS / "specs").exists())


if __name__ == "__main__":
    unittest.main()
