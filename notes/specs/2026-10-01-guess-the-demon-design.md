# Guess the Demon — Design Spec

**Date:** 2026-10-01
**Status:** Approved in conversation; written for implementation

## Overview

A second game for the site, in the style of Wordle. A hidden level is chosen from
the Pointercrate Demonlist's Main and Extended lists (positions 1–150), with the length of
each level taken from its Pointercrate page (see Data). The player
guesses levels by name; each guess reveals how its **stats** compare to the answer
instead of letters. Six guesses per round.

Two modes: **Daily** (one level per day, the same for everyone) and **Infinite**
(random levels, play as many rounds as you like). Everything runs in the browser.
There is no backend, no network request, and no account.

### Goals

- A fair puzzle: every stat is a fact a player can reason about and look up.
- Zero new infrastructure. Static page, build-time data, `localStorage`.
- Feels like the rest of the site: same chrome, same motion rules, same accessibility.
- The 150-level snapshot is refreshable without rewriting history (past daily
  answers never change).

### Non-goals

- No leaderboard, no accounts, no network. (The naming game's record boards are
  separate and untouched.)
- No anti-cheat. The answer list is in the page; the site has said it does not
  care about cheating.
- No hint system beyond the stats themselves.

## Decisions (from brainstorming)

| Question | Decision |
|---|---|
| Which 150 | Pointercrate Demonlist, Main (1–75) + Extended (76–150) |
| Guesses | 6 per round, in both modes |
| Stats | Rank, Peak rank, Verification year, Version, Length (real time), Number of creators |
| Daily mechanism | Committed schedule file; answer chosen by local calendar date |
| Navigation | Top-right tab becomes **Games**, opening a hub at `/games/` |
| Name / path | **Guess the Demon**, `/guess/` (renameable by editing `data/site.json`) |

## Data

### Source files

- `data/guess/demonlist.json` — the snapshot (generated, committed).
- `data/guess/schedule.json` — the daily schedule (generated once, extended on refresh, committed).
- `data/guess/overrides.json` — hand-checked values that win over derived ones, keyed by `levelId` (`seconds`, `year`), each with a short `why` (committed).

### Level record (one per level, ordered by rank)

```json
{
  "id": 219,                 // Pointercrate demon id (stable key for the name list)
  "levelId": 52374843,       // in-game level id; the join key to AREDL and GD History
  "name": "Zodiac",
  "rank": 165,
  "peak": 1,                 // best position ever held (minimum of the movement history)
  "year": 2019,              // verification year, see rule below
  "version": "2.1",          // one of 1.8, 1.9PS, 2.0, 2.1, 2.2
  "seconds": 194,            // real length, whole seconds
  "creators": 22,            // number of credited creators
  "creatorNames": ["Bianox", "..."],   // for the hover list only
  "sources": {"length": "wiki.gg|fandom|computed|manual"}
}
```

The snapshot header carries `fetched` (ISO date) and `source` URLs. The page states
the snapshot date, since ranks move weekly.

### Fetch tool: `tools/fetch_demonlist.py`

Python standard library only (matching `tools/fetch_aredl.py`). Steps:

1. `GET https://pointercrate.com/api/v2/demons/listed/` (two pages of ≤100) to get
   the top 150: id, position, name, level_id, creators (names).
2. `GET https://api.aredl.net/v2/api/aredl/levels` and the per-level detail
   (`/levels/{uuid}`) for the verification list and tags. Join on `level_id`.
3. Derive fields (rules below). Any level that cannot be fully derived stops the
   run with a message naming the level and the missing field. Nothing is guessed.
4. Write `demonlist.json` and extend `schedule.json`.

### Derivation rules

- **rank**: Pointercrate position.
- **peak**: the smallest `new_position` in Pointercrate's movement history for the level
  (`/api/v2/demons/<id>/audit/movement/`), never worse than the current rank. A level with
  no history stops the run.
- **year**: year of the *first* verification record on AREDL for the level, matching
  the site's rule of using the legitimate verification. Where AREDL's list holds a
  hack-verification that is known to be void, the tool uses the first verification
  by the credited verifier on the Pointercrate record. Levels where those two
  disagree stop the run and are settled by hand in `overrides.json`.
- **version**: AREDL tag in {`1.8`, `1.9PS`, `2.0`, `2.1`, `2.2`}. Exactly one must be
  present, else the tool stops. Ordinal scale in that order.
- **creators**: Pointercrate's credited creators, de-duplicated case-insensitively;
  the count is the stat. Names are kept for the hover list.
