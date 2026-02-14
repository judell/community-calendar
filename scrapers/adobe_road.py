#!/usr/bin/env python3
"""
Adobe Road Winery Petaluma - scrapes events via JSON-LD structured data

Adobe Road Winery uses WordPress with Modern Events Calendar (MEC).
The /mec-category/petaluma-events/ page has JSON-LD Event schema embedded.
"""

import html as html_mod
import json
import re
import sys
import hashlib
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

EVENTS_URL = "https://adoberoadwines.com/mec-category/petaluma-events/"
VENUE_NAME = "Adobe Road Winery"
VENUE_ADDRESS = "1995 S McDowell Blvd, Petaluma, CA 94954"

def fetch_page(url):
    """Fetch a URL and return HTML."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; CommunityCalendar/1.0)',
    }
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=15) as resp:
            return resp.read().decode('utf-8')
    except (HTTPError, URLError) as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        return None

def fix_json_description(raw):
    """Fix malformed JSON-LD where description contains unescaped HTML with quotes."""
    # Find "description": "..." and escape the inner HTML quotes
    def escape_desc(m):
        prefix = m.group(1)  # "description": "
        content = m.group(2)
        suffix = m.group(3)  # ",  or "} etc.
        # Escape unescaped quotes inside the description value
        fixed = content.replace('"', '\\"')
        return f'{prefix}{fixed}{suffix}'

    # Match "description": "<content-with-html>", or "description": "<content>"}
    # The content may span one line (MEC puts it all on one line)
    pattern = r'("description":\s*")(.+?)("\s*[,}])'
    return re.sub(pattern, escape_desc, raw)

def extract_jsonld_events(html):
    """Extract JSON-LD Event objects from HTML."""
    pattern = r'<script\s+type="application/ld\+json"[^>]*>(.*?)</script>'
    matches = re.findall(pattern, html, re.DOTALL)

    events = []
    for match in matches:
        try:
            data = json.loads(match)
        except json.JSONDecodeError:
            # Try fixing malformed description fields (common in MEC plugin)
            try:
                fixed = fix_json_description(match)
                data = json.loads(fixed)
            except json.JSONDecodeError:
                continue

        # Handle both single objects and arrays
        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict) and item.get('@type') == 'Event':
                events.append(item)

    return events

def parse_events(jsonld_events):
    """Parse JSON-LD events into our format."""
    events = []
    now = datetime.now(timezone.utc)

    for item in jsonld_events:
        title = html_mod.unescape(item.get('name', 'Untitled'))
        start_str = item.get('startDate', '')
        end_str = item.get('endDate', '')

        if not start_str:
            continue

        try:
            start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        except ValueError:
            print(f"  Skipping {title}: bad date {start_str}", file=sys.stderr)
            continue

        # Skip past events
        if start_dt.replace(tzinfo=timezone.utc if start_dt.tzinfo is None else start_dt.tzinfo) < now:
            continue

        end_dt = None
        if end_str:
            try:
                end_dt = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
            except ValueError:
                pass

        desc = item.get('description', '') or ''
        desc = re.sub(r'<[^>]+>', ' ', desc).strip()
        desc = re.sub(r'\s+', ' ', desc)[:500]

        url = item.get('url', '')

        # Location from JSON-LD or fallback
        loc = item.get('location', {})
        if isinstance(loc, dict):
            loc_name = loc.get('name', VENUE_NAME)
            addr = loc.get('address', {})
            if isinstance(addr, dict):
                street = addr.get('streetAddress', '')
                city = addr.get('addressLocality', 'Petaluma')
                state = addr.get('addressRegion', 'CA')
                loc_str = f"{loc_name}, {street}, {city}, {state}" if street else f"{loc_name}, {VENUE_ADDRESS}"
            else:
                loc_str = f"{loc_name}, {VENUE_ADDRESS}"
        else:
            loc_str = f"{VENUE_NAME}, {VENUE_ADDRESS}"

        events.append({
            'title': title,
            'start': start_dt,
            'end': end_dt,
            'description': desc,
            'location': loc_str,
            'url': url,
        })

    return events

def events_to_ics(events):
    """Convert events to ICS format."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Community Calendar//Adobe Road Scraper//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Adobe Road Winery Petaluma",
    ]

    for event in events:
        uid = hashlib.md5(f"{event['title']}{event['start'].isoformat()}".encode()).hexdigest()

        # Format dates - use local time (no Z suffix) if no timezone
        if event['start'].tzinfo:
            dtstart = event['start'].strftime('%Y%m%dT%H%M%SZ')
        else:
            dtstart = event['start'].strftime('%Y%m%dT%H%M%S')

        if event['end']:
            if event['end'].tzinfo:
                dtend = event['end'].strftime('%Y%m%dT%H%M%SZ')
            else:
                dtend = event['end'].strftime('%Y%m%dT%H%M%S')
        else:
            dtend = dtstart

        desc = event['description'].replace('\n', '\\n').replace(',', '\\,').replace(';', '\\;')
        summary = event['title'].replace(',', '\\,')
        location = event['location'].replace(',', '\\,')

        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{uid}@adobe-road.community-calendar")
        lines.append(f"DTSTAMP:{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}")
        lines.append(f"DTSTART:{dtstart}")
        lines.append(f"DTEND:{dtend}")
        lines.append(f"SUMMARY:{summary}")
        lines.append(f"LOCATION:{location}")
        lines.append(f"DESCRIPTION:{desc}")
        if event['url']:
            lines.append(f"URL:{event['url']}")
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    return '\n'.join(lines)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Scrape Adobe Road Winery Petaluma events')
    parser.add_argument('--json', action='store_true', help='Output JSON instead of ICS')
    args = parser.parse_args()

    print("Fetching Adobe Road Winery events...", file=sys.stderr)
    html = fetch_page(EVENTS_URL)
    if not html:
        print("Failed to fetch events page", file=sys.stderr)
        return

    jsonld_events = extract_jsonld_events(html)
    print(f"Found {len(jsonld_events)} JSON-LD events on page", file=sys.stderr)

    events = parse_events(jsonld_events)
    print(f"Found {len(events)} upcoming events", file=sys.stderr)

    if args.json:
        out = []
        for e in events:
            out.append({
                'title': e['title'],
                'start': e['start'].isoformat(),
                'end': e['end'].isoformat() if e['end'] else None,
                'description': e['description'],
                'location': e['location'],
                'url': e['url'],
            })
        print(json.dumps(out, indent=2))
    else:
        print(events_to_ics(events))

if __name__ == '__main__':
    main()
