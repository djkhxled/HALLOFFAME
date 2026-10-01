"""Guess the Demon: data layer, schedule, built pages."""
import datetime
import json
import pathlib
import re
import unittest

from hall import guess

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"


def lv(i, **kw):
    base = {"id": i, "pcId": i, "name": f"Level {i}", "rank": i, "year": 2020,
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

    def test_creators_are_deduplicated_ignoring_case_keeping_first_spelling(self):
        self.assertEqual(guess.dedupe_names(["Bianox", "BIANOX", "Enlex", " enlex "]),
                         ["Bianox", "Enlex"])

    def test_length_text_parses_to_whole_seconds(self):
        self.assertEqual(guess.parse_length("2m 54s (XL)"), 174)
        self.assertEqual(guess.parse_length("1m 0s (Long)"), 60)
        self.assertEqual(guess.parse_length("45s"), 45)
        with self.assertRaises(ValueError):
            guess.parse_length("long")


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
        self.assertEqual(sorted(out["levels"][0]), ["c", "cn", "id", "n", "r", "s", "v", "y"])
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


if __name__ == "__main__":
    unittest.main()
