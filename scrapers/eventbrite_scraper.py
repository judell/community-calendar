#!/usr/bin/env python3
"""
Eventbrite scraper - extracts event data from individual event pages
Uses JSON-LD structured data embedded in pages
"""

import json
import re
import sys
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

def fetch_event(url):
    """Fetch and parse a single Eventbrite event page"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8')
    except (HTTPError, URLError) as e:
        print(f"  Error fetching {url}: {e}", file=sys.stderr)
        return None
    
    # Extract JSON-LD
    pattern = r'<script type="application/ld\+json">([^<]+)</script>'
    matches = re.findall(pattern, html)
    
    for match in matches:
        try:
            data = json.loads(match)
            if isinstance(data, dict) and data.get('@type') in ['Event', 'Festival', 'MusicEvent', 'SocialEvent']:
                return data
        except json.JSONDecodeError:
            continue
    return None

def event_to_ics(event):
    """Convert event dict to ICS VEVENT"""
    name = event.get('name', 'Untitled')
    desc = event.get('description', '')
    url = event.get('url', '')
    start = event.get('startDate', '')
    end = event.get('endDate', '')
    
    # Location
    loc = event.get('location', {})
    if isinstance(loc, dict):
        place_name = loc.get('name', '')
        addr = loc.get('address', {})
        if isinstance(addr, dict):
            street = addr.get('streetAddress', '')
            city = addr.get('addressLocality', '')
            state = addr.get('addressRegion', '')
            location = f"{place_name}, {street}, {city}, {state}".strip(', ')
        else:
            location = place_name
    else:
        location = str(loc)
    
    # Format dates for ICS
    def to_ics_date(iso_date):
        if not iso_date:
            return ''
        # Parse ISO 8601 with timezone
        try:
            dt = datetime.fromisoformat(iso_date.replace('Z', '+00:00'))
            return dt.strftime('%Y%m%dT%H%M%S')
        except:
            return ''
    
    dtstart = to_ics_date(start)
    dtend = to_ics_date(end)
    
    if not dtstart:
        return None
    
    # Generate UID from URL
    uid = url.replace('https://', '').replace('http://', '').replace('/', '-')
    
    # Escape ICS special chars
    def ics_escape(s):
        return s.replace('\\', '\\\\').replace(',', '\\,').replace(';', '\\;').replace('\n', '\\n')
    
    vevent = f"""BEGIN:VEVENT
UID:{uid}
DTSTART:{dtstart}
DTEND:{dtend if dtend else dtstart}
SUMMARY:{ics_escape(name)}
DESCRIPTION:{ics_escape(desc[:500])}
LOCATION:{ics_escape(location)}
URL:{url}
END:VEVENT"""
    return vevent

if __name__ == '__main__':
    # Read URLs from stdin or args
    if len(sys.argv) > 1:
        urls = sys.argv[1:]
    else:
        urls = [line.strip() for line in sys.stdin if line.strip()]
    
    events = []
    for url in urls:
        if not url.startswith('http'):
            url = 'https://www.eventbrite.com/e/' + url
        print(f"Fetching: {url}", file=sys.stderr)
        event = fetch_event(url)
        if event:
            # Check if in Santa Rosa area
            loc = event.get('location', {})
            addr = loc.get('address', {}) if isinstance(loc, dict) else {}
            city = addr.get('addressLocality', '') if isinstance(addr, dict) else ''
            
            if city.lower() in ['santa rosa', 'petaluma', 'sebastopol', 'rohnert park', 'cotati', 'sonoma', 'healdsburg', 'windsor']:
                events.append(event)
                print(f"  ✓ {event.get('name')} @ {city}", file=sys.stderr)
            else:
                print(f"  ✗ Skipped (location: {city})", file=sys.stderr)
    
    # Output ICS
    print("BEGIN:VCALENDAR")
    print("VERSION:2.0")
    print("PRODID:-//Community Calendar//Eventbrite Scraper//EN")
    print("X-WR-CALNAME:Eventbrite Santa Rosa")
    
    for event in events:
        vevent = event_to_ics(event)
        if vevent:
            print(vevent)
    
    print("END:VCALENDAR")
    
    print(f"\nTotal: {len(events)} local events", file=sys.stderr)
