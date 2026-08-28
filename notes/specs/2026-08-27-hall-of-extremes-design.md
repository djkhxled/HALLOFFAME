# Baylor's Hall of Extremes — Design Spec

**Date:** 2026-08-27
**Status:** Approved, pending implementation plan

## Overview

A personal, scroll-driven website presenting Baylor's 25 favourite Geometry Dash
extreme demons of all time. Each level gets its own page, themed to that level's
own visual identity. The landing page is itself a scroll experience: a countdown
from rank 25 to rank 1.

The tone follows a cinematic documentary reference — near-black field, one
enormous display word, hairline rules, small letterspaced monospace metadata
pinned to the corners, scroll acting as the timeline.

### Goals

- 26 pages: one landing countdown, 25 level pages.
- Ranks 1–10 feel hand-built. Ranks 11–25 feel consistent and intentional.
- Every factual claim about a level is researched and sourced, never invented.
- Baylor's own commentary is the emotional centre of each level page.
- Ships as static files on GitHub Pages with no CI and no runtime dependencies.

### Non-goals

- Not a difficulty ranking and not a competitor to Pointercrate or AREDL. This is
  a personal favourites list and the site says so plainly.
- No user accounts, comments, database, or backend of any kind.
- No AI-generated raster imagery. Art is procedural SVG/CSS/Canvas, authored by
  hand. (No image-generation API is configured, and vector art suits the subject
  better regardless.)
- No build-time package dependencies. Python standard library only.

## Constraints

- **Node.js and npm are not installed** on the target machine. This rules out
  React, Vite, Astro, and any npm-based toolchain.
- Python 3.14.7 is available, standard library only (no jinja2 installed).
- `gh` CLI is authenticated as `djkhxled`.
- Repo: `hall-of-extremes`, **private initially**. GitHub Pages on a private repo
  requires a paid plan, so the live deploy waits until Baylor makes it public.

## The 25 levels

Ordering is Baylor's personal ranking. Creator strings below are as supplied and
**must be verified during the content pass** — the source list already contains
at least one confirmed error and one suspected one.

| # | Level | Creator (as supplied) | Tier |
|---|---|---|---|
| 1 | Deimos | ItsHybrid and more | bespoke |
| 2 | Nhelv | SirGuillester and more | bespoke |
| 3 | The Yandere | Dorami and more | bespoke |
| 4 | Cold Sweat | Para and more | bespoke |
| 5 | Acheron | Riot & Ryamu and more | bespoke |
| 6 | Tidal Wave | OniLink | bespoke |
| 7 | Solar Flare | Linear, Swiborg, Rynoxious | bespoke |
| 8 | Slaughterhouse | icedcave and more | bespoke |
| 9 | Kyouki | Demishio | bespoke |
| 10 | Titan Complex | TCTeam | bespoke |
| 11 | Freedom08 | Pennutoh and more | themed |
| 12 | Idols | Zafkiel7 and more | themed |
| 13 | Subsonic | Viprin and more | themed |
| 14 | Codependence | TCTeam | themed |
| 15 | Zodiac | BIANOX and more | themed |
| 16 | Bloodlust | Manix and more | themed |
| 17 | Black Blizzard | KrmaL | themed |
| 18 | Maniacial Chains | LordDivinity | themed |
| 19 | Antarctic Lights | Declan, SkyJax, Tolstyh, Arcturus | themed |
| 20 | Firework | cherryteam | themed |
| 21 | Andromeda | Insxne | themed |
| 22 | The Golden | BoBoBoBoBoBoBo and more | themed |
| 23 | Ocular Miracle | Davphla and more | themed |
| 24 | Killbot | Lithifusion | themed |
| 25 | Edge of Destiny | CDMusic and more | themed |

### Known corrections to apply

- **Nhelv** — creator is **SrGuillester** (not "SirGuillester"), a collaboration
  with notlsa and DienID, verified and published by SrGuillester on 2021-04-14.
  Its decoration is modelled on the official music video for Silentroom's
  "Nhelv".
- **Deimos** — hosted and published by ItsHybrid but **verified by Doggie** on
  2023-08-05. Sequel to *Phobos*. A separate, unrelated *Deimos* by EndLevel
  exists; the page must disambiguate.
