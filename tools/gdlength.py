"""The real, in-game length of a level, worked out from its level data.

The official Geometry Dash server gives level data to anyone who asks, which is
how every level browser works. A level is a strip of objects laid out along x.
The player crosses it at a speed set by the speed portals passed on the way
(the header says which speed the level starts at), so the length is the time to
reach the last object.

Calibrated against the Geometry Dash wiki's published times
(tools/validate_lengths.py): the raw figure runs about 0.7 s under the wiki's.
"""
import base64
import urllib.parse
import urllib.request
import zlib

# Units covered per second at each speed. The key is the header's kA4 value and
# what a speed portal switches to: 0 = 1x, 1 = 0.5x, 2 = 2x, 3 = 3x, 4 = 4x.
UNITS_PER_SECOND = {0: 311.58, 1: 251.16, 2: 387.42, 3: 468.0, 4: 576.0}
# Object ids of the speed portals -> the speed key each selects.
PORTALS = {200: 1, 201: 0, 202: 2, 203: 3, 1334: 4}
START_OFFSET = 0.7

SERVER = "http://www.boomlings.com/database/downloadGJLevel22.php"
SECRET = "Wmfd2893gb7"  # the game's own public request secret


def decode(field: str) -> str:
    raw = base64.urlsafe_b64decode(field + "=" * (-len(field) % 4))
    return zlib.decompress(raw, 15 + 32).decode("latin1")  # 15+32: gzip or zlib


def download(level_id: int) -> str:
    """The decoded level string for a level id."""
    req = urllib.request.Request(
        SERVER,
        data=urllib.parse.urlencode({"levelID": level_id, "secret": SECRET}).encode(),
        headers={"User-Agent": ""},
    )
    text = urllib.request.urlopen(req, timeout=60).read().decode()
    if text.startswith("-"):
        raise ValueError(f"server refused level {level_id}: {text}")
    parts = text.split("#")[0].split(":")
    fields = dict(zip(parts[0::2], parts[1::2]))
    if "4" not in fields:
        raise ValueError(f"level {level_id}: no level data in response")
    return decode(fields["4"])


def parse(level_string: str):
    """(starting speed key, [(x, object id), ...]) with bad chunks dropped."""
    chunks = level_string.split(";")
    head = chunks[0].split(",")
    header = dict(zip(head[0::2], head[1::2]))
    try:
        start = int(header.get("kA4", "0") or 0)
    except ValueError:
        start = 0
    if start not in UNITS_PER_SECOND:
        start = 0
    objs = []
    for chunk in chunks[1:]:
        if not chunk:
            continue
        p = chunk.split(",")
        d = dict(zip(p[0::2], p[1::2]))
        try:
            objs.append((float(d["2"]), int(d["1"])))
        except (KeyError, ValueError):
            continue
    return start, objs


def raw_seconds(level_string: str) -> float:
    start, objs = parse(level_string)
    if not objs:
        raise ValueError("level has no objects")
    last = max(x for x, _ in objs)
    t, x0, speed = 0.0, 0.0, start
    for x, key in sorted((x, PORTALS[i]) for x, i in objs if i in PORTALS):
        if x >= last:
            break
        t += (x - x0) / UNITS_PER_SECOND[speed]
        x0, speed = x, key
    return t + (last - x0) / UNITS_PER_SECOND[speed]


def whole_seconds(level_string: str) -> int:
    return int(raw_seconds(level_string) + START_OFFSET + 0.5)
