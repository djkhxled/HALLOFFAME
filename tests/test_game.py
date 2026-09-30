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
                        "[[contact]]", "not your real name"):
            self.assertIn(promise, out, promise)
        self.assertNotIn("does not collect anything about you", out)
        terms = game.apply_records_blocks(self.terms_raw, True)
        self.assertNotRegex(terms, r"accepts no\s+submissions")
        self.assertIn("[[contact]]", terms)

    def test_the_privacy_page_states_the_number_the_service_keeps(self):
        """"Each board keeps its best 100" is a claim about worker/records.js."""
        keep = int(re.search(r"const KEEP = (\d+);", _code(WORKER)).group(1))
        on = game.apply_records_blocks(self.privacy_raw, True)
        self.assertIn(f"best {keep}", on)

    def test_it_is_off_until_a_service_is_connected(self):
        self.assertIsNone(self.site["records"]["endpoint"])
        page = (DOCS / "game" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("data-records", page)
        self.assertNotIn("records.js", page)
        self.assertNotIn("Cloudflare",
                         (DOCS / "privacy" / "index.html").read_text(encoding="utf-8"))

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
