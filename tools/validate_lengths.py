"""Does gdlength agree with the wiki? Prints the gate result for the spec.

Gate: at least 95% of levels with a published time must land within 1 second of
it after the calibration offset. Run with no arguments.
"""
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import gdlength  # noqa: E402

wiki = json.load(open(ROOT / "data" / "guess" / "wiki_lengths.json"))["lengths"]
rows = []
for lid, w in wiki.items():
    try:
        raw = gdlength.raw_seconds(gdlength.download(int(lid)))
    except Exception as exc:  # noqa: BLE001
        print(f"  ! {w['name']} ({lid}): {exc}", file=sys.stderr)
        continue
    rows.append((w["name"], lid, w["seconds"], raw))
    time.sleep(0.25)

best = None
for off in [x / 20 for x in range(0, 41)]:
    ok = sum(1 for _, _, want, raw in rows if abs(int(raw + off + 0.5) - want) <= 1)
    if best is None or ok > best[1]:
        best = (off, ok)
off = gdlength.START_OFFSET
within = sum(1 for _, _, want, raw in rows if abs(int(raw + off + 0.5) - want) <= 1)
print(f"{len(rows)} compared; offset {off}: {within} within 1 s ({100 * within / len(rows):.1f}%)")
print(f"best offset {best[0]:.2f} would give {best[1]}")
for name, lid, want, raw in sorted(rows, key=lambda r: -abs(int(r[3] + off + 0.5) - r[2])):
    d = int(raw + off + 0.5) - want
    if abs(d) > 1:
        print(f"  off by {d:+d}: {name} ({lid}) wiki {want}s computed {raw + off:.1f}s")
print("GATE", "PASS" if within / len(rows) >= 0.95 else "FAIL")
