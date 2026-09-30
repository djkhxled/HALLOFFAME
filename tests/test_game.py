"""The name-every-demon game.

Most of what can go wrong here goes wrong quietly: a level that can never be
named still renders a perfectly good empty row, and a rule that drifted
between the build and the browser just makes some answers "wrong". So these
check the rules, against the real snapshot, rather than the page.
"""

import json
import pathlib
import re
import subprocess
import unittest

from hall import game

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
SNAPSHOT = ROOT / "data" / "game" / "aredl.json"


def lv(p, name, lid=None, legacy=False):
    return {"p": p, "name": name, "id": lid or f"id{p:05d}", "legacy": legacy}


class Normalising(unittest.TestCase):
    def test_case_spacing_and_punctuation_never_decide_an_answer(self):
        for typed in ("society", "  SOCIETY!! ", "S o c i e t y", "so-ciety"):
            self.assertEqual(game.norm(typed), "society")

    def test_accents_fold_away(self):
        self.assertEqual(game.norm("Café Niño"), "cafenino")

    def test_the_creator_suffix_is_split_off(self):
        self.assertEqual(game.split_name("Deimos (EndLevel)"), ("Deimos", "EndLevel"))
        self.assertEqual(game.split_name("Deimos"), ("Deimos", None))
        # a name that is nothing but parentheses is not split into nothing
        self.assertEqual(game.split_name("(Solo)"), ("(Solo)", None))

    def test_the_browser_normalises_exactly_as_the_build_does(self):
        """There is no Node here, so game.js cannot be run by a test. What can
        be checked is that its normaliser is still the one game.norm()
        documents; if one changes and not the other, some answers silently
        stop matching."""
        js = (ROOT / "src" / "js" / "game.js").read_text(encoding="utf-8")
        self.assertIn('normalize("NFKD")', js)
        self.assertIn(r'replace(/[̀-ͯ]/g, "")', js)
        self.assertIn(".toLowerCase()", js)
        self.assertIn(r'replace(/[^a-z0-9]/g, "")', js)


class Rules(unittest.TestCase):
    def test_a_name_shared_by_several_levels_fills_them_in_rank_order(self):
        levels = [lv(40, "Deimos (ItsHybrid)"), lv(270, "Deimos (EndLevel)")]
        index, _ = game.build_index(levels)
        self.assertEqual(index["deimos"], [0, 1])

    def test_the_full_form_aims_at_exactly_one(self):
        levels = [lv(40, "Deimos (ItsHybrid)"), lv(270, "Deimos (EndLevel)")]
        index, _ = game.build_index(levels)
        self.assertEqual(index["deimosendlevel"], [1])
        self.assertEqual(index["deimositshybrid"], [0])

    def test_a_leading_the_is_optional(self):
        index, _ = game.build_index([lv(1, "The Golden")])
        self.assertEqual(index["thegolden"], [0])
        self.assertEqual(index["golden"], [0])

    def test_a_name_that_merely_starts_with_the_is_left_alone(self):
        """"Theory" must not become "ory"."""
        index, _ = game.build_index([lv(1, "Theory")])
        self.assertIn("theory", index)
        self.assertNotIn("ory", index)

    def test_a_prefix_waits_only_while_the_longer_level_is_unnamed(self):
        levels = [lv(1, "Aurora"), lv(2, "Aurorae")]
        index, plain = game.build_index(levels)
        hold = game.build_hold(levels, index, plain)
        self.assertEqual(hold["aurora"], [1])
        self.assertNotIn("aurorae", hold)   # nothing longer to be mistaken for

    def test_creator_suffixes_do_not_make_shared_names_wait(self):
        """"deimos" is the start of "deimositshybrid", and nobody types that by
        accident. If it counted, every shared name would lag 750ms."""
        levels = [lv(1, "Deimos (ItsHybrid)"), lv(2, "Deimos (EndLevel)")]
        index, plain = game.build_index(levels)
        self.assertNotIn("deimos", game.build_hold(levels, index, plain))

    def test_a_key_never_waits_on_the_levels_it_already_answers_to(self):
        levels = [lv(1, "Aurora (A)"), lv(2, "Aurora (B)"), lv(3, "Aurorae")]
        index, plain = game.build_index(levels)
        hold = game.build_hold(levels, index, plain)
        self.assertFalse(set(hold["aurora"]) & set(index["aurora"]))

    def test_unnameable_levels_are_caught(self):
        errors = game.validate([lv(1, "!!!"), lv(2, "Fine")])
        self.assertTrue(any("could never be named" in e for e in errors))

    def test_duplicate_ids_are_caught(self):
        errors = game.validate([lv(1, "A", "x"), lv(2, "B", "x")])
        self.assertTrue(any("appears twice" in e for e in errors))