- **seconds** (Length): a published time only, first available of
  1. `data/guess/overrides.json` manual value (always wins),
  2. the **Pointercrate level page** (`https://pointercrate.com/demonlist/<rank>/`,
     "Level Length 1m:26s"), accepted only if the page's Level ID equals the level's
     id (pages are addressed by rank and ranks move),
  3. a time from the Geometry Dash wiki or fan wiki (`data/guess/wiki_lengths.json`,
     captured through a browser and matched by infobox level id), used only for a
     level whose Pointercrate page shows no length (ORBIT: its ball pit has none).
  A level with none of these is held out and listed in `data/guess/pending.json`.

Pointercrate is the one source for nearly every level so that the stat is consistent
and anyone can check it on the level's page. It does not agree with the wikis: of the
82 levels both cover, 23 are within one second, the median difference is 0 and the
mean absolute difference is 6.7 s (Every End: 440 s on the wiki, 544 s on
Pointercrate). Neither is "wrong"; they measure differently. The wiki times are kept
only as the ORBIT fallback and as a cross-check. A length computed from the level
data (`tools/gdlength.py`, with `tools/validate_lengths.py`) matches the wiki on 89%
of levels but is wrong by up to 40 s on the rest with no way to tell which, so it is
a research tool and is never used for the game.

### Schedule: `data/guess/schedule.json`

```json
{ "launch": "2026-10-01", "seed": 20261001, "days": [ {"date": "2026-10-05", "levelId": 52374843}, ... ] }
```

- Day 1 is the `launch` date; the game shows "#N" where N is days since launch + 1.
- Generated with `random.Random(seed)` over the sorted level ids: a shuffled order
  of the whole pool repeated until the schedule covers 3 years; each cycle is a fresh
  shuffle and no level repeats within a cycle.
- **Past days are immutable.** On refresh the tool only (re)generates days after
  today. A level that has left the top 150 is skipped for future days only.
- A day with no entry (schedule exhausted) falls back to a deterministic pick from
  the date so the game never breaks; a build check fails long before that happens
  (schedule must cover at least 180 days ahead of the build date).
- The page contains the schedule, so the daily answer is readable from the source.
  That is accepted (see non-goals).

The browser decides "today" from the player's **local** date.

## Judging rules

The judging function is pure: `judge(guess, answer) -> {rank, peak, year, version, seconds, creators}`,
each result `{state, arrow}` where `state` is `exact`, `close` or `miss`, and `arrow`
is `up`, `down` or `none`. `exact` always has no arrow.

