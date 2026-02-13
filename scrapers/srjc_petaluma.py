#!/usr/bin/env python3
"""SRJC Petaluma Campus Events Scraper

Scrapes events from Santa Rosa Junior College that are:
- Located at the Petaluma Campus
- Part of the Petaluma Cinema Series
- Otherwise related to the Petaluma location

Data source: LiveWhale calendar at calendar.santarosa.edu
"""

import argparse
import requests
import sys
from datetime import datetime, timedelta, timezone
import re

def fetch_events():
    """Fetch all events from SRJC calendar API"""
    all_events = []
    page = 1
    
    while True:
        url = f"https://calendar.santarosa.edu/live/json/events/?page={page}"
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            events = data.get('data', [])
            if not events:
                break
                
            all_events.extend(events)
            
            # Check if there are more pages
            meta = data.get('meta', {})
            if page >= meta.get('total_pages', 1):
                break
            page += 1
            
        except Exception as e:
            print(f"Error fetching page {page}: {e}", file=sys.stderr)
            break
    
    return all_events

def is_petaluma_event(event):
    """Check if an event is related to Petaluma campus"""
    title = event.get('title', '').lower()
    url = event.get('url', '').lower()
    
    # Direct title matches
    petaluma_keywords = [
        'petaluma',
        'peta campus',  # Sometimes abbreviated
    ]
    
    for keyword in petaluma_keywords:
        if keyword in title or keyword in url:
            return True
    
    return False

def escape_ics_text(text):
    """Escape text for ICS format"""
    if not text:
        return ''
    # Replace backslashes, then commas and semicolons, then newlines
    text = text.replace('\\', '\\\\')
    text = text.replace(',', '\\,')
    text = text.replace(';', '\\;')
    text = text.replace('\n', '\\n')
    return text

def fold_line(line):
    """Fold a line to 75 characters per RFC 5545"""
    if len(line) <= 75:
        return line
    
    result = []
    while len(line) > 75:
        result.append(line[:75])
        line = ' ' + line[75:]
    result.append(line)
    return '\r\n'.join(result)

def event_to_ics(event):
    """Convert a single event to ICS VEVENT format"""
    lines = ['BEGIN:VEVENT']
    
    # UID
    uid = f"{event.get('id', 'unknown')}@calendar.santarosa.edu"
    lines.append(f"UID:{uid}")
    
    # DTSTAMP
    now = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    lines.append(f"DTSTAMP:{now}")
    
    # DTSTART and DTEND
    if event.get('is_all_day'):
        # All-day event
        if event.get('date_iso'):
            date_str = event['date_iso'][:10].replace('-', '')
            lines.append(f"DTSTART;VALUE=DATE:{date_str}")
            # End date is exclusive, so add one day
            if event.get('date2_iso'):
                end_date = event['date2_iso'][:10].replace('-', '')
            else:
                # Single day event - end is next day
                dt = datetime.strptime(date_str, '%Y%m%d')
                end_date = (dt + timedelta(days=1)).strftime('%Y%m%d')
            lines.append(f"DTEND;VALUE=DATE:{end_date}")
    else:
        # Timed event
        if event.get('date_iso'):
            # Parse ISO format and convert to ICS format
            dt_start = event['date_iso'].replace('-', '').replace(':', '')
            # Remove the timezone offset for local time
            dt_start = dt_start[:15]  # YYYYMMDDTHHMMSS
            lines.append(f"DTSTART:{dt_start}")
            
            if event.get('date2_iso'):
                dt_end = event['date2_iso'].replace('-', '').replace(':', '')[:15]
                lines.append(f"DTEND:{dt_end}")
    
    # SUMMARY
    title = escape_ics_text(event.get('title', 'Untitled Event'))
    # Unescape HTML entities
    title = title.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
    lines.append(fold_line(f"SUMMARY:{title}"))
    
    # URL
    if event.get('url'):
        lines.append(fold_line(f"URL:{event['url']}"))
    
    # LOCATION
    lines.append(f"LOCATION:SRJC Petaluma Campus")
    
    lines.append('END:VEVENT')
    return '\r\n'.join(lines)

def generate_ics(events):
    """Generate a complete ICS calendar from events"""
    lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//Community Calendar//SRJC Petaluma Scraper//EN',
        'X-WR-CALNAME:SRJC Petaluma Campus Events',
        'X-WR-TIMEZONE:America/Los_Angeles',
    ]
    
    for event in events:
        lines.append(event_to_ics(event))
    
    lines.append('END:VCALENDAR')
    return '\r\n'.join(lines)

def main():
    parser = argparse.ArgumentParser(description='Scrape SRJC Petaluma Campus events')
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    args = parser.parse_args()
    
    print("Fetching SRJC calendar events...", file=sys.stderr)
    all_events = fetch_events()
    print(f"Found {len(all_events)} total events", file=sys.stderr)
    
    # Filter for Petaluma events
    petaluma_events = [e for e in all_events if is_petaluma_event(e)]
    print(f"Found {len(petaluma_events)} Petaluma-related events", file=sys.stderr)
    
    # Generate ICS
    ics_content = generate_ics(petaluma_events)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(ics_content)
        print(f"Wrote {len(petaluma_events)} events to {args.output}", file=sys.stderr)
    else:
        print(ics_content)

if __name__ == '__main__':
    main()
