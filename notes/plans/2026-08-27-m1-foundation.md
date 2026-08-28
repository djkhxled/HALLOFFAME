# M1 — Foundation and Proof: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the generator, the design system, the 25→1 scroll countdown landing page, and two fully bespoke level pages (Deimos, Nhelv) — enough for Baylor to judge the whole design before 23 more pages are built.

**Architecture:** A dependency-free Python package (`hall/`) loads per-level JSON, validates it, and renders static HTML into `docs/` via logic-free `{{ slot }}` templates. Presentation is vanilla CSS with per-level token overrides; scroll behaviour is GSAP ScrollTrigger loaded from CDN, layered on top of fully-readable server-rendered HTML.

**Tech Stack:** Python 3.14 (stdlib only — `json`, `pathlib`, `html`, `unittest`), vanilla CSS, vanilla JS, GSAP 3 + ScrollTrigger via CDN, Google Fonts.

**Spec:** `notes/specs/2026-08-27-hall-of-extremes-design.md`

## Global Constraints

- **Python standard library only.** No `pip install`, no `jinja2`, no third-party imports. Node/npm are not installed and must not be required.
- **`docs/` is the GitHub Pages publish root and contains build output only.** `build.py` owns it and may clear it. Never write specs, plans, or notes there.
- **`notes/` is never published.**
- **Never invent a fact.** Unknown values are `null` in JSON and render as `—`. No guessed attempt counts, object counts, or dates.
- **`facts.sources[]` must be non-empty** for every published level.
- **Contrast floor:** body text ≥ 4.5:1, large/display text ≥ 3:1 against the level's `field` colour. Build fails below this.
- **`prefers-reduced-motion: reduce` disables all pinning, scrubbing, and parallax.** Hard requirement, checked before any ScrollTrigger registration.
- **No autoplay** of audio or video anywhere. Video and audio are click-to-load.
- **All content is server-rendered.** JavaScript adds motion only; the site is complete and readable with JS disabled or the CDN blocked.
- Repo: `djkhxled/HALLOFFAME` (currently empty, private).

## Spec Amendment

The spec's data model gains one field, required by the countdown:

- **`published`** (boolean). `true` → full validation applies and a level page is generated. `false` → the level appears in the countdown (rank, name, creators, tagline, palette) but is not linked and gets no page. M1 ships 2 published, 23 unpublished.

## File Structure

| File | Responsibility |
|---|---|
| `build.py` | CLI entry point; orchestrates load → validate → render → report |
| `hall/__init__.py` | Package marker |
| `hall/contrast.py` | WCAG relative luminance and contrast ratio maths |
| `hall/data.py` | Load level JSON, apply defaults, validate all rules |
| `hall/render.py` | `{{ slot }}` template filling with escaping; page composition |
| `hall/art.py` | Parametric SVG generation for themed-tier levels |
| `tests/test_contrast.py` | Contrast maths |
| `tests/test_data.py` | Loading and every validation rule |
| `tests/test_render.py` | Slot filling, escaping, raw slots |
| `tests/test_build.py` | End-to-end: build produces expected files |
| `templates/base.html` | Document shell: head, skip link, footer |
| `templates/index.html` | Landing hero + countdown |
| `templates/level.html` | Level page skeleton |
| `src/css/tokens.css` | Shared skeleton tokens — never vary per level |
| `src/css/base.css` | Reset, typography, layout primitives |
| `src/css/components.css` | Countdown, stat block, player, rank nav |
| `src/css/levels/deimos.css` | Deimos theme overrides |
| `src/css/levels/nhelv.css` | Nhelv theme overrides |
| `src/js/scroll.js` | Reduced-motion guard, GSAP signatures |
| `src/js/media.js` | Click-to-load video + opt-in audio |
| `src/art/deimos.svg` | Hand-authored Deimos art |
| `src/art/nhelv.svg` | Hand-authored Nhelv art |
| `bespoke/deimos.html` | Deimos `orbit` set-piece |
| `bespoke/nhelv.html` | Nhelv `glitch-assemble` set-piece |
| `data/site.json` | Title, disclaimer, colophon |
| `data/levels/01-deimos.json` … `25-edge-of-destiny.json` | Level records |

