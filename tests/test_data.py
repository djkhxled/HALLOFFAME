import json
import pathlib
import tempfile
import unittest

from hall.data import load_levels, validate_levels


def minimal(rank, slug, **over):
    rec = {
        "rank": rank,
        "slug": slug,
        "name": slug.title(),
        "tagline": "A line.",
        "published": False,
        "theme": {
            "tier": "themed",
            "palette": {
                "field": "#05060a",
                "ink": "#f4f4f5",
                "muted": "#9a9aa3",
                "accent": "#8b5cf6",
            },
            "texture": "grain",
            "signature": "static",
        },
    }
    rec.update(over)
    return rec


def write(tmp, records):
    levels = tmp / "data" / "levels"
    levels.mkdir(parents=True, exist_ok=True)
    for r in records:
        (levels / f"{r['rank']:02d}-{r['slug']}.json").write_text(json.dumps(r))
    return levels


class TestLoad(unittest.TestCase):
    def test_loads_sorted_by_rank(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = pathlib.Path(d)
            lv = write(tmp, [minimal(2, "beta"), minimal(1, "alpha")])
            got = load_levels(lv)
            self.assertEqual([r["slug"] for r in got], ["alpha", "beta"])


class TestValidate(unittest.TestCase):
    def _check(self, records):
        with tempfile.TemporaryDirectory() as d:
            tmp = pathlib.Path(d)
            lv = write(tmp, records)
            return validate_levels(load_levels(lv), tmp)

    def test_valid_records_produce_no_errors(self):
        self.assertEqual(self._check([minimal(1, "alpha"), minimal(2, "beta")]), [])

    def test_duplicate_rank_is_an_error(self):
        errs = self._check([minimal(1, "alpha"), minimal(1, "beta")])
        self.assertTrue(any("rank" in e for e in errs), errs)

    def test_gap_in_ranks_is_an_error(self):
        errs = self._check([minimal(1, "alpha"), minimal(3, "gamma")])
        self.assertTrue(any("rank" in e for e in errs), errs)

    def test_unknown_signature_is_an_error(self):
        bad = minimal(1, "alpha")
        bad["theme"]["signature"] = "wobble"
        errs = self._check([bad])
        self.assertTrue(any("signature" in e for e in errs), errs)

    def test_unknown_texture_is_an_error(self):
        bad = minimal(1, "alpha")
        bad["theme"]["texture"] = "velvet"
        errs = self._check([bad])
        self.assertTrue(any("texture" in e for e in errs), errs)

    def test_low_contrast_ink_is_an_error(self):
        bad = minimal(1, "alpha")
        bad["theme"]["palette"]["ink"] = "#0a0b10"
        errs = self._check([bad])
        self.assertTrue(any("contrast" in e for e in errs), errs)

    def test_low_contrast_muted_is_an_error(self):
        bad = minimal(1, "alpha")
        bad["theme"]["palette"]["muted"] = "#14161c"
        errs = self._check([bad])
        self.assertTrue(any("contrast" in e for e in errs), errs)

    def test_published_level_requires_sources(self):
        bad = minimal(1, "alpha", published=True)
        bad["theme"]["tier"] = "bespoke"
        bad["voice"] = {"why": "<p>x</p>"}
        bad["facts"] = {"sources": []}
        errs = self._check([bad])
        self.assertTrue(any("sources" in e for e in errs), errs)

    def test_published_level_requires_commentary(self):
        bad = minimal(1, "alpha", published=True)
        bad["theme"]["tier"] = "bespoke"
        bad["facts"] = {"sources": ["https://example.com"]}
        bad["voice"] = {"why": ""}
        errs = self._check([bad])
        self.assertTrue(any("voice.why" in e for e in errs), errs)

    def test_themed_level_may_declare_art(self):
        """The themed tier carries generated art; only the bespoke fragment
        and stylesheet are reserved to the bespoke tier."""
        ok = minimal(1, "alpha")
        ok["media"] = {"art": "src/art/tidal-wave.svg"}
        with tempfile.TemporaryDirectory() as d:
            tmp = pathlib.Path(d)
            (tmp / "src" / "art").mkdir(parents=True)
            (tmp / "src" / "art" / "tidal-wave.svg").write_text("<svg/>")
            lv = write(tmp, [ok])
            self.assertEqual(validate_levels(load_levels(lv), tmp), [])

    def test_art_must_exist_on_disk(self):
        bad = minimal(1, "alpha")
        bad["media"] = {"art": "src/art/nope.svg"}
        errs = self._check([bad])
        self.assertTrue(any("missing file" in e for e in errs), errs)

    def test_missing_tagline_is_an_error(self):
        bad = minimal(1, "alpha")
        bad["tagline"] = ""
        errs = self._check([bad])
        self.assertTrue(any("tagline" in e for e in errs), errs)


class TestRealData(unittest.TestCase):
    def test_the_shipped_records_are_valid(self):
        root = pathlib.Path(__file__).resolve().parent.parent
        levels = load_levels(root / "data" / "levels")
        self.assertEqual(len(levels), 25)
        self.assertEqual(validate_levels(levels, root), [])


if __name__ == "__main__":
    unittest.main()
