#!/usr/bin/env python3
"""BlogTO Events Scraper

Scrapes events from blogto.com/events/ for Toronto.
Extracts event data from the listing page and individual event pages.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from typing import Optional

import requests
from bs4 import BeautifulSoup

# ICS helpers
def ics_escape(text: str) -> str:
    """Escape text for ICS format."""
    if not text:
        return ""
    text = text.replace("\\", "\\\\")
    text = text.replace(",", "\\,")
    text = text.replace(";", "\\;")
    text = text.replace("\n", "\\n")
    return text

def fold_line(line: str) -> str:
    """Fold long lines per ICS spec (max 75 chars)."""
    if len(line) <= 75:
        return line
    result = []
    while len(line) > 75:
        result.append(line[:75])
        line = " " + line[75:]
    result.append(line)
    return "\r\n".join(result)


def parse_date_range(date_str: str) -> tuple[Optional[datetime], Optional[datetime]]:
    """Parse date strings like 'February 14 – 16, 2026' or 'February 14, 2026'.
    
    Returns (start_date, end_date). If single date, end_date is same as start_date.
    """
    if not date_str:
        return None, None
    
    date_str = date_str.strip()
    
    # Skip unparseable dates
    if date_str.lower() in ['various dates', 'ongoing', 'tba', 'tbd']:
        return None, None
    
    # Replace various dash characters with standard dash
    date_str = re.sub(r'[–—−]', '-', date_str)
    
    # Pattern: "February 14 - 16, 2026" (range within same month)
    match = re.match(r'([A-Za-z]+)\s+(\d{1,2})\s*-\s*(\d{1,2}),?\s*(\d{4})', date_str)
    if match:
        month, start_day, end_day, year = match.groups()
        try:
            start = datetime.strptime(f"{month} {start_day} {year}", "%B %d %Y")
            end = datetime.strptime(f"{month} {end_day} {year}", "%B %d %Y")
            return start, end
        except ValueError:
            pass
    
    # Pattern: "February 14, 2026 - March 1, 2026" (range across months)
    match = re.match(r'([A-Za-z]+\s+\d{1,2}),?\s*(\d{4})\s*-\s*([A-Za-z]+\s+\d{1,2}),?\s*(\d{4})', date_str)
    if match:
        start_md, start_y, end_md, end_y = match.groups()
        try:
            start = datetime.strptime(f"{start_md} {start_y}", "%B %d %Y")
            end = datetime.strptime(f"{end_md} {end_y}", "%B %d %Y")
            return start, end
        except ValueError:
            pass
    
    # Pattern: "February 14, 2026" (single date)
    match = re.match(r'([A-Za-z]+)\s+(\d{1,2}),?\s*(\d{4})', date_str)
    if match:
        month, day, year = match.groups()
        try:
            dt = datetime.strptime(f"{month} {day} {year}", "%B %d %Y")
            return dt, dt
        except ValueError:
            pass
    
    # Pattern: "Saturday, February 28, 2026" (day of week prefix)
    match = re.match(r'[A-Za-z]+,?\s+([A-Za-z]+)\s+(\d{1,2}),?\s*(\d{4})', date_str)
    if match:
        month, day, year = match.groups()
        try:
            dt = datetime.strptime(f"{month} {day} {year}", "%B %d %Y")
            return dt, dt
        except ValueError:
            pass
    
    return None, None


def parse_time(time_str: str) -> tuple[Optional[str], Optional[str]]:
    """Parse time strings like '10:00 AM – 4:00 PM'.
    
    Returns (start_time, end_time) as HH:MM strings in 24h format.
    """
    if not time_str:
        return None, None
    
    time_str = time_str.strip()
    time_str = re.sub(r'[–—−]', '-', time_str)
    
    # Pattern: "10:00 AM - 4:00 PM"
    match = re.match(r'(\d{1,2}:\d{2})\s*(AM|PM)\s*-\s*(\d{1,2}:\d{2})\s*(AM|PM)', time_str, re.I)
    if match:
        start_t, start_ampm, end_t, end_ampm = match.groups()
        try:
            start = datetime.strptime(f"{start_t} {start_ampm.upper()}", "%I:%M %p")
            end = datetime.strptime(f"{end_t} {end_ampm.upper()}", "%I:%M %p")
            return start.strftime("%H:%M"), end.strftime("%H:%M")
        except ValueError:
            pass
    
    # Pattern: "10:00 AM" (single time)
    match = re.match(r'(\d{1,2}:\d{2})\s*(AM|PM)', time_str, re.I)
    if match:
        t, ampm = match.groups()
        try:
            dt = datetime.strptime(f"{t} {ampm.upper()}", "%I:%M %p")
            return dt.strftime("%H:%M"), None
        except ValueError:
            pass
    
    return None, None


def fetch_event_urls_from_rss(session: requests.Session) -> list[str]:
    """Fetch event URLs from BlogTO RSS feed (limited to ~15 events)."""
    urls = []
    rss_url = "https://www.blogto.com/rss/events.xml"
    
    print(f"Fetching from RSS feed: {rss_url}", file=sys.stderr)
    try:
        resp = session.get(rss_url, timeout=30)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, 'xml')
        for item in soup.find_all('item'):
            link = item.find('link')
            if link and link.text:
                urls.append(link.text.strip())
    except Exception as e:
        print(f"Error fetching RSS: {e}", file=sys.stderr)
    
    print(f"Found {len(urls)} events from RSS", file=sys.stderr)
    return urls


def fetch_event_urls_from_file(filepath: str) -> list[str]:
    """Read event URLs from a file (one per line)."""
    urls = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line and line.startswith('http'):
                urls.append(line)
    print(f"Loaded {len(urls)} URLs from {filepath}", file=sys.stderr)
    return urls


def fetch_event_details(session: requests.Session, url: str) -> Optional[dict]:
    """Fetch details for a single event page."""
    try:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  Error fetching {url}: {e}", file=sys.stderr)
        return None
    
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # Extract JSON data from the page
    event_data = {}
    
    # Find var event = {...} in script
    for script in soup.find_all('script'):
        if script.string and 'var event = ' in (script.string or ''):
            match = re.search(r'var event = (\{[^}]+\})', script.string)
            if match:
                try:
                    event_data = json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
                break
    
    # Get date from the page
    date_el = soup.select_one('.rich-content-post-date')
    date_str = date_el.get_text(strip=True) if date_el else None
    
    # Get time - look for time in the event details
    time_str = None
    for el in soup.select('.event-detail-content, .rich-content'):
        text = el.get_text()
        # Look for time patterns
        time_match = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM)\s*[-–—]\s*\d{1,2}:\d{2}\s*(?:AM|PM))', text, re.I)
        if time_match:
            time_str = time_match.group(1)
            break
        time_match = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM))', text, re.I)
        if time_match:
            time_str = time_match.group(1)
            break
    
    if not event_data.get('title'):
        # Fallback: get title from page
        title_el = soup.select_one('h1, .event-detail-title')
        if title_el:
            event_data['title'] = title_el.get_text(strip=True)
    
    event_data['date_str'] = date_str
    event_data['time_str'] = time_str
    event_data['url'] = url
    
    return event_data


def event_to_ics(event: dict) -> Optional[str]:
    """Convert an event dict to ICS VEVENT format."""
    title = event.get('title', '')
    if not title:
        return None
    
    # Parse dates
    start_date, end_date = parse_date_range(event.get('date_str', ''))
    if not start_date:
        return None
    
    # Parse times
    start_time, end_time = parse_time(event.get('time_str', ''))
    
    # Build datetime strings
    if start_time:
        start_dt = start_date.replace(
            hour=int(start_time.split(':')[0]),
            minute=int(start_time.split(':')[1])
        )
        dtstart = f"DTSTART;TZID=America/Toronto:{start_dt.strftime('%Y%m%dT%H%M%S')}"
    else:
        # All-day event
        dtstart = f"DTSTART;VALUE=DATE:{start_date.strftime('%Y%m%d')}"
    
    if end_date and end_time:
        end_dt = end_date.replace(
            hour=int(end_time.split(':')[0]),
            minute=int(end_time.split(':')[1])
        )
        dtend = f"DTEND;TZID=America/Toronto:{end_dt.strftime('%Y%m%dT%H%M%S')}"
    elif end_date:
        # For multi-day events, DTEND should be the day after
        dtend = f"DTEND;VALUE=DATE:{(end_date + timedelta(days=1)).strftime('%Y%m%d')}"
    elif start_time and end_time:
        # Same day, different times
        end_dt = start_date.replace(
            hour=int(end_time.split(':')[0]),
            minute=int(end_time.split(':')[1])
        )
        dtend = f"DTEND;TZID=America/Toronto:{end_dt.strftime('%Y%m%dT%H%M%S')}"
    else:
        dtend = None
    
    # Build location
    venue = event.get('venue_name', '')
    address = event.get('address', '')
    location = f"{venue}, {address}" if venue and address else (venue or address)
    
    # Build description
    desc = event.get('description_stripped', '')
    url = event.get('url', '')
    if url:
        desc = f"{desc}\n\nMore info: {url}" if desc else url
    
    # Generate UID
    uid = f"blogto-{event.get('id', hash(title))}@blogto.com"
    
    # Build VEVENT
    lines = [
        "BEGIN:VEVENT",
        dtstart,
    ]
    
    if dtend:
        lines.append(dtend)
    
    lines.extend([
        f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}",
        f"UID:{uid}",
        fold_line(f"SUMMARY:{ics_escape(title)}"),
    ])
    
    if location:
        lines.append(fold_line(f"LOCATION:{ics_escape(location)}"))
    
    if desc:
        lines.append(fold_line(f"DESCRIPTION:{ics_escape(desc)}"))
    
    if event.get('website'):
        lines.append(f"URL:{event['website']}")
    
    lines.append("END:VEVENT")
    
    return "\r\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='Scrape BlogTO events')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)')
    parser.add_argument('--urls-file', help='File with event URLs (one per line)')
    parser.add_argument('--limit', type=int, default=200, help='Max events to fetch')
    args = parser.parse_args()
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (compatible; CommunityCalendar/1.0)'
    })
    
    # Fetch event URLs
    if args.urls_file:
        urls = fetch_event_urls_from_file(args.urls_file)[:args.limit]
    else:
        # Fall back to RSS feed (limited to ~15 events)
        urls = fetch_event_urls_from_rss(session)[:args.limit]
    
    # Fetch details for each event
    events = []
    for i, url in enumerate(urls):
        print(f"[{i+1}/{len(urls)}] {url.split('/')[-2]}", file=sys.stderr)
        event = fetch_event_details(session, url)
        if event:
            events.append(event)
    
    print(f"Fetched {len(events)} events", file=sys.stderr)
    
    # Build ICS
    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Community Calendar//BlogTO Scraper//EN",
        "X-WR-CALNAME:BlogTO Events",
        "X-WR-TIMEZONE:America/Toronto",
    ]
    
    count = 0
    for event in events:
        vevent = event_to_ics(event)
        if vevent:
            ics_lines.append(vevent)
            count += 1
    
    ics_lines.append("END:VCALENDAR")
    
    ics_content = "\r\n".join(ics_lines)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(ics_content)
        print(f"Wrote {count} events to {args.output}", file=sys.stderr)
    else:
        print(ics_content)
        print(f"Total: {count} events", file=sys.stderr)


if __name__ == '__main__':
    main()
