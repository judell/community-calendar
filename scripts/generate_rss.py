#!/usr/bin/env python3
"""Generate per-city RSS feeds for GitHub Pages.

Two feeds per city, written to rss/:
  rss/<city>-full.xml   — every upcoming event (next 90 days), sorted by start
  rss/<city>-latest.xml — newly discovered events (first seen this build)

State model: the previous build's committed rss/<city>-full.xml lists every
event UID known then, so "new" = current UIDs minus the previous full feed's
GUIDs. The previous -latest.xml supplies pubDates for items still in the
window, so an item keeps its first-seen timestamp across builds. No storage
beyond the feeds themselves.

Usage (run after ics_to_json.py, before the metadata commit):
    python scripts/generate_rss.py <city>
"""

import argparse
import hashlib
import html
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
SITE_BASE = "https://judell.github.io/community-calendar"
FULL_WINDOW_DAYS = 90
LATEST_MAX_ITEMS = 100


def parse_dt(value):
    """Parse an events.json start_time into an aware datetime, or None."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def event_guid(ev):
    uid = ev.get('source_uid')
    if uid:
        return uid
    basis = f"{ev.get('title', '')}|{ev.get('start_time', '')}"
    return hashlib.md5(basis.encode('utf-8')).hexdigest()


def esc(text):
    return html.escape(text or '', quote=False)


def render_item(ev, guid, pub_dt, app_link, desc_cap=1000):
    start = parse_dt(ev.get('start_time'))
    datestr = start.strftime('%a %b %-d, %-I:%M %p') if start and not ev.get('all_day') \
        else (start.strftime('%a %b %-d') if start else '')
    title_bits = [ev.get('title', 'Untitled')]
    if datestr:
        title_bits.append(datestr)
    loc = (ev.get('location') or '').split(',')[0].strip()
    if loc:
        title_bits.append(loc)
    desc = (ev.get('description') or '').strip()
    source = ev.get('source') or ''
    if source:
        desc = f"{desc}\n\nSource: {source}" if desc else f"Source: {source}"
    link = ev.get('url') or app_link
    return (
        "    <item>\n"
        f"      <title>{esc(' — '.join(title_bits))}</title>\n"
        f"      <link>{esc(link)}</link>\n"
        f"      <guid isPermaLink=\"false\">{esc(guid)}</guid>\n"
        f"      <pubDate>{format_datetime(pub_dt)}</pubDate>\n"
        f"      <description>{esc(desc[:desc_cap])}</description>\n"
        "    </item>\n"
    )


def render_feed(title, description, app_link, self_url, items):
    now = format_datetime(datetime.now(timezone.utc))
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
        '  <channel>\n'
        f'    <title>{esc(title)}</title>\n'
        f'    <link>{esc(app_link)}</link>\n'
        f'    <atom:link href="{esc(self_url)}" rel="self" type="application/rss+xml"/>\n'
        f'    <description>{esc(description)}</description>\n'
        f'    <lastBuildDate>{now}</lastBuildDate>\n'
        + ''.join(items) +
        '  </channel>\n'
        '</rss>\n'
    )


def read_prev_feed(path):
    """Return {guid: pubDate-string} from an existing feed, or {}."""
    if not path.exists():
        return {}
    text = path.read_text(encoding='utf-8', errors='replace')
    out = {}
    for m in re.finditer(
            r'<guid[^>]*>([^<]+)</guid>\s*<pubDate>([^<]+)</pubDate>', text):
        out[html.unescape(m.group(1))] = m.group(2)
    return out


def main():
    parser = argparse.ArgumentParser(description='Generate per-city RSS feeds')
    parser.add_argument('city')
    parser.add_argument('--events', help='Path to events.json (default cities/<city>/events.json)')
    parser.add_argument('--outdir', default=str(ROOT / 'rss'))
    args = parser.parse_args()

    events_path = Path(args.events) if args.events else ROOT / 'cities' / args.city / 'events.json'
    if not events_path.exists():
        print(f"generate_rss: {events_path} not found, skipping {args.city}")
        return 0

    events = json.loads(events_path.read_text())
    now = datetime.now(timezone.utc)
    horizon = now + timedelta(days=FULL_WINDOW_DAYS)

    upcoming = []
    for ev in events:
        start = parse_dt(ev.get('start_time'))
        if start and now - timedelta(hours=12) <= start <= horizon:
            upcoming.append((start, ev))
    upcoming.sort(key=lambda pair: pair[0])

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    full_path = outdir / f"{args.city}-full.xml"
    latest_path = outdir / f"{args.city}-latest.xml"
    app_link = f"{SITE_BASE}/xmlui/index.html?city={args.city}"
    city_title = args.city.capitalize()

    prev_full_guids = set(read_prev_feed(full_path))
    prev_latest = read_prev_feed(latest_path)

    # Full feed: every upcoming event, pubDate = event start.
    full_items = [render_item(ev, event_guid(ev), start, app_link, desc_cap=300)
                  for start, ev in upcoming]
    full_path.write_text(render_feed(
        f"{city_title} Community Calendar — all upcoming events",
        f"Every event in the next {FULL_WINDOW_DAYS} days, regenerated daily.",
        app_link, f"{SITE_BASE}/rss/{full_path.name}", full_items))

    # Latest feed: events not present in the previous build's full feed,
    # plus carried-over recent items that are still upcoming.
    latest = []
    current_guids = set()
    for start, ev in upcoming:
        guid = event_guid(ev)
        current_guids.add(guid)
        if guid in prev_latest:
            pub = parse_dt(None)  # placeholder; keep original string via re-render below
            latest.append((prev_latest[guid], start, ev, guid, True))
        elif prev_full_guids and guid not in prev_full_guids:
            latest.append((format_datetime(now), start, ev, guid, False))
        elif not prev_full_guids:
            # First run: no memory — seed with the soonest events, stamped now.
            latest.append((format_datetime(now), start, ev, guid, False))

    def pub_key(entry):
        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(entry[0])
        except Exception:
            return now
    latest.sort(key=pub_key, reverse=True)
    latest = latest[:LATEST_MAX_ITEMS]

    latest_items = []
    for pub_str, start, ev, guid, _carried in latest:
        item = render_item(ev, guid, now, app_link)
        item = re.sub(r'<pubDate>[^<]+</pubDate>', f'<pubDate>{pub_str}</pubDate>', item)
        latest_items.append(item)
    latest_path.write_text(render_feed(
        f"{city_title} Community Calendar — new events",
        "Events newly added to the calendar, most recent first.",
        app_link, f"{SITE_BASE}/rss/{latest_path.name}", latest_items))

    print(f"generate_rss: {args.city}: full={len(full_items)} latest={len(latest_items)}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
