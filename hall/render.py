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


def esc(value) -> str:
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
        return esc(", ".join(str(v) for v in value))
    return esc(value)


ROSTER_MIN = 7  # below this a roster reads fine inline in the stat block


def _creators_cell(creators):
    """A 29-name roster destroys the stat grid; show the count and let
    roster_html carry the names."""
    if isinstance(creators, list) and len(creators) >= ROSTER_MIN:
        return f"{len(creators)} creators"
    return creators


STAT_ROWS = [
    ("Host", lambda f: f.get("host")),
    ("Creators", lambda f: _creators_cell(f.get("creators"))),
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
            f'<dt class="statblock__key">{esc(label)}</dt>'
            f'<dd class="statblock__val">{_fact(getter(facts))}</dd>'
            f"</div>"
        )
    song = facts.get("song") or {}
    if song.get("name"):
        artist = song.get("artist")
        val = esc(song["name"])
        if artist:
            val += f' <span class="statblock__by">by {esc(artist)}</span>'
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
        f'<li><a href="{esc(url)}" rel="nofollow noopener" '
        f'target="_blank">{esc(url)}</a></li>'
        for url in sources
    )
    return (
        '<section class="sources" aria-labelledby="sources-h">'
        '<h2 id="sources-h" class="eyebrow">Sources</h2>'
        f"<ul>{items}</ul></section>"
    )


def spotlight_html(theme: dict) -> str:
    """A full-bleed statement panel for the themed tier.

    The bespoke levels each get a pinned set-piece; the themed ones had
    nothing between the stat block and the commentary, and the signature they
    declare in their theme drives no markup at all. This gives them one
    moment at full size, built from a fact the level's own record already
    states rather than from decoration.
    """
    spot = (theme or {}).get("spotlight")
    if not spot:
        return ""
    sub = spot.get("sub")
    return (
        '<section class="spotlight" data-motion aria-labelledby="spot-h">'
        '<div class="spotlight__inner page">'
        f'<p class="eyebrow" id="spot-h">{esc(spot.get("eyebrow", ""))}</p>'
        f'<p class="spotlight__big">{esc(spot["big"])}</p>'
        + (f'<p class="spotlight__sub measure">{esc(sub)}</p>' if sub else "")
        + "</div></section>"
    )


def roster_html(facts: dict) -> str:
    """The full credit list, for collabs too large to sit in the stat block."""
    creators = (facts or {}).get("creators") or []
    if not isinstance(creators, list) or len(creators) < ROSTER_MIN:
        return ""
    names = "".join(f"<li>{esc(n)}</li>" for n in creators)
    return (
        '<section class="roster" aria-labelledby="roster-h">'
        '<h2 id="roster-h" class="eyebrow">Everyone who built it</h2>'
        f'<ol class="roster__list">{names}</ol></section>'
    )


