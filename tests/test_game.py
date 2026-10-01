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
        index = game.build_index(levels)
        self.assertEqual(index["deimos"], [0, 1])

    def test_the_full_form_aims_at_exactly_one(self):
        levels = [lv(40, "Deimos (ItsHybrid)"), lv(270, "Deimos (EndLevel)")]
        index = game.build_index(levels)
        self.assertEqual(index["deimosendlevel"], [1])
        self.assertEqual(index["deimositshybrid"], [0])

    def test_a_leading_the_is_optional(self):
        index = game.build_index([lv(1, "The Golden")])
        self.assertEqual(index["thegolden"], [0])
        self.assertEqual(index["golden"], [0])

    def test_a_name_that_merely_starts_with_the_is_left_alone(self):
        """"Theory" must not become "ory"."""
        index = game.build_index([lv(1, "Theory")])
        self.assertIn("theory", index)
        self.assertNotIn("ory", index)

    def test_a_name_that_starts_a_longer_one_still_answers_to_itself(self):
        """"Aurora" is the start of "Aurorae". Answers are taken the instant
        they match, so both must be reachable as separate answers."""
        index = game.build_index([lv(1, "Aurora"), lv(2, "Aurorae")])
        self.assertEqual(index["aurora"], [0])
        self.assertEqual(index["aurorae"], [1])

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
        cls.index = game.build_index(cls.levels)

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

    def test_blocks_cover_every_level_exactly_once(self):
        seen = [i for _, idxs in game.blocks(self.levels) for i in idxs]
        self.assertEqual(sorted(seen), list(range(len(self.levels))))

    def test_legacy_levels_get_their_own_block(self):
        titles = [t for t, _ in game.blocks(self.levels)]
        self.assertTrue(titles[-1].startswith("Legacy"))

    def test_the_payload_round_trips_and_cannot_close_its_script_tag(self):
        text = game.data_json(self.levels, self.index, "2026-01-01")
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

    def test_answers_are_taken_instantly(self):
        """Removed on purpose: an earlier version held answers that start a
        longer level for 750ms. The game takes an exact match at once, like
        Sporcle, and nothing in the matching path may wait."""
        self.assertNotRegex(self.code, r"\bhold\b|HOLD_MS|holdTimer")
        self.assertNotIn("mayBeLonger", self.code)
        match = re.search(r"function onInput\(.*?\n  \}", self.code, re.S).group(0)
        self.assertNotIn("setTimeout", match)

    def test_typing_on_past_a_named_level_is_not_interrupted(self):
        """With answers instant, clearing the box on an ALREADY-named match
        would make "aurorae" untypeable once Aurora was in: the box would
        empty at "aurora" every time."""
        match = re.search(r"function onInput\(.*?\n  \}", self.code, re.S).group(0)
        already = match[match.index("firstUnnamed(list_) === -1"):]
        already = already[:already.index("return;")]
        self.assertNotIn('input.value = ""', already)

    def test_it_reaches_no_other_host(self):
        self.assertNotRegex(self.code, r"https?://")

    def test_it_writes_storage_only_under_one_key(self):
        self.assertEqual(len(re.findall(r"setItem\(", self.code)), 1)
        self.assertNotIn("sessionStorage", self.code)
        self.assertNotIn("indexedDB", self.code)
        self.assertNotIn("document.cookie", self.code)

    def test_only_the_game_and_the_notice_touch_storage(self):
        """Two scripts write to localStorage, each under its own key, and the
        privacy page describes exactly those two."""
        for js in (ROOT / "src" / "js").glob("*.js"):
            if js.name in ("game.js", "gate.js"):
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


# ---------------------------------------------------------------- the records

WORKER = ROOT / "worker" / "records.js"


def _code(path):
    """Source with comments stripped, so a test is about what the file does
    and not about the prose that explains why it avoids things."""
    raw = path.read_text(encoding="utf-8")
    raw = re.sub(r"/\*.*?\*/", "", raw, flags=re.S)
    return re.sub(r"(?m)^\s*//.*$", "", raw)


