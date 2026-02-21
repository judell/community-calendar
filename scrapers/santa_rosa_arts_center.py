#!/usr/bin/env python3
"""
Scraper for Santa Rosa Arts Center events.
https://santarosaartscenter.org/events/

The events are displayed as Elementor content with event details in HTML.
"""

import argparse
import logging
import re
from datetime import datetime, timedelta
from typing import Optional

from bs4 import BeautifulSoup
from icalendar import Calendar, Event

import sys
sys.path.insert(0, '/home/exedev/community-calendar/scrapers')
from lib.utils import fetch_with_retry, generate_uid, append_source, parse_time_flexible

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = 'https://santarosaartscenter.org'
EVENTS_URL = f'{BASE_URL}/events/'
DOMAIN = 'santarosaartscenter.org'
LOCATION = '312 South A Street, Santa Rosa, CA 95401'

# Month name to number mapping
MONTH_MAP = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
    'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6, 'jul': 7, 'aug': 8, 
    'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
}


def parse_event_date(text: str, target_year: int) -> Optional[datetime]:
    """
    Parse dates like:
    - "February 12 6-8pm" -> Feb 12
    - "Wednesday February 18" -> Feb 18
    """
    if not text:
        return None
    
    text = text.lower().strip()
    
    # Pattern: Month Day (with optional day-of-week prefix)
    match = re.search(r'(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\s+(\d{1,2})', text)
    if match:
        month_str = match.group(1)
        day = int(match.group(2))
        month = MONTH_MAP.get(month_str)
        if month:
            return datetime(target_year, month, day)
    
    return None


def parse_time_range(text: str) -> tuple[Optional[tuple[int, int]], Optional[tuple[int, int]]]:
    """
    Parse time ranges like:
    - "6-8pm" -> (18, 0), (20, 0)
    - "6 – 7:30 PM" -> (18, 0), (19, 30)
    - "5-8PM" -> (17, 0), (20, 0)
    """
    if not text:
        return None, None
    
    text = text.upper().strip()
    
    # Pattern: start-end with optional pm/am
    # Handle various dash types: -, –, —
    match = re.search(r'(\d{1,2}):?(\d{2})?\s*[-–—]\s*(\d{1,2}):?(\d{2})?\s*(AM|PM)?', text)
    if match:
        start_hour = int(match.group(1))
        start_min = int(match.group(2) or 0)
        end_hour = int(match.group(3))
        end_min = int(match.group(4) or 0)
        ampm = match.group(5)
        
        # If PM specified, adjust hours (assuming both are PM for evening events)
        if ampm == 'PM':
            if end_hour != 12:
                end_hour += 12
            if start_hour != 12 and start_hour < end_hour - 12:
                start_hour += 12
        
        return (start_hour, start_min), (end_hour, end_min)
    
    return None, None


