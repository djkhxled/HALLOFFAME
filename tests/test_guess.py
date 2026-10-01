"""Demondle: data layer, schedule, built pages."""
import datetime
import json
import pathlib
import re
import unittest

from hall import guess

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"


def lv(i, **kw):
    base = {"id": i, "pcId": i, "name": f"Level {i}", "rank": i, "peak": i, "year": 2020,
            "version": "2.1", "seconds": 100, "creators": 2, "creatorNames": ["a", "b"]}
    base.update(kw)
    return base


class Derivation(unittest.TestCase):
    def test_version_is_the_one_version_tag(self):
        self.assertEqual(guess.version_from_tags(["2.1", "Long", "Wave"]), "2.1")
        self.assertEqual(guess.version_from_tags(["1.9PS", "XL"]), "1.9PS")

    def test_zero_or_two_version_tags_stop_the_run(self):
        with self.assertRaises(ValueError):
            guess.version_from_tags(["Long"])
        with self.assertRaises(ValueError):
            guess.version_from_tags(["2.1", "2.2"])

    def test_verification_year_is_the_first_verification(self):
        v = [{"achieved_at": "2021-02-16T00:00:00Z"}, {"achieved_at": "2018-08-11T21:06:19Z"}]
        self.assertEqual(guess.verification_year(v), 2018)

    def test_no_verification_stops_the_run(self):
        with self.assertRaises(ValueError):
            guess.verification_year([])
        with self.assertRaises(ValueError):
            guess.verification_year([{"achieved_at": None}])

    def test_peak_is_the_best_position_in_the_movement_history(self):
        events = [{"reason": "Added", "new_position": 40},
                  {"reason": "Moved", "new_position": 3},
                  {"reason": "Moved", "new_position": 88}]
        self.assertEqual(guess.peak_from_movement(events), 3)

    def test_an_empty_history_stops_the_run(self):
        with self.assertRaises(ValueError):
            guess.peak_from_movement([])
        with self.assertRaises(ValueError):
            guess.peak_from_movement([{"new_position": None}])

    def test_creators_are_deduplicated_ignoring_case_keeping_first_spelling(self):
        self.assertEqual(guess.dedupe_names(["Bianox", "BIANOX", "Enlex", " enlex "]),
                         ["Bianox", "Enlex"])

    def test_length_text_parses_to_whole_seconds(self):
        self.assertEqual(guess.parse_length("2m 54s (XL)"), 174)
        self.assertEqual(guess.parse_length("1m 0s (Long)"), 60)
        self.assertEqual(guess.parse_length("45s"), 45)
        with self.assertRaises(ValueError):
            guess.parse_length("long")


class PointercratePage(unittest.TestCase):
    HTML = ('<b>Level ID</b><br>99703915</div><div><b>Level Length</b><br>1m:26s</div>'
            '<div><b>Object Count</b><br>67789')

    def test_the_length_is_read_in_seconds(self):
        self.assertEqual(guess.parse_pointercrate_length(self.HTML, 99703915), 86)
        self.assertEqual(guess.parse_pointercrate_length(
            self.HTML.replace("1m:26s", "8m:45s"), 99703915), 525)

    def test_a_page_with_no_length_gives_none(self):
        html = '<b>Level ID</b><br>133175713</div><div><b>Object Count</b><br>5'
        self.assertIsNone(guess.parse_pointercrate_length(html, 133175713))

    def test_a_page_for_another_level_is_refused(self):
        with self.assertRaises(ValueError):
            guess.parse_pointercrate_length(self.HTML, 1)
        self.assertIsNone(guess.parse_pointercrate_length("<html></html>", 99703915))