class RealSnapshot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snap = game.load_snapshot(SNAPSHOT)
        cls.levels = cls.snap["levels"]
        cls.index, cls.plain = game.build_index(cls.levels)
        cls.hold = game.build_hold(cls.levels, cls.index, cls.plain)

    def test_it_is_the_whole_list(self):
        self.assertGreaterEqual(len(self.levels), 1500)
        self.assertEqual(self.snap["count"], len(self.levels))

    def test_it_validates(self):
        self.assertEqual(game.validate(self.levels), [])

    def test_every_single_level_can_be_named(self):
        """The one that matters. A level with no key is a slot the game can
        never fill, which makes 100% unreachable and says nothing about it."""
        reachable = {i for bucket in self.index.values() for i in bucket}
        missing = [self.levels[i]["name"]
                   for i in range(len(self.levels)) if i not in reachable]
        self.assertEqual(missing, [])

    def test_every_level_answers_to_its_own_full_name(self):
        bad = []
        for i, level in enumerate(self.levels):
            if i not in self.index.get(game.norm(level["name"]), []):
                bad.append(level["name"])
        self.assertEqual(bad, [])

    def test_buckets_are_in_rank_order(self):
        for key, bucket in self.index.items():
            ranks = [self.levels[i]["p"] for i in bucket]
            self.assertEqual(ranks, sorted(ranks), key)

    def test_hold_points_at_real_levels_and_never_at_its_own(self):
        for key, rivals in self.hold.items():
            for i in rivals:
                self.assertTrue(0 <= i < len(self.levels))
            self.assertFalse(set(rivals) & set(self.index[key]), key)

    def test_the_known_prefix_cases_are_held_and_the_shared_names_are_not(self):
        self.assertIn("aurora", self.hold)
        self.assertNotIn("deimos", self.hold)
        self.assertNotIn("firepower", self.hold)

    def test_blocks_cover_every_level_exactly_once(self):
        seen = [i for _, idxs in game.blocks(self.levels) for i in idxs]
        self.assertEqual(sorted(seen), list(range(len(self.levels))))

    def test_legacy_levels_get_their_own_block(self):
        titles = [t for t, _ in game.blocks(self.levels)]
        self.assertTrue(titles[-1].startswith("Legacy"))

    def test_the_payload_round_trips_and_cannot_close_its_script_tag(self):
        text = game.data_json(self.levels, self.index, self.hold, "2026-01-01")
        self.assertNotIn("<", text)
        payload = json.loads(text)
        self.assertEqual(len(payload["levels"]), len(self.levels))
        self.assertEqual(payload["levels"][0][2], self.levels[0]["name"])


class BuiltPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(["python3", "build.py"], cwd=ROOT, check=True,
                       capture_output=True)
        cls.html = (DOCS / "game" / "index.html").read_text(encoding="utf-8")
        cls.index = (DOCS / "index.html").read_text(encoding="utf-8")
        cls.total = len(game.load_snapshot(SNAPSHOT)["levels"])

    def test_every_level_has_a_slot(self):
        self.assertEqual(self.html.count('class="slot"'), self.total)

    def test_unnamed_slots_are_hidden_from_assistive_tech(self):
        """1,621 announcements of "not yet named" would bury the page."""
        slots = re.findall(r'<li class="slot"[^>]*>', self.html)
        self.assertTrue(all('aria-hidden="true"' in s for s in slots))

    def test_the_markup_holds_no_level_names(self):
        """Names arrive from the data only when earned; the list is not a wall
        of spoilers to select-all or to a screen reader."""
        listing = self.html[self.html.index('data-list'):
                            self.html.index('class="gsource"')]
        names = re.findall(r'<span class="slot__name">([^<]+)</span>', listing)
        self.assertEqual(names, [])

    def test_the_game_drives_the_progress_bar(self):
        self.assertIn("data-attempt-manual", self.html)
        self.assertIn("game.js", self.html)

    def test_the_tab_is_on_the_landing_page_and_points_at_the_game(self):
        self.assertRegex(self.index,
                         r'<nav class="topnav"[^>]*>.*?href="game/".*?</nav>')

    def test_the_game_links_back_to_the_hall(self):
        nav = re.search(r'<nav class="topnav".*?</nav>', self.html, re.S).group(0)
        self.assertIn('aria-current="page"', nav)
        self.assertIn('href="../"', nav)

    def test_only_the_game_page_loads_the_game_script(self):
        others = [p for p in DOCS.rglob("*.html")
                  if p != DOCS / "game" / "index.html"]
        for page in others:
            self.assertNotIn("game.js", page.read_text(encoding="utf-8"), page)


class Promises(unittest.TestCase):
    """The privacy page makes claims about this script. Hold it to them."""

    @classmethod
    def setUpClass(cls):
        raw = (ROOT / "src" / "js" / "game.js").read_text(encoding="utf-8")
        cls.raw = raw
        code = re.sub(r"/\*.*?\*/", "", raw, flags=re.S)
        cls.code = re.sub(r"(?m)^\s*//.*$", "", code)

    def test_it_makes_no_network_requests(self):
        for call in ("fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket",
                     "EventSource", "new Image", "importScripts"):
            self.assertNotIn(call, self.code, call)

    def test_it_reaches_no_other_host(self):
        self.assertNotRegex(self.code, r"https?://")

    def test_it_writes_storage_only_under_one_key(self):
        self.assertEqual(len(re.findall(r"setItem\(", self.code)), 1)
        self.assertNotIn("sessionStorage", self.code)
        self.assertNotIn("indexedDB", self.code)
        self.assertNotIn("document.cookie", self.code)

    def test_no_other_script_touches_storage(self):
        for js in (ROOT / "src" / "js").glob("*.js"):
            if js.name == "game.js":
                continue
            self.assertNotIn("localStorage",
                             js.read_text(encoding="utf-8"), js.name)

    def test_the_privacy_page_says_the_game_stores_progress(self):
        """If the script stores anything, the page a visitor reads to find out
        must say so, and must no longer claim nothing is stored."""
        privacy = (ROOT / "pages" / "privacy.html").read_text(encoding="utf-8")
        self.assertIn("localStorage", self.code)
        self.assertIn("localStorage", privacy)
        self.assertIn("Game", privacy)
        self.assertNotIn("No browser storage", privacy)
        self.assertNotIn("nowhere on this\n    site to type", privacy)

    def test_animation_and_sound_respect_the_visitors_settings(self):
        self.assertIn("prefers-reduced-motion", self.code)
        # Every animation goes through one helper, and that helper checks the
        # preference. A second .animate( anywhere would be a way round it.
        self.assertEqual(len(re.findall(r"\.animate\(", self.code)), 1)
        helper = re.search(r"function motion\(.*?\n  \}", self.code, re.S).group(0)
        self.assertIn("calm", helper)
        self.assertIn("prefers-reduced-motion", self.code)
        # No audio before a gesture: the context starts as null, and the one
        # place it is ever constructed is unlock(), which is reached from a
        # pointerdown/keydown listener, the sound button, or an answer.
        self.assertIn("var ctx = null;", self.code)
        self.assertEqual(len(re.findall(r"new AC\(", self.code)), 1)
        unlock = re.search(r"function unlock\(\) \{.*?\n  \}", self.code, re.S).group(0)
        self.assertIn("new AC(", unlock)
        self.assertIn('"pointerdown", "keydown"', self.code)


if __name__ == "__main__":
    unittest.main()
