#!/usr/bin/env python3
"""
Scraper for Sonoma County Government calendar
https://sonomacounty.gov/sonoma-county-calendar

Uses JSON API endpoint - includes county meetings, parks events, and more.
"""

import requests
from icalendar import Calendar, Event
from datetime import datetime
import argparse
import logging
import hashlib

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_URL = 'https://sonomacounty.gov/api/FeedData/CalendarEvents'
PAGE_ID = 'x116193'

def fetch_events(year, month):
    """Fetch events from the JSON API."""
    # Calculate start and end dates
    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"
    
    params = {
        'pageId': PAGE_ID,
        'start': start_date,
        'end': end_date
    }
    
    logger.info(f"Fetching events from {start_date} to {end_date}")
    response = requests.get(API_URL, params=params, timeout=30)
    response.raise_for_status()
    
    return response.json()

def parse_events(events_data, target_year, target_month):
    """Parse events from JSON data."""
    events = []
    seen_urls = set()
    
    for event_data in events_data:
        try:
            title = event_data.get('title', '').strip()
            if not title:
                continue
            
            # Skip canceled events
            if event_data.get('className') == 'canceled':
                logger.info(f"Skipping canceled event: {title}")
                continue
            
            # Skip if title starts with CANCELED
            if title.upper().startswith('CANCELED'):
                continue
            
            url = event_data.get('url', '')
            
            # Dedupe by URL
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            # Parse start time
            start_str = event_data.get('start', '')
            if not start_str:
                continue
            
            try:
                dt_start = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    dt_start = datetime.strptime(start_str, "%Y-%m-%d")
                except ValueError:
                    logger.warning(f"Could not parse date: {start_str}")
                    continue
            
            # Filter by target month
            if dt_start.year != target_year or dt_start.month != target_month:
                continue
            
            # Parse end time
            end_str = event_data.get('end', '')
            if end_str:
                try:
                    dt_end = datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    dt_end = dt_start
            else:
                dt_end = dt_start
            
            description = event_data.get('abstract', '')
            
            events.append({
                'title': title,
                'url': url,
                'dtstart': dt_start,
                'dtend': dt_end,
                'description': description,
                'location': 'Sonoma County, CA'
            })
            
            logger.info(f"Found event: {title} on {dt_start}")
            
        except Exception as e:
            logger.warning(f"Error parsing event: {e}")
            continue
    
    return events

def create_calendar(events, year, month):
    """Create an iCalendar from parsed events."""
    cal = Calendar()
    cal.add('prodid', '-//Sonoma County Government//sonomacounty.gov//')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', f'Sonoma County Government - {year}/{month:02d}')
    cal.add('x-wr-timezone', 'America/Los_Angeles')
    
    for event_data in events:
        event = Event()
        event.add('summary', event_data['title'])
        event.add('dtstart', event_data['dtstart'])
        event.add('dtend', event_data['dtend'])
        event.add('url', event_data['url'])
        event.add('location', event_data['location'])
        
        if event_data.get('description'):
            event.add('description', event_data['description'])
        
        # Generate a UID
        uid_str = f"{event_data['title']}-{event_data['dtstart'].isoformat()}"
        uid = hashlib.md5(uid_str.encode()).hexdigest()
        event.add('uid', f"{uid}@sonomacounty.gov")
        
        cal.add_component(event)
    
    return cal

def main():
    parser = argparse.ArgumentParser(description='Scrape Sonoma County Government calendar')
    parser.add_argument('--year', type=int, required=True, help='Target year')
    parser.add_argument('--month', type=int, required=True, help='Target month (1-12)')
    parser.add_argument('--output', type=str, help='Output filename')
    args = parser.parse_args()
    
    events_data = fetch_events(args.year, args.month)
    events = parse_events(events_data, args.year, args.month)
    
    logger.info(f"Found {len(events)} events for {args.year}-{args.month:02d}")
    
    cal = create_calendar(events, args.year, args.month)
    
    output_file = args.output or f'sonoma_county_gov_{args.year}_{args.month:02d}.ics'
    with open(output_file, 'wb') as f:
        f.write(cal.to_ical())
    
    logger.info(f"Written to {output_file}")
    return output_file

if __name__ == '__main__':
    main()
