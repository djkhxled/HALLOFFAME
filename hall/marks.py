"""One glyph per signature, drawn in the level's own colours.

The countdown was thirty rows of identical text. Each level already declares
a signature that describes what its page does — eclipse, surge, corrupt —
and that is a perfectly good name for a shape. So the list gets a mark per
row, built from the same two facts the row already carries: the signature
and the palette.

Deliberately tiny and stroke-only. These sit at 22px next to a rank number;
anything with fill and detail turns to mud at that size, and thirty of them
have to read as a set before any one of them reads as itself.

No file is written. The glyphs are inlined into the countdown, which costs
about 300 bytes a row and saves thirty requests.
"""

BOX = 24
MID = BOX / 2

# Every path is drawn inside a 24x24 box on a single stroke weight, so the
# set holds together however different the shapes are.
GLYPHS = {
    "eclipse": '<circle cx="12" cy="12" r="7"/><path d="M12 5a7 7 0 0 0 0 14"/>',
    "orbit": '<circle cx="12" cy="12" r="3.2"/>'
             '<ellipse cx="12" cy="12" rx="10" ry="4.4"/>',
    "glitch-assemble": '<path d="M3 8h9M7 12h14M3 16h11"/>'
                       '<path d="M15 8h6M2 12h2"/>',
    "slash": '<path d="M4 20L20 4"/><path d="M9 6h9v9"/>',
    "prism": '<path d="M12 3L21 19H3z"/><path d="M12 3v16"/>',
    "descend": '<path d="M5 5l7 6 7-6"/><path d="M5 13l7 6 7-6"/>',
    "ascend": '<path d="M5 19l7-6 7 6"/><path d="M5 11l7-6 7 6"/>',
    "surge": '<path d="M2 15c3-6 7-6 10 0s7 6 10 0"/>'
             '<path d="M2 20c3-5 7-5 10 0s7 5 10 0"/>',
    "ignite": '<circle cx="12" cy="12" r="3.4"/>'
              '<path d="M12 2v3M12 19v3M2 12h3M19 12h3'
              'M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2"/>',
    "pulse": '<circle cx="12" cy="12" r="2.4"/><circle cx="12" cy="12" r="6"/>'
             '<circle cx="12" cy="12" r="9.6"/>',
    "fracture": '<path d="M12 2L4 9l3 12M12 2l8 7-3 12M4 9h16M7 21h10"/>',
    "aurora": '<path d="M4 20c0-9 2-14 4-16M11 21c0-10 2-15 4-17'
              'M18 21c0-8 1.6-12 3-14"/>',
    "flood": '<path d="M2 20h20"/><path d="M6 20v-6M12 20V8M18 20v-9"/>',
    "twin": '<path d="M8 5l3 3-3 3-3-3z"/><path d="M16 13l3 3-3 3-3-3z"/>'
            '<path d="M8 11v2M16 11v2"/>',
    "whiteout": '<path d="M3 4h18M5 9h14M7 14h10M9 19h6"/>',
    "overgrow": '<path d="M12 21V8"/><path d="M12 12c-5 0-6-4-6-6 4 0 6 2 6 6z"/>'
                '<path d="M12 15c5 0 6-4 6-6-4 0-6 2-6 6z"/>',
    "iris": '<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7-10-7-10-7z"/>'
            '<circle cx="12" cy="12" r="2.8"/>',
    "corrupt": '<path d="M3 6h11M8 10h13M3 14h9M11 18h10"/>',
    "static": '<path d="M5 7h.01M12 7h.01M19 7h.01M5 12h.01M12 12h.01'
              'M19 12h.01M5 17h.01M12 17h.01M19 17h.01"/>',
}

FALLBACK = '<circle cx="12" cy="12" r="8"/>'


def mark_svg(signature: str, label: str = "") -> str:
    """The glyph for a signature, as an inline SVG.

    currentColor throughout, so the row's own palette drives it through one
    CSS property and nothing here has to know a colour.
    """
    body = GLYPHS.get(signature or "", FALLBACK)
    return (
        f'<svg class="mark" viewBox="0 0 {BOX} {BOX}" width="22" height="22" '
        'fill="none" stroke="currentColor" stroke-width="1.6" '
        'stroke-linecap="round" stroke-linejoin="round" '
        'aria-hidden="true" focusable="false">'
        f"{body}</svg>"
    )


def known_signatures() -> set:
    return set(GLYPHS)
