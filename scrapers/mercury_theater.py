#!/usr/bin/env python3
"""
Mercury Theater Petaluma - scrapes events via Squarespace JSON API

Mercury Theater is at 3333 Petaluma Blvd N (the former Cinnabar Theater space).
Their site is Squarespace, which exposes a JSON API at ?format=json-pretty.
"""

import json
import sys
import hashlib
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

EVENTS_URL = "https://www.mercurytheater.org/mercury-theater-calendar?format=json-pretty"
VENUE_NAME = "Mercury Theater"
VENUE_ADDRESS = "3333 Petaluma Blvd N, Petaluma, CA 94952"

def fetch_json(url):
    """Fetch URL and parse JSON response."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; CommunityCalendar/1.0)',
        'Accept': 'application/json',
    }
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except (HTTPError, URLError, json.JSONDecodeError) as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        return None

def parse_events(data):
    """Parse Squarespace JSON into event dicts."""
    events = []
    upcoming = data.get('upcoming', data.get('items', []))

    for item in upcoming:
        title = item.get('title', 'Untitled')
        start_ms = item.get('startDate')
        end_ms = item.get('endDate')
        if not start_ms:
            continue

        start_dt = datetime.fromtimestamp(start_ms / 1000, tz=timezone.utc)
        end_dt = datetime.fromtimestamp(end_ms / 1000, tz=timezone.utc) if end_ms else None

        # Extract plain text from HTML body
        body = item.get('body', '') or ''
        # Strip HTML tags for description
        import re
        desc = re.sub(r'<[^>]+>', ' ', body).strip()
        desc = re.sub(r'\s+', ' ', desc)[:500]

        location = item.get('location', {})
        loc_str = location.get('addressLine1', VENUE_ADDRESS) if isinstance(location, dict) else VENUE_ADDRESS

        full_url = item.get('fullUrl', '')
        if full_url and not full_url.startswith('http'):
            full_url = f"https://www.mercurytheater.org{full_url}"

        events.append({
            'title': title,
            'start': start_dt,
            'end': end_dt,
            'description': desc,
            'location': f"{VENUE_NAME}, {loc_str}",
            'url': full_url,
        })

    return events

def events_to_ics(events):
    """Convert events to ICS format."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Community Calendar//Mercury Theater Scraper//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Mercury Theater Petaluma",
    ]

    for event in events:
        uid = hashlib.md5(f"{event['title']}{event['start'].isoformat()}".encode()).hexdigest()
        dtstart = event['start'].strftime('%Y%m%dT%H%M%SZ')
        if event['end']:
            dtend = event['end'].strftime('%Y%m%dT%H%M%SZ')
        else:
            dtend = dtstart

        desc = event['description'].replace('\n', '\\n').replace(',', '\\,').replace(';', '\\;')
        summary = event['title'].replace(',', '\\,')
        location = event['location'].replace(',', '\\,')

        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{uid}@mercury-theater.community-calendar")
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
    parser = argparse.ArgumentParser(description='Scrape Mercury Theater Petaluma events')
    parser.add_argument('--json', action='store_true', help='Output JSON instead of ICS')
    args = parser.parse_args()

    print("Fetching Mercury Theater events...", file=sys.stderr)
    data = fetch_json(EVENTS_URL)
    if not data:
        print("Failed to fetch events", file=sys.stderr)
        return

    events = parse_events(data)
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
