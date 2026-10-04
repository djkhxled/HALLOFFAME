"""GeometryGuessr: the data, the built page, and the promises the privacy page makes.

The rules themselves (scoring, dealing, search, the run) are pure JavaScript in
src/js/gg-core.js and are checked in the browser by tests/gg.check.html.
"""
import json
import pathlib
import re
import subprocess
import tempfile
import unittest

from hall import gg

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"


def strip_comments(code: str) -> str:
    code = re.sub(r"/\*.*?\*/", "", code, flags=re.S)
    return re.sub(r"(?m)^\s*//.*$", "", code)


class Data(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.levels = [{"id": i, "name": f"L{i}", "creator": "c", "downloads": 100 - i,
                        "difficulty": "Easy Demon", "slug": f"l{i}"} for i in range(1, 8)]
        self.shots = []
        for i in range(1, 6):
            (self.tmp / f"l{i}").mkdir()
            (self.tmp / f"l{i}" / "040.webp").write_bytes(b"x")
            self.shots.append({"level": i, "pct": 40, "file": f"l{i}/040.webp"})

    def test_good_data_passes(self):
        self.assertEqual(gg.validate(self.levels, self.shots, self.tmp), [])

    def test_a_shot_of_an_unknown_level_fails(self):
        self.shots[0]["level"] = 999
        self.assertTrue(any("not in levels.json" in e for e in gg.validate(self.levels, self.shots, self.tmp)))

    def test_a_shot_at_the_very_start_or_end_fails(self):
        self.shots[0]["pct"] = 1
        self.shots[1]["pct"] = 99
        errors = gg.validate(self.levels, self.shots, self.tmp)
        self.assertEqual(sum("outside" in e for e in errors), 2)

    def test_a_missing_image_fails(self):
        self.shots[0]["file"] = "l1/077.webp"
        self.assertTrue(any("no such file" in e for e in gg.validate(self.levels, self.shots, self.tmp)))

    def test_too_few_levels_with_pictures_fails(self):
        errors = gg.validate(self.levels, self.shots[:4], self.tmp)
        self.assertTrue(any("needs" in e for e in errors))

    def test_duplicate_ids_fail(self):
        self.levels[1]["id"] = 1
        self.assertTrue(any("duplicate level id" in e for e in gg.validate(self.levels, self.shots, self.tmp)))

    def test_page_data_uses_short_keys_and_is_safe_in_a_script(self):
        self.levels[0]["name"] = "</script><b>"
        out = gg.data_json(self.levels, self.shots, "2026-10-03")
        self.assertNotIn("</script>", out)
        data = json.loads(out.replace("<\\/", "</"))
        self.assertEqual(set(data["levels"][0]), {"id", "n", "c", "d"})
        self.assertEqual(set(data["shots"][0]), {"l", "p", "f"})


class RealData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snap, cls.shots = gg.load(ROOT / "data" / "gg" / "levels.json", ROOT / "data" / "gg" / "shots.json")

    def test_the_committed_data_is_valid(self):
        self.assertEqual(gg.validate(self.snap["levels"], self.shots, ROOT / "src" / "shots"), [])

    def test_the_search_list_is_the_100_most_downloaded_demons(self):
        levels = self.snap["levels"]
        self.assertEqual(len(levels), 100)
        self.assertTrue(all("Demon" in lv["difficulty"] for lv in levels))
        downloads = [lv["downloads"] for lv in levels]
        self.assertEqual(downloads, sorted(downloads, reverse=True))

    def test_names_carry_no_stray_spaces(self):
        for lv in self.snap["levels"]:
            self.assertEqual(lv["name"], " ".join(lv["name"].split()), lv["name"])

    def test_every_crop_is_a_16_9_box_inside_a_shot_that_exists(self):
        path = ROOT / "data" / "gg" / "crops.json"
        crops = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        keys = {s["file"].rsplit(".", 1)[0] for s in self.shots}
        for key, (x, y, size) in crops.items():
            self.assertIn(key, keys, key)
            self.assertTrue(0.3 <= size <= 1, key)
            self.assertTrue(0 <= x <= 1 - size + 1e-9 and 0 <= y <= 1 - size + 1e-9, key)

    def test_every_image_is_used_and_every_used_image_exists(self):
        on_disk = {p.relative_to(ROOT / "src" / "shots").as_posix() for p in (ROOT / "src" / "shots").rglob("*.webp")}
        self.assertEqual(on_disk, {s["file"] for s in self.shots})


class BuiltPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(["python3", "build.py"], cwd=ROOT, check=True, capture_output=True)
        cls.html = (DOCS / "geometryguessr" / "index.html").read_text(encoding="utf-8")
        cls.home = (DOCS / "index.html").read_text(encoding="utf-8")
        cls.moved = (DOCS / "games" / "index.html").read_text(encoding="utf-8")
        cls.list = (DOCS / "list" / "index.html").read_text(encoding="utf-8")

    def test_the_page_loads_the_rules_before_the_interface(self):
        self.assertLess(self.html.index("/gg-core.js"), self.html.index("/gg.js"))

    def test_the_page_carries_its_data(self):
        m = re.search(r'<script type="application/json" id="gg-data">(.*?)</script>', self.html, re.S)
        data = json.loads(m.group(1).replace("<\\/", "</"))
        self.assertEqual(len(data["levels"]), 100)
        self.assertGreaterEqual(len({s["l"] for s in data["shots"]}), gg.MIN_POOL)

    def test_the_images_are_published_where_the_page_looks(self):
        base = re.search(r'data-shots="([^"]+)"', self.html).group(1)
        self.assertEqual(base, "../assets/shots/")
        m = re.search(r'id="gg-data">(.*?)</script>', self.html, re.S)
        first = json.loads(m.group(1).replace("<\\/", "</"))["shots"][0]["f"]
        self.assertTrue((DOCS / "assets" / "shots" / first).is_file())

    def test_the_games_tab_is_current(self):
        nav = re.search(r'<nav class="topnav".*?</nav>', self.html, re.S).group(0)
        self.assertRegex(nav, r'<a class="topnav__link"[^>]*aria-current="page">Games</a>')

    def test_the_landing_page_offers_it_first(self):
        tiles = re.findall(r'<a class="gtile gtile--\w+" href="([^"]+)"', self.home)
        self.assertEqual(tiles, ["geometryguessr/", "demondle/", "game/"])

    def test_the_landing_page_offers_the_games_above_the_fold(self):
        hero = self.home[:self.home.index("</section>")]
        self.assertIn('class="herocta" href="#play"', hero)
        self.assertIn('id="play"', self.home)

    def test_the_landing_page_links_to_the_list_but_is_not_the_list(self):
        self.assertIn('href="list/"', self.home)
        self.assertNotIn('class="countdown__entry', self.home)
        self.assertIn('class="countdown__entry', self.list)
        self.assertNotIn('class="gtile', self.list)

    def test_the_old_games_address_forwards_to_the_landing_page(self):
        self.assertIn('http-equiv="refresh" content="0; url=../"', self.moved)
        self.assertIn('href="../"', self.moved)

    def test_the_games_tab_is_marked_so_it_can_stand_out(self):
        self.assertIn('data-tab="games"', self.home)

    def test_the_logo_has_a_name_for_screen_readers(self):
        self.assertRegex(self.html, r'<h1 id="gg-logo" class="gg-logo" aria-label="GeometryGuessr">')

    def test_there_are_no_lives(self):
        """Five rounds, like GeoGuessr: a wrong name scores nothing and the game goes on."""
        self.assertNotIn("gg-heart", self.html)
        self.assertNotIn("lives", (ROOT / "src" / "js" / "gg-core.js").read_text(encoding="utf-8").lower())

    def test_the_page_says_it_is_not_finished(self):
        site = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))["gg"]
        self.assertIn(f'class="gg-sticker" aria-hidden="true">{site["stage"]}</span>', self.html)
        self.assertRegex(self.html, rf'v{re.escape(site["version"])} &middot; \d+ of 100 demons so far')

    def test_the_cube_is_a_slider(self):
        self.assertRegex(self.html, r'class="gg-cube"[^>]*role="slider"')