class TimedModes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.js = _code(ROOT / "src" / "js" / "game.js")
        cls.template = (ROOT / "templates" / "game.html").read_text(encoding="utf-8")

    def test_the_five_modes_are_offered(self):
        values = re.findall(r'<input type="radio" name="mode" value="([^"]+)"',
                            self.template)
        self.assertEqual(values, ["free", "5", "10", "30", "60"])

    def test_the_browser_and_the_service_agree_on_the_limits(self):
        """5, 10, 30 and 60 minutes. If the script's limit and the service's
        drift apart, every score in that mode is refused as impossible."""
        js = dict(re.findall(r'"(\d+)": (\d+)', re.search(
            r"var MODE_MS = \{(.*?)\};", self.js, re.S).group(1)))
        worker = dict(re.findall(r'"(\d+)": (\d+)', re.search(
            r"const MODES = \{(.*?)\};", _code(WORKER), re.S).group(1)))
        self.assertEqual({k: int(v) // 1000 for k, v in js.items()},
                         {k: int(v) for k, v in worker.items()})

    def test_a_reload_resumes_the_clock(self):
        """After a reload `started` is true from the saved run but nothing ran
        the clock, so the timer froze -- unlimited time in a timed mode."""
        on_input = re.search(r"function onInput\(.*?\n  \}", self.js, re.S).group(0)
        self.assertRegex(on_input, r"if \(!started\) begin\(\); else resume\(\);")

    def test_an_answer_after_the_deadline_cannot_count(self):
        settle = re.search(r"function settle\(.*?\n  \}", self.js, re.S).group(0)
        self.assertLess(settle.index("limit && nowMs() >= limit"),
                        settle.index("name(target, true)"))

    def test_the_mode_locks_when_the_run_starts(self):
        begin = re.search(r"function begin\(\) \{.*?\}", self.js, re.S).group(0)
        self.assertIn("lockModes()", begin)


class RecordsSwitch(unittest.TestCase):
    """The board is off until a service is connected, and the wording of the
    policy pages follows the switch."""

    @classmethod
    def setUpClass(cls):
        subprocess.run(["python3", "build.py"], cwd=ROOT, check=True,
                       capture_output=True)
        cls.privacy_raw = (ROOT / "pages" / "privacy.html").read_text(encoding="utf-8")
        cls.terms_raw = (ROOT / "pages" / "terms.html").read_text(encoding="utf-8")
        cls.site = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))

    def test_blocks_are_paired(self):
        for raw in (self.privacy_raw, self.terms_raw):
            for kind in ("on", "off"):
                self.assertEqual(raw.count(f"<!-- records:{kind} -->"),
                                 raw.count(f"<!-- /records:{kind} -->"), kind)

    def test_switching_on_and_off_leaves_no_markers(self):
        for raw in (self.privacy_raw, self.terms_raw):
            for enabled in (True, False):
                out = game.apply_records_blocks(raw, enabled)
                self.assertNotIn("records:", out)

    def test_off_says_nothing_is_collected_and_never_mentions_the_board(self):
        out = game.apply_records_blocks(self.privacy_raw, False)
        self.assertIn("does not collect anything about you", out)
        self.assertNotIn("Cloudflare", out)
        self.assertNotIn("record board", out.lower())
        terms = game.apply_records_blocks(self.terms_raw, False)
        self.assertRegex(terms, r"accepts no\s+submissions")

    def test_on_describes_what_is_sent_where_and_how_to_get_it_removed(self):
        out = game.apply_records_blocks(self.privacy_raw, True)
        for promise in ("Show records", "Submit to", "username", "Cloudflare",
                        "[[dm]]", "not your real name"):
            self.assertIn(promise, out, promise)
        self.assertNotIn("does not collect anything about you", out)
        terms = game.apply_records_blocks(self.terms_raw, True)
        self.assertNotRegex(terms, r"accepts no\s+submissions")
        self.assertIn("[[dm]]", terms)

    def test_the_privacy_page_states_the_number_the_service_keeps(self):
        """"Each board keeps its best 100" is a claim about worker/records.js."""
        keep = int(re.search(r"const KEEP = (\d+);", _code(WORKER)).group(1))
        on = game.apply_records_blocks(self.privacy_raw, True)
        self.assertIn(f"best {keep}", on)

    def test_it_is_off_until_a_service_is_connected(self):
        """Built with no endpoint, whatever data/site.json says today."""
        import build
        base = build.read(build.TEMPLATES / "base.html")
        off = build.build_game({**self.site, "records": {"endpoint": None}}, base)
        self.assertNotIn("data-records", off)
        self.assertNotIn("records.js", off)
        self.assertNotIn("Cloudflare",
                         game.apply_records_blocks(self.privacy_raw, False))

    def test_the_endpoint_is_validated(self):
        ok = {"discord": "bperk"}
        self.assertIsNone(game.records_endpoint({**ok, "records": {"endpoint": None}}))
        self.assertIsNone(game.records_endpoint(ok))
        for good in ("https://hall.example.workers.dev", "http://127.0.0.1:3010",
                     "http://localhost:3010"):
            self.assertEqual(game.records_endpoint({**ok, "records": {"endpoint": good}}), good)
        for bad in ("https://hall.example.workers.dev/", "https://x.dev/path",
                    "http://hall.example.workers.dev", "ftp://x.dev", "x.dev"):
            with self.assertRaises(ValueError, msg=bad):
                game.records_endpoint({**ok, "records": {"endpoint": bad}})

    def test_the_board_will_not_switch_on_with_nobody_to_ask(self):
        """It stores usernames, and the privacy page promises removal on
        request. With no contact of any kind that promise cannot be kept."""
        with self.assertRaises(ValueError):
            game.records_endpoint({"records": {"endpoint": "https://a.workers.dev"}})
        for contact in ({"contact": "a@b.c"}, {"discord": "bperk"}):
            game.records_endpoint({**contact, "records": {"endpoint": "https://a.workers.dev"}})

    def test_contact_can_be_an_email_a_discord_handle_or_both(self):
        from hall import render
        self.assertIsNone(render.contact_html({}))
        self.assertIn("mailto:a@b.c", render.contact_html({"contact": "a@b.c"}))
        self.assertIn("@bperk", render.contact_html({"discord": "bperk"}))
        self.assertIn("@bperk", render.contact_html({"discord": "@bperk"}))
        both = render.contact_html({"contact": "a@b.c", "discord": "bperk"})
        self.assertIn("mailto:a@b.c", both)
        self.assertIn("@bperk", both)

    def test_every_policy_page_says_how_to_reach_the_owner(self):
        for slug in ("terms", "privacy", "credits"):
            page = (DOCS / slug / "index.html").read_text(encoding="utf-8")
            self.assertNotIn("Contact address not set yet", page, slug)
            self.assertRegex(page, r"Contact: .*@bperk", slug)


