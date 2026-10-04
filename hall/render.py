"""Logic-free {{ slot }} template filling and page composition."""

import html
import re

from hall.contrast import parse_hex, relative_luminance
from hall.marks import mark_svg

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


# Up to this many credited names are written out wherever a level is shown.
# One more and the line collapses to "HOST & N more", with the full list on
# hover/focus. The stat block's roster follows the same cut, so a level is
# either spelled out everywhere or summarised everywhere.
CREDIT_MAX = 5
ROSTER_MIN = CREDIT_MAX + 1


def credit_html(creators, host=None, *, tip_id: str | None = None) -> str:
    """Who built a level, as markup, in the space one line can hold.

    At most CREDIT_MAX names are listed. Past that it reads "HOST & N more"
    and the whole crew sits in a tooltip, shown on hover and on keyboard focus.

    tip_id decides how the tooltip is exposed. Given one, the summary is a
    real <button> that the tooltip describes, so keyboard and touch users can
    reach the names. Without one the summary sits inside a link (the home
    list) where a nested control is invalid and a tooltip would otherwise
    become part of the link's name, so the names are hidden from assistive
    tech there; the level page they lead to has the full roster.
    """
    names = [str(c) for c in (creators or []) if str(c).strip()]
    if not names:
        return DASH
    if len(names) <= CREDIT_MAX:
        return esc(", ".join(names))
    # host may be one name or a list of co-hosts; those credited lead.
    hosts = [host] if isinstance(host, str) else list(host or [])
    lead = [h for h in (str(x).strip() for x in hosts) if h in names] or names[:1]
    others = len(names) - len(lead)
    summary = f"{esc(', '.join(lead))} &amp; {others} more"
    crew = esc(", ".join(names))
    head = f'<span class="credit__head">All {len(names)} credited</span>'
    if tip_id:
        return (
            f'<button type="button" class="credit" aria-describedby="{esc(tip_id)}">'
            f'<span class="credit__lead">{summary}</span>'
            f'<span class="credit__all" id="{esc(tip_id)}" role="tooltip">'
            f"{head}{crew}</span></button>"
        )
    return (
        f'<span class="credit"><span class="credit__lead">{summary}</span>'
        f'<span class="credit__all" aria-hidden="true">{head}{crew}</span></span>'
    )


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


SOURCE_NAMES = {
    "geometrydash.wiki.gg": "Official Geometry Dash Wiki",
    "geometry-dash-fan.fandom.com": "Geometry Dash Fan Wiki",
    "geometry-dash-user-levels.fandom.com": "GD User Levels Wiki",
    "pointercrate.com": "Pointercrate",
    "gdbrowser.com": "GDBrowser",
    "demonlist.org": "demonlist.org",
}


