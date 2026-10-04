"""GeometryGuessr: the data the page is built from.

data/gg/levels.json   every level the search box offers (the 100 most downloaded demons)
data/gg/shots.json    one entry per screenshot: which level, where in it (percent), file

Both are written by tools/prepare_shots.py from the GG Capture mod's output. A level
with no screenshot is still searchable (a decoy), so the list of names never gives the
answer pool away. Nothing here is fetched by a visitor's browser: it is embedded in
the page at build time.
"""
import json
import pathlib

MIN_POOL = 5          # levels with at least one shot; fewer and the game is too small
PCT_RANGE = (3, 97)   # none from the very start or end of a level


def load(levels_path: pathlib.Path, shots_path: pathlib.Path):
    snap = json.loads(levels_path.read_text(encoding="utf-8"))
    shots = json.loads(shots_path.read_text(encoding="utf-8"))["shots"]
    return snap, shots


def validate(levels: list, shots: list, shots_dir: pathlib.Path) -> list:
    errors = []
    ids = [lv["id"] for lv in levels]
    slugs = [lv["slug"] for lv in levels]
    if len(set(ids)) != len(ids):
        errors.append("levels.json has a duplicate level id")
    if len(set(slugs)) != len(slugs):
        errors.append("levels.json has a duplicate slug")
    known = set(ids)
    seen = set()
    for s in shots:
        where = f"shot {s.get('file')}"
        if s["level"] not in known:
            errors.append(f"{where}: level {s['level']} is not in levels.json")
        if not (PCT_RANGE[0] <= s["pct"] <= PCT_RANGE[1]):
            errors.append(f"{where}: percent {s['pct']} is outside {PCT_RANGE[0]}-{PCT_RANGE[1]}")
        if not (shots_dir / s["file"]).is_file():
            errors.append(f"{where}: no such file under src/shots")
        key = (s["level"], s["pct"])
        if key in seen:
            errors.append(f"{where}: a second shot of the same level at the same percent")
        seen.add(key)
    pool = {s["level"] for s in shots}
    if len(pool) < MIN_POOL:
        errors.append(f"only {len(pool)} levels have screenshots; the game needs {MIN_POOL}")
    return errors


def data_json(levels: list, shots: list, fetched: str) -> str:
    """The page's data, short keys: levels n(ame) c(reator) d(ownloads) and
    shots l(evel) p(ercent) f(ile). Safe inside a <script> element."""
    data = {
        "fetched": fetched,
        "levels": [{"id": lv["id"], "n": lv["name"], "c": lv["creator"], "d": lv["downloads"]}
                   for lv in levels],
        "shots": [{"l": s["level"], "p": s["pct"], "f": s["file"]} for s in shots],
    }
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


# --- The score board (only when the records service is switched on) ---------------

def board_title_html() -> str:
    """On the title screen: a button to look at the board, and where it appears."""
    return (
        '<div class="gg-lead">'
        '<button class="gg-btn gg-lead__btn" type="button" data-rec-show>Show the board</button>'
        '<div class="gg-lead__box" data-rec-board aria-live="polite"></div></div>'
    )


def records_html(dm: str) -> str:
    """After a game: put a username and the score on the board. `dm` is the removal
    route, worded once in render.dm_html."""
    return (
        '<section class="gg-rec" data-rec hidden aria-labelledby="gg-rec-h">'
        '<h3 id="gg-rec-h" class="gg-rec__title">Put your score on the board</h3>'
        '<form class="gg-rec__form" data-rec-form autocomplete="off">'
        '<label class="visually-hidden" for="gg-rec-name">Username</label>'
        '<input id="gg-rec-name" class="gg-input gg-rec__name" data-rec-name type="text" maxlength="20" '
        'autocapitalize="off" autocorrect="off" spellcheck="false" placeholder="Your username">'
        '<button class="gg-btn gg-btn--go" type="button" data-rec-submit>Submit score</button>'
        '<button class="gg-btn" type="button" data-rec-show>Show the board</button></form>'
        f'<p class="gg-rec__note">Your username and score will be public. Use a username, not your '
        f'real name. To have it removed, {dm}. <a href="/privacy/">What gets sent</a>.</p>'
        '<p class="gg-rec__status" data-rec-status role="status"></p>'
        '<div class="gg-rec__board" data-rec-board aria-live="polite"></div></section>'
    )
