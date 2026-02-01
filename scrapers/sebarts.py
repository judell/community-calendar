import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event
from datetime import datetime, timedelta
import re
import argparse
from urllib.parse import urljoin
import logging
import time
import random

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fetch_with_retry(url, max_retries=5, base_delay=1):
    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching URL: {url}")
            response = requests.get(url)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to fetch {url} after {max_retries} attempts. Error: {str(e)}")
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            logger.warning(f"Request to {url} failed. Retrying in {delay:.2f} seconds... (Attempt {attempt + 1}/{max_retries})")
            time.sleep(delay)

def parse_events(html_content, base_url):
    soup = BeautifulSoup(html_content, 'html.parser')
    events = []
    for event_elem in soup.find_all('a', href=re.compile(r'/classes-lectures/')):
        event = {}
        event['url'] = urljoin(base_url, event_elem['href'])
        event['title'] = event_elem.text.strip()
        events.append(event)
        logger.info(f"Found event: {event['title']}")
    return events

def parse_event_details(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    details = {}

    # Find summary (title)
    title_elem = soup.find('h1', class_='page-title')
    if title_elem:
        details['summary'] = title_elem.text.strip()
    else:
        # Fallback to meta title if page title is not found
        meta_title = soup.find('meta', property='og:title')
        if meta_title:
            details['summary'] = meta_title['content'].strip()
        else:
            details['summary'] = "Untitled Event"

    # Find description
    description_elem = soup.find('div', class_='sqs-block-content')
    details['description'] = description_elem.text.strip() if description_elem else ""

    # Find date and time
    date_elem = soup.find('time', class_='event-date')
    if date_elem:
        date_str = date_elem.text.strip()
        time_elem = soup.find('time', class_='event-time')
        time_str = time_elem.text.strip() if time_elem else ""
        
        # Parse date and time
        try:
            # Remove the day of the week from the date string
            date_str = re.sub(r'^[A-Za-z]+,\s*', '', date_str)
            date_obj = datetime.strptime(date_str, "%B %d, %Y")
            if time_str:
                start_time, end_time = time_str.split(' - ')
                details['dtstart'] = datetime.strptime(f"{date_str} {start_time}", "%B %d, %Y %I:%M%p")
                details['dtend'] = datetime.strptime(f"{date_str} {end_time}", "%B %d, %Y %I:%M%p")
            else:
                details['dtstart'] = date_obj
                details['dtend'] = date_obj + timedelta(days=1)  # All-day event
        except ValueError as e:
            logger.error(f"Failed to parse date/time: {e}")
            details['dtstart'] = details['dtend'] = None

    logger.info(f"Parsed event details: {details['summary']}")
    return details

def create_calendar_event(event, details):
    cal_event = Event()
    cal_event.add('summary', details['summary'])
    cal_event.add('description', details.get('description', ''))
    cal_event.add('url', event['url'])
    
    if details.get('dtstart'):
        cal_event.add('dtstart', details['dtstart'])
    if details.get('dtend'):
        cal_event.add('dtend', details['dtend'])
    
    return cal_event

def event_in_target_month(event_date, target_year, target_month):
    return event_date and event_date.year == target_year and event_date.month == int(target_month)

def create_calendar(target_year, target_month, output=None):
    base_url = 'https://www.sebarts.org'
    events_url = f'{base_url}/classes-and-events'

    # Create a new calendar
    cal = Calendar()
    cal.add('prodid', '-//Sebastopol Center for the Arts Calendar//sebarts.org//')
    cal.add('version', '2.0')
    cal.add('x-wr-timezone', 'America/Los_Angeles')
    cal.add('x-wr-calname', f'Sebastopol Center for the Arts - {target_year}/{target_month}')

    # Fetch the main page and parse events (only once)
    main_page_content = fetch_with_retry(events_url)
    events = parse_events(main_page_content, base_url)

    # Process each event
    for event in events:
        event_content = fetch_with_retry(event['url'])
        details = parse_event_details(event_content)
        
        if event_in_target_month(details.get('dtstart'), target_year, int(target_month)):
            cal_event = create_calendar_event(event, details)
            cal.add_component(cal_event)
            logger.info(f"Added event to calendar: {details['summary']}")
        else:
            logger.info(f"Skipped event not in target month: {details['summary']}")
        
        # Add a delay between requests to avoid hitting rate limits
        time.sleep(2)

    # Write the calendar to a file
    filename = output or f'sebarts_{target_year}_{target_month}.ics'
    with open(filename, 'wb') as f:
        f.write(cal.to_ical())
    
    logger.info(f"Calendar file '{filename}' has been created")
    return filename

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create an iCalendar file for Sebastopol Center for the Arts events.')
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