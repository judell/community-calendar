#!/usr/bin/env python3
"""
Scraper for Copperfield's Books events
https://copperfieldsbooks.com/upcoming-events

Drupal site with clean HTML structure.
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

BASE_URL = 'https://copperfieldsbooks.com'
EVENTS_URL = f'{BASE_URL}/upcoming-events'

# Copperfield's store locations
STORE_LOCATIONS = {
    'petaluma': '140 Kentucky Street, Petaluma, CA 94952',
    'sebastopol': '138 N Main St, Sebastopol, CA 95472',
    'healdsburg': '104 Matheson Street, Healdsburg, CA 95448',
    'san rafael': '850 Fourth Street, San Rafael, CA 94901',
    'napa': '1300 First Street Suite 398, Napa, CA 94558',
    'calistoga': '1330 Lincoln Avenue, Calistoga, CA 94515',
    'montgomery village': '2316 Montgomery Drive, Santa Rosa, CA 95405',
}

def fetch_events_page():
    """Fetch the main events page."""
    logger.info(f"Fetching {EVENTS_URL}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    response = requests.get(EVENTS_URL, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text

def fetch_event_details(event_url):
    """Fetch detailed event page."""
    logger.info(f"Fetching event details: {event_url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        response = requests.get(event_url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.warning(f"Could not fetch event details: {e}")
        return None

def parse_event_detail_page(html_content):
    """Parse event details from individual event page."""
    soup = BeautifulSoup(html_content, 'html.parser')
    details = {}
    
    # Get description from meta or content
    meta_desc = soup.find('meta', {'name': 'description'})
    if meta_desc:
        details['description'] = meta_desc.get('content', '')
    
    # Look for time info
    time_elem = soup.find(class_=re.compile(r'time|hour'))
    if time_elem:
        details['time_text'] = time_elem.get_text(strip=True)
    
    return details

def parse_events(html_content, target_year, target_month):
    """Parse events from the events listing page."""
    soup = BeautifulSoup(html_content, 'html.parser')
    events = []
    seen_events = set()
    
    # Find all event rows
    for row in soup.find_all('div', class_='views-row'):
        try:
            # Get event title and link
            title_elem = row.find('h2') or row.find('h3') or row.find(class_='title')
            if not title_elem:
                continue
            
            link = title_elem.find('a') or row.find('a', href=re.compile(r'/event/'))
            if not link:
                continue
            
            title = title_elem.get_text(strip=True)
            event_url = link.get('href', '')
            if not event_url.startswith('http'):
                event_url = BASE_URL + event_url
            
            # Dedupe
            if event_url in seen_events:
                continue
            seen_events.add(event_url)
            
            # Get date from the date element
            date_elem = row.find(class_=re.compile(r'date'))
            if not date_elem:
                continue
            
            date_text = date_elem.get_text(' ', strip=True)
            
            # Parse date: "Feb 03" or similar
            date_match = re.search(r'([A-Za-z]{3})\s+(\d{1,2})', date_text)
            if not date_match:
                continue
            
            month_abbr = date_match.group(1)
            day = int(date_match.group(2))
            
            # Convert month abbreviation to number
            month_map = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}
            month = month_map.get(month_abbr.lower())
            if not month:
                continue
            
            # Infer year - if month is in the past, it might be next year
            year = target_year
            
            # Filter by target month
            if month != target_month:
                continue
            
            # Get location from tags or text
            location = None
            location_text = row.get_text(' ', strip=True).lower()
            for loc_name, address in STORE_LOCATIONS.items():
                if loc_name in location_text:
                    location = f"Copperfield's Books, {address}"
                    break
            
            if not location:
                location = "Copperfield's Books"  # Default
            
            # Get time if available - default to evening
            time_elem = row.find(class_=re.compile(r'time'))
            if time_elem:
                time_text = time_elem.get_text(strip=True)
                time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)', time_text, re.IGNORECASE)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2) or 0)
                    ampm = time_match.group(3).lower()
                    if ampm == 'pm' and hour != 12:
                        hour += 12
                    elif ampm == 'am' and hour == 12:
                        hour = 0
                    dt_start = datetime(year, month, day, hour, minute)
                else:
                    dt_start = datetime(year, month, day, 18, 0)  # Default 6 PM
            else:
                dt_start = datetime(year, month, day, 18, 0)  # Default 6 PM
            
            # Events typically 1-2 hours
            dt_end = dt_start + timedelta(hours=2)
            
            # Get event type tags
            tags = []
            for tag_elem in row.find_all(class_=re.compile(r'tag|category|type')):
                tag_text = tag_elem.get_text(strip=True)
                if tag_text and len(tag_text) < 50:
                    tags.append(tag_text)
            
            # Get description snippet
            desc_elem = row.find('p') or row.find(class_=re.compile(r'desc|body|summary'))
            description = ''
            if desc_elem:
                description = desc_elem.get_text(' ', strip=True)[:500]
            
            if tags:
                description = f"{', '.join(tags)}. {description}"
            
            description += f"\n\nMore info: {event_url}"
            
            events.append({
                'title': title,
                'url': event_url,
                'dtstart': dt_start,
                'dtend': dt_end,
                'location': location,
                'description': description.strip()
            })
            
            logger.info(f"Found event: {title} on {dt_start}")
            
        except Exception as e:
            logger.warning(f"Error parsing event: {e}")
            continue
    
    return events

def create_calendar(events, year, month):
    """Create an iCalendar from parsed events."""
    cal = Calendar()
    cal.add('prodid', '-//Copperfields Books//copperfieldsbooks.com//')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', f"Copperfield's Books - {year}/{month:02d}")
    cal.add('x-wr-timezone', 'America/Los_Angeles')
    
    for event_data in events:
        event = Event()
        event.add('summary', event_data['title'])
        event.add('dtstart', event_data['dtstart'])
        event.add('dtend', event_data['dtend'])
        event.add('url', event_data['url'])
        event.add('location', event_data['location'])
        event.add('description', event_data['description'])
        
        # Generate a UID
        uid_str = f"{event_data['title']}-{event_data['dtstart'].isoformat()}"
        uid = hashlib.md5(uid_str.encode()).hexdigest()
        event.add('uid', f"{uid}@copperfieldsbooks.com")
        event.add('x-source', "Copperfield's Books")
        
        cal.add_component(event)
    
    return cal

def main():
    parser = argparse.ArgumentParser(description="Scrape Copperfield's Books events")
    parser.add_argument('--year', type=int, required=True, help='Target year')
    parser.add_argument('--month', type=int, required=True, help='Target month (1-12)')
    parser.add_argument('--output', type=str, help='Output filename')
    args = parser.parse_args()
    
    html = fetch_events_page()
    events = parse_events(html, args.year, args.month)
    
    logger.info(f"Found {len(events)} events for {args.year}-{args.month:02d}")
    
    cal = create_calendar(events, args.year, args.month)
    
    output_file = args.output or f'copperfields_{args.year}_{args.month:02d}.ics'
    with open(output_file, 'wb') as f:
        f.write(cal.to_ical())
    
    logger.info(f"Written to {output_file}")
    return output_file

if __name__ == '__main__':
    main()