- **Acheron** — hosted by **ryamu**, co-hosted by **Riot**; verified by Zoink on
  2022-08-23 after 72,808 attempts. 47,984 objects, 1m07s, song "Thermodynamix"
  by dj-Nate, level ID 73667628. Middle entry of Riot's hell-themed Top 1
  trilogy.
- **Tidal Wave** — by OniLink, verified by Zoink on 2023-09-09 after
  approximately 49,534 attempts; reached #1 on 2024-02-18.
- **"Maniacial Chains"** — suspected misspelling of *Maniacal Chains*. Verify
  before publishing.

## Architecture

A dependency-free Python generator turns per-level JSON into static HTML.

```
hall-of-extremes/
├── build.py                  # stdlib-only generator
├── data/
│   ├── site.json             # title, nav, global credits, disclaimer
│   └── levels/
│       ├── 01-deimos.json
│       └── … 25 files, one per level
├── templates/
│   ├── base.html             # document shell: head, nav, footer
│   ├── index.html            # landing countdown
│   └── level.html            # level page skeleton
├── src/
│   ├── css/
│   │   ├── tokens.css        # design tokens
│   │   ├── base.css          # reset, typography, layout primitives
│   │   ├── components.css    # statblock, countdown, player, nav
│   │   └── levels/<slug>.css # per-level theme overrides
│   ├── js/
│   │   ├── scroll.js         # GSAP ScrollTrigger setup + reduced-motion guard
│   │   ├── audio.js          # opt-in song player
│   │   └── media.js          # click-to-load video embeds
│   └── art/<slug>.svg        # procedural art, authored per level
├── bespoke/<slug>.html       # custom scroll set-piece fragments (ranks 1–10)
├── notes/specs/              # design specs — NOT published
└── docs/                     # BUILD OUTPUT — served by GitHub Pages
    ├── index.html
    ├── assets/
    └── levels/<slug>/index.html
```

### Why `docs/` as the output directory

GitHub Pages serves `/docs` from `main` with no Actions workflow and no
`gh-pages` branch. Source and built output are committed together. This keeps
deployment to a single `git push` once the repo is public.

**`docs/` is therefore the publish root and contains build output only.**
Anything placed under it becomes a public URL once the repo goes public. Design
specs and working notes live in `notes/`, deliberately outside the publish root.
`build.py` owns `docs/` entirely and may clear it before writing.

### Templating approach

Templates are plain HTML files containing `{{ slot_name }}` tokens. `build.py`
composes every repeated structure (countdown entries, stat rows, nav) in Python
and substitutes the result. **Templates contain no logic** — no loops, no
conditionals. This keeps the generator predictable and avoids a template-engine
dependency.

### URL structure

- Landing: `/`
- Level: `/levels/<slug>/`

Clean directory-index URLs, so links are shareable and stable.

## Data model

One JSON file per level. Three clearly separated halves.

```json
{
  "rank": 2,
  "slug": "nhelv",
  "name": "Nhelv",
  "tagline": "One line, shown in the countdown.",

  "facts": {
    "creators": ["SrGuillester", "notlsa", "DienID"],
    "host": "SrGuillester",
    "verifier": "SrGuillester",
    "verifiedDate": "2021-04-14",
    "ratedDate": null,
    "attempts": null,
    "levelId": null,
    "objects": null,
    "length": null,
    "gdVersion": "2.1",
    "song": { "name": "Nhelv", "artist": "Silentroom", "newgroundsId": null },
    "peakRank": null,
    "currentRank": null,
    "sources": ["https://geometrydash.wiki.gg/wiki/Nhelv"]
  },

  "theme": {
    "tier": "bespoke",
    "palette": {
      "field": "#05060a",
      "ink": "#f4f4f5",
      "muted": "#8a8a93",
      "accent": "#8b5cf6",
      "accent2": "#22d3ee"
    },
    "texture": "scanline",
    "signature": "glitch-assemble",
    "displayFont": null,
    "mood": "Short prose note describing the intended feel."
  },

  "voice": {
    "hook": "A pull quote, one sentence.",
    "why": "<p>Baylor's commentary.</p>",
    "draftedByClaude": true
  },

  "media": {
    "video": { "youtubeId": null, "title": null, "channel": null },
    "art": "src/art/nhelv.svg",
    "images": []
  }
}
```

