# GeometryGuessr — Design Spec

**Date:** 2026-10-02
**Status:** Design approved in conversation; spec awaiting owner review

## Overview

A third game for the site, in the style of GeoGuessr. The player is shown a
screenshot taken from the middle of a Geometry Dash level and must work out
**which level it is**, then **where in the level it was taken**. It is an endless
streak game with three lives. Everything runs in the browser: no backend, no
network request from the game's scripts, no account.

The answer pool is the **100 most downloaded demons** (platformers left out) on the
official Geometry Dash servers. *(Grown on 2026-10-02 from the first 20; demons only.)* The search list the player picks from is larger than the
answer pool, so the list of names does not give the pool away.

### Goals

- A round the player can reason about: the screenshot is clear enough to recognise a
  level from its art, layout and colours.
- Two-part scoring in the spirit of GeoGuessr: right level, then closeness of the spot.
- Uniform screenshots, repeatable capture, and a pool that can grow without touching
  the game's code.
- Zero new infrastructure. Static page, build-time data, `localStorage`.
- Same chrome, motion and accessibility rules as the rest of the site.

### Non-goals (for now)

- No daily mode, leaderboard, multiplayer or accounts. Each can be added later without
  changing anything below.
- No hard mode, crops or blurring.
- No automated image scraping from videos (the footage is not ours to take).

## Gameplay

> **Changed 2026-10-03 (owner):** five rounds a game, five different demons, **no lives**
> (a wrong name scores 0 that round and the game goes on, as in GeoGuessr); score out of
> 5,000 (since 2026-10-04: 500 for the name plus up to 500 for the spot, so a right name
> always counts); ranked by score, then demons named. Shots can be cropped to a 16:9 box to make
> them harder (`tools/crop_shots.py`, applied by `tools/prepare_shots.py`). A
> public score board joined the game, on the same records service as the naming game. The
> text below describes the original endless, three-life version.

A **run** is a sequence of rounds. It starts with 3 lives and ends at 0.

### A round

1. A 16:9 screenshot is shown. No timer.
2. **The level.** The player searches the type-ahead list and picks one level. One
   guess per screenshot.
   - **Wrong:** lose a life. The correct level is revealed (name, creator, the real
     position), then the player continues to the next round. If that was the last life
     the run ends instead.
   - **Right:** Levels named goes up by one and step 3 appears.
3. **The spot.** A bar representing the whole level, 0% to 100%, with a draggable
   marker (also operable by keyboard). On confirm the real position is shown on the
   bar beside the guess, and the round's points are awarded.

### Scoring

- Round points = `round(1000 × max(0, 1 − max(0, |error| − 2) / 28))`, where `error`
  is the distance in percentage points between guess and truth. Within 2 points is a
  full 1,000; 30 or more points away is 0.
- A wrong level scores 0 for the round and skips step 3.
- The run has two numbers: **Levels named** (rounds where the level was picked
  correctly, over the whole run) and **Score** (the sum of spot points). The streak
  the player is chasing is Levels named, which only goes up; lives are what end the run.
  Both numbers are shown live and on the end screen, and the best of each is stored.

### Round selection

- A level is drawn at random from the pool, then one of its screenshots at random.
- No screenshot repeats within a run until every one in the pool has been shown, then
  the pool is reshuffled.
- A level never appears two rounds in a row when the pool has more than one level.

### Search list

- Contains the answer pool **plus decoys**: about 100 other popular demons by
  downloads (ids, names, creators only; no screenshots).
- Match by case-insensitive substring on name, as Demondle does.
- A decoy is never an answer. Picking one is a normal wrong guess.

## Data

### Popular levels (build-time, owner-reviewed)

`tools/fetch_popular.py` reads the official GD servers (the same `getGJLevels21.php`
access `tools/gdlength.py` uses for research) with demon difficulty, sorted by
downloads, and writes `data/spot/popular.json`:

```
{ "fetched": "2026-10-02",
  "levels": [ { "id": 10565740, "name": "...", "creator": "...", "downloads": 0, "rank": 1 } ] }
```

- The first 100 are the **answer pool**; the next ~100 are **decoys**.
- `data/spot/pool.json` is the owner-approved, committed list of answer ids (and slugs).
  The tool never edits it. The owner can drop any level from the pool.
- The tool is manual and never runs in the build. The build only reads committed files.

### Screenshots

`data/spot/shots.json`:

```
{ "shots": [ { "level": 10565740, "pct": 37, "file": "bloodbath/037.webp", "alt": "..." } ] }
```

- `pct` is the position in the level, 0–100, an integer, **recorded by the capture
  tool**, not guessed after the fact.
- Target: about 6 shots per level, spread across the level (not clustered), none from the
  very first or last 3%.
- **Target percentages differ per level**: drawn at random (seeded, so re-runnable) between
  4 and 96, at least 8 points apart. A fixed set (10, 25, 40…) for every level would let
  players learn the six answers and snap the slider to them.
- Image spec: WebP at the game's own render size, **1138×640** (16:9; the capture spike
  showed this is what the game renders at, and upscaling adds nothing), about 80 KB, no
  HUD, no attempt counter, no icon, no trails or hit rings. Source PNGs are not committed;
  only the WebP outputs.