---

### Task 1: Contrast maths

Pure functions with no I/O — the easiest thing to prove correct, and the build's accessibility gate depends on it.

**Files:**
- Create: `hall/__init__.py` (empty), `hall/contrast.py`
- Test: `tests/test_contrast.py`

**Interfaces:**
- Consumes: nothing
- Produces:
  - `parse_hex(value: str) -> tuple[int, int, int]` — accepts `#rgb` and `#rrggbb`, raises `ValueError` otherwise
  - `relative_luminance(rgb: tuple[int, int, int]) -> float`
  - `contrast_ratio(fg: str, bg: str) -> float` — takes hex strings, returns ratio 1.0–21.0

- [ ] **Step 1: Write the failing test**

```python
# tests/test_contrast.py
import unittest
from hall.contrast import parse_hex, relative_luminance, contrast_ratio


class TestParseHex(unittest.TestCase):
    def test_parses_six_digit(self):
        self.assertEqual(parse_hex("#ff8800"), (255, 136, 0))

    def test_parses_three_digit_shorthand(self):
        self.assertEqual(parse_hex("#f80"), (255, 136, 0))

    def test_rejects_garbage(self):
        with self.assertRaises(ValueError):
            parse_hex("not-a-colour")


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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_contrast -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'hall'`

- [ ] **Step 3: Write minimal implementation**

```python
# hall/contrast.py
"""WCAG 2.1 relative luminance and contrast ratio."""

def parse_hex(value: str) -> tuple[int, int, int]:
    if not isinstance(value, str) or not value.startswith("#"):
        raise ValueError(f"not a hex colour: {value!r}")
    digits = value[1:]
    if len(digits) == 3:
        digits = "".join(c * 2 for c in digits)
    if len(digits) != 6:
        raise ValueError(f"not a hex colour: {value!r}")
    try:
        return (int(digits[0:2], 16), int(digits[2:4], 16), int(digits[4:6], 16))
    except ValueError:
        raise ValueError(f"not a hex colour: {value!r}") from None


def _channel(c: int) -> float:
    s = c / 255
    return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb: tuple[int, int, int]) -> float:
    r, g, b = (_channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg: str, bg: str) -> float:
    lum_a = relative_luminance(parse_hex(fg))
    lum_b = relative_luminance(parse_hex(bg))
    lighter, darker = max(lum_a, lum_b), min(lum_a, lum_b)
    return (lighter + 0.05) / (darker + 0.05)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_contrast -v`
Expected: PASS, 5 tests

- [ ] **Step 5: Commit**

```bash
git add hall/ tests/test_contrast.py
git commit -m "feat: add WCAG contrast maths"
```

---

### Task 2: Level data loading and validation

Every rule from the spec's "Build validation" section, enforced here.

**Files:**
- Create: `hall/data.py`
- Test: `tests/test_data.py`

**Interfaces:**
- Consumes: `hall.contrast.contrast_ratio`
- Produces:
  - `SIGNATURES: frozenset[str]` — `orbit, glitch-assemble, descend, surge, ignite, pulse, fracture, flood, static`
  - `TEXTURES: frozenset[str]` — `starfield, scanline, grain, caustics, ember, snow, chrome, none`
  - `class ValidationError(Exception)`
  - `load_levels(levels_dir: pathlib.Path) -> list[dict]` — returns records sorted by rank
  - `validate_levels(levels: list[dict], root: pathlib.Path) -> list[str]` — returns list of human-readable error strings; empty means valid

