"""Turn the capture mod's screenshots into GeometryGuessr's images and data.

    python3 tools/prepare_shots.py [capture-dir]

capture-dir defaults to ~/Documents/Claude/geometryguessr-capture, the folder the GG
Capture mod (baylor.gg_capture) writes into. It holds:
    popular.json       the 100 most downloaded demons (fetch_popular.py)
    shots-raw/*.png    <slug>__<target>.png, one per captured target
and the mod's queue.json (in the game's config folder) says which targets are current:
a target that was swapped out after review is left behind even if its PNG is still there.

A shot with a crop in data/gg/crops.json (made with tools/crop_shots.py) is cut to
that 16:9 box first, then brought back to 1138x640 with a Lanczos filter, so every image
is the same size and the browser never has to stretch a small one.

The levels Baylor added beyond those 100 (data/gg/extras.json: his top 30, his picks, and
levels from the Impossible Levels List) follow the 100 in the list.

A level listed in data/gg/excluded.json gets no screenshots, whatever was captured: it
stays in the search box as a name but is never an answer.

Writes, all committed:
    src/shots/<slug>/<pct>.webp   1138x640 WebP
    data/gg/levels.json           every searchable level: the 100 and the extras, answer or not
    data/gg/shots.json            one entry per image: level id, percent, file

A ONE-OFF tool, like tools/make_cards.py: it needs Pillow, which the build does not.
Re-run it whenever new shots are captured; it replaces src/shots/ wholesale.
"""
import datetime
import json
import pathlib
import re
import shutil
import sys

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
CAPTURE = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
    pathlib.Path.home() / "Documents" / "Claude" / "geometryguessr-capture"
QUEUE = pathlib.Path.home() / ("Library/Application Support/Steam/steamapps/common/Geometry Dash/"
                               "Geometry Dash.app/Contents/geode/config/baylor.gg_capture/queue.json")
SHOTS = ROOT / "src" / "shots"
DATA = ROOT / "data" / "gg"
CROPS = DATA / "crops.json"
EXCLUDED = DATA / "excluded.json"
EXTRAS = DATA / "extras.json"
SIZE = (1138, 640)
QUALITY = 80


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def main():
    popular = json.loads((CAPTURE / "popular.json").read_text())
    extras = json.loads(EXTRAS.read_text(encoding="utf-8"))["levels"] if EXTRAS.exists() else []
    known = {lv["id"] for lv in popular}
    popular = popular + [lv for lv in extras if lv["id"] not in known]
    fetched = datetime.date.fromtimestamp((CAPTURE / "popular.json").stat().st_mtime).isoformat()
    targets = {j["slug"]: j["pcts"] for j in json.loads(QUEUE.read_text())["jobs"]}
    raw = CAPTURE / "shots-raw"
    crops = json.loads(CROPS.read_text(encoding="utf-8")) if CROPS.exists() else {}
    excluded = set(json.loads(EXCLUDED.read_text(encoding="utf-8"))["slugs"]) if EXCLUDED.exists() else set()
    cropped = 0

    if SHOTS.exists():
        shutil.rmtree(SHOTS)
    levels, shots, size = [], [], 0
    for lv in popular:
        s = slug(lv["name"])
        # Names come from the GD servers as typed by their creators, stray spaces included.
        entry = {"id": lv["id"], "name": " ".join(lv["name"].split()), "creator": lv["creator"].strip(),
                 "downloads": lv["downloads"], "difficulty": lv["difficulty"], "slug": s}
        if lv.get("group"):
            entry["group"] = lv["group"]
        levels.append(entry)
        for pct in ([] if s in excluded else targets.get(s, [])):
            src = raw / f"{s}__{pct:03d}.png"
            if not src.exists():
                continue
            out = SHOTS / s / f"{pct:03d}.webp"
            out.parent.mkdir(parents=True, exist_ok=True)
            im = Image.open(src).convert("RGB")
            if im.size != SIZE:
                im = im.resize(SIZE, Image.LANCZOS)
            crop = crops.get(f"{s}/{pct:03d}")
            if crop and crop[2] < 1:
                x, y, box = crop
                w, h = SIZE
                im = im.crop((round(x * w), round(y * h), round((x + box) * w), round((y + box) * h)))
                im = im.resize(SIZE, Image.LANCZOS)
                cropped += 1
            im.save(out, "WEBP", quality=QUALITY, method=6)
            size += out.stat().st_size
            shots.append({"level": lv["id"], "pct": pct, "file": f"{s}/{pct:03d}.webp"})

    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "levels.json").write_text(
        json.dumps({"fetched": fetched,
                    "source": "Geometry Dash servers: the 100 most downloaded demons, then Baylor's additions",
                    "levels": levels}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (DATA / "shots.json").write_text(json.dumps({"shots": shots}, indent=1) + "\n", encoding="utf-8")

    answers = len({s["level"] for s in shots})
    print(f"{len(shots)} shots of {answers} levels ({size / 1e6:.1f} MB, {cropped} cropped), "
          f"{len(levels)} searchable levels")


if __name__ == "__main__":
    main()
