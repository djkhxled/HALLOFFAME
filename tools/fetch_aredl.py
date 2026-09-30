#!/usr/bin/env python3
"""Snapshot the AREDL level list for the game.

The game names every extreme demon on AREDL (aredl.net), which is the
community list of extreme demons. The site promises that loading a page makes
no request to anyone but this host, so the list is fetched here, once, by the
person building the site, and committed -- never by a visitor's browser.

Only what the game uses is kept: position, name, whether the level is on the
legacy list, and a short id. AREDL's own id is a 36-character UUID, which is
a lot to store 1,621 times in someone's localStorage, so the first eight hex
digits stand in for it; the tool refuses to write a snapshot in which those
collide. GD's own level_id is not usable for this -- 18 of them are shared by
more than one AREDL entry.

Positions move every time a level is placed or lifted, which is why progress
is saved against the id and not the position.

Usage: python3 tools/fetch_aredl.py
Writes: data/game/aredl.json
"""

import datetime
import json
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "game" / "aredl.json"
URL = "https://api.aredl.net/v2/api/aredl/levels"
UA = "hall-of-extremes-snapshot (+https://www.b4ylor.com)"


def fetch() -> list[dict]:
    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def short_ids(levels: list[dict]) -> dict[str, str]:
    """The shortest prefix length that keeps every id unique, from eight up."""
    for width in range(8, 37):
        ids = {lv["id"]: lv["id"].replace("-", "")[:width] for lv in levels}
        if len(set(ids.values())) == len(ids):
            return ids
    raise SystemExit("AREDL ids are not unique even in full")


def main():
    raw = fetch()
    if len(raw) < 1000:
        raise SystemExit(f"only {len(raw)} levels came back; refusing to overwrite")

    ids = short_ids(raw)
    rows = []
    for lv in sorted(raw, key=lambda x: x["position"]):
        rows.append([lv["position"], lv["name"].strip(), ids[lv["id"]],
                     1 if lv.get("status") == "Legacy" else 0])

    positions = [r[0] for r in rows]
    if len(set(positions)) != len(positions):
        raise SystemExit("duplicate positions in the AREDL response")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    # One level per line, so a refresh shows up as a readable diff.
    body = ",\n".join("    " + json.dumps(r, ensure_ascii=False) for r in rows)
    head = json.dumps({
        "source": "https://aredl.net",
        "api": URL,
        "fetched": datetime.date.today().isoformat(),
        "count": len(rows),
    }, indent=2)
    OUT.write_text(head[:-2] + ',\n  "levels": [\n' + body + "\n  ]\n}\n",
                   encoding="utf-8")
    legacy = sum(r[3] for r in rows)
    print(f"{len(rows)} levels ({legacy} legacy), id width "
          f"{len(rows[0][2])} -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