class RecordsScript(unittest.TestCase):
    """records.js is the one script that can send anything anywhere."""

    @classmethod
    def setUpClass(cls):
        cls.code = _code(ROOT / "src" / "js" / "records.js")

    def test_there_is_exactly_one_place_a_request_is_made(self):
        self.assertEqual(len(re.findall(r"\bfetch\(", self.code)), 1)
        self.assertEqual(len(re.findall(r"\bnew XMLHttpRequest|sendBeacon|WebSocket|EventSource", self.code)), 0)

    def test_requests_are_only_made_from_a_button_press(self):
        """Nothing on load. request() is called from loadBoards and submit,
        and those are reached only through event listeners."""
        callers = set(re.findall(r"function (\w+)\([^)]*\) \{(?:(?!\n  function ).)*?request\(",
                                 self.code, re.S))
        self.assertEqual(callers - {"request"}, {"loadBoards", "submit"})
        # No direct call to loadBoards() anywhere, and the only direct call to
        # submit() is the Enter key in the username box -- which is a button
        # press by another route. Everything else is an event listener.
        self.assertEqual(re.findall(r"(?<!function )\bloadBoards\(\)", self.code), [])
        self.assertEqual(len(re.findall(r"(?<!function )\bsubmit\(\)", self.code)), 1)
        self.assertIn('if (e.key === "Enter") { e.preventDefault(); submit(); }', self.code)
        self.assertIn('btnLoad.addEventListener("click", loadBoards)', self.code)
        self.assertIn('btnSubmit.addEventListener("click", submit)', self.code)

    def test_requests_carry_no_cookies_and_no_referrer(self):
        self.assertIn('credentials: "omit"', self.code)
        self.assertIn('referrerPolicy: "no-referrer"', self.code)

    def test_it_never_touches_storage(self):
        for bad in ("localStorage", "sessionStorage", "indexedDB", "document.cookie"):
            self.assertNotIn(bad, self.code)

    def test_names_from_strangers_are_never_written_as_markup(self):
        for bad in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write"):
            self.assertNotIn(bad, self.code)

    def test_it_sends_only_the_four_fields_the_privacy_page_lists(self):
        body = re.search(r"JSON\.stringify\(\{(.*?)\}\)", self.code, re.S).group(1)
        fields = set(re.findall(r"(\w+):", body))
        self.assertEqual(fields, {"mode", "name", "score", "t"})

    def test_the_browser_and_the_service_apply_the_same_username_rule(self):
        client = re.search(r"var NAME_OK = (/.*?/u);", self.code).group(1)
        server = re.search(r"const NAME_OK = (/.*?/u);", _code(WORKER)).group(1)
        self.assertEqual(client, server)