**Validation rules:**
1. Ranks are exactly 1..N with no gaps or duplicates
2. Slugs unique and non-empty
3. Every level has `rank`, `slug`, `name`, `tagline`, `theme.palette.field`, `theme.palette.ink`
4. Published levels additionally require `theme.tier`, `theme.signature`, non-empty `facts.sources`, and `voice.why`
5. `theme.signature` ∈ `SIGNATURES`; `theme.texture` ∈ `TEXTURES`
6. `theme.tier` ∈ `{bespoke, themed}`
7. Themed-tier levels must not declare `media.art`, a `bespoke/<slug>.html`, or `src/css/levels/<slug>.css`
8. Referenced art, bespoke fragment, and level CSS files must exist on disk
9. Contrast: `ink` vs `field` ≥ 4.5, `muted` vs `field` ≥ 4.5

- [ ] **Step 1: Write the failing test**

```python
# tests/test_data.py
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
        self.assertTrue(any("rank" in e for e in errs))

    def test_gap_in_ranks_is_an_error(self):
        errs = self._check([minimal(1, "alpha"), minimal(3, "gamma")])
        self.assertTrue(any("rank" in e for e in errs))

    def test_unknown_signature_is_an_error(self):
        bad = minimal(1, "alpha")
        bad["theme"]["signature"] = "wobble"
        errs = self._check([bad])
        self.assertTrue(any("signature" in e for e in errs))

    def test_low_contrast_ink_is_an_error(self):
        bad = minimal(1, "alpha")
        bad["theme"]["palette"]["ink"] = "#0a0b10"
        errs = self._check([bad])
        self.assertTrue(any("contrast" in e for e in errs))

    def test_published_level_requires_sources(self):
        bad = minimal(1, "alpha", published=True)
        bad["voice"] = {"why": "<p>x</p>"}
        bad["facts"] = {"sources": []}
        errs = self._check([bad])
        self.assertTrue(any("sources" in e for e in errs))

    def test_themed_level_may_not_declare_art(self):
        bad = minimal(1, "alpha")
        bad["media"] = {"art": "src/art/alpha.svg"}
        errs = self._check([bad])
        self.assertTrue(any("themed" in e for e in errs))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_data -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'hall.data'`

- [ ] **Step 3: Implement `hall/data.py`**

Implement `load_levels` (glob `*.json`, parse, sort by `rank`) and `validate_levels` enforcing rules 1–9 above, accumulating errors into a list rather than raising on the first. Each error string names the offending slug and the rule, e.g. `"nhelv: contrast ink #.. on field #.. is 3.1, need 4.5"`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_data -v`
Expected: PASS, 8 tests

- [ ] **Step 5: Commit**

```bash
git add hall/data.py tests/test_data.py
git commit -m "feat: add level data loading and validation"
```

---

### Task 3: Template rendering

Logic-free `{{ slot }}` substitution. Escaping by default is what keeps level names and commentary from breaking the page.

**Files:**
- Create: `hall/render.py`
- Test: `tests/test_render.py`

**Interfaces:**
- Consumes: nothing
- Produces:
  - `fill(template: str, slots: dict[str, str]) -> str` — replaces `{{ key }}`; values HTML-escaped unless the key ends in `_html`; a `{{ key }}` with no matching slot raises `KeyError`; an unused slot raises `KeyError`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_render.py
import unittest
from hall.render import fill


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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_render -v`
Expected: FAIL — no module `hall.render`

- [ ] **Step 3: Implement `hall/render.py`**