def arc_html(voice: dict) -> str:
    """An optional reading of how the level moves, in order.

    Stops carry no timings unless the record states one, because the only
    sourced marker is whatever Baylor named himself.
    """
    stops = (voice or {}).get("arc") or []
    if not stops:
        return ""
    # An empty marker slot only earns its space when some other stop fills
    # one; an arc with no stated timings anywhere drops the row entirely.
    marked = any(stop.get("at") for stop in stops)
    items = []
    for stop in stops:
        mark = stop.get("at")
        if not marked:
            mark_html = ""
        elif mark:
            mark_html = f'<span class="arc__at">{esc(mark)}</span>'
        else:
            mark_html = '<span class="arc__at arc__at--none" aria-hidden="true"></span>'
        items.append(
            '<li class="arc__stop">'
            f'{mark_html}'
            f'<span class="arc__label">{esc(stop["label"])}</span>'
            f'<span class="arc__note">{esc(stop.get("note", ""))}</span>'
            "</li>"
        )
    return (
        '<section class="arc section page" aria-labelledby="arc-h">'
        '<h2 id="arc-h" class="eyebrow">The shape of it</h2>'
        f'<ol class="arc__track">{"".join(items)}</ol>'
        '<p class="arc__caveat">Baylor&rsquo;s reading of the level, not a '
        "sourced breakdown.</p></section>"
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
        parts.append(f'<p class="voice__hook">{esc(hook)}</p>')
    # The essay treatment marks commentary that is actually Baylor's, rather
    # than tracking length: a character threshold made the drop cap flip on
    # and off as he edited.
    essay = not drafted and body.count("<p>") >= 2
    cls = "voice__body measure voice__body--long" if essay else "voice__body measure"
    parts.append(f'<div class="{cls}">{body}</div>')
    if drafted:
        parts.append(
            '<p class="voice__drafted">Drafted placeholder &mdash; '
            "not yet in Baylor&rsquo;s words.</p>"
        )
    parts.append("</section>")
    return "".join(parts)


def footer_links_html(docs: list[dict]) -> str:
    links = "".join(
        f'<li><a href="/{d["slug"]}/">{d["heading"]}</a></li>' for d in docs
    )
    return ('<nav class="site-foot__nav" aria-label="Site information">'
            f"<ul>{links}</ul></nav>")


def docnav_html(docs: list[dict], current: str) -> str:
    """Cross-links between the policy pages, and back to the list."""
    items = ['<a class="docnav__home" href="/">Back to the list</a>']
    for d in docs:
        if d["slug"] == current:
            continue
        items.append(f'<a class="docnav__link" href="/{d["slug"]}/">'
                     f'{d["heading"]}</a>')
    return ('<nav class="docnav" aria-label="Site information">'
            + "".join(items) + "</nav>")


def doc_footer_html(contact, updated: str) -> str:
    """The contact line. Says plainly when no address has been set, rather
    than inventing one or quietly omitting it."""
    if contact:
        line = (f'Contact: <a href="mailto:{esc(contact)}">{esc(contact)}</a>')
    else:
        line = ('<strong class="doc__todo">Contact address not set yet</strong> '
                "&mdash; add one to data/site.json before relying on these "
                "pages.")
    return (f'<p class="doc__meta">{line}</p>'
            f'<p class="doc__meta">Last updated {esc(updated)}.</p>')


def video_html(media: dict, level_name: str) -> str:
    video = (media or {}).get("video") or {}
    yt = video.get("youtubeId")
    if not yt:
        return ""
    title = video.get("title") or f"{level_name} showcase"
    channel = video.get("channel")
    credit = f'<p class="videoframe__credit">{esc(title)}'
    if channel:
        credit += f" &middot; {esc(channel)}"
    credit += "</p>"
    return (
        '<section class="videoframe" aria-labelledby="video-h">'
        '<h2 id="video-h" class="eyebrow">Footage</h2>'
        f'<button class="videoframe__load" type="button" '
        f'data-youtube="{esc(yt)}" data-title="{esc(title)}">'
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
    line = esc(song["name"])
    if artist:
        line += f" &middot; {esc(artist)}"
    link = ""
    if ng:
        link = (
            f'<a class="player__ng" rel="nofollow noopener" target="_blank" '
            f'href="https://www.newgrounds.com/audio/listen/{esc(ng)}">'
            f"Listen on Newgrounds</a>"
        )
    elif song.get("nong"):
        # The level ships a placeholder Newgrounds track and the real song is
        # supplied separately. Linking the in-game song ID would play the
        # wrong music, so say so instead.
        link = (
            '<p class="player__nong">Not on Newgrounds &mdash; the level '
            "carries this track as a custom song.</p>"
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
            f'href="/levels/{esc(prev["slug"])}/">'
            f'<span class="ranknav__dir">Previous</span>'
            f'<span class="ranknav__rank">#{prev["rank"]}</span>'
            f'<span class="ranknav__name">{esc(prev["name"])}</span></a>'
        )
    else:
        parts.append("<span></span>")
    parts.append('<a class="ranknav__home" href="/">All 25</a>')
    if nxt:
        parts.append(
            f'<a class="ranknav__link ranknav__link--next" '
            f'href="/levels/{esc(nxt["slug"])}/">'
            f'<span class="ranknav__dir">Next</span>'
            f'<span class="ranknav__rank">#{nxt["rank"]}</span>'
            f'<span class="ranknav__name">{esc(nxt["name"])}</span></a>'
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
            f'<span class="countdown__name">{esc(lv["name"])}</span>'
            + (f'<span class="countdown__by">{esc(by)}</span>' if by else "")
            + f'<span class="countdown__tag">{esc(lv.get("tagline",""))}</span>'
        )
        if published:
            body = f'<a class="countdown__hit" href="/levels/{esc(slug)}/">{inner}<span class="countdown__cta">Enter</span></a>'
        else:
            body = (
                f'<div class="countdown__hit countdown__hit--soon">{inner}'
                f'<span class="countdown__cta">Page coming</span></div>'
            )
        entries.append(
            f'<li class="{classes}" data-rank="{lv["rank"]}" '
            f'data-slug="{esc(slug)}" style="{palette_style(lv)}">{body}</li>'
        )
    return f'<ol class="countdown" reversed>{"".join(entries)}</ol>'
