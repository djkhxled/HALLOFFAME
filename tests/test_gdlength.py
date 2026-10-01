"""Length from level data. Network-free: level strings are built by hand."""
import base64
import gzip
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import gdlength  # noqa: E402


def level(header, objs):
    """header: dict; objs: list of (id, x)."""
    h = ",".join(f"{k},{v}" for k, v in header.items())
    body = "".join(f"1,{i},2,{x};" for i, x in objs)
    return f"{h};{body}"


class Decode(unittest.TestCase):
    def test_round_trip(self):
        raw = "kS38,1;1,1,2,0;"
        field = base64.urlsafe_b64encode(gzip.compress(raw.encode())).decode().rstrip("=")
        self.assertEqual(gdlength.decode(field), raw)


class Seconds(unittest.TestCase):
    def test_one_speed_the_whole_way(self):
        s = level({"kA4": 0}, [(1, 0), (1, 3115.8)])
        self.assertAlmostEqual(gdlength.raw_seconds(s), 10.0, places=2)

    def test_a_speed_portal_changes_the_pace(self):
        # 10 s at 1x, then 2x (387.42 u/s) for 3874.2 u = 10 s
        s = level({"kA4": 0}, [(1, 0), (202, 3115.8), (1, 6990.0)])
        self.assertAlmostEqual(gdlength.raw_seconds(s), 20.0, places=2)

    def test_the_header_sets_the_starting_speed(self):
        s = level({"kA4": 2}, [(1, 0), (1, 3874.2)])
        self.assertAlmostEqual(gdlength.raw_seconds(s), 10.0, places=2)

    def test_a_missing_start_speed_means_normal(self):
        s = level({"kS38": 1}, [(1, 0), (1, 3115.8)])
        self.assertAlmostEqual(gdlength.raw_seconds(s), 10.0, places=2)

    def test_portals_after_the_last_ordinary_object_still_count_in_order(self):
        # The last object is the last by x of anything; a portal at the very end adds nothing.
        s = level({"kA4": 0}, [(1, 0), (203, 3115.8), (1, 3115.8)])
        self.assertAlmostEqual(gdlength.raw_seconds(s), 10.0, places=2)

    def test_portal_order_does_not_depend_on_file_order(self):
        a = level({"kA4": 0}, [(1, 0), (202, 3115.8), (200, 6990.0), (1, 9000.0)])
        b = level({"kA4": 0}, [(200, 6990.0), (1, 9000.0), (1, 0), (202, 3115.8)])
        self.assertAlmostEqual(gdlength.raw_seconds(a), gdlength.raw_seconds(b), places=6)

    def test_malformed_chunks_are_skipped(self):
        s = level({"kA4": 0}, [(1, 0), (1, 3115.8)]) + "garbage;1,x,2,y;;"
        self.assertAlmostEqual(gdlength.raw_seconds(s), 10.0, places=2)

    def test_whole_seconds_adds_the_offset_and_rounds(self):
        s = level({"kA4": 0}, [(1, 0), (1, 3115.8)])     # 10.0 raw
        self.assertEqual(gdlength.whole_seconds(s), round(10.0 + gdlength.START_OFFSET))

    def test_no_objects_is_an_error(self):
        with self.assertRaises(ValueError):
            gdlength.raw_seconds("kA4,0;")


if __name__ == "__main__":
    unittest.main()
