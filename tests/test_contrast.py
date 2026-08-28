import unittest

from hall.contrast import contrast_ratio, parse_hex, relative_luminance


class TestParseHex(unittest.TestCase):
    def test_parses_six_digit(self):
        self.assertEqual(parse_hex("#ff8800"), (255, 136, 0))

    def test_parses_three_digit_shorthand(self):
        self.assertEqual(parse_hex("#f80"), (255, 136, 0))

    def test_rejects_garbage(self):
        with self.assertRaises(ValueError):
            parse_hex("not-a-colour")

    def test_rejects_missing_hash(self):
        with self.assertRaises(ValueError):
            parse_hex("ff8800")


class TestContrastRatio(unittest.TestCase):
    def test_black_on_white_is_maximum(self):
        self.assertAlmostEqual(contrast_ratio("#000000", "#ffffff"), 21.0, places=2)

    def test_identical_colours_have_no_contrast(self):
        self.assertAlmostEqual(contrast_ratio("#3a7bd5", "#3a7bd5"), 1.0, places=2)

    def test_is_symmetric(self):
        a = contrast_ratio("#05060a", "#f4f4f5")
        b = contrast_ratio("#f4f4f5", "#05060a")
        self.assertAlmostEqual(a, b, places=6)

    def test_white_luminance_is_one(self):
        self.assertAlmostEqual(relative_luminance((255, 255, 255)), 1.0, places=6)

    def test_black_luminance_is_zero(self):
        self.assertAlmostEqual(relative_luminance((0, 0, 0)), 0.0, places=6)


if __name__ == "__main__":
    unittest.main()