Use `re.sub` over `\{\{\s*(\w+)\s*\}\}`. Escape with `html.escape` unless the key ends `_html`. Track which slots were consumed; raise `KeyError` listing any that were not.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_render -v`
Expected: PASS, 6 tests

- [ ] **Step 5: Commit**

```bash
git add hall/render.py tests/test_render.py
git commit -m "feat: add logic-free template rendering"
```

---

### Task 4: Design system — tokens, base, components

The shared skeleton. No level-specific values may appear in these files.

**Files:**
- Create: `src/css/tokens.css`, `src/css/base.css`, `src/css/components.css`

**Interfaces:**
- Produces CSS custom properties consumed by every page and overridden per level:
  `--field`, `--ink`, `--muted`, `--accent`, `--accent2` (theme surface)
  `--step--2 … --step-8` (type scale), `--space-1 … --space-12`, `--rule`, `--measure`

- [ ] **Step 1: Write `tokens.css`** — fluid type scale with `clamp()`, spacing scale, rule weights, durations. Theme surface variables get neutral defaults here so a page renders sanely before any level CSS loads.

- [ ] **Step 2: Write `base.css`** — reset, `body { background: var(--field); color: var(--ink) }`, display/mono/body font stacks from Google Fonts, `.measure` for readable line length, visible `:focus-visible` outline, skip-link, and a global `@media (prefers-reduced-motion: reduce)` block that sets `animation: none` and `transition: none` and unsets transforms on `[data-motion]` elements.

- [ ] **Step 3: Write `components.css`** — `.countdown`, `.countdown__entry`, `.rank-badge`, `.statblock` (mono grid, `—` for nulls), `.voice`, `.voice__drafted` marker, `.player`, `.videoframe` (click-to-load poster), `.ranknav`, `.sources`.

- [ ] **Step 4: Verify no level-specific values leaked**

Run: `grep -nE '#(?!fff|000)[0-9a-fA-F]{6}' src/css/tokens.css src/css/components.css || echo "clean"`
Expected: only neutral defaults in `tokens.css`; no accent colours in `components.css`

- [ ] **Step 5: Commit**

```bash
git add src/css/
git commit -m "feat: add design system tokens, base, and components"
```

---

### Task 5: Templates and page composition

**Files:**
- Create: `templates/base.html`, `templates/index.html`, `templates/level.html`
- Modify: `hall/render.py` — add `render_level`, `render_index`

**Interfaces:**
- Consumes: `fill`, level records
- Produces:
  - `render_level(level: dict, site: dict, prev: dict | None, nxt: dict | None, bespoke_html: str) -> str`
  - `render_index(levels: list[dict], site: dict) -> str`
  - `statblock_html(facts: dict) -> str` — renders `None` as `—`, never omits a labelled row

- [ ] **Step 1: Write `templates/base.html`** — `<!doctype html>`, `<html lang="en" data-level="{{ slug }}">`, meta description, Open Graph tags, Google Fonts preconnect, `{{ head_extra_html }}`, skip link, `{{ body_html }}`, footer with disclaimer, deferred scripts.

- [ ] **Step 2: Write `templates/level.html`** — the seven sections from the spec in order: hero, `{{ bespoke_html }}`, statblock, voice, video, player, ranknav, sources.

- [ ] **Step 3: Write `templates/index.html`** — hero with site title and the "personal favourites, not a difficulty ranking" statement, then `{{ countdown_html }}`, then colophon.

- [ ] **Step 4: Implement the render functions** in `hall/render.py`, composing all repetition in Python.

- [ ] **Step 5: Add an end-to-end test**

```python
# tests/test_build.py
import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent


class TestBuild(unittest.TestCase):
    def test_build_emits_expected_pages(self):
        subprocess.run(["python3", "build.py"], cwd=ROOT, check=True,
                       capture_output=True)
        self.assertTrue((ROOT / "docs" / "index.html").is_file())
        self.assertTrue((ROOT / "docs" / "levels" / "deimos" / "index.html").is_file())
        self.assertTrue((ROOT / "docs" / "levels" / "nhelv" / "index.html").is_file())

    def test_unpublished_levels_get_no_page(self):
        self.assertFalse((ROOT / "docs" / "levels" / "killbot").exists())

    def test_index_lists_all_25_ranks(self):
        html = (ROOT / "docs" / "index.html").read_text()
        self.assertEqual(html.count('class="countdown__entry'), 25)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 6: Commit**

```bash
git add templates/ hall/render.py tests/test_build.py
git commit -m "feat: add templates and page composition"
```

---

### Task 6: `build.py` orchestration

**Files:**
- Create: `build.py`, `data/site.json`

