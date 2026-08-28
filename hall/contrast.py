"""WCAG 2.1 relative luminance and contrast ratio."""


def parse_hex(value: str) -> tuple[int, int, int]:
    if not isinstance(value, str) or not value.startswith("#"):
        raise ValueError(f"not a hex colour: {value!r}")
    digits = value[1:]
    if len(digits) == 3:
        digits = "".join(c * 2 for c in digits)
    if len(digits) != 6:
        raise ValueError(f"not a hex colour: {value!r}")
    try:
        return (int(digits[0:2], 16), int(digits[2:4], 16), int(digits[4:6], 16))
    except ValueError:
        raise ValueError(f"not a hex colour: {value!r}") from None


def _channel(c: int) -> float:
    s = c / 255
    return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb: tuple[int, int, int]) -> float:
    r, g, b = (_channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg: str, bg: str) -> float:
    lum_a = relative_luminance(parse_hex(fg))
    lum_b = relative_luminance(parse_hex(bg))
    lighter, darker = max(lum_a, lum_b), min(lum_a, lum_b)
    return (lighter + 0.05) / (darker + 0.05)