class RecordsService(unittest.TestCase):
    """worker/records.js cannot be run by a test -- there is no Node here --
    so these pin what it is promised not to do. The behaviour itself was
    checked by loading the file in a browser against a stand-in for KV;
    worker/records.check.js is that check, and README says how to run it."""

    @classmethod
    def setUpClass(cls):
        cls.code = _code(WORKER)

    def test_it_stores_nothing_about_the_visitor_but_the_four_fields(self):
        for bad in ("CF-Connecting-IP", "X-Forwarded-For", "cf-ipcountry",
                    "User-Agent", "Set-Cookie", "Cookie", "console."):
            self.assertNotIn(bad.lower(), self.code.lower(), bad)
        entry = re.search(r"const entry = \{(.*?)\};", self.code).group(1)
        entry = re.sub(r"\([^()]*\)", "()", entry)          # drop call arguments
        keys = [re.match(r"\s*(\w+)", part).group(1) for part in entry.split(",")]
        self.assertEqual(keys, ["n", "s", "t", "d"])

    def test_a_mode_cannot_be_a_prototype_key(self):
        """"constructor" in {...} is true. Object.hasOwn is what stops a
        request naming a mode that does not exist."""
        self.assertIn("Object.hasOwn(MODES", self.code)
        self.assertNotRegex(self.code, r"\bin MODES\b")

    def test_it_only_writes_when_something_changed(self):
        self.assertRegex(self.code, r"if \(improved\) await env\.RECORDS\.put")

    def test_it_checks_the_origin_before_accepting_a_submission(self):
        submit = re.search(r"async function submit\(.*?\n\}", self.code, re.S).group(0)
        self.assertLess(submit.index("cors.ok"), submit.index("request.text()"))

    def test_it_refuses_the_plainly_impossible(self):
        for guard in ("MAX_LEVELS", "MAX_PER_SECOND", "NAME_OK.test(name)",
                      "Number.isInteger(score)", "Number.isInteger(t)"):
            self.assertIn(guard, self.code, guard)


