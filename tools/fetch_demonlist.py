"""Build data/guess/demonlist.json and extend data/guess/schedule.json.

    python3 tools/fetch_demonlist.py [--launch YYYY-MM-DD] [--today YYYY-MM-DD]

Reads Pointercrate (the top 150, creators, and each level's page for its
"Level Length") and AREDL (verifications, version tags). A length is, in order:
data/guess/overrides.json, the Pointercrate level page, then a wiki time from
data/guess/wiki_lengths.json for the rare level whose page shows none. A level
with none of those is held out and listed in pending.json. Anything else it
cannot fully derive stops the run with the level's name.
"""
import argparse
import datetime
import json
import pathlib
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from hall import guess  # noqa: E402

PC = "https://pointercrate.com/api/v2"
AREDL = "https://api.aredl.net/v2/api/aredl/levels"
UA = {"User-Agent": "hall-of-extremes data tool (https://www.b4ylor.com)"}
DATA = ROOT / "data" / "guess"
SEED = 20261001
DEFAULT_LAUNCH = "2026-10-01"
MIN_POOL = 60         # the build refuses a smaller pool


def get(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))


def top150():
    a = get(f"{PC}/demons/listed/?limit=100")
    b = get(f"{PC}/demons/listed/?limit=50&after=100")
    levels = a + b
    if len(levels) != 150 or levels[-1]["position"] != 150:
        raise SystemExit(f"expected Pointercrate's top 150, got {len(levels)}")
    return levels


def pointercrate_length(position, level_id):
    url = f"https://pointercrate.com/demonlist/{position}/"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh) hall-of-extremes data tool"})
    html = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "ignore")
    return guess.parse_pointercrate_length(html, level_id)


def load_json(path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--launch", default=DEFAULT_LAUNCH)
    ap.add_argument("--today", default=datetime.date.today().isoformat())
    args = ap.parse_args()
    today = datetime.date.fromisoformat(args.today)

    overrides = load_json(DATA / "overrides.json", {})
    wiki = load_json(DATA / "wiki_lengths.json", {"lengths": {}})["lengths"]
    aredl = {l["level_id"]: l for l in get(AREDL)}

    levels, problems, pending = [], [], []
    for p in top150():
        name, lid = p["name"], p["level_id"]
        try:
            a = aredl.get(lid)
            if not a:
                raise ValueError("not on AREDL (join by level id failed)")
            detail = get(f"{AREDL}/{a['id']}")
            pc = get(f"{PC}/demons/{p['id']}/")["data"]
            creators = guess.dedupe_names([c["name"] for c in pc["creators"]])
            ov = overrides.get(str(lid), {})

            year = ov.get("year") or guess.verification_year(detail.get("verifications", []))
            version = guess.version_from_tags(a["tags"])

            # A published length only (see the spec): an override, Pointercrate's
            # own page for the level, or a wiki time. Nothing is computed or guessed.
            if "seconds" in ov:
                seconds, source = ov["seconds"], "override"
            else:
                seconds = pointercrate_length(p["position"], lid)
                source = "pointercrate"
                if seconds is None and str(lid) in wiki:
                    seconds, source = wiki[str(lid)]["seconds"], wiki[str(lid)]["source"]
            if seconds is None:
                pending.append({"levelId": lid, "name": name, "rank": p["position"]})
                print(f"  {p['position']:>3} {name}: no published length, held out", file=sys.stderr)
                continue
            peak = min(p["position"],
                       guess.peak_from_movement(get(f"{PC}/demons/{p['id']}/audit/movement/")))
            levels.append({
                "id": lid, "pcId": p["id"], "name": name, "rank": p["position"], "peak": peak,
                "year": year, "version": version, "seconds": seconds,
                "creators": len(creators), "creatorNames": creators, "lengthSource": source,
            })
            print(f"  {p['position']:>3} {name}", file=sys.stderr)
        except Exception as exc:  # noqa: BLE001 - name the level, keep going, fail at the end
            problems.append(f"{p['position']:>3} {name} ({lid}): {exc}")
        time.sleep(0.15)

    if problems:
        print("\nCannot derive:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 1
    errors = guess.validate(levels)
    if len(levels) < MIN_POOL:
        errors.append(f"only {len(levels)} levels have a verified length (need {MIN_POOL})")
    if errors:
        print("\nInvalid:\n  " + "\n  ".join(errors), file=sys.stderr)
        return 1

    snapshot = {
        "fetched": today.isoformat(),
        "source": {"list": "https://pointercrate.com/demonlist/", "verifications": "https://aredl.net",
                   "lengths": "Pointercrate level pages (wiki times only where a page shows none)"},
        "levels": levels,
    }
    (DATA / "demonlist.json").write_text(json.dumps(snapshot, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (DATA / "pending.json").write_text(json.dumps(
        {"fetched": today.isoformat(),
         "note": "Levels in the top 150 held out because no published length was found. Add a confirmed "
                 "value to overrides.json to admit a level.",
         "levels": pending}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    sched_path = DATA / "schedule.json"
    sched = load_json(sched_path, {"launch": args.launch, "seed": SEED, "days": []})
    sched = guess.extend_schedule(sched, [lv["id"] for lv in levels], today, lookahead=1100)
    sched_path.write_text(json.dumps(sched, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"wrote {len(levels)} levels ({len(pending)} held out), {len(sched['days'])} schedule days", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