def sources_html(facts: dict) -> str:
    """Named, not raw. A column of full URLs is unreadable and tells the
    reader less than the name of the site does."""
    sources = (facts or {}).get("sources") or []
    if not sources:
        return ""
    items = []
    for url in sources:
        host = url.split("//", 1)[-1].split("/", 1)[0]
        name = SOURCE_NAMES.get(host, host)
        items.append(
            f'<li><a href="{esc(url)}" rel="nofollow noopener" target="_blank">'
            f'<span class="sources__name">{esc(name)}</span>'
            f'<span class="sources__url">{esc(url)}</span></a></li>'
        )
    return (
        '<section class="sources" aria-labelledby="sources-h">'
        '<h2 id="sources-h" class="eyebrow">Sources</h2>'
        f'<ul>{"".join(items)}</ul></section>'
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


def _digits(value) -> int | None:
    """The number inside a formatted fact. "220,134" is stored as written
    because that is how it is displayed; charting it needs the integer."""
    if not value:
        return None
    only = re.sub(r"[^0-9]", "", str(value))
    return int(only) if only else None


def numbers_html(levels: list[dict]) -> str:
    """The whole list as data, in the two facts that carry it.

    Crew size is the only figure known for every single level, which is why
    it leads: thirty bars, no gaps, from one person to twenty-nine. Object
    counts run second and are known for twenty-three, so seven bars are
    drawn as voids rather than dropped. Hiding them would make the chart
    look complete and quietly overstate what is actually known, which is the
    opposite of what every other page here does with a missing fact.
    """
    ordered = sorted(levels, key=lambda lv: lv["rank"])

    def chart(key, getter, heading, note, unit):
        values = [(lv, getter(lv)) for lv in ordered]
        known = [v for _, v in values if v]
        if not known:
            return ""
        top = max(known)
        bars = []
        for lv, value in values:
            pct = (value / top) * 100 if value else 0
            cls = "nchart__bar" if value else "nchart__bar nchart__bar--nil"
            reading = f"{value:,} {unit}" if value else "not known"
            bars.append(
                f'<li class="{cls}" style="{palette_style(lv)}">'
                f'<span class="nchart__fill" style="height:{pct:.1f}%"></span>'
                f'<span class="nchart__tip">{esc(lv["name"])} &mdash; '
                f"{esc(reading)}</span></li>"
            )
        missing = len(values) - len(known)
        caveat = (f"{missing} of {len(values)} not known, shown as gaps."
                  if missing else f"Known for all {len(values)}.")
        return (
            f'<figure class="nchart" data-chart="{key}">'
            f'<figcaption class="nchart__head"><span class="nchart__title">'
            f"{heading}</span> <span class=\"nchart__note\">{note}</span>"
            f'</figcaption>'
            f'<ol class="nchart__bars">{"".join(bars)}</ol>'
            f'<p class="nchart__axis"><span>#{ordered[0]["rank"]}</span>'
            f'<span class="nchart__caveat">{caveat}</span>'
            f'<span>#{ordered[-1]["rank"]}</span></p></figure>'
        )

    crew = chart(
        "crew", lambda lv: len((lv.get("facts") or {}).get("creators") or []),
        "Everyone who built it",
        "one bar per level, ordered #1 to #30", "credited")
    objects = chart(
        "objects", lambda lv: _digits((lv.get("facts") or {}).get("objects")),
        "Objects placed", "same order", "objects")
    return crew + objects


def countdown_mark(level: dict) -> str:
    theme = level.get("theme") or {}
    return mark_svg(theme.get("signature"))


# Above this the page counts as light. Every field on the site is either
# near-black or near-white, so the exact threshold does not matter much --
# Nhelv's paper white sits at 0.84 and the darkest fields are under 0.01.
LIGHT_ABOVE = 0.5


def chrome_html(field: str) -> str:
    """Hand the browser's own furniture the page's ground colour.

    theme-color paints the address bar and status bar on a phone, so
    Slaughterhouse arrives with red chrome and Nhelv with white. color-scheme
    is the same fact told to a different consumer: it decides the scrollbar,
    and a dark page with a bright system scrollbar down the side is the one
    piece of the window that gives away that this is a document.

    Both come from --field rather than from an accent. The chrome sits
    against the page's ground, not against its highlights.
    """
    ground = field or "#000000"
    light = relative_luminance(parse_hex(ground)) > LIGHT_ABOVE
    scheme = "light" if light else "dark"
    return (f'<meta name="theme-color" content="{esc(ground)}">'
            f"<style>:root{{color-scheme:{scheme};}}</style>")


TABS = [("/list/", "The List", "list"), ("/", "Games", "games")]


def topnav_html(current: str) -> str:
    """The tabs in the top right of the hero, on the landing page and the game.

    The landing page is the games (most visitors come for them); the ranked list
    has its own page at /list/. Two entries and no more: level pages have their own rank navigation at the
    bottom and need nothing up here. The tab for the page you are on is marked
    with aria-current rather than dropped, so the pair reads the same from
    either side. data-tab lets the Games tab be styled louder than the rest:
    most visitors come for the games.
    """
    links = "".join(
        f'<a class="topnav__link" data-tab="{key}" href="{href}"'
        f'{" aria-current=\"page\"" if key == current else ""}>{label}</a>'
        for href, label, key in TABS
    )
    return f'<nav class="topnav" aria-label="Sections">{links}</nav>'


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
    items = ['<a class="docnav__home" href="/list/">Back to the list</a>']
    for d in docs:
        if d["slug"] == current:
            continue
        items.append(f'<a class="docnav__link" href="/{d["slug"]}/">'
                     f'{d["heading"]}</a>')
    return ('<nav class="docnav" aria-label="Site information">'
            + "".join(items) + "</nav>")


def contact_html(site: dict) -> str | None:
    """How to reach the site's owner, as markup, or None if there is no way.

    An email address and a Discord handle are both accepted; if both are set,
    both are shown. Everything that tells a visitor "ask me to remove it" goes
    through here, so the answer is written down once.
    """
    parts = []
    if site.get("contact"):
        addr = esc(site["contact"])
        parts.append(f'<a href="mailto:{addr}">{addr}</a>')
    if site.get("discord"):
        handle = str(site["discord"]).lstrip("@")
        parts.append(f"Discord <strong>@{esc(handle)}</strong>")
    return " or ".join(parts) if parts else None


def dm_html(site: dict) -> str:
    """The sentence fragment for getting an entry removed.

    "Privately message @bperk on Discord", plus "or email <address>" when an
    address is set. These are the routes the site names and the ones the
    notice asks people to accept. Every place that says how to have an entry
    removed uses this, so it is worded once.
    """
    routes = []
    if site.get("discord"):
        handle = str(site["discord"]).lstrip("@")
        routes.append(f"privately message <strong>@{esc(handle)}</strong> on Discord")
    if site.get("contact"):
        addr = esc(site["contact"])
        routes.append(f'email <a href="mailto:{addr}">{addr}</a>')
    if routes:
        return " or ".join(routes)
    return "contact the site owner"


def social_card_html(site: dict, path: str, alt: str, width: int = 1200, height: int = 630) -> str:
    """The tags that make a shared link show a picture: Open Graph (Discord,
    Facebook, iMessage, most chat apps) and the large Twitter/X card. The
    address has to be absolute, because the crawler reading the page is not
    on this site, so it is built from site.domain rather than relativised."""
    domain = site.get("domain")
    url = f"https://{domain}{path}" if domain else path
    return (
        f'<meta property="og:image" content="{esc(url)}">'
        f'<meta property="og:image:width" content="{width}">'
        f'<meta property="og:image:height" content="{height}">'
        f'<meta property="og:image:alt" content="{esc(alt)}">'
        '<meta name="twitter:card" content="summary_large_image">'
        f'<meta name="twitter:image" content="{esc(url)}">'
        f'<meta name="twitter:image:alt" content="{esc(alt)}">'
    )


def doc_footer_html(site: dict) -> str:
    """The contact line. Says plainly when there is no way to reach anyone,
    rather than inventing one or quietly omitting it."""
    who = contact_html(site)
    if who:
        line = f"Contact: {who}"
    else:
        line = ('<strong class="doc__todo">Contact address not set yet</strong> '
                "&mdash; add one to data/site.json before relying on these "
                "pages.")
    updated = site.get("updated", "")
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
    line = '<span class="player__name">' + esc(song["name"]) + "</span>"
    if artist:
        line += '<span class="player__artist">' + esc(artist) + "</span>"
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
    # A Geometry Dash level can only point at a Newgrounds upload, and those
    # are routinely re-uploaded under the level's own name rather than the
    # track's. Deimos plays SR20DET by Blksmiith from an upload titled
    # "Deimos" by Solkrieg. Naming the track and hiding that would make the
    # link look wrong; naming the upload and hiding the track would credit
    # the wrong artist. Both are stated.
    as_uploaded = ""
    upload = song.get("uploadedAs") or {}
    if upload.get("name"):
        who = f' by {esc(upload["artist"])}' if upload.get("artist") else ""
        as_uploaded = (
            '<p class="player__as">Carried in game as '
            f'<span class="player__as-name">{esc(upload["name"])}</span>'
            f"{who} &mdash; the Newgrounds upload the level points at.</p>"
        )

    return (
        '<section class="player" aria-labelledby="song-h">'
        '<h2 id="song-h" class="eyebrow">Song</h2>'
        f'<p class="player__title">{line}</p>{as_uploaded}{link}</section>'
    )


def ranknav_html(prev: dict | None, nxt: dict | None, total: int = 25) -> str:
    """Previous/next, each carrying the palette of the page it leads to so the
    link previews its destination rather than borrowing the current level's
    colour.

    prev and nxt are neighbours in COUNTDOWN order, so prev is the higher
    rank number. build.py resolves that; this only lays them out.

    total is passed in rather than hardcoded because it was hardcoded, in
    six places, and every one of them still said 25 the moment the list grew.
    """
    parts = ['<nav class="ranknav" aria-label="Rank navigation">']

    def link(lv, direction, css_class):
        return (
            f'<a class="ranknav__link {css_class}" '
            f'href="/levels/{esc(lv["slug"])}/" style="{palette_style(lv)}">'
            f'<span class="ranknav__swatch" aria-hidden="true"></span>'
            f'<span class="ranknav__dir">{direction}</span>'
            f'<span class="ranknav__rank">#{lv["rank"]}</span>'
            f'<span class="ranknav__name">{esc(lv["name"])}</span></a>'
        )

    parts.append(link(prev, "Previous", "ranknav__link--prev") if prev
                 else "<span></span>")
    parts.append(f'<a class="ranknav__home" href="/list/">All {total}</a>')
    parts.append(link(nxt, "Next", "ranknav__link--next") if nxt
                 else "<span></span>")
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
        facts = lv.get("facts") or {}
        creators = facts.get("creators") or lv.get("creators") or []
        by = credit_html(creators, facts.get("host")) if creators else ""
        classes = "countdown__entry"
        if published:
            classes += " countdown__entry--live"
        inner = (
            f'<span class="countdown__chip" aria-hidden="true"></span>'
            f'<span class="countdown__rank" aria-hidden="true">'
            f'{lv["rank"]:02d}</span>'
            f'<span class="countdown__mark" aria-hidden="true">'
            f'{countdown_mark(lv)}</span>'
            f'<span class="countdown__name">{esc(lv["name"])}</span>'
            + (f'<span class="countdown__by">{by}</span>' if by else "")
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


# --- Games: tiles, the strip under the landing hero, the hero's call to play ---

def _gg_art() -> str:
    """A scrolling run of spikes and blocks, a cube mid-jump, a question mark."""
    period = 200
    shapes = []
    for k in range(3):
        o = k * period
        shapes += [
            f'<path d="M{o+18} 170l12-22 12 22z"/>', f'<path d="M{o+42} 170l12-22 12 22z"/>',
            f'<rect x="{o+86}" y="144" width="26" height="26"/>',
            f'<rect x="{o+112}" y="118" width="26" height="52"/>',
            f'<path d="M{o+160} 170l12-22 12 22z"/>',
        ]
    return (
        '<svg viewBox="0 0 400 220" preserveAspectRatio="xMidYMid slice" focusable="false" aria-hidden="true">'
        '<defs><linearGradient id="gga-sky" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#14052b"/><stop offset=".62" stop-color="#420a5c"/>'
        '<stop offset="1" stop-color="#ff2bd6"/></linearGradient></defs>'
        '<rect width="400" height="220" fill="url(#gga-sky)"/>'
        '<circle cx="292" cy="150" r="78" fill="#ff2bd6" opacity=".16"/>'
        '<circle cx="292" cy="150" r="48" fill="#ffd23f" opacity=".14"/>'
        f'<g class="gart-scroll" fill="#07030f" stroke="#21e6ff" stroke-width="1.5">{"".join(shapes)}</g>'
        '<rect y="170" width="400" height="50" fill="#07030f"/>'
        '<rect y="169" width="400" height="2.5" fill="#21e6ff"/>'
        '<g class="gart-bob"><rect x="62" y="118" width="26" height="26" rx="2" fill="#a8ff2e" '
        'stroke="#000" stroke-width="2.5"/><rect x="69" y="125" width="12" height="12" fill="#21e6ff" '
        'stroke="#000" stroke-width="1.5"/></g>'
        '<text x="300" y="128" text-anchor="middle" font-family="Bungee, sans-serif" font-size="96" '
        'fill="#fff" opacity=".92">?</text></svg>'
    )


def _demondle_art() -> str:
    colours = {"g": "#2f9e5b", "y": "#c79a16", "x": "#2a2f3d"}
    rows = ["xxyxxx", "xyxgyx", "gyxggy", "gggggg"]
    cells = []
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            cells.append(f'<rect class="gart-flip" style="--i:{r * 6 + c}" x="{88 + c * 38}" '
                         f'y="{30 + r * 42}" width="32" height="36" rx="4" fill="{colours[ch]}"/>')
    return ('<svg viewBox="0 0 400 220" preserveAspectRatio="xMidYMid slice" focusable="false" aria-hidden="true">'
            '<rect width="400" height="220" fill="#0b1410"/>' + "".join(cells) + '</svg>')


def _names_art() -> str:
    cells = []
    for r in range(7):
        for c in range(10):
            i = r * 10 + c
            cells.append(f'<rect class="gart-fill" style="--i:{(i * 37) % 70}" x="{22 + c * 36}" '
                         f'y="{18 + r * 27}" width="30" height="19" rx="4" fill="#1c2236"/>')
    return ('<svg viewBox="0 0 400 220" preserveAspectRatio="xMidYMid slice" focusable="false" aria-hidden="true">'
            '<rect width="400" height="220" fill="#0a0d18"/>' + "".join(cells) + '</svg>')


GAME_ART = {"gg": _gg_art, "demondle": _demondle_art, "names": _names_art}


def games_tiles_html(cards: list) -> str:
    """One tile per game, in the order data/site.json lists them; the first leads."""
    out = []
    for c in cards:
        art = c.get("art") or ""
        draw = GAME_ART.get(art)
        badge = f'<span class="gtile__badge">{esc(c["badge"])}</span>' if c.get("badge") else ""
        out.append(
            f'<a class="gtile gtile--{esc(art)}" href="{esc(c["href"])}">'
            f'<span class="gtile__art" aria-hidden="true">{draw() if draw else ""}</span>{badge}'
            f'<span class="gtile__body"><span class="gtile__title">{esc(c["title"])}</span>'
            f'<span class="gtile__desc">{esc(c["desc"])}</span>'
            f'<span class="gtile__go" aria-hidden="true">Play</span></span></a>')
    return "".join(out)


def games_band_html(games: dict) -> str:
    """The games, on the landing page, straight after the hero."""
    cards = games.get("cards") or []
    if not cards:
        return ""
    return (
        '<section class="gband page" id="play" aria-labelledby="gband-h">'
        '<div class="gband__head"><h2 id="gband-h" class="gband__title">Play</h2>'
        f'<p class="gband__lede">{esc(games.get("lede") or "")}</p>'
        '</div>'
        f'<div class="gtiles">{games_tiles_html(cards)}</div></section>'
    )


def hero_cta_html(games: dict, href: str = "#play") -> str:
    """A call to play, above the fold on the landing page: down to the games."""
    cards = games.get("cards") or []
    if not cards:
        return ""
    new = next((c for c in cards if c.get("badge")), None)
    small = f"{len(cards)} games" + (f" · new: {esc(new['title'])}" if new else "")
    return (
        f'<a class="herocta" href="{esc(href)}"><span class="herocta__play" aria-hidden="true"></span>'
        '<span class="herocta__text"><span class="herocta__big">Play the games</span>'
        f'<span class="herocta__small">{small}</span></span></a>'
    )