Arrows point toward the answer: `up` means the answer's number is larger than the
guess's, except **Rank**, which is read like a leaderboard: `up` means higher on the list
(a smaller rank number, nearer #1), so guessing #1 can never say the answer is higher.

| Stat | exact | close | miss |
|---|---|---|---|
| Rank | same rank | `abs(diff) <= 10` | otherwise |
| Peak | same peak | `abs(diff) <= 5` | otherwise |
| Year | same year | `abs(diff) <= 1` | otherwise |
| Version | same | adjacent on 1.8 < 1.9PS < 2.0 < 2.1 < 2.2 | otherwise |
| Length | same whole second | `abs(diff) <= 30` seconds | otherwise |
| Creators | same count | `abs(diff) <= max(2, round(0.2 * answerCount))` | otherwise |

A guess equal to the answer is a win (all five exact). Guessing the same level twice
is refused.

## Interface

### Page `/guess/`

- Hero in the same style as the naming game (eyebrow, art, title "Guess the Demon",
  lede, top nav with "Games" current).
- Mode switch: **Daily** / **Infinite** (a radio group).
- Input: text field with an accessible combobox listbox of matches (substring,
  case/diacritic-insensitive, same normalisation as the naming game). Arrow keys +
  Enter, tap to choose. Only levels in the pool are accepted. Matches show name and
  rank.
- Board: six rows. Each row is the level name plus six cells (two rows of three on a phone). Each cell shows the
  value, a glyph (`✓` exact, `~` close, `✗` miss) and an arrow (`▲`/`▼`). Cell text
  and a visually-hidden label carry the meaning, so colour is never the only signal.
  The Creators cell shows the count; the names are in a tooltip using the existing
  `credit` tooltip component (hover, focus, and tap).
- Time is shown as `2m 54s`.
- Reveal: cells flip left to right with a short stagger via the shared `motion()`
  helper (instant under `prefers-reduced-motion`). Sound: a soft tick per row and a
  chime on a win, using the naming game's WebAudio helper and its mute button.
- Result card (win or lose): the answer's name, rank, a one-line summary ("You got
  it in 4 of 6"), and if the answer is one of the Hall's ranked levels, a link to its
  page. Buttons: **Share**, and **Next level** (Infinite) or a countdown to the next
  daily (Daily).
- Share text: `Hall of Extremes — Guess the Demon #N · 4/6` followed by a
  🟩🟨⬛ grid (one emoji per cell, one row per guess), no level names, no arrows.
- Stats panel: played, win %, current streak, best streak, and a 1–6 distribution,
  separately for Daily and Infinite (streaks for Daily only).
- Snapshot note: "Ranks as of <date>".

### Games hub `/games/` and navigation

- `render.TABS` changes the second tab to **Games** → `/games/`.
- `/games/` is a small page: a card per game (Name Every Extreme Demon → `/game/`,
  Guess the Demon → `/guess/`), in the site's document style.
- The hero tab for `/game/` and `/guess/` is marked `aria-current` as "Games".
- `/game/` is unchanged and keeps working.

## State and storage

One `localStorage` key, `hall-of-extremes.guess.v1`, JSON:

```json
{ "v": 1, "sound": true, "mode": "daily",
  "daily":    { "day": 12, "guesses": [levelId, ...], "done": true, "won": true },
  "infinite": { "levelId": 52374843, "guesses": [levelId, ...], "done": false, "seen": [levelId, ...] },
  "stats":    { "daily": {"played":0,"won":0,"streak":0,"best":0,"dist":[0,0,0,0,0,0]},
                "infinite": {"played":0,"won":0,"dist":[0,0,0,0,0,0]} } }
```

- Reads and writes are wrapped in try/catch; the game works without storage.
- A saved daily whose `day` differs from today is archived into the stats and
  replaced with a fresh round. Missing a day resets the daily streak.
- A saved guess id no longer in the pool (after a refresh) is dropped from display;
  a saved answer no longer in the pool for Infinite starts a new round.
- Infinite picks uniformly from levels not in `seen`; when all are seen, `seen`
  resets.

## Privacy

No network access. The privacy page's storage list gains one line for this key. A
test fails the build if the guess script contains a network call, mirroring the
naming game's rule.

## Build integration

- `hall/guess.py`: load and validate the data (at least 60 levels, all fields present,
  ordinals valid, schedule long enough), build the page markup and the JSON blob.
- `templates/guess.html`, `templates/games.html`.
- `src/js/guess.js`, `src/css/guess.css`.
- `build.py`: `build_guess()`, `build_games()`; the hub and game pages are added to
  the sitemap/nav the same way `/game/` is. Asset hashing, relative URLs and the
  `data/site.json` copy (title, lede) follow the existing pattern.
- `data/site.json` gains a `guess` block (title, lede) like `game`.

## Testing

- **Python (`tests/test_guess.py`)**: data validity (count, field presence and types,
  version in the scale, year in range, seconds positive, no duplicate ids or names,
  every `levelId` in the schedule is in the pool); schedule (past days immutable,
  no repeats within a cycle, covers the lookahead); build (page and hub exist; nav
  tab is Games and current on both game pages; `/game/` still builds); the guess
  script has no network call; privacy page mentions the storage key.
- **Browser check page (`tests/guess.check.html`)**: loads the real script's
  `judge`/`pick`/`storage` functions and asserts: each stat's exact/close/miss and
  arrow at the boundaries (10 and 11 ranks, 30 and 31 seconds, creator band for
  answers of 1, 10 and 25), version adjacency including 1.9PS, daily day rollover and
  streak reset, no-repeat Infinite, refused duplicate guess, and share text. It is
  run through `python3 -m http.server` as the Worker check is.
- **Accessibility test** (existing `test_a11y.py`) scans the new pages.
- Verification in a browser at desktop and 390px: board fits, the combobox works by
  keyboard and touch, reduced motion, dark and light ground.

## Risks and open points

- **Length source.** Pointercrate's lengths and the wikis' differ (see Data). The game
  uses Pointercrate's so every level has one consistent, checkable number.
- **Verification year ambiguity** for hack-verified or re-verified levels; handled
  by the rule above plus hand checks, with the cases listed in the data.
- **List drift.** Ranks move weekly. The snapshot date is shown and refreshes never
  change past daily answers.
- **Pointercrate / AREDL terms.** Both publish public APIs; this reuses names and
  numeric facts and credits both on the page, as the naming game does for AREDL.