**Interfaces:**
- Consumes: `hall.data`, `hall.render`, `hall.art`
- Produces: CLI. Exit code 0 on success, 1 with errors printed on validation failure.

- [ ] **Step 1: Implement** — clear `docs/`, load site + levels, validate (abort on any error), copy `src/css` and `src/js` and `src/art` to `docs/assets/`, render index and each published level, write files.

- [ ] **Step 2: Print the report**

```
Hall of Extremes — build
  levels:  25 records, 2 published
  pages:   3 written
  voice:   0/25 in your words
```

- [ ] **Step 3: Verify the validation gate actually blocks**

Temporarily set `ink` to `#0a0b10` in one level, run `python3 build.py`, confirm exit code 1 and a contrast error naming that level, then revert.

- [ ] **Step 4: Commit**

```bash
git add build.py data/site.json
git commit -m "feat: add build orchestration and validation gate"
```

---

### Task 7: Motion and media JavaScript

**Files:**
- Create: `src/js/scroll.js`, `src/js/media.js`

- [ ] **Step 1: Write `scroll.js`** — first statement checks `window.matchMedia('(prefers-reduced-motion: reduce)').matches` and returns immediately if true, before GSAP is touched. Then guard `typeof gsap === 'undefined'` and return (CDN failure path). Then register ScrollTrigger and implement the signature dispatch: read `document.documentElement.dataset.signature` and run the matching setup. Implement `orbit`, `glitch-assemble`, and the countdown's pinned rank scrub; the remaining signatures are stubs that fall back to reveal-only.

- [ ] **Step 2: Write `media.js`** — click-to-load: replace the video poster button with the YouTube iframe only on click; audio player with explicit play/pause, no autoplay, keyboard operable, and a labelled control.

- [ ] **Step 3: Verify the reduced-motion path**

Load the page with reduced motion emulated and confirm no `ScrollTrigger` instances are created and all content is visible and static.

- [ ] **Step 4: Commit**

```bash
git add src/js/
git commit -m "feat: add scroll signatures and click-to-load media"
```

---

### Task 8: All 25 level records

Research-backed for the two published levels; countdown-minimal for the rest.

**Files:**
- Create: `data/levels/01-deimos.json` … `data/levels/25-edge-of-destiny.json`

- [ ] **Step 1: Research Deimos and Nhelv** — creators, host, verifier, dates, level ID, object count, length, song and artist, peak rank. Record every source URL in `facts.sources`. **Anything not confirmed stays `null`.**

- [ ] **Step 2: Write the two published records** with `published: true`, `tier: "bespoke"`, full `facts`, `theme`, and a drafted `voice.why` with `draftedByClaude: true`.

- [ ] **Step 3: Write the 23 unpublished records** with `published: false` and only rank, slug, name, creators as supplied, a one-line tagline, and a palette matching each level's known visual identity. Correct the spellings flagged in the spec (SrGuillester; verify "Maniacal Chains").

- [ ] **Step 4: Run the build and confirm validation passes**

Run: `python3 build.py`
Expected: exit 0, `25 records, 2 published`

- [ ] **Step 5: Commit**

```bash
git add data/levels/
git commit -m "content: add all 25 level records, 2 published"
```

---

### Task 9: Deimos — art, theme, set-piece

**Files:**
- Create: `src/art/deimos.svg`, `src/css/levels/deimos.css`, `bespoke/deimos.html`

- [ ] **Step 1: Author the art** — original SVG on the Mars-moon reading of the name: a cratered body, a hard terminator line, starfield. No traced or copied imagery.
- [ ] **Step 2: Write the theme CSS** — palette overrides plus the `starfield` texture layer.
- [ ] **Step 3: Write the `orbit` set-piece** — layered bodies parallaxing at different rates as the section scrubs, with the level name holding position.
- [ ] **Step 4: Build and screenshot** at desktop and mobile; confirm zero console errors.
- [ ] **Step 5: Commit**

```bash
git add src/art/deimos.svg src/css/levels/deimos.css bespoke/deimos.html
git commit -m "feat: add Deimos bespoke treatment"
```

