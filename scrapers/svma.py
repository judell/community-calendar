#!/usr/bin/env python3
"""
Scraper for Sonoma Valley Museum of Art (SVMA) events
https://www.svma.org/events
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])  # Add scrapers/ to path

import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event
from datetime import datetime, timedelta
import re
import argparse
import logging

from lib.utils import generate_uid, append_source, DEFAULT_HEADERS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = 'https://svma.org'
EVENTS_URL = f'{BASE_URL}/events'
VENUE_ADDRESS = "Sonoma Valley Museum of Art, 551 Broadway, Sonoma, CA 95476"

def fetch_events_page():
    """Fetch the main events page."""
    logger.info(f"Fetching {EVENTS_URL}")
    response = requests.get(EVENTS_URL, headers=DEFAULT_HEADERS, timeout=30)
    response.raise_for_status()
    return response.text

def parse_events(html_content, target_year, target_month):
    """Parse events from the events page."""
    soup = BeautifulSoup(html_content, 'html.parser')
    events = []
    seen_urls = set()
    
    # Find all event links
    for link in soup.find_all('a', href=re.compile(r'/event/')):
        try:
            href = link.get('href', '')
            if not href or href in seen_urls:
                continue
            
            # Get the parent container for context
            parent = link.find_parent(['div', 'article', 'section'])
            if not parent:
                continue
            
            parent_text = parent.get_text(' ', strip=True)
            
            # Parse date: "02.07.26 | 4:00PM" format
            date_match = re.search(r'(\d{2})\.(\d{2})\.(\d{2})\s*\|\s*(\d{1,2}:\d{2}\s*(?:AM|PM)?)', parent_text, re.IGNORECASE)
            if not date_match:
                # Try date range format: "04.09.26 - 04.24.26"
                date_match = re.search(r'(\d{2})\.(\d{2})\.(\d{2})', parent_text)
                if date_match:
                    month, day, year = date_match.groups()
                    year = 2000 + int(year)
                    month = int(month)
                    day = int(day)
                    if year != target_year or month != target_month:
                        continue
                    dt_start = datetime(year, month, day, 10, 0)  # Default 10 AM
                    dt_end = dt_start + timedelta(hours=2)
                else:
                    continue
            else:
                month, day, year, time_str = date_match.groups()
                year = 2000 + int(year)
                month = int(month)
                day = int(day)
                
                if year != target_year or month != target_month:
                    continue
                
                # Parse time
                time_str = time_str.strip().upper()
                try:
                    if 'AM' in time_str or 'PM' in time_str:
                        time_obj = datetime.strptime(time_str, "%I:%M%p")
                    else:
                        time_obj = datetime.strptime(time_str, "%H:%M")
                    dt_start = datetime(year, month, day, time_obj.hour, time_obj.minute)
                except ValueError:
                    dt_start = datetime(year, month, day, 18, 0)  # Default 6 PM
                
                dt_end = dt_start + timedelta(hours=2)
            
            # Get title from link text
            title = link.get_text(strip=True)
            if not title or title in ['more info', '.st1{fill:url(#SVGID_1_);}']:
                # Try to find a better title in the parent
                h_tag = parent.find(['h2', 'h3', 'h4'])
                if h_tag:
                    title = h_tag.get_text(strip=True)
                else:
                    continue
            
            if not title or len(title) < 3:
                continue
            
            seen_urls.add(href)
            
            full_url = href if href.startswith('http') else BASE_URL + href
            
            events.append({
                'title': title,
                'url': full_url,
                'dtstart': dt_start,
                'dtend': dt_end,
                'location': VENUE_ADDRESS,
                'description': f'Event at Sonoma Valley Museum of Art. More info: {full_url}'
            })
            
            logger.info(f"Found event: {title} on {dt_start}")
            
        except Exception as e:
            logger.warning(f"Error parsing event: {e}")
            continue
    
    return events

def create_calendar(events, year, month):
    """Create an iCalendar from parsed events."""
    cal = Calendar()
    cal.add('prodid', '-//Sonoma Valley Museum of Art//svma.org//')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', f'SVMA Events - {year}/{month:02d}')
    cal.add('x-wr-timezone', 'America/Los_Angeles')
    
    for event_data in events:
        event = Event()
        event.add('summary', event_data['title'])
        event.add('dtstart', event_data['dtstart'])
        event.add('dtend', event_data['dtend'])
        event.add('url', event_data['url'])
        event.add('location', event_data['location'])
        event.add('description', append_source(event_data.get('description', ''), 'Sonoma Valley Museum of Art'))
        event.add('uid', generate_uid(event_data['title'], event_data['dtstart'], 'svma.org'))
        event.add('x-source', 'Sonoma Valley Museum of Art')
        
        cal.add_component(event)
    
    return cal

def main():
    parser = argparse.ArgumentParser(description='Scrape SVMA events')
    parser.add_argument('--year', type=int, required=True, help='Target year')
    parser.add_argument('--month', type=int, required=True, help='Target month (1-12)')
    parser.add_argument('--output', type=str, help='Output filename')
    args = parser.parse_args()
    
    html = fetch_events_page()
    events = parse_events(html, args.year, args.month)
    
    logger.info(f"Found {len(events)} events for {args.year}-{args.month:02d}")
    
    cal = create_calendar(events, args.year, args.month)
    
    output_file = args.output or f'svma_{args.year}_{args.month:02d}.ics'
    with open(output_file, 'wb') as f:
        f.write(cal.to_ical())
    
    logger.info(f"Written to {output_file}")
    return output_file

if __name__ == '__main__':
    main()
