"""The name-every-demon game: snapshot loading, answer keys, and markup.

The interesting decision lives here rather than in the browser. There is no
Node on this project, so nothing in game.js can be unit-tested; what can be
tested is Python. So everything that decides WHAT COUNTS AS A CORRECT ANSWER
is computed at build time into a table the browser only has to look things up
in. The script's one remaining job of that kind is normalising what the
player typed, and it is five lines that must match norm() below exactly.

Why the rules are not just "the name":

AREDL disambiguates levels that share a name by appending the creator --
"Deimos (ItsHybrid)" and "Deimos (EndLevel)" are two different levels that
are both called Deimos. There are 46 such names covering 93 levels, and
FIREPOWER alone is three. A player types "Deimos"; nobody types the
parenthetical. So the answer to a level is its name WITHOUT the suffix, and a
name shared by several levels fills them one at a time in rank order, as
typing it again should. The full form, "Deimos (EndLevel)", is also accepted
and aims at exactly that one.
"""

import html
import json
import pathlib
import re
import unicodedata

CHUNK = 100                       # rows per block of the list
SUFFIX = re.compile(r"^(.*?)\s*\(([^()]*)\)\s*$")
LEADING_THE = re.compile(r"^the\s+", re.I)


def norm(text: str) -> str:
    """Fold a typed or stored name down to lowercase a-z and 0-9.

    Case, accents, spacing and punctuation never decide whether an answer is
    right. game.js repeats this exactly:
      s.normalize("NFKD").replace(/[\\u0300-\\u036f]/g, "")
       .toLowerCase().replace(/[^a-z0-9]/g, "")
    """
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", text.lower())


def split_name(name: str) -> tuple[str, str | None]:
    """'Deimos (EndLevel)' -> ('Deimos', 'EndLevel'); no suffix -> (name, None)."""
    m = SUFFIX.match(name)
    if not m or not m.group(1).strip():
        return name, None
    return m.group(1).strip(), m.group(2).strip()