class GamePageCopy(unittest.TestCase):
    """The page's title and intro live in data/site.json so that an edit there
    survives a build. Baylor edited the generated docs/game/index.html directly
    once, and the next build would have erased it."""

    @classmethod
    def setUpClass(cls):
        subprocess.run(["python3", "build.py"], cwd=ROOT, check=True,
                       capture_output=True)
        cls.site = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))
        cls.page = (DOCS / "game" / "index.html").read_text(encoding="utf-8")

    def test_the_title_and_lede_are_the_ones_in_site_json(self):
        import html
        copy = self.site["game"]
        title = html.unescape(re.search(r"<title>(.*?)</title>", self.page).group(1))
        og = html.unescape(re.search(r'og:title" content="(.*?)"', self.page).group(1))
        self.assertEqual(title, copy["title"])
        self.assertEqual(og, f"{copy['title']} — {self.site['title']}")
        self.assertIn(html.escape(copy["lede"], quote=False), self.page)

    def test_the_intro_does_not_claim_there_is_no_time_limit(self):
        """True of free play only, and there are timed modes now."""
        self.assertNotIn("No time limit", self.site["game"]["lede"])

    def test_every_other_page_keeps_its_title_and_social_title_the_same(self):
        import html
        for page in DOCS.rglob("*.html"):
            if page == DOCS / "game" / "index.html":
                continue
            s = page.read_text(encoding="utf-8")
            t = html.unescape(re.search(r"<title>(.*?)</title>", s).group(1))
            o = html.unescape(re.search(r'og:title" content="(.*?)"', s).group(1))
            self.assertEqual(t, o, page)

    def test_a_typo_in_site_json_says_where(self):
        import tempfile
        from unittest import mock
        import build
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "data").mkdir()
            (root / "data" / "site.json").write_text('{\n  "a": 1\n  "b": 2\n}\n',
                                                     encoding="utf-8")
            with mock.patch.object(build, "ROOT", root):
                with self.assertRaises(SystemExit) as caught:
                    build.load_site()
        message = str(caught.exception)
        self.assertIn("site.json", message)
        self.assertIn("line 3", message)



# ------------------------------------------------------------------- the notice

class NoticeMarkup(unittest.TestCase):
    DM = "privately message <strong>@bperk</strong> on Discord"

    def test_it_asks_for_what_it_needs_to(self):
        html_ = game.gate_html(self.DM, "abcd1234")
        self.assertIn("<dialog", html_)
        self.assertNotIn(" open", html_.split(">")[0], "it must start closed")
        self.assertIn('href="/privacy/" target="_blank" rel="noopener"', html_)
        self.assertIn("Accept</button>", html_)
        self.assertIn("Deny</button>", html_)
        self.assertIn("Don&rsquo;t ask me again", html_)
        self.assertIn('type="checkbox"', html_)
        self.assertIn("only way", html_)
        self.assertIn("@bperk", html_)
        self.assertIn('data-version="abcd1234"', html_)

    def test_it_is_labelled_for_assistive_tech(self):
        html_ = game.gate_html(self.DM, "abcd1234")
        self.assertIn('aria-labelledby="gate-h"', html_)
        self.assertIn('id="gate-h"', html_)
        self.assertIn('aria-describedby="gate-d"', html_)
        self.assertIn('id="gate-d"', html_)

    def test_the_version_changes_with_the_wording_and_only_then(self):
        a = game.gate_version("the policy", "the notice")
        self.assertEqual(a, game.gate_version("the policy", "the notice"))
        self.assertEqual(a, game.gate_version("the   policy\n", " the notice"))
        self.assertNotEqual(a, game.gate_version("the policy!", "the notice"))
        self.assertNotEqual(a, game.gate_version("the policy", "the notice!"))
        # not the same as running the two together
        self.assertNotEqual(game.gate_version("ab", "c"), game.gate_version("a", "bc"))

    def test_the_removal_route_is_worded_once(self):
        from hall import render
        self.assertEqual(render.dm_html({"discord": "bperk"}), self.DM)
        self.assertEqual(render.dm_html({"discord": "@bperk"}), self.DM)
        self.assertIn("a@b.c", render.dm_html({"contact": "a@b.c"}))
        self.assertIn("contact", render.dm_html({}))


