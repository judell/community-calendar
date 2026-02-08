#!/usr/bin/env python3
"""
Eventbrite scraper - extracts event data from individual event pages
Uses JSON-LD structured data embedded in pages

Usage:
  # Scrape Santa Rosa events for next 2 months:
  python eventbrite_scraper.py --location "ca--santa-rosa" --months 2
  
  # Or pipe URLs directly:
  echo "https://eventbrite.com/e/some-event" | python eventbrite_scraper.py --stdin
"""

import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

# Cities to include (lowercase)
SONOMA_COUNTY_CITIES = [
    'santa rosa', 'petaluma', 'sebastopol', 'rohnert park', 
    'cotati', 'sonoma', 'healdsburg', 'windsor'
]

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

def get_event_urls(location, months_ahead=2):
    """Get event URLs from Eventbrite location page with date filter"""
    end_date = (datetime.now() + timedelta(days=months_ahead*30)).strftime('%Y-%m-%d')
    url = f"https://www.eventbrite.com/d/{location}/all-events/?end_date={end_date}"
    print(f"Fetching: {url}", file=sys.stderr)
    
    html = fetch_page(url)
    if not html:
        return []
    
    pattern = r'eventbrite\.com/e/([^"?\s]+)'
    matches = re.findall(pattern, html)
    urls = list(set(f"https://www.eventbrite.com/e/{m}" for m in matches))
    print(f"Found {len(urls)} events", file=sys.stderr)
    return urls

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
    
    def to_ics_date(iso_date):
        if not iso_date:
            return ''
        try:
            dt = datetime.fromisoformat(iso_date.replace('Z', '+00:00'))
            return dt.strftime('%Y%m%dT%H%M%S')
        except:
            return ''
    
    dtstart = to_ics_date(start)
    dtend = to_ics_date(end)
    
    if not dtstart:
        return None
    
    uid = url.replace('https://', '').replace('http://', '').replace('/', '-')
    
    def ics_escape(s):
        return s.replace('\\', '\\\\').replace(',', '\\,').replace(';', '\\;').replace('\n', '\\n')
    
    return f"""BEGIN:VEVENT
UID:{uid}
DTSTART:{dtstart}
DTEND:{dtend if dtend else dtstart}
SUMMARY:{ics_escape(name)}
DESCRIPTION:{ics_escape(desc[:500])}
LOCATION:{ics_escape(location)}
URL:{url}
END:VEVENT"""

def main():
    parser = argparse.ArgumentParser(description='Scrape Eventbrite events')
    parser.add_argument('--location', '-l', default='ca--santa-rosa',
                        help='Eventbrite location slug (default: ca--santa-rosa)')
    parser.add_argument('--months', '-m', type=int, default=2,
                        help='Months ahead to fetch (default: 2)')
    parser.add_argument('--cities', '-c', nargs='+', default=SONOMA_COUNTY_CITIES,
                        help='Cities to include (lowercase)')
    parser.add_argument('--stdin', action='store_true',
                        help='Read URLs from stdin instead of fetching from location page')
    args = parser.parse_args()
    
    if args.stdin:
        urls = [line.strip() for line in sys.stdin if line.strip()]
        urls = [u if u.startswith('http') else f'https://www.eventbrite.com/e/{u}' for u in urls]
    else:
        urls = get_event_urls(args.location, args.months)
    
    events = []
    for i, url in enumerate(urls):
        print(f"[{i+1}/{len(urls)}] {url.split('/')[-1][:50]}", file=sys.stderr)
        event = fetch_event(url)
        if event:
            loc = event.get('location', {})
            addr = loc.get('address', {}) if isinstance(loc, dict) else {}
            city = addr.get('addressLocality', '') if isinstance(addr, dict) else ''
            
            if city.lower() in args.cities:
                events.append(event)
                print(f"  ✓ {city}", file=sys.stderr)
            else:
                print(f"  ✗ {city or 'unknown'}", file=sys.stderr)
    
    # Output ICS to stdout
    print("BEGIN:VCALENDAR")
    print("VERSION:2.0")
    print("PRODID:-//Community Calendar//Eventbrite Scraper//EN")
    print("X-WR-CALNAME:Eventbrite Santa Rosa")
    
    for event in events:
        vevent = event_to_ics(event)
        if vevent:
            print(vevent)
    
    print("END:VCALENDAR")
    print(f"\nTotal: {len(events)} local events from {len(urls)} scraped", file=sys.stderr)

if __name__ == '__main__':
    main()