---

### Task 10: Nhelv — art, theme, set-piece

**Files:**
- Create: `src/art/nhelv.svg`, `src/css/levels/nhelv.css`, `bespoke/nhelv.html`

- [ ] **Step 1: Author the art** — original SVG echoing the level's documented music-video-derived decoration: violet field, hard geometric slices, flashing rhythm. Original work, not a trace of the level or the video.
- [ ] **Step 2: Write the theme CSS** — violet/cyan palette plus the `scanline` texture.
- [ ] **Step 3: Write the `glitch-assemble` set-piece** — the headline assembles from horizontally displaced slices as the section scrubs.
- [ ] **Step 4: Build and screenshot**; confirm zero console errors.
- [ ] **Step 5: Commit**

```bash
git add src/art/nhelv.svg src/css/levels/nhelv.css bespoke/nhelv.html
git commit -m "feat: add Nhelv bespoke treatment"
```

---

### Task 11: Verification pass

- [ ] **Step 1: Run the full test suite**

Run: `python3 -m unittest discover -s tests -v`
Expected: all pass

- [ ] **Step 2: Serve and drive the site** — start a preview server, visit `/`, `/levels/deimos/`, `/levels/nhelv/`; check console for errors on each.
- [ ] **Step 3: Screenshot** each page at desktop (1440) and mobile (375).
- [ ] **Step 4: Verify reduced-motion** renders the static fallback with all content present.
- [ ] **Step 5: Verify the no-JS path** — confirm all text content is in the HTML source.
- [ ] **Step 6: Commit any fixes**

---

### Task 12: Push to GitHub

`djkhxled/HALLOFFAME` is empty and private — confirmed before planning.

- [ ] **Step 1: Write `README.md`** — what the site is, that it's a personal favourites list unaffiliated with RobTop Games, how to build (`python3 build.py`), how to test, and how to edit commentary.
- [ ] **Step 2: Review what is staged**

Run: `git status --short` and confirm no `.DS_Store`, no secrets, no stray files.

- [ ] **Step 3: Add the remote and push**

```bash
git remote add origin https://github.com/djkhxled/HALLOFFAME.git
git push -u origin main
```

- [ ] **Step 4: Report the Pages situation** — the repo is private, so GitHub Pages will not serve it until Baylor makes it public. Do not change repo visibility.

---

## Self-Review

**Spec coverage.** Architecture → Tasks 1–6. Data model → Task 2, 8. Design system → Task 4. Page structures → Task 5. Theme engine and signature library → Tasks 7, 9, 10. Accessibility → Tasks 4, 7, 11. Build validation → Tasks 2, 6. Testing → Tasks 1–3, 5, 11. Attribution → Tasks 8, 12. Art-by-tier rule → Task 2 rule 7. Every spec section maps to a task.

**Placeholders.** Tasks 1–3 carry complete test code and Task 1 carries complete implementation code. Tasks 4–10 specify exact files, named interfaces, and concrete acceptance checks; their content is design work that cannot be pre-written without simply writing it, but no step says "implement later" or "handle edge cases" — each names its deliverable and how to verify it.

**Type consistency.** `contrast_ratio(fg, bg)` returns a float and is called by `validate_levels`. `fill(template, slots)` is used by `render_level` and `render_index`. `load_levels` returns rank-sorted dicts, matching what `validate_levels` and `render_index` consume. `statblock_html(facts)` consumes the `facts` sub-dict only. Slug-keyed file lookups (`src/css/levels/<slug>.css`, `bespoke/<slug>.html`, `src/art/<slug>.svg`) use the same `slug` field throughout.

**Known deferral.** Signatures `descend`, `surge`, `ignite`, `pulse`, `fracture`, and `flood` are declared in the library and validated against, but only `orbit` and `glitch-assemble` are implemented in M1 — the rest fall back to reveal-only until the levels that need them are built in M2. This is deliberate and stated in Task 7 Step 1.