- Files live under `src/shots/<slug>/` and are copied to `docs/` by the build with
  content-hashed names, like other assets.
- `alt` is a short description for screen readers that does not name the level.

`tools/prepare_shots.py` (one-off, needs Pillow, like `tools/make_cards.py`; **not**
part of the standard-library-only build) crops to 16:9, resizes, converts to WebP, names
files and updates `shots.json`.

## Capture

**Spike result (2026-10-02):** the automatic version (mod plays the level alone) failed:
with no input the icon falls out of the path in ship/wave sections and the camera follows
it. The working version is **owner plays, mod shoots**: the owner plays each queued level
following the real path; the mod forces noclip on queued levels only, takes each shot in a
single frame with the icon, trails, hit rings and HUD hidden, blocks completion, and
restores the level's progress on quit. Bloodbath test: 6/6 shots, each within 0.01% of
target, clean. Source: `~/Documents/Claude/geometryguessr-capture/` (not in the site repo).

The original plan, kept for the record:

### Spike: Geode mod

A small Geode mod, kept outside the site's published output (under `tools/` or a sibling
folder; `notes/` and `worker/` are never published and neither is this), using the
owner's existing Geode setup on macOS.

- Input: a list of level ids and target percentages.
- Behaviour: load the level, run it with noclip so it plays through, save a HUD-free
  screenshot when the player reaches each target percentage, and write the real
  percentage in the filename.
- Uses only the owner's own copy of the game, with levels downloaded in-game.

**Success criteria (one level):** 6 frames, each at its intended percentage within 1
point, identical resolution, no HUD, clear enough to recognise the level.

**Fallback:** if the mod is unreliable (Mac quirks, HUD cannot be hidden, timing drift),
stop. The owner captures by hand from a checklist (level, six target percentages) using
practice mode or a start position, and `prepare_shots.py` does the rest. The game and data
format do not change between the two routes.

## Page and code

Follows the Demondle structure.

- Page: `/geometryguessr/`, built by `build_geometryguessr` in `build.py` into
  `docs/geometryguessr/`.
- `src/js/gg-core.js` (`window.GGCore`): pure rules. Scoring, round selection, search
  matching, run state transitions. No DOM, no storage, no network. Tested by
  `tests/gg.check.html`, run in a browser via `python3 -m http.server`, like
  `guess.check.html`.
- `src/js/gg.js`: UI only (screenshot, search box, hearts, the level bar and marker,
  reveal and end screens). One localStorage key, `hall-of-extremes.gg.v1`, storing the
  best of each number and the sound preference if one is added.
- `src/css/gg.css`, `templates/gg.html`.
- Build-time data embedded into the page the way `guess.data_json` does it: short keys,
  `fetched`, shots list, answer pool, decoys.
- Build fails if: the pool has fewer than 5 levels, any shot in `shots.json` has no file,
  a shot's `pct` is outside 3–97, or an answer id is missing from `popular.json`.

### Navigation and chrome

- Third card on the Games hub (`/games/`) and a mention in the hub lede if it names the
  games. Site name for the game: **GeometryGuessr**.
- A share card, `src/art/og-geometryguessr.png`, drawn with `tools/make_cards.py` like the
  others; `card()` in `build.py` and the `CARD_ALT` entry wired the same way, and the
  existing `ShareCard` test then covers it.
- `pages/privacy.html`: add the new storage key and keep the sentence that no script
  other than the games writes to localStorage correct.
- `pages/credits.html`: a section crediting the levels and creators shown, and stating
  that the screenshots are of other people's levels (see Rights).

## Accessibility and motion

- Screenshot has `alt` text that does not give the answer away.
- Search box is a labelled combobox, fully keyboard-operable; lives and results are
  announced via a live region.
- The level bar's marker is a slider (`role="slider"`, arrow keys, Home/End, value text
  "37 percent").
- Honour `prefers-reduced-motion`. No flashing.
- The mobile layout puts the screenshot full-width above the controls.

## Testing

- `gg-core` checks (browser page): scoring at 0, 2, 30 and 100 points of error; the
  no-repeat and no-back-to-back rules; life and end-of-run transitions; search matching.
- Python tests: data validation rules above, built-page contents, hub card present,
  privacy lists the key, share card exists and is 1200×630, no network calls in the
  game's scripts (the existing "no network" scan extended to `gg.js` and `gg-core.js`).
- Full existing suite stays green.

## Rights and risk (owner's decision recorded)

Screenshots show other creators' levels and RobTop Games' artwork. This is common practice
for fan sites and very likely fine, but it is not a licence.

- Every reveal names the level and its creator.
- The credits page says what the screenshots are.
- A creator who wants a level removed can ask at the support email and the level is
  dropped from the pool; the build must still pass without it (minimum 5 levels).
- Only WebP outputs are committed, no game files, no level data, no extracted assets.

## Open items for the owner

1. Drop any of the 100 that do not work as a guess.
2. Decide the **rights approach** above, or change it.
3. Confirm the spike result before we commit to the mod for all 20 levels.

## Build order

1. `fetch_popular.py`, then the owner approves the pool.
2. Capture spike on one level (fallback to hand capture if it fails).
3. Capture the remaining levels.
4. `gg-core` with checks, then the UI, page and tests.
5. Hub card, share card, privacy and credits pages, README, deploy.
