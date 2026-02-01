#!/usr/bin/env python3
"""
Scraper for Sonoma County Regional Parks calendar
https://parks.sonomacounty.ca.gov/play/calendar
"""

import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event
from datetime import datetime
import re
import argparse
import logging
import hashlib

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = 'https://parks.sonomacounty.ca.gov'
CALENDAR_URL = f'{BASE_URL}/play/calendar'

def fetch_calendar_page():
    """Fetch the main calendar page."""
    logger.info(f"Fetching {CALENDAR_URL}")
    response = requests.get(CALENDAR_URL, timeout=30)
    response.raise_for_status()
    return response.text

def parse_events(html_content, target_year, target_month):
    """Parse events from the calendar HTML."""
    soup = BeautifulSoup(html_content, 'html.parser')
    events = []
    
    # Find all event listings - they're in .listing divs
    for listing in soup.find_all('div', class_='listing'):
        try:
            # Get title and URL
            title_link = listing.find('h3')
            if not title_link:
                title_link = listing.find('h4')
            if not title_link:
                continue
                
            anchor = title_link.find('a')
            if not anchor:
                continue
                
            title = anchor.get_text(strip=True)
            # Clean up "sold out |" prefix
            title = re.sub(r'^sold out\s*\|\s*', '', title, flags=re.IGNORECASE)
            url = anchor.get('href', '')
            
            # Get event content div
            content = listing.find('div', class_='content')
            if not content:
                continue
            
            # Extract date and time from text
            text = content.get_text(' ', strip=True)
            
            # Parse date - format: "February 3, 2026"
            date_match = re.search(r'(\w+)\s+(\d{1,2}),\s+(\d{4})', text)
            if not date_match:
                continue
                
            month_name, day, year = date_match.groups()
            
            # Parse time - format: "4:00 pm - 5:30 pm" or "10:00 am - 12:00 pm"
            time_match = re.search(r'(\d{1,2}:\d{2})\s*(am|pm)\s*-\s*(\d{1,2}:\d{2})\s*(am|pm)', text, re.IGNORECASE)
            
            if time_match:
                start_time_str = f"{time_match.group(1)} {time_match.group(2)}"
                end_time_str = f"{time_match.group(3)} {time_match.group(4)}"
            else:
                # Try single time
                single_time = re.search(r'(\d{1,2}:\d{2})\s*(am|pm)', text, re.IGNORECASE)
                if single_time:
                    start_time_str = f"{single_time.group(1)} {single_time.group(2)}"
                    end_time_str = None
                else:
                    start_time_str = "12:00 pm"
                    end_time_str = None
            
            # Parse the datetime
            try:
                date_str = f"{month_name} {day}, {year}"
                dt_start = datetime.strptime(f"{date_str} {start_time_str}", "%B %d, %Y %I:%M %p")
                if end_time_str:
                    dt_end = datetime.strptime(f"{date_str} {end_time_str}", "%B %d, %Y %I:%M %p")
                else:
                    dt_end = dt_start
            except ValueError as e:
                logger.warning(f"Could not parse date/time for '{title}': {e}")
                continue
            
            # Filter by target month
            if dt_start.year != target_year or dt_start.month != target_month:
                continue
            
            # Get location if present (usually after the pipe)
            location_match = re.search(r'\|\s*([^|]+?)\s*(?:$|PETALUMA|Description)', text)
            location = None
            if location_match:
                loc_text = location_match.group(1).strip()
                # Common location patterns
                if any(word in loc_text.lower() for word in ['park', 'trail', 'regional', 'preserve']):
                    location = loc_text
            
            # Get description (text after the date/time/location info)
            desc_elem = listing.find('p')
            description = desc_elem.get_text(strip=True) if desc_elem else ''
            
            events.append({
                'title': title,
                'url': url,
                'dtstart': dt_start,
                'dtend': dt_end,
                'location': location,
                'description': description
            })
            
            logger.info(f"Found event: {title} on {dt_start}")
            
        except Exception as e:
            logger.warning(f"Error parsing event: {e}")
            continue
    
    return events

def create_calendar(events, year, month):
    """Create an iCalendar from parsed events."""
    cal = Calendar()
    cal.add('prodid', '-//Sonoma County Regional Parks//parks.sonomacounty.ca.gov//')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', f'Sonoma County Parks - {year}/{month:02d}')
    cal.add('x-wr-timezone', 'America/Los_Angeles')
    
    for event_data in events:
        event = Event()
        event.add('summary', event_data['title'])
        event.add('dtstart', event_data['dtstart'])
        event.add('dtend', event_data['dtend'])
        event.add('url', event_data['url'])
        
        if event_data.get('location'):
            event.add('location', event_data['location'])
        if event_data.get('description'):
            event.add('description', event_data['description'])
        
        # Generate a UID
        uid_str = f"{event_data['title']}-{event_data['dtstart'].isoformat()}"
        uid = hashlib.md5(uid_str.encode()).hexdigest()
        event.add('uid', f"{uid}@parks.sonomacounty.ca.gov")
        
        cal.add_component(event)
    
    return cal

def main():
    parser = argparse.ArgumentParser(description='Scrape Sonoma County Parks calendar')
    parser.add_argument('--year', type=int, required=True, help='Target year')
    parser.add_argument('--month', type=int, required=True, help='Target month (1-12)')
    parser.add_argument('--output', type=str, help='Output filename')
    args = parser.parse_args()
    
    html = fetch_calendar_page()
    events = parse_events(html, args.year, args.month)
    
    logger.info(f"Found {len(events)} events for {args.year}-{args.month:02d}")
    
    cal = create_calendar(events, args.year, args.month)
    
    output_file = args.output or f'sonoma_parks_{args.year}_{args.month:02d}.ics'
    with open(output_file, 'wb') as f:
        f.write(cal.to_ical())
    
    logger.info(f"Written to {output_file}")
    return output_file

if __name__ == '__main__':
    main()