class Validation(unittest.TestCase):
    def test_a_clean_pool_has_no_errors(self):
        self.assertEqual(guess.validate([lv(1), lv(2)]), [])

    def test_each_rule_is_checked(self):
        cases = {
            "empty": [],
            "duplicate id": [lv(1), lv(1, name="Other", rank=2)],
            "duplicate name": [lv(1, name="Same"), lv(2, name="same")],
            "duplicate rank": [lv(1, rank=5), lv(2, rank=5)],
            "bad version": [lv(1, version="3.0")],
            "peak below the top": [lv(1, peak=0)],
            "peak worse than the rank": [lv(5, peak=9)],
            "peak missing": [{k: v for k, v in lv(1).items() if k != "peak"}],
            "bad year": [lv(1, year=2005)],
            "bad seconds": [lv(1, seconds=3)],
            "no creators": [lv(1, creators=0, creatorNames=[])],
            "count mismatch": [lv(1, creators=3)],
        }
        for label, levels in cases.items():
            self.assertTrue(guess.validate(levels), label)


class Schedule(unittest.TestCase):
    POOL = list(range(1, 11))

    def test_a_cycle_uses_every_level_once(self):
        days = guess.make_schedule(self.POOL, datetime.date(2026, 10, 5), 7, 10)
        self.assertEqual(sorted(d["levelId"] for d in days), self.POOL)
        self.assertEqual(days[0]["date"], "2026-10-05")
        self.assertEqual(days[9]["date"], "2026-10-14")

    def test_the_same_seed_gives_the_same_order(self):
        a = guess.make_schedule(self.POOL, datetime.date(2026, 10, 5), 7, 25)
        b = guess.make_schedule(self.POOL, datetime.date(2026, 10, 5), 7, 25)
        self.assertEqual(a, b)

    def test_no_level_repeats_back_to_back_across_a_cycle_boundary(self):
        days = guess.make_schedule(self.POOL, datetime.date(2026, 10, 5), 7, 200)
        ids = [d["levelId"] for d in days]
        self.assertTrue(all(a != b for a, b in zip(ids, ids[1:])))

    def test_extending_never_changes_the_past(self):
        sched = {"launch": "2026-10-05", "seed": 7,
                 "days": guess.make_schedule(self.POOL, datetime.date(2026, 10, 5), 7, 30)}
        today = datetime.date(2026, 10, 15)
        past = [d for d in sched["days"] if d["date"] <= today.isoformat()]
        shrunk = [x for x in self.POOL if x != 4]          # one level left the list
        new = guess.extend_schedule(sched, shrunk, today, lookahead=40)
        self.assertEqual([d for d in new["days"] if d["date"] <= today.isoformat()], past)
        future = [d["levelId"] for d in new["days"] if d["date"] > today.isoformat()]
        self.assertNotIn(4, future)
        self.assertGreaterEqual(len(new["days"]), (today - datetime.date(2026, 10, 5)).days + 40)

    def test_dates_are_contiguous_from_launch(self):
        sched = {"launch": "2026-10-05", "seed": 7, "days": []}
        new = guess.extend_schedule(sched, self.POOL, datetime.date(2026, 10, 1), lookahead=30)
        dates = [datetime.date.fromisoformat(d["date"]) for d in new["days"]]
        self.assertEqual(dates[0], datetime.date(2026, 10, 5))
        self.assertTrue(all((b - a).days == 1 for a, b in zip(dates, dates[1:])))

    def test_day_numbers_count_from_one(self):
        self.assertEqual(guess.day_number("2026-10-05", "2026-10-05"), 1)
        self.assertEqual(guess.day_number("2026-10-05", "2026-10-17"), 13)


class PageData(unittest.TestCase):
    def test_json_is_safe_inside_a_script_tag(self):
        levels = [lv(1, name="</script><b>x")]
        out = guess.data_json(levels, {"launch": "2026-10-05", "seed": 1,
                                       "days": [{"date": "2026-10-05", "levelId": 1}]},
                              "2026-10-01", {})
        self.assertNotIn("</script>", out)
        data = json.loads(out.replace("<\\/", "</"))
        self.assertEqual(data["levels"][0]["n"], "</script><b>x")
        self.assertEqual(data["launch"], "2026-10-05")
        self.assertEqual(data["sched"], [1])

    def test_levels_use_the_short_keys_the_script_reads(self):
        out = json.loads(guess.data_json([lv(1)], {"launch": "2026-10-05", "seed": 1,
                                                    "days": [{"date": "2026-10-05", "levelId": 1}]},
                                         "2026-10-01", {1: "deimos"}).replace("<\\/", "</"))
        self.assertEqual(sorted(out["levels"][0]), ["c", "cn", "id", "n", "p", "r", "s", "v", "y"])
        self.assertEqual(out["hall"], {"1": "deimos"})
        self.assertEqual(out["fetched"], "2026-10-01")


