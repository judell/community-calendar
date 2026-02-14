#!/usr/bin/env python3
"""
HenHouse Brewing Events Scraper

Scrapes events from henhousebrewing.com/events/
Filters to Petaluma location only.

Output: ICS format to stdout
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import hashlib
import sys

def parse_datetime(date_str):
    """Parse date strings like 'Saturday, February 14, 2026 • 6-Closing' or 'Every Thursday • 6-8pm'"""
    # Handle recurring events
    if date_str.lower().startswith('every '):
        return None, date_str  # Return as recurring
    
    # Extract the date part and time part
    # Format: "Saturday, February 14, 2026 • 6-Closing"
    parts = date_str.split('•')
    date_part = parts[0].strip()
    time_part = parts[1].strip() if len(parts) > 1 else None
    
    # Parse date - "Saturday, February 14, 2026"
    try:
        # Remove day of week if present
        if ',' in date_part:
            date_part = date_part.split(',', 1)[1].strip()
        dt = datetime.strptime(date_part, "%B %d, %Y")
    except ValueError:
        return None, date_str
    
    # Parse start time
    start_hour = 12  # default noon
    if time_part:
        time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', time_part.lower())
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            ampm = time_match.group(3)
            if ampm == 'pm' and hour != 12:
                hour += 12
            elif ampm == 'am' and hour == 12:
                hour = 0
            # If no am/pm and hour < 8, assume PM for evening events
            elif not ampm and hour < 8:
                hour += 12
            start_hour = hour
            dt = dt.replace(hour=start_hour, minute=minute)
    
    return dt, time_part

def scrape_henhouse(location_filter='petaluma'):
    """Scrape HenHouse events, optionally filtering by location."""
    url = "https://henhousebrewing.com/events/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; CommunityCalendar/1.0)'
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    events = []
    
    for listing in soup.find_all('div', class_='event-listing'):
        # Get date/time
        date_h2 = listing.find('h2', class_='title--4')
        date_str = date_h2.get_text(strip=True) if date_h2 else ''
        
        # Get location
        location_span = listing.find('span', class_='title--4 primary-1')
        location = location_span.get_text(strip=True).lower() if location_span else ''
        
        # Filter by location
        if location_filter and location_filter.lower() not in location:
            continue
        
        # Get title
        title_h3 = listing.find('h3', class_='title--2')
        title = title_h3.get_text(strip=True) if title_h3 else 'Untitled Event'
        
        # Get description
        desc_div = listing.find('div', class_='font-light')
        description = desc_div.get_text(strip=True) if desc_div else ''
        
        # Get link
        link_a = listing.find('a', class_='button')
        link = link_a.get('href') if link_a else ''
        
        # Parse datetime
        dt, time_str = parse_datetime(date_str)
        
        event = {
            'title': title,
            'date': dt,
            'date_str': date_str,
            'time_str': time_str,
            'location': 'HenHouse Brewing Petaluma',
            'address': '1333 N. McDowell Boulevard, Petaluma, CA 94954',
            'description': description,
            'url': link,
            'recurring': dt is None
        }
        events.append(event)
    
    return events

def to_ics(events):
    """Convert events to ICS format."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Community Calendar//HenHouse Scraper//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:HenHouse Brewing Petaluma",
    ]
    
    for event in events:
        if event['recurring']:
            # Skip recurring events without specific dates for now
            # Could generate instances but that's complex
            continue
        
        if not event['date']:
            continue
            
        uid = hashlib.md5(f"{event['title']}{event['date']}".encode()).hexdigest()
        
        dtstart = event['date'].strftime("%Y%m%dT%H%M%S")
        # Assume 2 hour duration
        dtend = event['date'].replace(hour=event['date'].hour + 2)
        dtend_str = dtend.strftime("%Y%m%dT%H%M%S")
        
        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{uid}@henhouse.community-calendar")
        lines.append(f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}")
        lines.append(f"DTSTART:{dtstart}")
        lines.append(f"DTEND:{dtend_str}")
        lines.append(f"SUMMARY:{event['title']}")
        lines.append(f"LOCATION:{event['location']}, {event['address']}")
        
        desc = event['description']
        if event['url']:
            desc += f"\n\nMore info: {event['url']}"
        desc = desc.replace('\n', '\\n').replace(',', '\\,')
        lines.append(f"DESCRIPTION:{desc}")
        
        if event['url']:
            lines.append(f"URL:{event['url']}")
        
        lines.append("END:VEVENT")
    
    lines.append("END:VCALENDAR")
    return '\n'.join(lines)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Scrape HenHouse Brewing events')
    parser.add_argument('--location', default='petaluma', help='Filter by location (default: petaluma)')
    parser.add_argument('--all', action='store_true', help='Include all locations')
    parser.add_argument('--json', action='store_true', help='Output JSON instead of ICS')
    args = parser.parse_args()
    
    location = None if args.all else args.location
    events = scrape_henhouse(location)
    
    if args.json:
        import json
        # Convert datetime to string for JSON
        for e in events:
            if e['date']:
                e['date'] = e['date'].isoformat()
        print(json.dumps(events, indent=2))
    else:
        print(to_ics(events))
    
    print(f"# Found {len(events)} events", file=sys.stderr)

if __name__ == '__main__':
    main()
