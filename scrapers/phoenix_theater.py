#!/usr/bin/env python3
"""
Phoenix Theater Petaluma - scrapes events via Eventbrite search

The Phoenix Theater is a legendary all-ages punk venue at 201 Washington St, Petaluma.
Events are ticketed via Eventbrite.
"""

import re
import json
import sys
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
import hashlib

def fetch_page(url):
    """Fetch a URL and return HTML"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=15) as resp:
            return resp.read().decode('utf-8')
    except (HTTPError, URLError) as e:
        print(f"  Error: {e}", file=sys.stderr)
        return None

def get_phoenix_event_urls():
    """Get Phoenix Theater event URLs from Eventbrite search"""
    url = "https://www.eventbrite.com/d/ca--petaluma/phoenix-theater/"
    html = fetch_page(url)
    if not html:
        return []
    
    pattern = r'eventbrite\.com/e/([^"?\s]+)'
    matches = re.findall(pattern, html)
    urls = list(set(f"https://www.eventbrite.com/e/{m}" for m in matches))
    
    # Filter to only Phoenix Theater Petaluma events
    phoenix_urls = []
    for event_url in urls:
        event_html = fetch_page(event_url)
        if event_html and '201 Washington' in event_html and 'Petaluma' in event_html:
            phoenix_urls.append(event_url)
    
    return phoenix_urls

def fetch_event(url):
    """Fetch and parse a single Eventbrite event page"""
    html = fetch_page(url)
    if not html:
        return None
    
    pattern = r'<script type="application/ld\+json">([^<]+)</script>'
    matches = re.findall(pattern, html)
    
    for match in matches:
        try:
            data = json.loads(match)
            if isinstance(data, dict) and data.get('@type') in ['Event', 'MusicEvent', 'SocialEvent']:
                return data
        except json.JSONDecodeError:
            continue
    return None

def events_to_ics(events):
    """Convert events to ICS format"""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Community Calendar//Phoenix Theater Scraper//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Phoenix Theater Petaluma",
    ]
    
    for event in events:
        name = event.get('name', 'Untitled')
        desc = event.get('description', '')
        url = event.get('url', '')
        start = event.get('startDate', '')
        end = event.get('endDate', start)
        
        # Parse datetime - Eventbrite uses ISO 8601
        try:
            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
            dtstart = start_dt.strftime('%Y%m%dT%H%M%S')
            dtend = end_dt.strftime('%Y%m%dT%H%M%S')
        except:
            continue
        
        # Location
        loc = event.get('location', {})
        loc_name = loc.get('name', 'Phoenix Theater')
        loc_addr = loc.get('address', {})
        street = loc_addr.get('streetAddress', '201 Washington St')
        city = loc_addr.get('addressLocality', 'Petaluma')
        state = loc_addr.get('addressRegion', 'CA')
        location = f"{loc_name}, {street}, {city}, {state}"
        
        uid = hashlib.md5(f"{name}{start}".encode()).hexdigest()
        
        # Escape special characters
        desc = desc.replace('\n', '\\n').replace(',', '\\,').replace(';', '\\;')
        name = name.replace(',', '\\,')
        location = location.replace(',', '\\,')
        
        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{uid}@phoenix-theater.community-calendar")
        lines.append(f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}")
        lines.append(f"DTSTART:{dtstart}")
        lines.append(f"DTEND:{dtend}")
        lines.append(f"SUMMARY:{name}")
        lines.append(f"LOCATION:{location}")
        lines.append(f"DESCRIPTION:{desc[:500]}")
        if url:
            lines.append(f"URL:{url}")
        lines.append("END:VEVENT")
    
    lines.append("END:VCALENDAR")
    return '\n'.join(lines)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Scrape Phoenix Theater Petaluma events')
    parser.add_argument('--json', action='store_true', help='Output JSON instead of ICS')
    args = parser.parse_args()
    
    print("Searching for Phoenix Theater events...", file=sys.stderr)
    
    # Get event URLs
    url = "https://www.eventbrite.com/d/ca--petaluma/phoenix-theater/"
    html = fetch_page(url)
    if not html:
        print("Failed to fetch Eventbrite search page", file=sys.stderr)
        return
    
    pattern = r'eventbrite\.com/e/([^"?\s]+)'
    matches = re.findall(pattern, html)
    urls = list(set(f"https://www.eventbrite.com/e/{m}" for m in matches))
    print(f"Found {len(urls)} potential events", file=sys.stderr)
    
    # Fetch each event and filter to Phoenix Theater
    events = []
    for i, event_url in enumerate(urls):
        print(f"[{i+1}/{len(urls)}] {event_url.split('/')[-1][:50]}...", file=sys.stderr)
        event = fetch_event(event_url)
        if event:
            loc = event.get('location', {})
            loc_name = loc.get('name', '')
            loc_addr = loc.get('address', {})
            street = loc_addr.get('streetAddress', '')
            
            # Check if it's at Phoenix Theater
            if 'phoenix' in loc_name.lower() or '201 washington' in street.lower():
                events.append(event)
                print(f"  ✓ Phoenix Theater", file=sys.stderr)
            else:
                print(f"  ✗ {loc_name}", file=sys.stderr)
    
    print(f"\nTotal: {len(events)} Phoenix Theater events", file=sys.stderr)
    
    if args.json:
        print(json.dumps(events, indent=2))
    else:
        print(events_to_ics(events))

if __name__ == '__main__':
    main()
