"""Draw the share cards (1200x630 PNG) for the pages other than the home page.

    python3 tools/make_cards.py

A ONE-OFF design tool, not part of the build: it needs Pillow (the build itself is
standard library only) and macOS's Arial Black / Menlo fonts, and its output is
committed under src/art/. Re-run it only to change a card. The home card, and the
card every level page shares, is the owner's own og-home.png and is not drawn here.
"""
import pathlib
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "art"
W, H, S = 1200, 630, 2                      # drawn at 2x and reduced, for clean edges
FIELD = (6, 7, 11)                          # the site's ground colour, #06070b
INK = (242, 243, 247)
MUTED = (142, 148, 165)
HEAVY = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
MONO = "/System/Library/Fonts/Menlo.ttc"

GREEN, YELLOW, GREY = (27, 107, 65), (138, 98, 0), (38, 42, 53)


def font(path, size):
    return ImageFont.truetype(path, size * S)


def canvas(seed):
    """Dark ground with a few stars, like the site's own."""
    img = Image.new("RGB", (W * S, H * S), FIELD)
    d = ImageDraw.Draw(img)
    rnd = random.Random(seed)
    for _ in range(140):
        x, y = rnd.randrange(W * S), rnd.randrange(int(H * S * 0.75))
        r = rnd.choice((1, 1, 2)) * S // 2 + 1
        shade = rnd.randrange(50, 130)
        d.ellipse((x, y, x + r, y + r), fill=(shade, shade, shade + 20))
    return img