class NoticeScript(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code = _code(ROOT / "src" / "js" / "gate.js")
        cls.game_code = _code(ROOT / "src" / "js" / "game.js")

    def test_it_makes_no_requests_and_writes_markup_nowhere(self):
        for bad in ("fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket",
                    "innerHTML", "document.cookie", "sessionStorage", "indexedDB"):
            self.assertNotIn(bad, self.code, bad)

    def test_it_keeps_one_marker_under_its_own_key(self):
        key = re.search(r'var KEY = "([^"]+)"', self.code).group(1)
        game_key = re.search(r'var KEY = "([^"]+)"', self.game_code).group(1)
        self.assertNotEqual(key, game_key)
        self.assertEqual(len(re.findall(r"setItem\(", self.code)), 1)
        # the marker is the version and nothing else: the privacy page says so
        self.assertIn("JSON.stringify({ v: version })", self.code)

    def test_only_a_ticked_accept_remembers_and_deny_stores_nothing(self):
        accept = re.search(r'btnAccept\.addEventListener\("click", function \(\) \{(.*?)\n  \}\);',
                           self.code, re.S).group(1)
        self.assertIn("if (again.checked) remember(); else forget();", accept)
        deny = re.search(r'btnDeny\.addEventListener\("click", function \(\) \{(.*?)\n  \}\);',
                         self.code, re.S).group(1)
        for bad in ("remember", "forget", "setItem", "removeItem", "close()"):
            self.assertNotIn(bad, deny, f"Deny must not call {bad}")

    def test_it_cannot_be_dismissed_without_accepting(self):
        self.assertIn('dialog.addEventListener("cancel", function (e) { e.preventDefault(); });', self.code)
        close = re.search(r'dialog\.addEventListener\("close", function \(\) \{(.*?)\}\);',
                          self.code, re.S).group(1)
        self.assertIn("if (!accepted) dialog.showModal();", close)

    def test_a_marker_from_other_wording_does_not_count(self):
        self.assertIn("v.v === version", self.code)

    def test_the_game_is_not_left_reachable_behind_it(self):
        """showModal() is what makes the page inert; a non-modal show() would
        leave the game clickable behind a blur."""
        self.assertIn("dialog.showModal();", self.code)
        self.assertNotRegex(self.code, r"dialog\.show\(")
        self.assertNotIn("setAttribute(\"open\"", self.code)

    def test_it_loads_before_the_game_does(self):
        build_py = (ROOT / "build.py").read_text(encoding="utf-8")
        tag = lambda name: build_py.index(f'<script src="/assets/js/{name}.js"')
        self.assertLess(tag("gate"), tag("records"))
        self.assertLess(tag("records"), tag("game"))

    def test_animation_respects_reduced_motion(self):
        css = (ROOT / "src" / "css" / "game.css").read_text(encoding="utf-8")
        block = css[css.index("@media (prefers-reduced-motion: reduce)"):]
        self.assertIn(".ggate::backdrop", block)
        self.assertIn("animation: none", block)


class NoticeInTheBuild(unittest.TestCase):
    """The notice exists only while the board does."""

    @classmethod
    def setUpClass(cls):
        import build
        cls.build = build
        subprocess.run(["python3", "build.py"], cwd=ROOT, check=True, capture_output=True)
        cls.site = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))
        base = build.read(build.TEMPLATES / "base.html")
        on = {**cls.site, "records": {"endpoint": "https://hall.example.workers.dev"}}
        cls.on = build.build_game(on, base)
        cls.off = build.build_game({**cls.site, "records": {"endpoint": None}}, base)

    def test_off_there_is_no_notice(self):
        self.assertNotIn("ggate", self.off)
        self.assertNotIn("gate.js", self.off)
        self.assertNotIn("<dialog", self.off)

    def test_on_there_is_one_and_its_script_comes_first(self):
        self.assertEqual(self.on.count("<dialog"), 1)
        order = [self.on.index(s) for s in ("gate.js", "records.js", "game.js")]
        self.assertEqual(order, sorted(order))

    def test_the_version_follows_the_privacy_page(self):
        """Edit the policy and everyone is asked again."""
        import build
        a = re.search(r'data-version="([0-9a-f]{8})"', self.on).group(1)
        priv = ROOT / "pages" / "privacy.html"
        original = priv.read_text(encoding="utf-8")
        try:
            priv.write_text(original.replace("Choose a username", "Please choose a username"),
                            encoding="utf-8")
            base = build.read(build.TEMPLATES / "base.html")
            on = {**self.site, "records": {"endpoint": "https://hall.example.workers.dev"}}
            b = re.search(r'data-version="([0-9a-f]{8})"', build.build_game(on, base)).group(1)
        finally:
            priv.write_text(original, encoding="utf-8")
        self.assertNotEqual(a, b)

    def test_the_page_with_the_notice_keeps_the_accessibility_rules(self):
        """The accessibility tests run on the default build, where the board is
        off. This is the same handful of checks on the page with it on."""
        page = self.on
        self.assertEqual(len(re.findall(r"<h1\b", page)), 1)
        prev = 0
        for m in re.finditer(r"<h([1-6])\b", page):
            lvl = int(m.group(1))
            self.assertLessEqual(lvl, prev + 1, f"h{prev} -> h{lvl}")
            prev = lvl
        ids = re.findall(r'\bid="([^"]+)"', page)
        self.assertEqual(len(ids), len(set(ids)), "duplicate ids")
        for ref in re.findall(r'aria-(?:labelledby|describedby)="([^"]+)"', page):
            self.assertIn(ref, ids, f"{ref} points at nothing")
        for m in re.finditer(r"<button\b([^>]*)>(.*?)</button>", page, re.S):
            text = re.sub(r"<[^>]+>", "", m.group(2)).strip()
            self.assertTrue(text or "aria-label" in m.group(1), m.group(0)[:70])
        for a in re.findall(r'<a\b[^>]*target="_blank"[^>]*>', page):
            self.assertIn("noopener", a)


