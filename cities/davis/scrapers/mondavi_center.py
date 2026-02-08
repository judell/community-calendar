#!/usr/bin/env python3
"""
Scraper for Mondavi Center for the Performing Arts
https://www.mondaviarts.org/events-and-tickets/

Extracts events and converts to ICS format.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import sys
from zoneinfo import ZoneInfo

def fetch_events():
    """Fetch and parse events from Mondavi Center."""
    url = "https://www.mondaviarts.org/events-and-tickets/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; DavisCalendar/1.0)'
    }
    
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    events = []
    
    # Find all event cards
    for card in soup.find_all('div', class_='c-event-card'):
        try:
            event = parse_event_card(card)
            if event:
                events.append(event)
        except Exception as e:
            print(f"Warning: Failed to parse event card: {e}", file=sys.stderr)
            continue
    
    return events


def parse_event_card(card):
    """Parse a single event card."""
    # Get link and title
    link_elem = card.find('a', class_='c-event-card__link')
    if not link_elem:
        return None
    
    url = link_elem.get('href', '')
    
    title_elem = card.find('h3', class_='c-event-card__title')
    title = title_elem.get_text(strip=True) if title_elem else 'Untitled Event'
    
    # Get datetime from the time element
    time_elem = card.find('time', class_='c-event-card__time-label')
    if time_elem and time_elem.get('datetime'):
        dt_str = time_elem['datetime']
        # Parse ISO datetime: 2026-02-07T19:30:00-08:00
        try:
            dt = datetime.fromisoformat(dt_str)
        except:
            dt = None
    else:
        dt = None
    
    # If no time element, try to parse from daterange text
    if dt is None:
        daterange_elem = card.find('p', class_='c-event-card__daterange')
        if daterange_elem:
            dt = parse_daterange(daterange_elem.get_text(strip=True))
    
    if dt is None:
        return None
    
    # Get promoter/presenter
    promoter_elem = card.find('span', class_='c-event-card__promoter')
    promoter = promoter_elem.get_text(strip=True) if promoter_elem else ''
    
    # Get availability
    avail_elem = card.find('p', class_='c-event-card__availability')
    availability = avail_elem.get_text(strip=True) if avail_elem else ''
    
    return {
        'title': title,
        'url': url,
        'datetime': dt,
        'promoter': promoter,
        'availability': availability,
        'location': 'Mondavi Center for the Performing Arts, UC Davis'
    }


def parse_daterange(text):
    """Parse daterange text like 'Sat, Feb 7, 2026' or 'Thu, Feb 12 – Sat, Feb 14, 2026'."""
    # Remove icons and extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Try to extract first date
    # Patterns: "Sat, Feb 7, 2026" or "Thu, Feb 12"
    match = re.search(r'([A-Z][a-z]+),?\s+([A-Z][a-z]+)\s+(\d+)(?:,?\s+(\d{4}))?', text)
    if match:
        month_str = match.group(2)
        day = int(match.group(3))
        year = int(match.group(4)) if match.group(4) else datetime.now().year
        
        months = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        month = months.get(month_str[:3], 1)
        
        # Default time to 7:30 PM for evening events
        return datetime(year, month, day, 19, 30, tzinfo=ZoneInfo('America/Los_Angeles'))
    
    return None


def to_ics(events):
    """Convert events to ICS format."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Davis Community Calendar//Mondavi Center Scraper//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Mondavi Center Events",
        "X-WR-TIMEZONE:America/Los_Angeles"
    ]
    
    for event in events:
        dt = event['datetime']
        
        # Create unique ID
        uid = f"mondavi-{dt.strftime('%Y%m%d%H%M')}-{hash(event['title']) % 100000}@davis-calendar"
        
        # Format datetime
        dtstart = dt.strftime('%Y%m%dT%H%M%S')
        dtend = (dt + timedelta(hours=2)).strftime('%Y%m%dT%H%M%S')
        
        # Build description
        desc_parts = []
        if event.get('promoter'):
            desc_parts.append(f"Presented by: {event['promoter']}")
        if event.get('availability'):
            desc_parts.append(f"Status: {event['availability']}")
        desc_parts.append(f"More info: {event['url']}")
        description = '\\n'.join(desc_parts)
        
        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}",
            f"DTSTART;TZID=America/Los_Angeles:{dtstart}",
            f"DTEND;TZID=America/Los_Angeles:{dtend}",
            f"SUMMARY:{escape_ics(event['title'])}",
            f"DESCRIPTION:{description}",
            f"LOCATION:{event['location']}",
            f"URL:{event['url']}",
            "CATEGORIES:Performing Arts,Music,Dance",
            "END:VEVENT"
        ])
    
    lines.append("END:VCALENDAR")
    return '\n'.join(lines)


def escape_ics(text):
    """Escape special characters for ICS format."""
    return text.replace('\\', '\\\\').replace(',', '\\,').replace(';', '\\;').replace('\n', '\\n')


def main():
    print("Fetching Mondavi Center events...", file=sys.stderr)
    events = fetch_events()
    print(f"Found {len(events)} events", file=sys.stderr)
    
    if events:
        ics = to_ics(events)
        print(ics)
    
    return 0 if events else 1


if __name__ == '__main__':
    sys.exit(main())
