#!/usr/bin/env python3
"""
Eventbrite scraper using JSON-LD structured data.
No browser needed - just HTTP requests.
"""

import json
import re
import sys
from datetime import datetime
from icalendar import Calendar, Event, vText
import requests

LOCATION_CONFIGS = {
    'santarosa': {
        'url': 'https://www.eventbrite.com/d/ca--santa-rosa/all-events/',
        'timezone': 'US/Pacific',
        'prodid': '-//Eventbrite Santa Rosa Events//',
        'calname': 'Eventbrite Santa Rosa Events'
    },
    'bloomington': {
        'url': 'https://www.eventbrite.com/d/in--bloomington/all-events/',
        'timezone': 'America/Indiana/Indianapolis',
        'prodid': '-//Eventbrite Bloomington Events//',
        'calname': 'Eventbrite Bloomington Events'
    }
}

def fetch_events_from_page(url, session):
    """Fetch and parse JSON-LD events from a single page."""
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    
    matches = re.findall(r'<script type="application/ld\+json">(.*?)</script>', resp.text, re.DOTALL)
    
    events = []
    for m in matches:
        try:
            data = json.loads(m)
            if isinstance(data, dict) and data.get('@type') == 'ItemList':
                for item in data.get('itemListElement', []):
                    event = item.get('item', {})
                    if event.get('@type') == 'Event':
                        events.append(event)
        except json.JSONDecodeError:
            continue
    
    return events

def scrape_eventbrite(location, target_year, target_month, max_pages=20):
    """Scrape Eventbrite events for a location and month."""
    config = LOCATION_CONFIGS.get(location)
    if not config:
        raise ValueError(f"Unknown location: {location}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Linux"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
    }
    
    all_events = []
    seen_urls = set()
    
    # Use a session to maintain cookies across requests
    session = requests.Session()
    session.headers.update(headers)
    
    for page in range(1, max_pages + 1):
        if page == 1:
            url = config['url']
        else:
            url = f"{config['url']}?page={page}"
        
        print(f"Fetching page {page}: {url}")
        
        try:
            events = fetch_events_from_page(url, session)
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            break
        
        if not events:
            print(f"No events found on page {page}, stopping.")
            break
        
        # Track if we've gone past target month
        events_in_month = 0
        events_past_month = 0
        
        for event in events:
            event_url = event.get('url', '')
            if event_url in seen_urls:
                continue
            seen_urls.add(event_url)
            
            start_date = event.get('startDate', '')
            if not start_date:
                continue
            
            try:
                # Parse date (format: 2026-02-21 or 2026-02-21T19:00:00)
                if 'T' in start_date:
                    dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                else:
                    dt = datetime.strptime(start_date, '%Y-%m-%d')
                
                if dt.year == target_year and dt.month == target_month:
                    events_in_month += 1
                    all_events.append(event)
                elif dt.year > target_year or (dt.year == target_year and dt.month > target_month):
                    events_past_month += 1
            except ValueError as e:
                print(f"Could not parse date '{start_date}': {e}")
                continue
        
        print(f"  Found {len(events)} events, {events_in_month} in target month, {events_past_month} past target")
        
        # Stop if all events on page are past target month
        if events_in_month == 0 and events_past_month > 0:
            print("All events past target month, stopping pagination.")
            break
    
    return all_events, config

def create_ics(events, config, target_year, target_month):
    """Create ICS calendar from events."""
    cal = Calendar()
    cal.add('prodid', config['prodid'])
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    cal.add('method', 'PUBLISH')
    cal.add('x-wr-calname', config['calname'])
    cal.add('x-wr-timezone', config['timezone'])
    
    for event_data in events:
        event = Event()
        
        event.add('summary', event_data.get('name', 'Untitled Event'))
        
        start_date = event_data.get('startDate', '')
        end_date = event_data.get('endDate', start_date)
        
        try:
            if 'T' in start_date:
                dt_start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            else:
                dt_start = datetime.strptime(start_date, '%Y-%m-%d')
            event.add('dtstart', dt_start)
            
            if end_date:
                if 'T' in end_date:
                    dt_end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                else:
                    dt_end = datetime.strptime(end_date, '%Y-%m-%d')
                event.add('dtend', dt_end)
        except ValueError:
            continue
        
        # Location
        location = event_data.get('location', {})
        if isinstance(location, dict):
            loc_name = location.get('name', '')
            address = location.get('address', {})
            if isinstance(address, dict):
                street = address.get('streetAddress', '')
                city = address.get('addressLocality', '')
                state = address.get('addressRegion', '')
                loc_str = ', '.join(filter(None, [loc_name, street, city, state]))
            else:
                loc_str = loc_name
            if loc_str:
                event.add('location', vText(loc_str))
        
        # URL
        if event_data.get('url'):
            event.add('url', event_data['url'])
        
        # Description
        if event_data.get('description'):
            event.add('description', event_data['description'])
        
        # UID
        event.add('uid', f"{event_data.get('url', '')}-{start_date}")
        
        cal.add_component(event)
    
    return cal

def main():
    if len(sys.argv) != 4:
        print("Usage: python eventbrite_jsonld.py <location> <year> <month>")
        print("  Locations: santarosa, bloomington")
        sys.exit(1)
    
    location = sys.argv[1].lower()
    target_year = int(sys.argv[2])
    target_month = int(sys.argv[3])
    
    if location not in LOCATION_CONFIGS:
        print(f"Unknown location: {location}")
        print(f"Available: {', '.join(LOCATION_CONFIGS.keys())}")
        sys.exit(1)
    
    print(f"Scraping Eventbrite for {location}, {target_year}-{target_month:02d}")
    
    events, config = scrape_eventbrite(location, target_year, target_month)
    
    print(f"\nTotal events in {target_year}-{target_month:02d}: {len(events)}")
    
    cal = create_ics(events, config, target_year, target_month)
    
    filename = f"./{location}/eventbrite_{target_year}_{target_month:02d}.ics"
    with open(filename, 'wb') as f:
        f.write(cal.to_ical())
    
    print(f"Wrote {filename}")

if __name__ == '__main__':
    main()
