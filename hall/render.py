"""Logic-free {{ slot }} template filling and page composition."""

import html
import re

SLOT = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def fill(template: str, slots: dict) -> str:
    used: set[str] = set()

    def replace(match: re.Match) -> str:
        key = match.group(1)
        if key not in slots:
            raise KeyError(f"template references unknown slot {key!r}")
        used.add(key)
        value = slots[key]
        text = "" if value is None else str(value)
        return text if key.endswith("_html") else html.escape(text)

    out = SLOT.sub(replace, template)
    unused = set(slots) - used
    if unused:
        raise KeyError(f"slots provided but never used: {sorted(unused)}")
    return out


def _esc(value) -> str:
    return html.escape("" if value is None else str(value))


def hero_size(longest_line: str) -> str:
    """A font-size for the hero word that fits its longest line.

    Archivo 900 uppercase runs about 0.72em per character including
    sidebearings; the page keeps roughly 88vw between its gutters. Sizing off
    the character count stops long names overflowing while letting short ones
    fill the screen the way the reference does.
    """
    chars = max(len(longest_line.strip()), 1)
    vw = 88 / (chars * 0.72)
    vw = min(vw, 26.0)
    return f"clamp(2.75rem, {vw:.1f}vw, 15rem)"


DASH = '<span class="nil" aria-label="not known">&mdash;</span>'


def _fact(value) -> str:
    if value is None or value == "" or value == []:
        return DASH
    if isinstance(value, list):
        return _esc(", ".join(str(v) for v in value))
    return _esc(value)


STAT_ROWS = [
    ("Host", lambda f: f.get("host")),
    ("Creators", lambda f: f.get("creators")),
    ("Verifier", lambda f: f.get("verifier")),
    ("Verified", lambda f: f.get("verifiedDate")),
    ("Attempts", lambda f: f.get("attempts")),
    ("Rated", lambda f: f.get("ratedDate")),
    ("Level ID", lambda f: f.get("levelId")),
    ("Objects", lambda f: f.get("objects")),
    ("Length", lambda f: f.get("length")),
    ("GD version", lambda f: f.get("gdVersion")),
    ("Peak rank", lambda f: f.get("peakRank")),
]


def statblock_html(facts: dict) -> str:
    facts = facts or {}
    rows = []
    for label, getter in STAT_ROWS:
        rows.append(
            f'<div class="statblock__row">'
            f'<dt class="statblock__key">{_esc(label)}</dt>'
            f'<dd class="statblock__val">{_fact(getter(facts))}</dd>'
            f"</div>"
        )
    song = facts.get("song") or {}
    if song.get("name"):
        artist = song.get("artist")
        val = _esc(song["name"])
        if artist:
            val += f' <span class="statblock__by">by {_esc(artist)}</span>'
    else:
        val = DASH
    rows.append(
        f'<div class="statblock__row">'
        f'<dt class="statblock__key">Song</dt>'
        f'<dd class="statblock__val">{val}</dd></div>'
    )
    return f'<dl class="statblock">{"".join(rows)}</dl>'


def sources_html(facts: dict) -> str:
    sources = (facts or {}).get("sources") or []
    if not sources:
        return ""
    items = "".join(
        f'<li><a href="{_esc(url)}" rel="nofollow noopener" '
        f'target="_blank">{_esc(url)}</a></li>'
        for url in sources
    )
    return (
        '<section class="sources" aria-labelledby="sources-h">'
        '<h2 id="sources-h" class="eyebrow">Sources</h2>'
        f"<ul>{items}</ul></section>"
    )


def voice_html(voice: dict) -> str:
    voice = voice or {}
    body = voice.get("why") or ""
    if not body.strip():
        return ""
    hook = voice.get("hook")
    drafted = voice.get("draftedByClaude", True)
    parts = ['<section class="voice" aria-labelledby="voice-h">']
    parts.append('<h2 id="voice-h" class="eyebrow">Why it&rsquo;s here</h2>')
    if hook:
        parts.append(f'<p class="voice__hook">{_esc(hook)}</p>')
    parts.append(f'<div class="voice__body measure">{body}</div>')
    if drafted:
        parts.append(
            '<p class="voice__drafted">Drafted placeholder &mdash; '
            "not yet in Baylor&rsquo;s words.</p>"
        )
    parts.append("</section>")
    return "".join(parts)


