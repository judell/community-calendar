#!/usr/bin/env python3
"""
Scraper for City of Sonoma calendar
https://www.sonomacity.org/calendar

Includes city council meetings, commission meetings, and special events.
"""

import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event
from datetime import datetime, timedelta
import re
import argparse
import logging
import hashlib

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = 'https://www.sonomacity.org'
CALENDAR_URL = f'{BASE_URL}/calendar'
DEFAULT_LOCATION = "City Council Chambers, 177 First St. West, Sonoma, CA 95476"

def fetch_calendar_page():
    """Fetch the main calendar page."""
    logger.info(f"Fetching {CALENDAR_URL}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    response = requests.get(CALENDAR_URL, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text

def parse_events(html_content, target_year, target_month):
    """Parse events from the calendar page."""
    soup = BeautifulSoup(html_content, 'html.parser')
    events = []
    seen_urls = set()
    
    # Find all event links
    for link in soup.find_all('a', href=re.compile(r'/event/')):
        try:
            href = link.get('href', '')
            if not href or href in seen_urls:
                continue
            
            title = link.get_text(strip=True)
            if not title or len(title) < 3:
                continue
            
            # Get the parent container
            parent = link.find_parent(['article', 'div', 'li'])
            if not parent:
                continue
            
            parent_text = parent.get_text(' ', strip=True)
            
            # Parse date: "Feb 4 2026" or "Feb 4, 2026"
            date_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})', parent_text, re.IGNORECASE)
            if not date_match:
                continue
            
            month_name, day, year = date_match.groups()
            year = int(year)
            day = int(day)
            
            # Convert month name to number
            month_map = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}
            month = month_map.get(month_name.lower())
            if not month:
                continue
            
            # Filter by target month
            if year != target_year or month != target_month:
                continue
            
            # Parse time: "6:00pm - 9:00pm" or "6:00pm"
            time_match = re.search(r'(\d{1,2}:\d{2})\s*(am|pm)', parent_text, re.IGNORECASE)
            if time_match:
                time_str = f"{time_match.group(1)} {time_match.group(2)}"
                try:
                    time_obj = datetime.strptime(time_str, "%I:%M %p")
                    dt_start = datetime(year, month, day, time_obj.hour, time_obj.minute)
                except ValueError:
                    dt_start = datetime(year, month, day, 18, 0)  # Default 6 PM
            elif 'all day' in parent_text.lower():
                dt_start = datetime(year, month, day, 0, 0)
            else:
                dt_start = datetime(year, month, day, 18, 0)  # Default 6 PM
            
            # Parse end time
            end_match = re.search(r'-\s*(\d{1,2}:\d{2})\s*(am|pm)', parent_text, re.IGNORECASE)
            if end_match:
                end_time_str = f"{end_match.group(1)} {end_match.group(2)}"
                try:
                    end_time_obj = datetime.strptime(end_time_str, "%I:%M %p")
                    dt_end = datetime(year, month, day, end_time_obj.hour, end_time_obj.minute)
                except ValueError:
                    dt_end = dt_start + timedelta(hours=2)
            else:
                dt_end = dt_start + timedelta(hours=2)
            
            seen_urls.add(href)
            
            full_url = href if href.startswith('http') else BASE_URL + href
            
            # Get location if mentioned
            location = DEFAULT_LOCATION
            if 'city council chambers' in parent_text.lower():
                location = DEFAULT_LOCATION
            
            events.append({
                'title': title,
                'url': full_url,
                'dtstart': dt_start,
                'dtend': dt_end,
                'location': location,
                'description': f'City of Sonoma event. More info: {full_url}'
            })
            
            logger.info(f"Found event: {title} on {dt_start}")
            
        except Exception as e:
            logger.warning(f"Error parsing event: {e}")
            continue
    
    return events

def create_calendar(events, year, month):
    """Create an iCalendar from parsed events."""
    cal = Calendar()
    cal.add('prodid', '-//City of Sonoma//sonomacity.org//')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', f'City of Sonoma - {year}/{month:02d}')
    cal.add('x-wr-timezone', 'America/Los_Angeles')
    
    for event_data in events:
        event = Event()
        event.add('summary', event_data['title'])
        event.add('dtstart', event_data['dtstart'])
        event.add('dtend', event_data['dtend'])
        event.add('url', event_data['url'])
        event.add('location', event_data['location'])
        event.add('description', event_data['description'])
        
        uid_str = f"{event_data['title']}-{event_data['dtstart'].isoformat()}"
        uid = hashlib.md5(uid_str.encode()).hexdigest()
        event.add('uid', f"{uid}@sonomacity.org")
        event.add('x-source', 'City of Sonoma')
        
        cal.add_component(event)
    
    return cal

def main():
    parser = argparse.ArgumentParser(description='Scrape City of Sonoma calendar')
    parser.add_argument('--year', type=int, required=True, help='Target year')
    parser.add_argument('--month', type=int, required=True, help='Target month (1-12)')
    parser.add_argument('--output', type=str, help='Output filename')
    args = parser.parse_args()
    
    html = fetch_calendar_page()
    events = parse_events(html, args.year, args.month)
    
    logger.info(f"Found {len(events)} events for {args.year}-{args.month:02d}")
    
    cal = create_calendar(events, args.year, args.month)
    
    output_file = args.output or f'sonoma_city_{args.year}_{args.month:02d}.ics'
    with open(output_file, 'wb') as f:
        f.write(cal.to_ical())
    
    logger.info(f"Written to {output_file}")
    return output_file

if __name__ == '__main__':
    main()
