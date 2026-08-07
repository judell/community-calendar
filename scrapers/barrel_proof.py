#!/usr/bin/env python3
"""
Barrel Proof Lounge scraper - scrapes directly from their website

The 2026 site redesign moved events from server-rendered homepage widget
blocks to an /events/ page whose "Widget for Eventbrite API" FullCalendar
embeds the complete event list as an inline JSON array
(`var wfea_events_N = [...]`) with title/start/end/excerpt/url fields.
This scraper extracts and parses that array.

Usage:
  python barrel_proof.py --output cities/santarosa/barrel_proof.ics
"""

import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
import html as html_module

EVENTS_URL = "https://barrelprooflounge.com/events/"
VENUE_NAME = "Barrel Proof Lounge"
VENUE_ADDRESS = "501 Mendocino Ave, Santa Rosa, CA 95401"

def fetch_page(url):
    """Fetch a URL and return HTML"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=30) as resp:
            return resp.read().decode('utf-8')
    except (HTTPError, URLError) as e:
        print(f"  Error fetching {url}: {e}", file=sys.stderr)
        return None

def parse_events(html):
    """Parse the inline `var wfea_events_N = [...]` JSON on the events page."""
    events = []

    m = re.search(r'var wfea_events_\d+\s*=\s*(\[.*?\]);', html, re.DOTALL)
    if not m:
        print("  Error: no wfea_events array found on events page", file=sys.stderr)
        return events

    try:
        items = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        print(f"  Error: failed to parse wfea_events JSON: {e}", file=sys.stderr)
        return events

    for item in items:
        title = html_module.unescape((item.get('title') or '').strip())
        start_str = item.get('start') or ''
        if not title or not start_str:
            continue

        try:
            start_dt = datetime.fromisoformat(start_str)
        except ValueError:
            print(f"  Warning: Could not parse date for {title}: {start_str}", file=sys.stderr)
            continue

        end_dt = None
        end_str = item.get('end') or ''
        if end_str:
            try:
                end_dt = datetime.fromisoformat(end_str)
            except ValueError:
                pass
        if end_dt is None or end_dt < start_dt:
            end_dt = start_dt + timedelta(hours=2)

        desc = html_module.unescape((item.get('excerpt') or '').strip())
        url = item.get('url') or EVENTS_URL

        events.append({
            'title': title,
            'start': start_dt,
            'end': end_dt,
            'description': desc,
            'url': url
        })

    return events

def event_to_ics(event):
    """Convert event dict to ICS VEVENT"""
    title = event['title'].replace(',', '\\,').replace(';', '\\;')
    desc = event['description'].replace('\n', '\\n').replace(',', '\\,').replace(';', '\\;')
    desc = desc[:500] + '...' if len(desc) > 500 else desc
    
    uid = f"barrelproof-{event['start'].strftime('%Y%m%d%H%M')}-{hash(event['title']) % 100000}"
    
    lines = [
        'BEGIN:VEVENT',
        f'UID:{uid}@barrelprooflounge.com',
        f'DTSTART:{event["start"].strftime("%Y%m%dT%H%M%S")}',
        f'DTEND:{event["end"].strftime("%Y%m%dT%H%M%S")}',
        f'SUMMARY:{title}',
        f'LOCATION:{VENUE_NAME}\\, {VENUE_ADDRESS}',
        f'X-SOURCE:{VENUE_NAME}',
    ]

    if desc:
        lines.append(f'DESCRIPTION:{desc}')

    lines.extend([
        f'URL:{event["url"]}',
        'END:VEVENT'
    ])
    return '\n'.join(lines)

def main():
    parser = argparse.ArgumentParser(description='Scrape Barrel Proof Lounge events')
    parser.add_argument('--output', '-o', help='Output ICS file')
    args = parser.parse_args()
    
    print(f"Fetching: {EVENTS_URL}", file=sys.stderr)
    html = fetch_page(EVENTS_URL)
    if not html:
        print("Failed to fetch events page", file=sys.stderr)
        sys.exit(1)
    
    events = parse_events(html)
    print(f"Found {len(events)} events", file=sys.stderr)
    
    for e in events:
        print(f"  {e['start'].strftime('%m/%d %I:%M%p')} - {e['title'][:60]}", file=sys.stderr)
    
    ics_events = [event_to_ics(e) for e in events]
    
    ics_content = '\n'.join([
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//Community Calendar//Barrel Proof Lounge Scraper//EN',
        'X-WR-CALNAME:Barrel Proof Lounge',
        *ics_events,
        'END:VCALENDAR'
    ])
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(ics_content)
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(ics_content)

if __name__ == '__main__':
    main()
