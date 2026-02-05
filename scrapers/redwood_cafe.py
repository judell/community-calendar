#!/usr/bin/env python3
"""
Scraper for Redwood Cafe Cotati events
https://redwoodcafecotati.com/events/

Uses WordPress "My Calendar" plugin
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

from lib.utils import generate_uid, append_source

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = 'https://redwoodcafecotati.com'
EVENTS_URL = f'{BASE_URL}/events/'

VENUE_ADDRESS = "Redwood Cafe, 8240 Old Redwood Hwy, Cotati, CA 94931"

def fetch_events_page(year, month):
    """Fetch the events page for a specific month."""
    url = f"{EVENTS_URL}?month={month:02d}&yr={year}"
    logger.info(f"Fetching {url}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.text

def parse_events(html_content, target_year, target_month):
    """Parse events from the calendar HTML."""
    soup = BeautifulSoup(html_content, 'html.parser')
    events = []
    
    # Find calendar event articles
    for article in soup.find_all('article', class_='calendar-event'):
        try:
            # Get event title from button data-modal-title attribute
            button = article.find('button', class_='mc-modal')
            if not button:
                continue
            
            title = button.get('data-modal-title', '')
            if not title:
                continue
            
            # Decode HTML entities
            title = title.replace('&amp;', '&')
            
            # Get time from button text (e.g., "6:00 PM: Cedar Mountain String Band")
            button_text = button.get_text(' ', strip=True)
            time_match = re.search(r'(\d{1,2}:\d{2})\s*(AM|PM)', button_text, re.IGNORECASE)
            
            # Find the date from the mc-day-date span in the parent structure
            # The structure is: <span class='mc-date'>...<span class='mc-day-date'>February 5, 2026</span>...</span>
            # Look in the HTML before this article for the date
            article_id = article.get('id', '')
            
            # Parse day from article ID (e.g., mc_calendar_05_482-calendar-482 -> day 05)
            day_match = re.search(r'mc_calendar_(\d{2})_', article_id)
            if not day_match:
                continue
            
            day = int(day_match.group(1))
            
            # Construct the date
            try:
                event_date = datetime(target_year, target_month, day)
            except ValueError:
                logger.warning(f"Invalid date: {target_year}-{target_month}-{day}")
                continue
            
            # Parse time
            if time_match:
                time_str = f"{time_match.group(1)} {time_match.group(2)}"
                try:
                    time_obj = datetime.strptime(time_str, "%I:%M %p")
                    dt_start = event_date.replace(hour=time_obj.hour, minute=time_obj.minute)
                except ValueError:
                    dt_start = event_date.replace(hour=18, minute=0)  # Default 6 PM
            else:
                dt_start = event_date.replace(hour=18, minute=0)  # Default 6 PM
            
            # Events typically run 2-3 hours
            dt_end = dt_start + timedelta(hours=3)
            
            events.append({
                'title': title,
                'url': EVENTS_URL,
                'dtstart': dt_start,
                'dtend': dt_end,
                'location': VENUE_ADDRESS,
                'description': f'Live music at Redwood Cafe Cotati.'
            })
            
            logger.info(f"Found event: {title} on {dt_start}")
            
        except Exception as e:
            logger.warning(f"Error parsing event: {e}")
            continue
    
    return events

def create_calendar(events, year, month):
    """Create an iCalendar from parsed events."""
    cal = Calendar()
    cal.add('prodid', '-//Redwood Cafe Cotati//redwoodcafecotati.com//')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', f'Redwood Cafe Cotati - {year}/{month:02d}')
    cal.add('x-wr-timezone', 'America/Los_Angeles')
    
    for event_data in events:
        event = Event()
        event.add('summary', event_data['title'])
        event.add('dtstart', event_data['dtstart'])
        event.add('dtend', event_data['dtend'])
        event.add('url', event_data['url'])
        event.add('location', event_data['location'])
        event.add('description', append_source(event_data.get('description', ''), 'Redwood Cafe'))
        event.add('uid', generate_uid(event_data['title'], event_data['dtstart'], 'redwoodcafecotati.com'))
        event.add('x-source', 'Redwood Cafe')
        
        cal.add_component(event)
    
    return cal

def main():
    parser = argparse.ArgumentParser(description='Scrape Redwood Cafe events')
    parser.add_argument('--year', type=int, required=True, help='Target year')
    parser.add_argument('--month', type=int, required=True, help='Target month (1-12)')
    parser.add_argument('--output', type=str, help='Output filename')
    args = parser.parse_args()
    
    html = fetch_events_page(args.year, args.month)
    events = parse_events(html, args.year, args.month)
    
    logger.info(f"Found {len(events)} events for {args.year}-{args.month:02d}")
    
    cal = create_calendar(events, args.year, args.month)
    
    output_file = args.output or f'redwood_cafe_{args.year}_{args.month:02d}.ics'
    with open(output_file, 'wb') as f:
        f.write(cal.to_ical())
    
    logger.info(f"Written to {output_file}")
    return output_file

if __name__ == '__main__':
    main()
