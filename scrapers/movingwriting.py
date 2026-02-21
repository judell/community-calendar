#!/usr/bin/env python3
"""
Scraper for MovingWriting events.
https://www.movingwriting.com/workshops

This is a Squarespace site but NOT using their events collection.
Events are embedded as static page content, so we parse the HTML.
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
from lib.utils import fetch_with_retry, generate_uid, append_source

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = 'https://www.movingwriting.com'
WORKSHOPS_URL = f'{BASE_URL}/workshops'
DOMAIN = 'movingwriting.com'
LOCATION = 'Private studio, Sebastopol, CA'

# Month name to number mapping
MONTH_MAP = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
    'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6, 'jul': 7, 'aug': 8, 
    'sep': 9, 'sept': 9, 'oct': 10, 'nov': 11, 'dec': 12
}


def parse_workshop_dates(text: str, target_year: int) -> list[datetime]:
    """
    Parse workshop dates from text like:
    - "Saturdays, Mar 21; June 20; Sept 19; Dec 12"
    - "March 21, June 20, September 19, December 12"
    """
    dates = []
    text = text.lower()
    
    # Pattern: Month Day (with optional comma/semicolon separators)
    pattern = r'(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+(\d{1,2})'
    
    for match in re.finditer(pattern, text):
        month_str = match.group(1)
        day = int(match.group(2))
        
        # Normalize month name
        if month_str.startswith('sep'):
            month_str = 'sep'
        month = MONTH_MAP.get(month_str[:3])
        
        if month:
            dates.append(datetime(target_year, month, day))
    
    return dates


def parse_time_range(text: str) -> tuple[Optional[tuple[int, int]], Optional[tuple[int, int]]]:
    """
    Parse time from text like:
    - "2-5pm" -> (14, 0), (17, 0)
    - "10am-noon" or "10-noon" -> (10, 0), (12, 0)
    - "10am-12pm" -> (10, 0), (12, 0)
    """
    if not text:
        return None, None
    
    text = text.lower().strip()
    
    # Handle "noon"
    text = text.replace('noon', '12pm')
    
    # Pattern: start-end with optional am/pm
    match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)?\s*[-–—]\s*(\d{1,2}):?(\d{2})?\s*(am|pm)?', text)
    if match:
        start_hour = int(match.group(1))
        start_min = int(match.group(2) or 0)
        start_ampm = match.group(3)
        end_hour = int(match.group(4))
        end_min = int(match.group(5) or 0)
        end_ampm = match.group(6)
        
        # Apply AM/PM to end time first
        if end_ampm == 'pm' and end_hour != 12:
            end_hour += 12
        elif end_ampm == 'am' and end_hour == 12:
            end_hour = 0
        
        # Apply AM/PM to start time
        if start_ampm == 'pm' and start_hour != 12:
            start_hour += 12
        elif start_ampm == 'am' and start_hour == 12:
            start_hour = 0
        elif not start_ampm:
            # Infer start AM/PM from end time and context
            if end_ampm == 'pm':
                # If end is PM and start < end (in 12hr), start is also PM
                # e.g., "2-5pm" -> start=2, end=17, so start should be 14
                if start_hour < (end_hour - 12 if end_hour > 12 else end_hour):
                    start_hour += 12
                elif start_hour == end_hour - 12:
                    # Same hour range like "12-2pm" - start is 12 (noon)
                    pass
            elif end_ampm == 'am':
                # Both probably AM
                pass
        
        return (start_hour, start_min), (end_hour, end_min)
    
    return None, None


def parse_recurring_monthly(text: str, target_year: int, target_month: int) -> list[datetime]:
    """
    Parse recurring events like:
    - "First Friday of the month, 10-noon"
    
    Returns dates for the target month.
    """
    dates = []
    text_lower = text.lower()
    
    # Map ordinal to week number
    ordinal_map = {
        'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'last': -1
    }
    
    # Map day name to weekday number (0=Monday, 6=Sunday)
    day_map = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6
    }
    
    # Pattern: "First Friday of the month" or "Third Wednesday"
    match = re.search(r'(first|second|third|fourth|last)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)', text_lower)
    
    if match:
        ordinal = ordinal_map.get(match.group(1))
        weekday = day_map.get(match.group(2))
        
        if ordinal is not None and weekday is not None:
            # Find the nth weekday of the target month
            first_of_month = datetime(target_year, target_month, 1)
            
            if ordinal == -1:  # last
                # Go to next month, back one day, find last occurrence
                if target_month == 12:
                    next_month = datetime(target_year + 1, 1, 1)
                else:
                    next_month = datetime(target_year, target_month + 1, 1)
                last_day = next_month - timedelta(days=1)
                
                # Find last weekday
                days_back = (last_day.weekday() - weekday) % 7
                target_date = last_day - timedelta(days=days_back)
            else:
                # Find first occurrence of weekday
                days_ahead = (weekday - first_of_month.weekday()) % 7
                first_occurrence = first_of_month + timedelta(days=days_ahead)
                
                # Add weeks to get nth occurrence
                target_date = first_occurrence + timedelta(weeks=ordinal - 1)
            
            # Verify it's still in target month
            if target_date.month == target_month:
                dates.append(target_date)
    
    return dates


def scrape_events(target_year: int, target_month: int) -> list[dict]:
    """Scrape events from MovingWriting workshops page."""
    html = fetch_with_retry(WORKSHOPS_URL)
    soup = BeautifulSoup(html, 'html.parser')
    
    events = []
    
    # The page has workshop info embedded in the HTML
    # Look for the JSON in the script tag or parse visible content
    
    # Method 1: Look for structured data in page
    page_text = soup.get_text()
    
    # Weekend Workshops: specific dates
    # Pattern: "2026 Weekend Afternoons" followed by dates
    if '2026 weekend' in page_text.lower() or 'weekend afternoon' in page_text.lower():
        # Look for the date list
        dates_match = re.search(r'(sat(?:urdays?)?,?\s*)?(mar(?:ch)?\s+\d{1,2})[;,]?\s*(june?\s+\d{1,2})[;,]?\s*(sep(?:t(?:ember)?)?\s+\d{1,2})[;,]?\s*(dec(?:ember)?\s+\d{1,2})', page_text.lower())
        if dates_match:
            date_text = ' '.join(dates_match.groups())
            workshop_dates = parse_workshop_dates(date_text, target_year)
            
            # Weekend workshops are 2-5pm per the website
            start_time = (14, 0)  # 2pm
            end_time = (17, 0)    # 5pm
            
            for dt in workshop_dates:
                if dt.month == target_month:
                    event = {
                        'title': 'MovingWriting Weekend Workshop',
                        'description': 'Embodied expressive writing workshop. Exploring MovingWriting practice and community. $75 per afternoon. Limited to 8 participants. Advance registration required.',
                        'dtstart': dt.replace(hour=start_time[0], minute=start_time[1]) if start_time else dt,
                        'dtend': dt.replace(hour=end_time[0], minute=end_time[1]) if end_time else dt + timedelta(hours=3),
                        'location': LOCATION,
                        'url': WORKSHOPS_URL
                    }
                    events.append(event)
                    logger.info(f"Found: {event['title']} on {event['dtstart']}")
    
    # Monthly Women's Circle: recurring
    if 'first friday' in page_text.lower() and 'women' in page_text.lower():
        # This is a recurring event - first Friday
        circle_dates = parse_recurring_monthly('first friday of the month', target_year, target_month)
        
        for dt in circle_dates:
            event = {
                'title': "MovingWriting Women's Circle",
                'description': 'Monthly MovingWriting Women\'s Circle. Intimate, semi-closed drop-in group. 10am-noon. $30-50 sliding scale. Contact to be placed on roster.',
                'dtstart': dt.replace(hour=10, minute=0),
                'dtend': dt.replace(hour=12, minute=0),
                'location': LOCATION,
                'url': WORKSHOPS_URL
            }
            events.append(event)
            logger.info(f"Found: {event['title']} on {event['dtstart']}")
    
    return events


def create_calendar(events: list[dict], year: int, month: int) -> Calendar:
    """Create iCalendar from events."""
    cal = Calendar()
    cal.add('prodid', f'-//MovingWriting//{DOMAIN}//')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', f'MovingWriting - {year}/{month:02d}')
    cal.add('x-wr-timezone', 'America/Los_Angeles')
    
    for event_data in events:
        event = Event()
        event.add('summary', event_data['title'])
        event.add('dtstart', event_data['dtstart'])
        event.add('dtend', event_data['dtend'])
        
        if event_data.get('location'):
            event.add('location', event_data['location'])
        
        description = append_source(event_data.get('description', ''), event_data.get('url', WORKSHOPS_URL))
        event.add('description', description)
        
        event.add('uid', generate_uid(event_data['title'], event_data['dtstart'], DOMAIN))
        
        cal.add_component(event)
    
    return cal


def main():
    parser = argparse.ArgumentParser(description='Scrape MovingWriting events')
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
