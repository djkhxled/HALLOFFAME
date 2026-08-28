"""Load and validate level records."""

import json
import pathlib

from hall.contrast import contrast_ratio

SIGNATURES = frozenset(
    {
        "orbit",
        "glitch-assemble",
        "descend",
        "surge",
        "ignite",
        "pulse",
        "fracture",
        "flood",
        "eclipse",
        "static",
    }
)

TEXTURES = frozenset(
    {"starfield", "scanline", "grain", "caustics", "ember", "snow", "chrome", "none"}
)

TIERS = frozenset({"bespoke", "themed"})

BODY_CONTRAST_MIN = 4.5
LARGE_CONTRAST_MIN = 3.0


class ValidationError(Exception):
    pass


def load_levels(levels_dir: pathlib.Path) -> list[dict]:
    records = []
    for path in sorted(levels_dir.glob("*.json")):
        with path.open(encoding="utf-8") as handle:
            record = json.load(handle)
        record.setdefault("published", False)
        record.setdefault("theme", {})
        record.setdefault("facts", {})
        record.setdefault("voice", {})
        record.setdefault("media", {})
        record["_source_file"] = path.name
        records.append(record)
    return sorted(records, key=lambda r: r.get("rank", 0))


def _palette(level: dict) -> dict:
    return level.get("theme", {}).get("palette", {}) or {}


def validate_levels(levels: list[dict], root: pathlib.Path) -> list[str]:
    errors: list[str] = []

    if not levels:
        return ["no level records found"]

    # Rule 1: ranks are exactly 1..N, no gaps or duplicates.
    ranks = [lv.get("rank") for lv in levels]
    expected = list(range(1, len(levels) + 1))
    if sorted(r for r in ranks if isinstance(r, int)) != expected:
        errors.append(
            f"rank sequence must be exactly 1..{len(levels)} with no gaps or "
            f"duplicates, got {sorted(r for r in ranks if isinstance(r, int))}"
        )

    # Rule 2: slugs unique and non-empty.
    seen: dict[str, str] = {}
    for lv in levels:
        slug = lv.get("slug")
        if not slug:
            errors.append(f"{lv.get('_source_file')}: missing slug")
            continue
        if slug in seen:
            errors.append(f"{slug}: duplicate slug (also in {seen[slug]})")
        seen[slug] = lv.get("_source_file", "?")

    for lv in levels:
        slug = lv.get("slug", lv.get("_source_file", "?"))
        theme = lv.get("theme", {})
        palette = _palette(lv)

        # Rule 3: fields required of every record.
        for field in ("rank", "slug", "name", "tagline"):
            if not lv.get(field):
                errors.append(f"{slug}: missing required field '{field}'")
        for key in ("field", "ink"):
            if not palette.get(key):
                errors.append(f"{slug}: missing theme.palette.{key}")

        # Rule 5/6: enumerated values.
        signature = theme.get("signature")
        if signature is not None and signature not in SIGNATURES:
            errors.append(
                f"{slug}: unknown signature {signature!r}, "
                f"expected one of {sorted(SIGNATURES)}"
            )
        texture = theme.get("texture")
        if texture is not None and texture not in TEXTURES:
            errors.append(f"{slug}: unknown texture {texture!r}")
        tier = theme.get("tier")
        if tier is not None and tier not in TIERS:
            errors.append(f"{slug}: unknown tier {tier!r}")

        css_path = root / "src" / "css" / "levels" / f"{slug}.css"
        bespoke_path = root / "bespoke" / f"{slug}.html"
        art = (lv.get("media") or {}).get("art")

        # Rule 7: themed tier owns no bespoke assets.
        if tier == "themed" or (tier is None and not lv.get("published")):
            if art:
                errors.append(
                    f"{slug}: themed-tier level must not declare media.art "
                    f"({art}); themed art is generated parametrically"
                )
            if css_path.exists():
                errors.append(f"{slug}: themed-tier level must not have {css_path}")
            if bespoke_path.exists():
                errors.append(f"{slug}: themed-tier level must not have {bespoke_path}")

        # Rule 8: referenced files exist.
        if art and not (root / art).exists():
            errors.append(f"{slug}: media.art points at missing file {art}")

        # Rule 9: contrast floor.
        field_colour = palette.get("field")
        if field_colour:
            for key, floor in (
                ("ink", BODY_CONTRAST_MIN),
                ("muted", BODY_CONTRAST_MIN),
            ):
                colour = palette.get(key)
                if not colour:
                    continue
                try:
                    ratio = contrast_ratio(colour, field_colour)
                except ValueError as exc:
                    errors.append(f"{slug}: {exc}")
                    continue
                if ratio < floor:
                    errors.append(
                        f"{slug}: contrast {key} {colour} on field {field_colour} "
                        f"is {ratio:.2f}:1, need {floor}:1"
                    )

        # Rule 4: extra requirements for published levels.
        if lv.get("published"):
            if not tier:
                errors.append(f"{slug}: published level needs theme.tier")
            if not signature:
                errors.append(f"{slug}: published level needs theme.signature")
            if not (lv.get("facts", {}).get("sources") or []):
                errors.append(f"{slug}: published level needs non-empty facts.sources")
            if not (lv.get("voice", {}).get("why") or "").strip():
                errors.append(f"{slug}: published level needs voice.why")
            if tier == "bespoke":
                if not bespoke_path.exists():
                    errors.append(f"{slug}: bespoke level missing {bespoke_path}")
                if not css_path.exists():
                    errors.append(f"{slug}: bespoke level missing {css_path}")

    return errors


def voice_progress(levels: list[dict]) -> tuple[int, int]:
    """Return (in Baylor's own words, total)."""
    total = len(levels)
    own = sum(
        1
        for lv in levels
        if (lv.get("voice") or {}).get("why")
        and not (lv.get("voice") or {}).get("draftedByClaude", True)
    )
    return own, total
