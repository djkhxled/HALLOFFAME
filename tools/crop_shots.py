"""Crop GeometryGuessr's screenshots, one after another, in the browser.

    python3 tools/crop_shots.py              # opens http://127.0.0.1:8770/
    python3 tools/crop_shots.py --no-browser

Shows each captured shot full size (the PNG from the capture folder, not the published
WebP) with a 16:9 box over it. Move and resize the box, press Enter, and the next shot
comes up. Every crop is saved the moment it is made, to data/gg/crops.json, so you can
stop and pick up where you left off. Then:

    python3 tools/prepare_shots.py && python3 build.py

which cuts each shot to its box. A shot with no crop is published whole.

A crop is [x, y, size], fractions of the frame: the box's left and top edges, and its
width as a share of the frame's width. The box keeps the frame's own 16:9 shape, so
the same number is its share of the height. Local only: it listens on 127.0.0.1.
Standard library only.
"""
import argparse
import json
import pathlib
import re
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = pathlib.Path(__file__).resolve().parent.parent
CAPTURE = pathlib.Path.home() / "Documents" / "Claude" / "geometryguessr-capture" / "shots-raw"
CROPS = ROOT / "data" / "gg" / "crops.json"
PAGE = ROOT / "tools" / "cropper.html"
RAW_NAME = re.compile(r"^[a-z0-9-]+__\d{3}\.png$")
KEY = re.compile(r"^[a-z0-9-]+/\d{3}$")
MIN_SIZE = 0.3


def load_crops() -> dict:
    return json.loads(CROPS.read_text(encoding="utf-8")) if CROPS.exists() else {}


def save_crops(crops: dict) -> None:
    tmp = CROPS.with_suffix(".tmp")
    tmp.write_text(json.dumps(dict(sorted(crops.items())), indent=1) + "\n", encoding="utf-8")
    tmp.replace(CROPS)


def valid(crop) -> bool:
    if not (isinstance(crop, list) and len(crop) == 3 and all(isinstance(v, (int, float)) for v in crop)):
        return False
    x, y, size = crop
    return MIN_SIZE <= size <= 1 and 0 <= x <= 1 - size + 1e-9 and 0 <= y <= 1 - size + 1e-9


def state() -> dict:
    levels = {lv["id"]: lv for lv in json.loads((ROOT / "data" / "gg" / "levels.json").read_text())["levels"]}
    shots = json.loads((ROOT / "data" / "gg" / "shots.json").read_text())["shots"]
    out = []
    for s in shots:
        slug, pct = s["file"].rsplit(".", 1)[0].split("/")
        raw = f"{slug}__{pct}.png"
        if (CAPTURE / raw).exists():
            out.append({"key": f"{slug}/{pct}", "raw": raw, "name": levels[s["level"]]["name"], "pct": s["pct"]})
    return {"shots": out, "crops": load_crops()}


class Handler(BaseHTTPRequestHandler):
    lock = threading.Lock()

    def log_message(self, *args):   # quiet
        pass

    def send(self, code: int, body: bytes, kind: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def json(self, code: int, data) -> None:
        self.send(code, json.dumps(data).encode(), "application/json")

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/":
            return self.send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
        if path == "/api/state":
            return self.json(200, state())
        if path.startswith("/raw/"):
            name = path[len("/raw/"):]
            if RAW_NAME.match(name) and (CAPTURE / name).is_file():
                return self.send(200, (CAPTURE / name).read_bytes(), "image/png")
        self.json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/api/crop":
            return self.json(404, {"error": "not found"})
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        except ValueError:
            return self.json(400, {"error": "unreadable"})
        key, crop = body.get("key"), body.get("crop")
        if not isinstance(key, str) or not KEY.match(key):
            return self.json(400, {"error": "bad key"})
        if crop is not None and not valid(crop):
            return self.json(400, {"error": "bad crop"})
        with self.lock:
            crops = load_crops()
            if crop is None:
                crops.pop(key, None)
            else:
                crops[key] = [round(v, 4) for v in crop]
            save_crops(crops)
        self.json(200, {"ok": True, "cropped": len(crops)})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8770)
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{args.port}/"
    print(f"GG Cropper on {url}  (Ctrl+C to stop; crops go to {CROPS.relative_to(ROOT)})")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()


if __name__ == "__main__":
    main()