def video_html(media: dict, level_name: str) -> str:
    video = (media or {}).get("video") or {}
    yt = video.get("youtubeId")
    if not yt:
        return ""
    title = video.get("title") or f"{level_name} showcase"
    channel = video.get("channel")
    credit = f'<p class="videoframe__credit">{_esc(title)}'
    if channel:
        credit += f" &middot; {_esc(channel)}"
    credit += "</p>"
    return (
        '<section class="videoframe" aria-labelledby="video-h">'
        '<h2 id="video-h" class="eyebrow">Footage</h2>'
        f'<button class="videoframe__load" type="button" '
        f'data-youtube="{_esc(yt)}" data-title="{_esc(title)}">'
        f"<span class=\"videoframe__play\" aria-hidden=\"true\">&#9654;</span>"
        f'<span class="videoframe__label">Load video from YouTube</span>'
        f"</button>{credit}"
        '<p class="videoframe__note">Nothing loads from YouTube until you '
        "press play.</p></section>"
    )


def player_html(facts: dict) -> str:
    song = (facts or {}).get("song") or {}
    if not song.get("name"):
        return ""
    artist = song.get("artist")
    ng = song.get("newgroundsId")
    line = _esc(song["name"])
    if artist:
        line += f" &middot; {_esc(artist)}"
    link = ""
    if ng:
        link = (
            f'<a class="player__ng" rel="nofollow noopener" target="_blank" '
            f'href="https://www.newgrounds.com/audio/listen/{_esc(ng)}">'
            f"Listen on Newgrounds</a>"
        )
    return (
        '<section class="player" aria-labelledby="song-h">'
        '<h2 id="song-h" class="eyebrow">Song</h2>'
        f'<p class="player__title">{line}</p>{link}</section>'
    )


def ranknav_html(prev: dict | None, nxt: dict | None) -> str:
    parts = ['<nav class="ranknav" aria-label="Rank navigation">']
    if prev:
        parts.append(
            f'<a class="ranknav__link ranknav__link--prev" '
            f'href="/levels/{_esc(prev["slug"])}/">'
            f'<span class="ranknav__dir">Previous</span>'
            f'<span class="ranknav__rank">#{prev["rank"]}</span>'
            f'<span class="ranknav__name">{_esc(prev["name"])}</span></a>'
        )
    else:
        parts.append("<span></span>")
    parts.append('<a class="ranknav__home" href="/">All 25</a>')
    if nxt:
        parts.append(
            f'<a class="ranknav__link ranknav__link--next" '
            f'href="/levels/{_esc(nxt["slug"])}/">'
            f'<span class="ranknav__dir">Next</span>'
            f'<span class="ranknav__rank">#{nxt["rank"]}</span>'
            f'<span class="ranknav__name">{_esc(nxt["name"])}</span></a>'
        )
    else:
        parts.append("<span></span>")
    parts.append("</nav>")
    return "".join(parts)


def palette_style(level: dict) -> str:
    palette = (level.get("theme") or {}).get("palette") or {}
    decls = "".join(f"--{k}:{v};" for k, v in palette.items() if v)
    return decls


def countdown_html(levels: list[dict]) -> str:
    entries = []
    for lv in sorted(levels, key=lambda r: -r["rank"]):
        slug = lv["slug"]
        published = lv.get("published")
        creators = (lv.get("facts") or {}).get("creators") or lv.get("creators") or []
        by = ", ".join(str(c) for c in creators) if creators else ""
        classes = "countdown__entry"
        if published:
            classes += " countdown__entry--live"
        inner = (
            f'<span class="countdown__rank" aria-hidden="true">'
            f'{lv["rank"]:02d}</span>'
            f'<span class="countdown__name">{_esc(lv["name"])}</span>'
            + (f'<span class="countdown__by">{_esc(by)}</span>' if by else "")
            + f'<span class="countdown__tag">{_esc(lv.get("tagline",""))}</span>'
        )
        if published:
            body = f'<a class="countdown__hit" href="/levels/{_esc(slug)}/">{inner}<span class="countdown__cta">Enter</span></a>'
        else:
            body = (
                f'<div class="countdown__hit countdown__hit--soon">{inner}'
                f'<span class="countdown__cta">Page coming</span></div>'
            )
        entries.append(
            f'<li class="{classes}" data-rank="{lv["rank"]}" '
            f'data-slug="{_esc(slug)}" style="{palette_style(lv)}">{body}</li>'
        )
    return f'<ol class="countdown" reversed>{"".join(entries)}</ol>'
