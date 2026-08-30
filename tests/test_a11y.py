"""Accessibility rules, checked against every built page.

These are the machine-checkable parts of WCAG 2.1 AA. They are not the whole
standard — colour contrast lives in test_contrast.py, and reduced motion,
focus order and keyboard reachability are exercised by hand — but they are
the ones that silently regress when a page is added.
"""

import collections
import pathlib
import re
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"


class TestAccessibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(["python3", "build.py"], cwd=ROOT, check=True,
                       capture_output=True)
        # Every HTML page, not only index.html: 404.html is a real page a
        # visitor lands on and it was outside every rule below.
        cls.pages = {
            str(f.relative_to(DOCS)): f.read_text(encoding="utf-8")
            for f in sorted(DOCS.rglob("*.html"))
        }
        assert cls.pages, "no pages were built"

    def report(self, bad, rule):
        if bad:
            lines = "\n".join(f"    {b}" for b in bad[:8])
            more = f"\n    ... and {len(bad) - 8} more" if len(bad) > 8 else ""
            self.fail(f"{rule} ({len(bad)}):\n{lines}{more}")

    def test_every_image_has_an_alt_attribute(self):
        bad = [f"{p}: {img[:70]}"
               for p, s in self.pages.items()
               for img in re.findall(r"<img\b[^>]*>", s)
               if "alt=" not in img]
        self.report(bad, "images without alt")

    def test_each_page_has_exactly_one_h1(self):
        bad = [f"{p}: {len(re.findall(r'<h1\\b', s))}"
               for p, s in self.pages.items()
               if len(re.findall(r"<h1\b", s)) != 1]
        self.report(bad, "pages whose h1 count is not 1")

    def test_heading_levels_are_never_skipped(self):
        bad = []
        for p, s in self.pages.items():
            prev = 0
            for m in re.finditer(r"<h([1-6])\b[^>]*>(.*?)</h\1>", s, re.S):
                lvl = int(m.group(1))
                if prev and lvl > prev + 1:
                    txt = re.sub("<[^>]+>", "", m.group(2)).strip()[:34]
                    bad.append(f"{p}: h{prev} -> h{lvl} ({txt})")
                prev = lvl
        self.report(bad, "skipped heading levels")

    def test_links_and_buttons_have_accessible_names(self):
        bad = []
        for p, s in self.pages.items():
            for tag in ("a", "button"):
                for m in re.finditer(rf"<{tag}\b([^>]*)>(.*?)</{tag}>", s, re.S):
                    attrs, inner = m.group(1), m.group(2)
                    text = re.sub(r"<[^>]+>", "", inner).strip()
                    if not text and "aria-label" not in attrs:
                        bad.append(f"{p}: {m.group(0)[:60]}")
        self.report(bad, "links or buttons with no accessible name")

    def test_svgs_are_either_hidden_or_labelled(self):
        """A decorative SVG must be aria-hidden; a meaningful one needs a role
        and a label. Anything else is read out as a shapeless blob."""
        bad = [f"{p}: {svg[:70]}"
               for p, s in self.pages.items()
               for svg in re.findall(r"<svg\b[^>]*>", s)
               if "aria-hidden" not in svg and "role=" not in svg]
        self.report(bad, "SVGs neither hidden nor labelled")

    def test_new_tab_links_carry_rel_and_say_so(self):
        bad = [f"{p}: {a[:70]}"
               for p, s in self.pages.items()
               for a in re.findall(r'<a\b[^>]*target="_blank"[^>]*>', s)
               if "noopener" not in a]
        self.report(bad, "target=_blank without rel=noopener")

    def test_documents_declare_language_title_and_a_skip_target(self):
        bad = []
        for p, s in self.pages.items():
            if not re.search(r'<html[^>]*\blang="', s):
                bad.append(f"{p}: no lang")
            if not re.search(r"<title>.+?</title>", s):
                bad.append(f"{p}: no title")
            if 'id="main"' not in s:
                bad.append(f"{p}: no #main for the skip link")
            if 'class="skip"' not in s:
                bad.append(f"{p}: no skip link")
        self.report(bad, "document-level failures")

    def test_reduced_motion_is_honoured(self):
        css = (ROOT / "src" / "css" / "base.css").read_text(encoding="utf-8")
        self.assertIn("prefers-reduced-motion", css)
        js = (ROOT / "src" / "js" / "scroll.js").read_text(encoding="utf-8")
        self.assertIn("prefers-reduced-motion", js,
                      "scroll.js must bail before registering ScrollTrigger")

    def test_focus_is_always_visible(self):
        css = (ROOT / "src" / "css" / "base.css").read_text(encoding="utf-8")
        self.assertIn(":focus-visible", css)
        self.assertNotIn("outline: none", css)

    def test_the_skip_link_becomes_visible_when_focused(self):
        """A skip link parked off-screen that never comes back is worse than
        none: a keyboard user tabs to it and sees nothing happen."""
        css = (ROOT / "src" / "css" / "base.css").read_text(encoding="utf-8")
        hidden = re.search(r"\.skip\s*\{([^}]*)\}", css)
        shown = re.search(r"\.skip:focus\s*\{([^}]*)\}", css)
        self.assertIsNotNone(hidden, ".skip has no base rule")
        self.assertIsNotNone(shown, ".skip:focus is missing")
        self.assertIn("-9999px", hidden.group(1))
        self.assertIn("left:", shown.group(1))
        self.assertNotIn("-9999", shown.group(1))
        # and the focus rule has to come after the base rule to win
        self.assertLess(css.index(".skip {"), css.index(".skip:focus"))

    def test_hero_titles_have_something_behind_them(self):
        """Sampling the band each hero title occupies, peak backdrop
        luminance ran 0.18-0.80 across the themed tier while the mean looked
        fine everywhere, so titles have to be given separation somehow.

        A shared CSS scrim used to do it and read as a dark ellipse stuck on
        the artwork. The themed art now carries the haze itself, so the check
        is that the band is still being drawn into every generated piece."""
        gen = (ROOT / "tools" / "gen_themed.py").read_text(encoding="utf-8")
        self.assertIn("def band(", gen)
        self.assertIn("band(p, rng, c", gen)
        for slug in ("firework", "killbot", "zodiac", "black-blizzard"):
            svg = (ROOT / "src" / "art" / f"{slug}.svg").read_text(encoding="utf-8")
            self.assertIn('fill="url(#g-band)"', svg, f"{slug} lost its band")

    def test_only_slaughterhouse_keeps_a_title_scrim(self):
        """It is the one level whose backdrop cannot be handled in the art:
        the skull glow behind the title measured 0.499 peak."""
        shared = (ROOT / "src" / "css" / "components.css").read_text(encoding="utf-8")
        self.assertNotIn(".hero__art + .hero__title::before", shared)
        own = (ROOT / "src" / "css" / "levels" / "slaughterhouse.css").read_text(
            encoding="utf-8")
        self.assertIn(".hero__art + .hero__title::before", own)

    def test_grid_rows_can_shrink_on_narrow_screens(self):
        """Grid items default to min-width:auto, so a long level name refused
        to shrink and pushed the countdown past the viewport on a phone."""
        css = (ROOT / "src" / "css" / "components.css").read_text(encoding="utf-8")
        self.assertIn(".countdown__hit > * {", css)
        block = css[css.index(".countdown__hit > * {"):]
        self.assertIn("min-width: 0", block[: block.index("}")])

    def test_the_spotlight_entrance_cannot_hide_content(self):
        """Two guarantees. The hidden state is scoped to [data-enter], which
        only scroll.js sets, so a page whose JS never runs shows the panel.
        And the resting rule carries the [data-signature] prefix, because the
        per-signature entrance rules outrank a bare .spotlight[data-enter=in]
        and would otherwise park the headline at its entrance transform."""
        css = (ROOT / "src" / "css" / "components.css").read_text(encoding="utf-8")
        self.assertIn('.spotlight[data-enter] .spotlight__big', css)
        self.assertIn('[data-signature] .spotlight[data-enter="in"] '
                      '.spotlight__big', css)
        js = (ROOT / "src" / "js" / "scroll.js").read_text(encoding="utf-8")
        self.assertIn('setAttribute("data-enter", "")', js)
        self.assertIn("seenScroll", js,
                      "the failsafe must reveal when no scroll event arrives")

    def test_no_third_party_requests_on_load(self):
        """Fonts and GSAP are self-hosted. A page load must not hand the
        visitor's IP to anyone the visitor did not choose to contact."""
        offenders = collections.defaultdict(list)
        for p, s in self.pages.items():
            for host in ("fonts.googleapis.com", "fonts.gstatic.com",
                         "cdn.jsdelivr.net", "googletagmanager.com"):
                if host in s:
                    offenders[host].append(p)
        self.report([f"{h}: {len(v)} pages" for h, v in offenders.items()],
                    "third-party hosts referenced")


if __name__ == "__main__":
    unittest.main()