### Rules governing the data

1. **Unknown facts are `null`, never guessed.** The template renders `null` as
   an em dash. A missing object count is honest; a fabricated one is not.
2. **`facts.sources[]` is required and non-empty** for every level. Each level
   page renders its sources in the footer. These are claims about real people's
   records, so they must be traceable.
3. **`voice.draftedByClaude`** starts `true`. Pages render a small, quiet marker
   on drafted commentary, and `build.py` reports `voice: N/25 in your words`.
   Baylor sets the flag to `false` when he rewrites a section, and the marker
   disappears. This makes the draft-then-rewrite workflow visible rather than
   forgotten.
4. **`theme.tier`** is `bespoke` (ranks 1–10) or `themed` (ranks 11–25). Only
   `bespoke` levels may have a `bespoke/<slug>.html` fragment or a
   `src/css/levels/<slug>.css` file.
5. **Art differs by tier.** `bespoke` levels have hand-authored
   `src/art/<slug>.svg`, and `media.art` points at it. `themed` levels set
   `media.art` to `null` and instead receive art from a shared parametric
   generator driven by their `palette` and `texture` — no per-level art files.
   The build rejects a `themed` level that names an art file.

## Design system

### Type

- **Display** — a heavy grotesque, very tight tracking, set at extreme sizes.
  Carries the level name and the site title.
- **Mono** — small, wide letterspacing, uppercase. Metadata, labels, rank
  numbers, stat block.
- **Body** — a readable grotesque at a comfortable measure for the commentary.

Fonts come from Google Fonts. Exact faces are selected during M1 using the
`frontend-design` skill rather than being fixed here.

### Tokens

`tokens.css` defines the shared skeleton: spacing scale, type scale, rule
weights, section rhythm, transition durations. **These never vary per level.**

Per-level CSS overrides only the theme surface: `--field`, `--ink`, `--muted`,
`--accent`, `--accent2`, and the texture layer. Each page carries
`data-level="<slug>"` on `<html>`, so a level's stylesheet is scoped and cannot
leak.

### Textures

A fixed library of background treatments, implemented in CSS/SVG:
`starfield`, `scanline`, `grain`, `caustics`, `ember`, `snow`, `chrome`, `none`.

## Page structures

### Landing — scroll countdown 25 → 1

1. **Hero** — "BAYLOR'S HALL OF EXTREMES" as enormous display type over
   procedural art, with a short statement of what the list is (personal
   favourites, explicitly not a difficulty ranking).
2. **Countdown** — a pinned section. As the user scrolls, the rank number
   descends 25 → 1. Each level announces itself with name, creator, and its
   `tagline`, while the page ground transitions to that level's palette. Each
   entry links to its page.
3. **Finale** — rank 1 is given the most weight and hold time.
4. **Colophon** — credits, sources, disclaimer.

**Fallback:** without JavaScript or under `prefers-reduced-motion`, the countdown
renders as a plain, complete ranked list of 25 links. All content is present in
the HTML; scroll behaviour is an enhancement layer only.

### Level page

1. **Hero** — level name as huge display type; rank badge; creator, verifier, and
   year set small in the corners.
2. **Signature set-piece** — the level's scroll moment. Hand-built for ranks
   1–10; drawn from the signature library for 11–25.
3. **Stat block** — the researched facts in a monospace grid.
4. **"Why it's here"** — Baylor's commentary. The emotional centre of the page.
5. **Video** — click-to-load embed. No third-party iframe is inserted until the
   user activates it.
6. **Song** — opt-in player. Never autoplays. Song and artist credited.
7. **Rank navigation** — previous and next by rank.
8. **Sources** — footnoted citations for the facts on the page.

## Theme engine

Each level declares one `signature`, a named scroll behaviour. The library:

