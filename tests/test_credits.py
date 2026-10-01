"""How a level's builders are written: in full up to five, "HOST & N more" past that."""
import json
import pathlib
import re
import unittest

from hall import render

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"


def names(n):
    return [f"n{i}" for i in range(n)]


class CreditHtml(unittest.TestCase):
    def test_five_or_fewer_are_written_out(self):
        for n in range(1, 6):
            out = render.credit_html(names(n), "n0")
            self.assertEqual(out, ", ".join(names(n)))
            self.assertNotIn("more", out)

    def test_six_or_more_collapse_to_host_and_a_count(self):
        out = render.credit_html(names(6), "n0")
        self.assertIn("n0 &amp; 5 more", out)
        out = render.credit_html(names(29), "n0")
        self.assertIn("n0 &amp; 28 more", out)

    def test_the_host_leads_even_when_not_listed_first(self):
        out = render.credit_html(["a", "b", "c", "d", "e", "f", "g"], "c")
        self.assertIn("c &amp; 6 more", out)

    def test_an_unlisted_host_falls_back_to_the_first_name(self):
        out = render.credit_html(["a", "b", "c", "d", "e", "f"], "nobody")
        self.assertIn("a &amp; 5 more", out)

    def test_the_tooltip_carries_every_name_once(self):
        crew = names(12)
        out = render.credit_html(crew, "n0")
        tip = re.search(r'class="credit__all"[^>]*>(.*?)</span></span>', out, re.S).group(1)
        for n in crew:
            self.assertEqual(len(re.findall(rf"\b{n}\b", tip)), 1, n)
        self.assertIn("All 12 credited", tip)

    def test_names_are_escaped(self):
        out = render.credit_html(["<b>x</b>"] + names(6), "<b>x</b>")
        self.assertNotIn("<b>", out)

    def test_with_a_tip_id_it_is_a_button_the_tooltip_describes(self):
        out = render.credit_html(names(8), "n0", tip_id="t1")
        self.assertIn('<button type="button" class="credit" aria-describedby="t1">', out)
        self.assertIn('id="t1" role="tooltip"', out)

    def test_inside_a_link_there_is_no_control_and_the_names_stay_out_of_the_link_name(self):
        out = render.credit_html(names(8), "n0")
        self.assertNotIn("<button", out)
        self.assertIn('class="credit__all" aria-hidden="true"', out)

    def test_nobody_credited_is_a_dash(self):
        self.assertIn("nil", render.credit_html([], None))

    def test_the_roster_section_follows_the_same_cut(self):
        self.assertEqual(render.ROSTER_MIN, render.CREDIT_MAX + 1)
        self.assertEqual(render.roster_html({"creators": names(5)}), "")
        self.assertIn("roster", render.roster_html({"creators": names(6)}))


class CoHosts(unittest.TestCase):
    def test_every_co_host_leads_and_the_count_drops_by_that_many(self):
        crew = ["a", "b", "c", "d", "e", "f", "g", "h"]
        out = render.credit_html(crew, ["b", "a"])
        self.assertIn("b, a &amp; 6 more", out)

    def test_a_co_host_who_is_not_credited_is_ignored(self):
        crew = ["a", "b", "c", "d", "e", "f"]
        out = render.credit_html(crew, ["a", "ghost"])
        self.assertIn("a &amp; 5 more", out)


def _others(facts):
    crew = facts["creators"]
    host = facts.get("host")
    hosts = [host] if isinstance(host, str) else list(host or [])
    lead = [h for h in hosts if h in crew] or crew[:1]
    return len(crew) - len(lead)


class InTheBuild(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.levels = {}
        for f in sorted((ROOT / "data" / "levels").glob("*.json")):
            d = json.loads(f.read_text(encoding="utf-8"))
            cls.levels[d["slug"]] = d

    def test_every_level_page_header_follows_the_rule(self):
        for slug, lv in self.levels.items():
            facts = lv.get("facts") or {}
            crew = facts.get("creators") or []
            page = (DOCS / "levels" / slug / "index.html").read_text(encoding="utf-8")
            if len(crew) > render.CREDIT_MAX:
                self.assertIn(f"&amp; {_others(facts)} more", page, slug)
                self.assertEqual(page.count('class="credit"'), 1, slug)
            elif crew:
                self.assertNotIn('class="credit"', page, slug)
                self.assertIn(", ".join(crew), page, slug)

    def test_the_home_list_follows_the_rule(self):
        home = (DOCS / "index.html").read_text(encoding="utf-8")
        long_crews = [lv for lv in self.levels.values()
                      if len((lv.get("facts") or {}).get("creators") or []) > render.CREDIT_MAX]
        self.assertEqual(home.count('class="credit"'), len(long_crews))
        for lv in long_crews:
            self.assertIn(f"&amp; {_others(lv['facts'])} more", home, lv["slug"])

    def test_no_page_has_two_tooltips_with_the_same_id(self):
        for page in DOCS.rglob("index.html"):
            ids = re.findall(r'id="([^"]+)"', page.read_text(encoding="utf-8"))
            self.assertEqual(len(ids), len(set(ids)), str(page))


if __name__ == "__main__":
    unittest.main()
