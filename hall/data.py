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
        "slash",
        "prism",
        "aurora",
        "static",
        # written for the themed tier, where the level wanted something the
        # bespoke vocabulary could not say
        "twin",
        "whiteout",
        "overgrow",
        "iris",
        "corrupt",
        # the mirror of descend: the ground falls away instead
        "ascend",
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


def _line_at(path: pathlib.Path, lineno: int) -> str:
    """The offending line itself, so the error can be read without opening
    the file."""
    try:
        return path.read_text(encoding="utf-8").splitlines()[lineno - 1].strip()
    except (OSError, IndexError):
        return ""


def load_levels(levels_dir: pathlib.Path) -> list[dict]:
    records = []
    for path in sorted(levels_dir.glob("*.json")):
        with path.open(encoding="utf-8") as handle:
            try:
                record = json.load(handle)
            except json.JSONDecodeError as exc:
                # These files get edited by hand, often through GitHub's web
                # editor, and the failure mode is always the same: a value
                # typed without quotes. "attempts": 25,000 parses as the
                # number 25 followed by junk, and "ratedDate": 2021-10-29 is
                # not a number at all. A raw traceback names neither the file
                # nor the line, so say both and say what to do.
                raise ValidationError(
                    f"{path.name} is not valid JSON: {exc.msg} "
                    f"(line {exc.lineno}, column {exc.colno})\n"
                    f"    {_line_at(path, exc.lineno)}\n"
                    "    Every value in these files is a quoted string or "
                    "null — numbers with commas and dates both need quotes."
                ) from None
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

        # Rule 7: what separates the tiers is hand-authoring, not features.
        # The themed tier carries generated art (tools/gen_themed.py) and a
        # generated set-piece (tools/gen_setpiece.py); what it must never own
        # is a stylesheet or a hand-written fragment, because those are the
        # things that do not scale to fifteen levels.
        #
        # The fragment check is by content, not by existence. A generated
        # stage uses .stage/[data-sig] and is painted entirely by the shared
        # stage.css out of palette tokens; a bespoke one uses .sig--<name>
        # and needs its own stylesheet, which this tier does not get. Letting
        # a .sig-- fragment through here would render it unstyled.
        if tier == "themed" or (tier is None and not lv.get("published")):
            if css_path.exists():
                errors.append(f"{slug}: themed-tier level must not have {css_path}")
            if bespoke_path.exists():
                fragment = bespoke_path.read_text(encoding="utf-8")
                if 'class="stage ' not in fragment:
                    errors.append(
                        f"{slug}: {bespoke_path.name} is not a generated stage — "
                        "the themed tier owns no stylesheet, so a hand-written "
                        "fragment would ship unstyled. Run tools/gen_setpiece.py."
                    )

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