def load_snapshot(path: pathlib.Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    levels = [
        {"p": p, "name": name, "id": lid, "legacy": bool(legacy)}
        for p, name, lid, legacy in data["levels"]
    ]
    data["levels"] = levels
    return data


def validate(levels: list[dict]) -> list[str]:
    """Problems that would make the game unwinnable or unfair."""
    errors = []
    if not levels:
        return ["the snapshot has no levels"]
    seen_p, seen_id = set(), set()
    for lv in levels:
        if lv["p"] in seen_p:
            errors.append(f"position {lv['p']} appears twice")
        seen_p.add(lv["p"])
        if lv["id"] in seen_id:
            errors.append(f"id {lv['id']} appears twice; progress is saved by it")
        seen_id.add(lv["id"])
        if not norm(lv["name"]):
            errors.append(f"#{lv['p']} {lv['name']!r} has nothing typeable in it "
                          "and could never be named")
    return errors


def _forms(name: str) -> tuple[set[str], set[str]]:
    """(plain, full) answer keys for one level.

    plain: the name as a person says it -- without the creator, and with or
    without a leading "The". full: the AREDL name, creator included, which is
    only ever typed to aim at one of several levels that share a name.
    """
    base, suffix = split_name(name)
    plain = {base}
    dropped = LEADING_THE.sub("", base)
    if dropped and dropped != base:
        plain.add(dropped)
    full = {name} if suffix else set()
    if suffix:
        d = LEADING_THE.sub("", name)
        if d and d != name:
            full.add(d)
    return ({norm(f) for f in plain if norm(f)},
            {norm(f) for f in full if norm(f)})


def build_index(levels: list[dict]) -> tuple[dict[str, list[int]], set[str]]:
    """(answer key -> indices, the keys that are plain names).

    A key that several levels share lists them all, lowest position first;
    the browser fills the first one not yet named.
    """
    index: dict[str, list[int]] = {}
    plain_keys: set[str] = set()
    for i, lv in enumerate(levels):
        plain, full = _forms(lv["name"])
        plain_keys |= plain
        for key in plain | full:
            bucket = index.setdefault(key, [])
            if i not in bucket:
                bucket.append(i)
    for bucket in index.values():
        bucket.sort(key=lambda i: levels[i]["p"])
    return index, plain_keys


def build_hold(levels: list[dict], index: dict[str, list[int]],
               plain_keys: set[str]) -> dict[str, list[int]]:
    """answer key -> the longer levels it could still turn out to be the
    start of.

    "Aurora" is also the first six letters of "Aurorae". Accepting on an exact
    match the way Sporcle does would clear the box before the "e" could be
    typed, so a key listed here waits for a pause or for Enter -- but only
    while one of these levels is still unnamed. Once Aurorae is named, Aurora
    has nothing left to be confused with and is taken at once.

    Only plain names are considered on the longer side. Counting the
    creator-suffixed forms would make every shared name wait: "deimos" is
    the start of "deimositshybrid", and nobody types that by accident.
    """
    hold: dict[str, list[int]] = {}
    longer = sorted(plain_keys)
    for key in index:
        rivals = sorted({
            i for other in longer
            if other != key and other.startswith(key)
            for i in index[other]
            if norm(split_name(levels[i]["name"])[0]) == other
            or other in _forms(levels[i]["name"])[0]
        })
        if rivals:
            hold[key] = rivals
    return hold


def blocks(levels: list[dict]) -> list[tuple[str, list[int]]]:
    """(title, indices) for each block of the list.

    The main list goes in hundreds; AREDL's legacy levels are their own block,
    since that is the distinction AREDL itself draws.
    """
    main = [i for i, lv in enumerate(levels) if not lv["legacy"]]
    legacy = [i for i, lv in enumerate(levels) if lv["legacy"]]
    out = []
    for start in range(0, len(main), CHUNK):
        chunk = main[start:start + CHUNK]
        out.append((f"#{levels[chunk[0]]['p']} – #{levels[chunk[-1]]['p']}",
                    chunk))
    if legacy:
        out.append((f"Legacy · #{levels[legacy[0]]['p']} – "
                    f"#{levels[legacy[-1]]['p']}", legacy))
    return out


def list_html(levels: list[dict]) -> str:
    """Every slot, empty. Names are not in the markup: they arrive from the
    data only when a level is named, so the page is not a wall of spoilers to
    a screen reader or to select-all.

    Unnamed slots are aria-hidden. A list of 1,621 "not yet named" is noise
    to anyone listening to it, and the live region already reports progress.
    """
    parts = []
    for n, (title, idxs) in enumerate(blocks(levels), 1):
        rows = "".join(
            f'<li class="slot" data-i="{i}" aria-hidden="true">'
            f'<span class="slot__rank">{levels[i]["p"]:04d}</span>'
            f'<span class="slot__name"></span></li>'
            for i in idxs
        )
        parts.append(
            f'<section class="gblock" data-block aria-labelledby="gb-{n}">'
            f'<h2 id="gb-{n}" class="gblock__title">'
            f'<span class="gblock__range">{html.escape(title)}</span>'
            f'<span class="gblock__count" data-count>0 / {len(idxs)}</span></h2>'
            f'<ol class="gblock__rows">{rows}</ol></section>'
        )
    return "".join(parts)


def data_json(levels: list[dict], index: dict, hold: dict,
              fetched: str) -> str:
    """The page's data, safe to sit inside a <script type=application/json>.

    A single-entry bucket is written as a bare number; most are.
    """
    keys = {k: (v[0] if len(v) == 1 else v) for k, v in sorted(index.items())}
    payload = {
        "fetched": fetched,
        "levels": [[lv["p"], lv["id"], lv["name"], 1 if lv["legacy"] else 0]
                   for lv in levels],
        "keys": keys,
        "hold": dict(sorted(hold.items())),
    }
    text = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
    # "</script" and "<!--" are the two things that can end the element early.
    return text.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