class Promises(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ui = (ROOT / "src" / "js" / "gg.js").read_text(encoding="utf-8")
        cls.core = (ROOT / "src" / "js" / "gg-core.js").read_text(encoding="utf-8")

    def test_no_network_calls(self):
        for name, code in (("gg.js", self.ui), ("gg-core.js", self.core)):
            code = strip_comments(code)
            for bad in ("fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket", "EventSource", "import(",
                        "importScripts"):
                self.assertNotIn(bad, code, f"{name}: {bad}")
            self.assertNotRegex(code, r"https?://", name)

    def test_the_rules_touch_no_storage_and_no_page(self):
        code = strip_comments(self.core)
        for bad in ("localStorage", "document", "window.", "Math.random"):
            self.assertNotIn(bad, code, bad)

    def test_one_storage_key_written_in_one_place(self):
        code = strip_comments(self.ui)
        self.assertEqual(len(re.findall(r"setItem\(", code)), 1)
        for bad in ("sessionStorage", "indexedDB", "document.cookie"):
            self.assertNotIn(bad, code)

    def test_the_storage_key_is_the_one_the_policy_names(self):
        key = re.search(r'var KEY = "([^"]+)"', self.ui).group(1)
        privacy = (ROOT / "pages" / "privacy.html").read_text(encoding="utf-8")
        self.assertIn(key, privacy)
        self.assertIn("GeometryGuessr", privacy)

    def test_motion_and_sound_respect_the_visitor(self):
        self.assertIn("prefers-reduced-motion", self.ui)
        css = (ROOT / "src" / "css" / "gg.css").read_text(encoding="utf-8")
        self.assertIn("prefers-reduced-motion", css)
        self.assertIn("store.sound", self.ui)



class Board(unittest.TestCase):
    """gg-records.js is the one GeometryGuessr script that can send anything."""

    @classmethod
    def setUpClass(cls):
        cls.code = strip_comments((ROOT / "src" / "js" / "gg-records.js").read_text(encoding="utf-8"))
        cls.worker = strip_comments((ROOT / "worker" / "records.js").read_text(encoding="utf-8"))

    def test_one_place_makes_a_request(self):
        self.assertEqual(len(re.findall(r"\bfetch\(", self.code)), 1)
        for bad in ("XMLHttpRequest", "sendBeacon", "WebSocket", "EventSource"):
            self.assertNotIn(bad, self.code)

    def test_requests_only_come_from_button_presses(self):
        callers = set(re.findall(r"function (\w+)\([^)]*\) \{(?:(?!\n  function ).)*?request\(", self.code, re.S))
        self.assertEqual(callers - {"request"}, {"showBoard", "submit"})
        self.assertEqual(re.findall(r"(?<!function )\bshowBoard\(\)", self.code), [])
        self.assertIn('btnSubmit.addEventListener("click", submit)', self.code)
        self.assertIn('if (e.key === "Enter") { e.preventDefault(); submit(); }', self.code)

    def test_no_cookies_no_referrer_no_storage_no_markup(self):
        self.assertIn('credentials: "omit"', self.code)
        self.assertIn('referrerPolicy: "no-referrer"', self.code)
        for bad in ("localStorage", "sessionStorage", "indexedDB", "document.cookie",
                    "innerHTML", "outerHTML", "insertAdjacentHTML", "document.write"):
            self.assertNotIn(bad, self.code, bad)

    def test_it_sends_only_what_the_privacy_page_lists(self):
        body = re.search(r"JSON\.stringify\(\{(.*?)\}\)", self.code, re.S).group(1)
        self.assertEqual(set(re.findall(r"(\w+):", body)), {"mode", "name", "score", "named"})
        privacy = (ROOT / "pages" / "privacy.html").read_text(encoding="utf-8")
        self.assertIn("GeometryGuessr&rsquo;s board", privacy)
        self.assertIn("how many of the five demons you named", privacy)

    def test_the_browser_and_the_service_apply_the_same_username_rule(self):
        client = re.search(r"var NAME_OK = (/.*?/u);", self.code).group(1)
        server = re.search(r"const NAME_OK = (/.*?/u);", self.worker).group(1)
        self.assertEqual(client, server)

    def test_the_service_and_the_game_agree_on_five_rounds_of_1000(self):
        core = (ROOT / "src" / "js" / "gg-core.js").read_text(encoding="utf-8")
        self.assertIn("var ROUNDS = 5;", core)
        self.assertIn("var FULL = 1000;", core)
        self.assertIn("const GG = { rounds: 5, perRound: 1000 };", self.worker)

    def test_the_board_is_off_until_a_service_is_connected(self):
        import build
        site = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))
        base = build.read(build.TEMPLATES / "base.html")
        off = build.build_gg({**site, "records": {"endpoint": None}}, base)
        self.assertNotIn("gg-records.js", off)
        self.assertNotIn("data-records-endpoint", off)
        self.assertNotIn("data-rec", off)
        on = build.build_gg(site, base)
        self.assertIn("gg-records.js", on)
        self.assertIn("@bperk", on)          # the removal route sits by the box


if __name__ == "__main__":
    unittest.main()
