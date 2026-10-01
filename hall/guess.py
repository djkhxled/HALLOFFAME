"""Guess the Demon: the data side.

Everything that decides a stat is decided here, at build time, so the browser
only compares numbers. The page's script (src/js/guess-core.js) reads the JSON
produced by data_json() and must agree with VERSIONS below.
"""
import datetime
import json
import pathlib
import random
import re

VERSIONS = ["1.8", "1.9PS", "2.0", "2.1", "2.2"]
YEAR_MIN, YEAR_MAX = 2013, datetime.date.today().year + 1
SECONDS_MIN, SECONDS_MAX = 15, 1200


def version_from_tags(tags) -> str:
    found = [t for t in tags if t in VERSIONS]
    if len(found) != 1:
        raise ValueError(f"expected exactly one version tag, found {found or 'none'} in {list(tags)}")
    return found[0]


def verification_year(verifications) -> int:
    dated = sorted(v["achieved_at"] for v in verifications if v.get("achieved_at"))
    if not dated:
        raise ValueError("no dated verification")
    return int(dated[0][:4])


def dedupe_names(names) -> list:
    seen, out = set(), []
    for n in names:
        n = str(n).strip()
        if n and n.lower() not in seen:
            seen.add(n.lower())
            out.append(n)
    return out


def parse_length(text: str) -> int:
    m = re.search(r"(\d+)\s*m\s*(\d+)\s*s", text)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))
    m = re.search(r"\b(\d+)\s*s\b", text)
    if m:
        return int(m.group(1))
    raise ValueError(f"cannot read a length from {text!r}")


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def validate(levels) -> list:
    errors = []
    if not levels:
        return ["no levels"]
    ids, names, ranks = set(), set(), set()
    for lv in levels:
        who = f"{lv.get('name')!r} ({lv.get('id')})"
        if lv["id"] in ids:
            errors.append(f"duplicate id: {who}")
        ids.add(lv["id"])
        if _norm(lv["name"]) in names:
            errors.append(f"duplicate name: {who}")
        names.add(_norm(lv["name"]))
        if lv["rank"] in ranks:
            errors.append(f"duplicate rank {lv['rank']}: {who}")
        ranks.add(lv["rank"])
        if lv["version"] not in VERSIONS:
            errors.append(f"bad version {lv['version']!r}: {who}")
        if not YEAR_MIN <= lv["year"] <= YEAR_MAX:
            errors.append(f"year {lv['year']} out of range: {who}")
        if not SECONDS_MIN <= lv["seconds"] <= SECONDS_MAX:
            errors.append(f"seconds {lv['seconds']} out of range: {who}")
        if lv["creators"] < 1 or lv["creators"] != len(lv["creatorNames"]):
            errors.append(f"creator count does not match names: {who}")
    return errors


def make_schedule(pool_ids, launch: datetime.date, seed: int, days: int) -> list:
    """days entries starting on launch; a seeded shuffle per cycle, and no
    level repeated back to back across a cycle boundary."""
    rng = random.Random(seed)
    ids = sorted(pool_ids)
    order = []
    while len(order) < days:
        cycle = ids[:]
        rng.shuffle(cycle)
        if order and len(cycle) > 1 and cycle[0] == order[-1]:
            cycle[0], cycle[1] = cycle[1], cycle[0]
        order.extend(cycle)
    return [{"date": (launch + datetime.timedelta(days=i)).isoformat(), "levelId": lid}
            for i, lid in enumerate(order[:days])]


def extend_schedule(schedule: dict, pool_ids, today: datetime.date, lookahead: int = 1100) -> dict:
    """Keep every day up to and including today; re-draw the days after it."""
    launch = datetime.date.fromisoformat(schedule["launch"])
    past = [d for d in schedule.get("days", []) if d["date"] <= today.isoformat()]
    want = max(0, (today - launch).days + 1) + lookahead if today >= launch else lookahead + (launch - today).days
    total = max(want, len(past))
    seed = schedule["seed"] + len(past)
    fresh = make_schedule(pool_ids, launch + datetime.timedelta(days=len(past)), seed, total - len(past))
    if past and fresh and fresh[0]["levelId"] == past[-1]["levelId"] and len(fresh) > 1:
        fresh[0]["levelId"], fresh[1]["levelId"] = fresh[1]["levelId"], fresh[0]["levelId"]
    return {"launch": schedule["launch"], "seed": schedule["seed"], "days": past + fresh}


def day_number(launch_iso: str, today_iso: str) -> int:
    a = datetime.date.fromisoformat(launch_iso)
    b = datetime.date.fromisoformat(today_iso)
    return (b - a).days + 1


def load_snapshot(path) -> dict:
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def load_schedule(path) -> dict:
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def data_json(levels, schedule: dict, fetched: str, hall: dict) -> str:
    """The page's data as compact JSON, safe inside a <script> element."""
    payload = {
        "fetched": fetched,
        "launch": schedule["launch"],
        "sched": [d["levelId"] for d in schedule["days"]],
        "hall": {str(k): v for k, v in hall.items()},
        "levels": [
            {"id": lv["id"], "n": lv["name"], "r": lv["rank"], "y": lv["year"],
             "v": lv["version"], "s": lv["seconds"], "c": lv["creators"],
             "cn": lv["creatorNames"]}
            for lv in sorted(levels, key=lambda x: x["rank"])
        ],
    }
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