def beams(img, colours, seed, base=0.62, spread=1.0, count=34):
    """Soft vertical shafts of light rising from the bottom, the home page's motif."""
    glow = Image.new("RGB", img.size, (0, 0, 0))
    d = ImageDraw.Draw(glow)
    rnd = random.Random(seed)
    for i in range(count):
        x = int((i + rnd.random() * 0.6) / count * W * S)
        w = rnd.randrange(10, 30) * S
        top = int(H * S * (base + rnd.random() * 0.22 * spread))
        c = colours[rnd.randrange(len(colours))]
        k = 0.45 + rnd.random() * 0.55
        for y in range(top, H * S, 2 * S):
            t = (y - top) / (H * S - top)
            a = (1 - t) ** 0.4 * k * min(1, t * 6 + 0.15)   # brightest low down, fading as it rises
            wy = int(w * (0.12 + 0.88 * t))                  # a shaft, wider at its foot
            d.rectangle((x - wy // 2, y, x + wy // 2, y + 2 * S), fill=tuple(int(v * a) for v in c))
    glow = glow.filter(ImageFilter.GaussianBlur(7 * S))
    out = Image.new("RGB", img.size)
    px_a, px_b, px_o = img.load(), glow.load(), out.load()
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            a, b = px_a[x, y], px_b[x, y]
            px_o[x, y] = tuple(min(255, a[i] + int(b[i] * 1.9)) for i in range(3))
    return out


def fade_bottom(img, strength=0.55):
    """Darken the foot of the card so small text stays legible."""
    over = Image.new("RGB", img.size, FIELD)
    mask = Image.new("L", img.size, 0)
    md = ImageDraw.Draw(mask)
    for y in range(int(img.size[1] * 0.62), img.size[1]):
        md.line((0, y, img.size[0], y), fill=int(255 * strength * (y - img.size[1] * 0.62) / (img.size[1] * 0.38)))
    return Image.composite(over, img, mask)


def text(img, xy, s, fnt, fill=INK, anchor="la", spacing=0):
    d = ImageDraw.Draw(img)
    d.text((xy[0] * S, xy[1] * S), s, font=fnt, fill=fill, anchor=anchor, spacing=spacing * S)


def footer(img, left="b4ylor.com", right="BAYLOR'S HALL OF EXTREMES"):
    f = font(MONO, 20)
    text(img, (64, H - 52), left, f, MUTED)
    text(img, (W - 64, H - 52), right, f, MUTED, anchor="ra")


def finish(img, name):
    img = img.resize((W, H), Image.LANCZOS)
    path = OUT / f"og-{name}.png"
    img.save(path, optimize=True)
    print(f"{path.name}: {path.stat().st_size // 1024} KB")


def title_block(img, lines, size, baseline, eyebrow=None, subs=()):
    """Title lines set on baselines (cap height is ~0.74 of the size in Arial Black),
    an eyebrow above the first and any sub-lines below the last."""
    f = font(HEAVY, size)
    cap = int(size * 0.74)
    step = int(size * 0.98)
    if eyebrow:
        text(img, (64, baseline - cap - 40), eyebrow, font(MONO, 24), MUTED, anchor="ls")
    for i, line in enumerate(lines):
        text(img, (64, baseline + i * step), line, f, anchor="ls")
    y = baseline + (len(lines) - 1) * step + 62
    for line in subs:
        text(img, (64, y), line, font(MONO, 27), MUTED, anchor="ls")
        y += 40


# --- the cards -------------------------------------------------------------------

def games():
    img = beams(canvas(1), [(120, 90, 255), (60, 190, 255), (255, 90, 190), (90, 230, 200)], 11,
                base=0.56, spread=0.8)
    img = fade_bottom(img, 0.3)
    title_block(img, ["GAMES"], 190, 330, eyebrow="2 GAMES  ·  PICK ONE",
                subs=["Name Every Extreme Demon", "Demondle"])
    footer(img)
    finish(img, "games")


def demondle():
    img = canvas(2)
    d = ImageDraw.Draw(img)
    # a board, as the game draws it: six guesses, six stats
    cols, rows, cell, gap = 6, 6, 62, 10
    ox = W - 64 - (cols * cell + (cols - 1) * gap)
    oy = (H - (rows * cell + (rows - 1) * gap)) // 2 - 10
    pattern = ["xxyxxx", "xyxyxx", "yxgyxy", "gyxgyy", "gygggy", "gggggg"]
    colour = {"g": GREEN, "y": YELLOW, "x": GREY}
    for r in range(rows):
        for c in range(cols):
            x0 = (ox + c * (cell + gap)) * S
            y0 = (oy + r * (cell + gap)) * S
            d.rounded_rectangle((x0, y0, x0 + cell * S, y0 + cell * S), radius=8 * S, fill=colour[pattern[r][c]])
    title_block(img, ["DEMONDLE"], 96, 330, eyebrow="A WORDLE-STYLE GAME",
                subs=["Guess the hidden Demonlist level.", "Six guesses. Six stats."])
    footer(img)
    finish(img, "demondle")


def game():
    img = canvas(3)
    d = ImageDraw.Draw(img)
    # the list: a field of slots, some already named
    rnd = random.Random(33)
    rows, cols, sw, sh, gx, gy = 17, 6, 76, 20, 8, 11
    ox = W - 64 - (cols * sw + (cols - 1) * gx)
    oy = 58
    for r in range(rows):
        for c in range(cols):
            x0 = (ox + c * (sw + gx)) * S
            y0 = (oy + r * (sh + gy)) * S
            named = rnd.random() < 0.46
            d.rounded_rectangle((x0, y0, x0 + sw * S, y0 + sh * S), radius=5 * S,
                                fill=(46, 104, 168) if named else (26, 29, 40))
    title_block(img, ["NAME", "EVERY", "EXTREME", "DEMON"], 88, 168, eyebrow="1,621 LEVELS ON THE LIST",
                subs=["Type them in. Beat the clock."])
    footer(img)
    finish(img, "game")


def geometryguessr():
    """One of the game's own screenshots, a question over it, the level bar under it."""
    img = canvas(7)
    glowc = Image.new("RGB", img.size, (0, 0, 0))
    sx, sy, sw, sh = 64, 176, 668, 376
    ImageDraw.Draw(glowc).rounded_rectangle(((sx - 8) * S, (sy - 8) * S, (sx + sw + 8) * S, (sy + sh + 8) * S),
                                            radius=26 * S, fill=(170, 40, 150))
    glowc = glowc.filter(ImageFilter.GaussianBlur(26 * S))
    px_a, px_b = img.load(), glowc.load()
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            a, b = px_a[x, y], px_b[x, y]
            px_a[x, y] = tuple(min(255, a[i] + int(b[i] * 0.7)) for i in range(3))
    d = ImageDraw.Draw(img)
    shot = Image.open(ROOT / "src" / "shots" / "cataclysm" / "040.webp").convert("RGB").resize((sw * S, sh * S), Image.LANCZOS)
    mask = Image.new("L", shot.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, shot.size[0], shot.size[1]), radius=16 * S, fill=255)
    img.paste(shot, (sx * S, sy * S), mask)
    d.rounded_rectangle((sx * S, sy * S, (sx + sw) * S, (sy + sh) * S), radius=16 * S, outline=(255, 255, 255), width=2 * S)
    tag = font(HEAVY, 22)
    d.rounded_rectangle(((sx + 16) * S, (sy + 16) * S, (sx + 290) * S, (sy + 58) * S), radius=10 * S, fill=FIELD)
    text(img, (sx + 28, sy + 47), "WHICH LEVEL IS THIS?", tag, (255, 210, 63), anchor="ls")
    by = sy + sh + 24
    d.rounded_rectangle((sx * S, by * S, (sx + sw) * S, (by + 12) * S), radius=6 * S, fill=(38, 42, 53))
    mx = sx + int(sw * 0.43)
    d.rounded_rectangle((sx * S, by * S, mx * S, (by + 12) * S), radius=6 * S, fill=(168, 255, 46))
    d.rectangle(((mx - 14) * S, (by - 9) * S, (mx + 14) * S, (by + 19) * S), fill=(168, 255, 46), outline=(0, 0, 0), width=3 * S)
    d.rectangle(((mx - 6) * S, (by - 1) * S, (mx + 6) * S, (by + 11) * S), fill=(33, 230, 255), outline=(0, 0, 0), width=2 * S)

    text(img, (64, 74), "NEW GAME  \u00b7  THE 100 MOST DOWNLOADED DEMONS", font(MONO, 22), MUTED, anchor="ls")
    title = font(HEAVY, 84)
    x = 60
    for i, ch in enumerate("GEOMETRY"):
        text(img, (x, 152), ch, title, INK, anchor="ls")
        x += ImageDraw.Draw(img).textlength(ch, font=title) / S
    colours = [(33, 230, 255), (255, 43, 214), (255, 210, 63), (168, 255, 46), (255, 138, 43), (180, 123, 255)]
    for i, ch in enumerate("GUESSR"):
        text(img, (x, 152), ch, title, colours[i], anchor="ls")
        x += ImageDraw.Draw(img).textlength(ch, font=title) / S

    cx = 780
    steps = [("1", "NAME THE DEMON", "One screenshot."), ("2", "FIND THE SPOT", "Drag the cube."),
             ("3", "THREE LIVES", "How far can you get?")]
    y = 218
    for num, head, line in steps:
        d.ellipse((cx * S, y * S, (cx + 50) * S, (y + 50) * S), outline=(255, 210, 63), width=3 * S)
        text(img, (cx + 25, y + 36), num, font(HEAVY, 26), (255, 210, 63), anchor="ms")
        text(img, (cx + 68, y + 24), head, font(HEAVY, 25), INK, anchor="ls")
        text(img, (cx + 68, y + 52), line, font(MONO, 20), MUTED, anchor="ls")
        y += 112
    footer(img, left="")   # the level bar sits where the address would
    finish(img, "geometryguessr")


def document(name, title, eyebrow, colours, seed):
    img = beams(canvas(seed), colours, seed + 50, base=0.7, spread=0.6, count=28)
    img = fade_bottom(img, 0.3)
    title_block(img, [title], 170, 340, eyebrow=eyebrow)
    footer(img)
    finish(img, name)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    games()
    demondle()
    geometryguessr()
    game()
    document("privacy", "PRIVACY", "WHAT THIS SITE DOES WITH YOUR DATA", [(60, 200, 190), (60, 130, 220), (110, 160, 255)], 4)
    document("terms", "TERMS", "THE GROUND RULES", [(255, 170, 60), (255, 110, 70), (230, 200, 90)], 5)
    document("credits", "CREDITS", "WHO MADE WHAT", [(180, 110, 255), (255, 110, 200), (110, 140, 255)], 6)