class PolicyCoversTheNotice(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (ROOT / "pages" / "privacy.html").read_text(encoding="utf-8")
        cls.terms = (ROOT / "pages" / "terms.html").read_text(encoding="utf-8")
        cls.on = game.apply_records_blocks(cls.raw, True)
        cls.terms_on = game.apply_records_blocks(cls.terms, True)

    def test_it_covers_what_the_notice_asks_people_to_accept(self):
        for needed in ("The notice you accept first", "Deny", "Don&rsquo;t ask me again",
                       "version marker", "localStorage", "asked again",
                       "the only way to have your records removed"):
            self.assertIn(needed, self.on, needed)

    def test_it_covers_the_rest_of_what_a_board_needs(self):
        for needed in ("What is sent, and when", "Where it is kept", "What everyone can see",
                       "Removing an entry", "Cloudflare", "global network",
                       "best 100", "no accounts", "real name", "cannot check who is asking"):
            self.assertIn(needed, self.on, needed)

    def test_there_is_one_removal_route_and_it_is_the_same_everywhere(self):
        """No stray "[[contact]]" in the board's text: it would let an email
        address or a bare handle appear as a second way, against "the only
        way"."""
        for text in (self.on, self.terms_on):
            self.assertNotIn("[[contact]]", text)
            self.assertIn("[[dm]]", text)

    def test_it_says_what_the_marker_is_and_the_script_stores_exactly_that(self):
        self.assertIn("version marker", self.on)
        self.assertIn("a second, separate item", self.on)

    def test_with_the_board_off_the_notice_is_not_mentioned(self):
        off = game.apply_records_blocks(self.raw, False)
        for gone in ("notice", "Don&rsquo;t ask me again", "Deny"):
            self.assertNotIn(gone, off, gone)