def scrape_events(target_year: int, target_month: int) -> list[dict]:
    """Scrape events from Santa Rosa Arts Center."""
    html = fetch_with_retry(EVENTS_URL)
    soup = BeautifulSoup(html, 'html.parser')
    
    events = []
    
    # Find the main content widget
    content_widgets = soup.find_all('div', class_='elementor-widget-text-editor')
    
    for widget in content_widgets:
        # Get all elements in order
        elements = widget.find_all(['h3', 'h4', 'h5', 'p', 'div'])
        
        current_event = None
        
        for element in elements:
            text = element.get_text(strip=True)
            
            # Skip empty or very short text
            if not text or len(text) < 3:
                continue
            
            # Skip non-event headers (like address info)
            if 'Santa Rosa Arts Center' in text and 'South A Street' not in text:
                continue
            if '312 South A Street' in text:
                continue
            
            # h3 = major event title
            if element.name == 'h3':
                # Save previous event if valid
                if current_event and current_event.get('dtstart'):
                    events.append(current_event)
                
                # Start new event
                title = text.strip('"').strip()
                current_event = {
                    'title': title,
                    'description': '',
                    'url': EVENTS_URL
                }
                continue
            
            # h4 = secondary title or new event
            if element.name == 'h4':
                # Check if this is a subtitle or a new event
                if 'strong' in str(element) and not current_event:
                    # Save previous
                    if current_event and current_event.get('dtstart'):
                        events.append(current_event)
                    
                    title = text.strip('"').strip()
                    current_event = {
                        'title': title,
                        'description': '',
                        'url': EVENTS_URL
                    }
                elif current_event and not current_event.get('dtstart'):
                    # This might be a subtitle - append to title
                    if 'time to share' in text.lower() or 'dialogue' in text.lower():
                        current_event['title'] += ' - ' + text
                continue
            
            # h5 = usually contains date/time
            if element.name == 'h5' and current_event:
                # Try to parse as date
                date = parse_event_date(text, target_year)
                if date and not current_event.get('dtstart'):
                    # Also try to extract time
                    start_time, end_time = parse_time_range(text)
                    
                    if start_time:
                        current_event['dtstart'] = date.replace(hour=start_time[0], minute=start_time[1])
                    else:
                        current_event['dtstart'] = date.replace(hour=18, minute=0)  # default 6pm
                    
                    if end_time:
                        current_event['dtend'] = date.replace(hour=end_time[0], minute=end_time[1])
                elif not date and current_event:
                    # Might be additional info like "Featured poet..."
                    if current_event.get('description'):
                        current_event['description'] += ' ' + text
                    else:
                        current_event['description'] = text
                continue
            
            # p and div = description content
            if element.name in ['p', 'div'] and current_event and current_event.get('dtstart'):
                # Skip if it looks like another event title embedded
                if element.find('h4') or element.find('h5'):
                    continue
                
                if text and len(text) > 10:
                    if current_event.get('description'):
                        current_event['description'] += '\n' + text
                    else:
                        current_event['description'] = text
        
        # Don't forget last event from this widget
        if current_event and current_event.get('dtstart'):
            events.append(current_event)
    
    # Filter by target month and deduplicate
    seen = set()
    filtered = []
    for event in events:
        dt = event.get('dtstart')
        if dt and dt.year == target_year and dt.month == target_month:
            key = (event['title'], dt.date())
            if key not in seen:
                seen.add(key)
                event['location'] = LOCATION
                filtered.append(event)
                logger.info(f"Found: {event['title']} on {dt}")
    
    return filtered


def create_calendar(events: list[dict], year: int, month: int) -> Calendar:
    """Create iCalendar from events."""
    cal = Calendar()
    cal.add('prodid', f'-//Santa Rosa Arts Center//{DOMAIN}//')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', f'Santa Rosa Arts Center - {year}/{month:02d}')
    cal.add('x-wr-timezone', 'America/Los_Angeles')
    
    for event_data in events:
        event = Event()
        event.add('summary', event_data['title'])
        event.add('dtstart', event_data['dtstart'])
        
        if event_data.get('dtend'):
            event.add('dtend', event_data['dtend'])
        else:
            # Default 2-hour duration
            event.add('dtend', event_data['dtstart'] + timedelta(hours=2))
        
        if event_data.get('location'):
            event.add('location', event_data['location'])
        
        description = append_source(event_data.get('description', ''), event_data.get('url', EVENTS_URL))
        event.add('description', description)
        
        event.add('uid', generate_uid(event_data['title'], event_data['dtstart'], DOMAIN))
        
        cal.add_component(event)
    
    return cal


def main():
    parser = argparse.ArgumentParser(description='Scrape Santa Rosa Arts Center events')
    parser.add_argument('--year', type=int, help='Target year (default: current + next month)')
    parser.add_argument('--month', type=int, help='Target month 1-12 (default: current + next month)')
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    args = parser.parse_args()

    if args.year and args.month:
        months = [(args.year, args.month)]
    else:
        now = datetime.now()
        months = [(now.year, now.month)]
        nxt = (now.replace(day=28) + timedelta(days=4)).replace(day=1)
        months.append((nxt.year, nxt.month))

    all_events = []
    for y, m in months:
        events = scrape_events(y, m)
        logger.info(f"Found {len(events)} events for {y}/{m:02d}")
        all_events.extend(events)

    cal = create_calendar(all_events, months[0][0], months[0][1])
    ical_data = cal.to_ical().decode('utf-8')
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(ical_data)
        logger.info(f"Wrote {args.output}")
    else:
        print(ical_data)


if __name__ == '__main__':
    main()