| Signature | Behaviour | Example fit |
|---|---|---|
| `orbit` | Layered celestial parallax drift | Deimos, Andromeda |
| `glitch-assemble` | Headline assembles from displaced slices | Nhelv |
| `descend` | Continuous downward camera; content rises past the viewport | Acheron |
| `surge` | Horizontal pan scrubbed by scroll | Tidal Wave |
| `ignite` | Exposure and bloom ramp up | Solar Flare |
| `pulse` | Beat-locked scale and opacity throb | Kyouki |
| `fracture` | Content shatters and reforms between sections | Titan Complex |
| `flood` | A colour mask rises to fill the viewport | Cold Sweat |
| `static` | Reveals only — no pinning or scrubbing | reduced-motion default |

Ranks 1–10 additionally get bespoke art and a custom set-piece fragment. Ranks
11–25 compose palette + texture + signature only, with no custom code.

Under `prefers-reduced-motion`, **every** signature degrades to `static`.

### Motion library

GSAP with ScrollTrigger, loaded from CDN, for pinning and scrubbing. `scroll.js`
must:

- Check `prefers-reduced-motion` **before** registering any ScrollTrigger, and
  skip registration entirely if set.
- Function correctly if the CDN fails: pages remain fully readable, since content
  is server-rendered and animation only adds transforms.

## Accessibility

- `prefers-reduced-motion: reduce` disables all pinning, scrubbing, and parallax.
  The site becomes a clean static document. This is a hard requirement.
- All content is present in the generated HTML. Nothing meaningful is injected by
  JavaScript.
- Neon-on-dark palettes fail contrast easily. **`build.py` computes WCAG contrast
  ratios for body and muted text against each level's field colour and fails the
  build below 4.5:1 for body text and 3:1 for large display text.** Accent
  colours used decoratively are exempt.
- The countdown and the audio player are keyboard operable, with visible focus.
- Video and audio controls are labelled; no autoplay anywhere.

## Build validation

`build.py` fails loudly on any of the following:

- Duplicate `rank` or duplicate `slug`.
- Ranks that are not exactly 1–25 with no gaps.
- Missing required fields: `rank`, `slug`, `name`, `tagline`, `theme.tier`,
  `theme.palette`, `theme.signature`.
- Empty or missing `facts.sources`.
- A `signature` not present in the library.
- A referenced art file, image, or per-level CSS file that does not exist.
- A `themed`-tier level that has a bespoke fragment or per-level CSS.
- A palette that fails the contrast floor.

On success it prints a report: pages written, and `voice: N/25 in your words`.

## Testing

- **Build validation** as above, run on every build.
- **Playwright** via the `webapp-testing` skill: load every generated page at
  desktop and mobile widths, assert zero console errors, screenshot each, and
  verify the reduced-motion variant renders the static fallback.
- **Manual visual review** through the browser preview at each milestone.

## Milestones

**M1 — Foundation and proof.** `build.py`, the design system, the landing
countdown, and two fully bespoke level pages: Deimos (1) and Nhelv (2). Deliberately
narrow so Baylor can react to something real before 23 more are built.

**M2 — Bespoke top 10.** Ranks 3–10: research, art, per-level CSS, set-pieces.

**M3 — Themed 11–25.** Research and theme assignment; no custom code.

**M4 — Content, deploy, polish.** Full fact verification with sources for all 25,
Baylor's commentary rewrites, accessibility audit, Playwright pass, and public
deploy.

**The implementation plan that follows this spec covers M1 only.** M2–M4 are
scoped here for direction but each gets its own plan, written after the preceding
milestone is reviewed. M1 exists specifically to test the design against reality
before the expensive tiers are built.

## Attribution and content ethics

- The site states plainly that it is a personal favourites list by a fan, is
  unaffiliated with RobTop Games, and is not a difficulty ranking.
- Every level credits its creators, host, and verifier. Every song credits its
  artist.
- Facts carry sources. Unverified facts are omitted, not guessed.
- Any third-party imagery added later requires Baylor's explicit approval of the
  specific files and their sources before it enters the repo, and is credited on
  the page where it appears.

## Open questions

None blocking. Two items to confirm during implementation:

1. Whether the top-10 ordering is final before bespoke work begins on M2 (it is
   the most expensive tier to reorder later).
2. When to flip the repo public, which is what enables the GitHub Pages deploy.
