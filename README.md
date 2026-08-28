# Baylor's Hall of Extremes

My twenty-five favourite Geometry Dash extreme demons of all time, one page each.

This is a **personal list**. It is not a difficulty ranking and it is not trying
to be Pointercrate or AREDL. Every level is here for its own reason.

A fan project, unaffiliated with RobTop Games. All levels and songs belong to
their creators, who are credited on every page.

## Status

Milestone 1. The build system, the design system, the 25 → 1 scroll countdown,
and two fully bespoke level pages are done.

| | |
|---|---|
| Levels in the countdown | 25 |
| Full pages built | 2 — Deimos (#1), Nhelv (#2) |
| Commentary in Baylor's own words | 0 / 25 |

## Build

No dependencies. Python 3.11+ and nothing else — no Node, no npm, no pip install.

```bash
python3 build.py
```

That writes the whole site into `docs/`. Preview it with:

```bash
python3 -m http.server 3003 --directory docs
```

Run the tests with:

```bash
python3 -m unittest discover -s tests -t .
```

## Layout

```
build.py            generator entry point
hall/               contrast maths, data validation, rendering
data/site.json      site-level copy
data/levels/*.json  one record per level — the only place content lives
templates/          logic-free {{ slot }} HTML templates
src/css/            tokens, base, components, and per-level themes
src/js/             scroll signatures and click-to-load media
src/art/            hand-authored SVG for bespoke levels
bespoke/            custom scroll set-pieces for bespoke levels
notes/              specs and plans — deliberately NOT published
docs/               BUILD OUTPUT — do not edit by hand
```

`docs/` is the GitHub Pages publish root, so anything placed inside it becomes a
public URL. Working notes live in `notes/` for that reason. `build.py` owns
`docs/` and clears it on every run.

## Writing your own commentary

Each level's "Why it's here" section lives in its JSON file under `voice`:

```json
"voice": {
  "hook": "One line, shown large.",
  "why": "<p>Your take on the level.</p>",
  "draftedByClaude": true
}
```

Rewrite `why` in your own words, then set `draftedByClaude` to `false`. The
"drafted placeholder" marker disappears from the page, and the build's
`voice: N/25 in your words` counter goes up.

## Ground rules for content

1. **No invented facts.** Anything unconfirmed stays `null` in the JSON and
   renders as an em dash. These are real people's records.
2. **Every published level cites its sources** in `facts.sources`, shown in the
   page footer.
3. **Creators, hosts, verifiers, and song artists are always credited.**

## Accessibility

- `prefers-reduced-motion` disables every pinned, scrubbed, and parallaxed
  effect; the site becomes a plain static document.
- All content is server-rendered, so the site works with JavaScript disabled or
  the GSAP CDN blocked.
- The build **fails** if any level's body text falls below 4.5:1 contrast
  against its background.
- Nothing loads from YouTube until you press play.
