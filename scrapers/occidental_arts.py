import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])  # Add scrapers/ to path

import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event
from datetime import datetime, timedelta
from pytz import timezone
import re
import argparse
from urllib.parse import urljoin
import time
import logging

from lib.utils import fetch_with_retry

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fetch_page(url):
    return fetch_with_retry(url)

def parse_events(html_content, base_url):
    soup = BeautifulSoup(html_content, 'html.parser')
    events = []
    for event_elem in soup.find_all('article', class_='eventlist-event'):
        event = {}
        event['url'] = urljoin(base_url, event_elem.find('a', class_='eventlist-title-link')['href'])
        event['title'] = event_elem.find('a', class_='eventlist-title-link').text.strip()
        date_elem = event_elem.find('time', class_='event-date')
        
        if date_elem and 'datetime' in date_elem.attrs:
            event['date'] = datetime.strptime(date_elem['datetime'], '%Y-%m-%d')
        else:
            logger.warning(f"Skipping event {event['title']} due to missing date")
            continue  # Skip this event if we can't find a valid date
        
        time_start = event_elem.find('time', class_='event-time-localized-start')
        time_end = event_elem.find('time', class_='event-time-localized-end')
        
        # Default to all-day event if times are not found
        event['start'] = event['date']
        event['end'] = event['date'] + timedelta(days=1)
        
        if time_start and time_end:
            start_time = time_start.text.strip()
            end_time = time_end.text.strip()
            
            # Parse start time
            try:
                hour, minute = map(int, start_time.replace('AM', '').replace('PM', '').strip().split(':'))
                event['start'] = event['date'].replace(hour=hour % 12 + (12 if 'PM' in start_time else 0), minute=minute)
            except ValueError:
                logger.warning(f"Failed to parse start time for event {event['title']}")
            
            # Parse end time
            try:
                hour, minute = map(int, end_time.replace('AM', '').replace('PM', '').strip().split(':'))
                event['end'] = event['date'].replace(hour=hour % 12 + (12 if 'PM' in end_time else 0), minute=minute)
            except ValueError:
                logger.warning(f"Failed to parse end time for event {event['title']}")
        
        ical_link = event_elem.find('a', class_='eventlist-meta-export-ical')
        event['ical_link'] = urljoin(base_url, ical_link['href']) if ical_link else None
        
        events.append(event)
        logger.info(f"Parsed event: {event['title']} on {event['date']}")
    return events

def fetch_ical_content(ical_url):
    return fetch_with_retry(ical_url)

def parse_ical_description(ical_content):
    for line in ical_content.split('\n'):
        if line.startswith('DESCRIPTION:'):
            return line.split(':', 1)[1]
    return ""

def create_calendar_event(event, description):
    cal_event = Event()
    cal_event.add('summary', event['title'])
    cal_event.add('dtstart', event['start'])
    cal_event.add('dtend', event['end'])
    cal_event.add('description', description)
    cal_event.add('url', event['url'])
    return cal_event

def event_in_target_month(event, target_year, target_month):
    return event['date'].year == target_year and event['date'].month == int(target_month)

def create_calendar(target_year, target_month, output=None):
    base_url = 'https://www.occidentalcenterforthearts.org'
    events_url = f'{base_url}/upcoming-events'

    # Create a new calendar
    cal = Calendar()
    cal.add('prodid', '-//Occidental Center for the Arts Calendar//occidentalcenterforthearts.org//')
    cal.add('version', '2.0')
    cal.add('x-wr-timezone', 'America/Los_Angeles')
    cal.add('x-wr-calname', f'Occidental Center for the Arts - {target_year}/{target_month}')

    # Fetch the main page and parse events
    main_page_content = fetch_page(events_url)
    events = parse_events(main_page_content, base_url)

    # Process each event
    for event in events:
        if event_in_target_month(event, target_year, int(target_month)):
            description = ""
            if event['ical_link']:
                ical_content = fetch_ical_content(event['ical_link'])
                description = parse_ical_description(ical_content)
            cal_event = create_calendar_event(event, description)
            cal.add_component(cal_event)
            logger.info(f"Added event to calendar: {event['title']}")
        time.sleep(1)  # Add a 1-second delay between processing each event
        logger.debug("Sleeping for 1 second between events")

    # Write the calendar to a file
    filename = output or f'occidental_arts_{target_year}_{target_month}.ics'
    with open(filename, 'wb') as f:
        f.write(cal.to_ical())

    logger.info(f"Calendar file '{filename}' has been created")
    return filename

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create an iCalendar file for Occidental Center for the Arts events.')
    parser.add_argument('--year', type=str, required=True, help='Target year (e.g., 2024)')
    parser.add_argument('--month', type=str, required=True, help='Target month (01-12)')
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    if not args.month.isdigit() or int(args.month) < 1 or int(args.month) > 12:
        parser.error("Month must be a two-digit string between 01 and 12")

    if not args.year.isdigit() or len(args.year) != 4:
        parser.error("Year must be a four-digit string")

    filename = create_calendar(int(args.year), args.month, args.output)
    print(f"Calendar file '{filename}' has been created.")