class Promises(unittest.TestCase):
    def test_the_browser_version_scale_matches_the_build(self):
        code = (ROOT / "src" / "js" / "guess-core.js").read_text(encoding="utf-8")
        m = re.search(r"var VERSIONS = (\[[^\]]*\]);", code)
        self.assertEqual(json.loads(m.group(1)), guess.VERSIONS)

    def test_the_check_page_exists_and_loads_the_real_module(self):
        page = (ROOT / "tests" / "guess.check.html").read_text(encoding="utf-8")
        self.assertIn("../src/js/guess-core.js", page)


class RealSnapshot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snap = guess.load_snapshot(ROOT / "data" / "guess" / "demonlist.json")
        cls.sched = guess.load_schedule(ROOT / "data" / "guess" / "schedule.json")
        cls.levels = cls.snap["levels"]

    def test_the_pool_is_valid(self):
        self.assertEqual(guess.validate(self.levels), [])

    def test_it_is_the_main_and_extended_list(self):
        self.assertGreaterEqual(len(self.levels), 60)
        self.assertLessEqual(max(l["rank"] for l in self.levels), 150)

    def test_every_length_has_a_known_source(self):
        for l in self.levels:
            self.assertIn(l["lengthSource"], {"override", "pointercrate", "wiki.gg", "fandom"}, l["name"])

    def test_the_schedule_only_names_levels_in_the_pool(self):
        pool = {l["id"] for l in self.levels}
        past_and_future = [d["levelId"] for d in self.sched["days"]]
        self.assertTrue(set(past_and_future) <= pool)

    def test_the_schedule_covers_the_next_six_months(self):
        last = datetime.date.fromisoformat(self.sched["days"][-1]["date"])
        self.assertGreaterEqual((last - datetime.date.today()).days, 180)

    def test_the_schedule_launch_matches_its_first_day(self):
        self.assertEqual(self.sched["days"][0]["date"], self.sched["launch"])

    def test_every_override_is_applied_and_explained(self):
        ov = json.loads((ROOT / "data" / "guess" / "overrides.json").read_text(encoding="utf-8"))
        by_id = {str(l["id"]): l for l in self.levels}
        for lid, entry in ov.items():
            self.assertTrue(entry.get("why"), f"{lid} has an override with no reason")
            if lid in by_id and "year" in entry:
                self.assertEqual(by_id[lid]["year"], entry["year"], by_id[lid]["name"])
            if lid in by_id and "seconds" in entry:
                self.assertEqual(by_id[lid]["seconds"], entry["seconds"], by_id[lid]["name"])

    def test_the_hall_levels_agree_with_the_halls_own_verification_years(self):
        """The Hall's pages were checked by hand. Where a level is in both, the year the
        game uses must be the Hall's."""
        pool = {l["id"]: l for l in self.levels}
        for f in (ROOT / "data" / "levels").glob("*.json"):
            facts = json.loads(f.read_text(encoding="utf-8")).get("facts") or {}
            lid, date = facts.get("levelId"), facts.get("verifiedDate")
            if lid and date and int(lid) in pool:
                self.assertEqual(pool[int(lid)]["year"], int(date[:4]), f.name)

    def test_hall_levels_are_in_the_pool_when_they_should_be(self):
        """Every ranked Hall level on the Demonlist top 150 keeps a creators count
        that is at least the number the Hall page credits' unique names."""
        pool = {l["id"]: l for l in self.levels}
        for f in (ROOT / "data" / "levels").glob("*.json"):
            facts = json.loads(f.read_text(encoding="utf-8")).get("facts") or {}
            lid = facts.get("levelId")
            if lid and int(lid) in pool:
                self.assertGreaterEqual(pool[int(lid)]["creators"], 1, f.name)


class BuiltPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import subprocess
        subprocess.run(["python3", "build.py"], cwd=ROOT, check=True, capture_output=True)
        cls.html = (DOCS / "demondle" / "index.html").read_text(encoding="utf-8")
        cls.site = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))

    def test_the_page_exists_with_its_title_from_site_json(self):
        self.assertIn(f"<title>{self.site['guess']['title']}</title>", self.html)
        self.assertIn(self.site["guess"]["lede"].split(".")[0], self.html)

    def test_the_data_blob_is_valid_and_complete(self):
        m = re.search(r'<script type="application/json" id="guess-data">(.*?)</script>', self.html, re.S)
        data = json.loads(m.group(1).replace("<\\/", "</"))
        snap = guess.load_snapshot(ROOT / "data" / "guess" / "demonlist.json")
        self.assertEqual(len(data["levels"]), len(snap["levels"]))
        self.assertEqual(data["fetched"], snap["fetched"])

    def test_scripts_load_core_before_ui(self):
        self.assertLess(self.html.index("guess-core.js"), self.html.index("guess.js"))

    def test_the_hooks_the_script_needs_exist(self):
        for hook in ("data-guess", "data-input", "data-options", "data-board", "data-status",
                     "data-live", "data-result", "data-share", "data-next", "data-countdown",
                     "data-sound", "data-stats-daily", "data-stats-infinite", "data-result-link"):
            self.assertIn(hook, self.html, hook)
        self.assertEqual(self.html.count('name="mode"'), 2)

    def test_the_input_is_a_labelled_combobox(self):
        self.assertIn('role="combobox"', self.html)
        self.assertRegex(self.html, r'<label[^>]*for="guess-input"')
        self.assertIn('aria-controls=', self.html)

    def test_a_ranked_hall_level_in_the_pool_links_back(self):
        m = re.search(r'<script type="application/json" id="guess-data">(.*?)</script>', self.html, re.S)
        data = json.loads(m.group(1).replace("<\\/", "</"))
        for lid, slug in data["hall"].items():
            self.assertTrue((DOCS / "levels" / slug / "index.html").exists(), slug)


class Hub(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import subprocess
        subprocess.run(["python3", "build.py"], cwd=ROOT, check=True, capture_output=True)
        cls.hub = (DOCS / "games" / "index.html").read_text(encoding="utf-8")
        cls.pages = {p: (DOCS / p / "index.html").read_text(encoding="utf-8")
                     for p in ("game", "demondle", "games")}
        cls.home = (DOCS / "index.html").read_text(encoding="utf-8")

    def test_the_hub_lists_both_games(self):
        self.assertIn('href="../game/"', self.hub)
        self.assertIn('href="../demondle/"', self.hub)

    def test_the_tab_is_called_games_everywhere(self):
        for name, html in list(self.pages.items()) + [("home", self.home)]:
            m = re.search(r'<nav class="topnav".*?</nav>', html, re.S)
            self.assertIn(">Games</a>", m.group(0), name)
            self.assertNotIn(">Game</a>", m.group(0), name)

    def test_the_games_tab_is_current_on_the_hub_and_both_games(self):
        for name in ("game", "demondle", "games"):
            m = re.search(r'<nav class="topnav".*?</nav>', self.pages[name], re.S).group(0)
            self.assertEqual(m.count('aria-current="page"'), 1, name)
            self.assertRegex(m, r'<a class="topnav__link"[^>]*aria-current="page">Games</a>', name)

    def test_the_old_game_page_still_builds(self):
        self.assertIn("Name every extreme demon".lower(), self.pages["game"].lower())


class Moved(unittest.TestCase):
    def test_the_old_address_forwards_to_the_new_one(self):
        site = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))
        old = (DOCS / "guess" / "index.html").read_text(encoding="utf-8")
        self.assertIn('http-equiv="refresh" content="0; url=../demondle/"', old)
        self.assertIn(f'rel="canonical" href="https://{site["domain"]}/demondle/"', old)
        self.assertIn('href="../demondle/"', old)       # a visible link for anyone who stays

    def test_the_game_is_at_the_new_address(self):
        self.assertTrue((DOCS / "demondle" / "index.html").is_file())
        page = (DOCS / "demondle" / "index.html").read_text(encoding="utf-8")
        self.assertIn("guess-core.js", page)


