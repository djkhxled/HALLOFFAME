import unittest

from hall.render import fill, hero_size, statblock_html


class TestFill(unittest.TestCase):
    def test_substitutes_a_slot(self):
        self.assertEqual(fill("<h1>{{ name }}</h1>", {"name": "Nhelv"}), "<h1>Nhelv</h1>")

    def test_tolerates_no_inner_spaces(self):
        self.assertEqual(fill("{{name}}", {"name": "Deimos"}), "Deimos")

    def test_escapes_by_default(self):
        out = fill("{{ t }}", {"t": '<script>"x"</script>'})
        self.assertNotIn("<script>", out)

    def test_html_suffixed_slots_are_raw(self):
        out = fill("{{ body_html }}", {"body_html": "<p>hi</p>"})
        self.assertEqual(out, "<p>hi</p>")

    def test_missing_slot_raises(self):
        with self.assertRaises(KeyError):
            fill("{{ nope }}", {})

    def test_unused_slot_raises(self):
        with self.assertRaises(KeyError):
            fill("static", {"unused": "x"})


class TestHeroSize(unittest.TestCase):
    def test_longer_words_get_smaller_type(self):
        short = hero_size("Nhelv")
        long = hero_size("Antarctic Lights")
        self.assertLess(
            float(long.split(",")[1].strip().rstrip("vw")),
            float(short.split(",")[1].strip().rstrip("vw")),
        )

    def test_caps_short_words_so_they_do_not_explode(self):
        self.assertIn("26.0vw", hero_size("A"))


class TestStatblock(unittest.TestCase):
    def test_missing_values_render_as_a_dash_not_omitted(self):
        out = statblock_html({"creators": ["X"], "objects": None})
        self.assertIn("OBJECTS".title(), out.title())
        self.assertIn("mdash", out)

    def test_never_invents_a_value(self):
        out = statblock_html({})
        self.assertNotIn("None", out)

    def test_song_credits_the_artist(self):
        out = statblock_html({"song": {"name": "Nhelv", "artist": "Silentroom"}})
        self.assertIn("Silentroom", out)


if __name__ == "__main__":
    unittest.main()