class ShareCard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import subprocess
        subprocess.run(["python3", "build.py"], cwd=ROOT, check=True, capture_output=True)
        cls.home = (DOCS / "index.html").read_text(encoding="utf-8")

    def test_the_home_page_names_a_share_image_by_an_absolute_address(self):
        url = re.search(r'property="og:image" content="([^"]+)"', self.home).group(1)
        self.assertTrue(url.startswith("https://"), url)
        self.assertIn('name="twitter:card" content="summary_large_image"', self.home)
        self.assertIn(f'name="twitter:image" content="{url}"', self.home)

    def test_the_image_exists_and_is_the_size_the_tags_claim(self):
        import struct
        url = re.search(r'property="og:image" content="([^"]+)"', self.home).group(1)
        path = DOCS / url.split("/", 3)[3]
        data = path.read_bytes()
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        w, h = struct.unpack(">II", data[16:24])
        self.assertEqual((w, h), (1200, 630))
        self.assertIn('property="og:image:width" content="1200"', self.home)
        self.assertIn('property="og:image:height" content="630"', self.home)

    def test_it_has_alt_text(self):
        self.assertRegex(self.home, r'property="og:image:alt" content="[^"]{20,}"')

    @staticmethod
    def _card(page_html):
        m = re.search(r'property="og:image" content="([^"]+)"', page_html)
        return m.group(1) if m else None

    def _pages(self):
        """Every built page that is meant to be shared: all but the 404 and the
        forwarding page for the old address."""
        skip = {DOCS / "404.html", DOCS / "guess" / "index.html"}
        return [p for p in DOCS.rglob("*.html") if p not in skip]

    def test_every_shareable_page_has_a_card_that_exists_at_the_right_size(self):
        import struct
        for page in self._pages():
            url = self._card(page.read_text(encoding="utf-8"))
            self.assertIsNotNone(url, f"{page} has no share image")
            data = (DOCS / url.split("/", 3)[3]).read_bytes()
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n", url)
            self.assertEqual(struct.unpack(">II", data[16:24]), (1200, 630), url)

    def test_every_ranked_level_shares_the_home_card(self):
        home = self._card(self.home)
        levels = list((DOCS / "levels").glob("*/index.html"))
        self.assertGreaterEqual(len(levels), 30)
        for page in levels:
            self.assertEqual(self._card(page.read_text(encoding="utf-8")), home, str(page))

    def test_the_other_pages_each_have_their_own_card(self):
        home = self._card(self.home)
        own = {}
        for name in ("game", "demondle", "games", "privacy", "terms", "credits"):
            url = self._card((DOCS / name / "index.html").read_text(encoding="utf-8"))
            self.assertNotEqual(url, home, name)
            own[name] = url
        self.assertEqual(len(set(own.values())), len(own), "two pages share a card")


class Privacy(unittest.TestCase):
    def test_the_guess_scripts_make_no_network_call(self):
        for name in ("guess.js", "guess-core.js"):
            code = re.sub(r"/\*.*?\*/", "", (ROOT / "src" / "js" / name).read_text(encoding="utf-8"), flags=re.S)
            code = re.sub(r"//[^\n]*", "", code)
            for bad in ("fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket", "EventSource", "import("):
                self.assertNotIn(bad, code, f"{name}: {bad}")

    def test_the_storage_key_is_the_one_the_policy_names(self):
        code = (ROOT / "src" / "js" / "guess.js").read_text(encoding="utf-8")
        key = re.search(r'var KEY = "([^"]+)"', code).group(1)
        privacy = (ROOT / "pages" / "privacy.html").read_text(encoding="utf-8")
        self.assertIn(key, privacy)

    def test_the_policy_says_what_guess_stores(self):
        privacy = (DOCS / "privacy" / "index.html").read_text(encoding="utf-8")
        for word in ("Demondle", "streak"):
            self.assertIn(word, privacy)


if __name__ == "__main__":
    unittest.main()
