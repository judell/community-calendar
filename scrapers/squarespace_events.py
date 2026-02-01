#!/usr/bin/env python3
"""
Scraper for Squarespace event pages
Supports sites like sjshbg.org, cantiamosonoma.org

Fetches individual event iCal files and combines them.
"""

import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event
from datetime import datetime
import re
import argparse
import logging
import hashlib
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Known Squarespace event sites
SITES = {
    'sjshbg': {
        'name': 'St. John the Baptist Catholic School',
        'base_url': 'https://sjshbg.org',
        'events_path': '/events'
    },
    'cantiamo': {
        'name': 'Cantiamo Sonoma',
        'base_url': 'https://cantiamosonoma.org',
        'events_path': '/events'
    }
}

def fetch_page(url):
    """Fetch a page with retry logic."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text

def get_event_urls(site_config):
    """Get all event URLs from the events page."""
    url = site_config['base_url'] + site_config['events_path']
    logger.info(f"Fetching event list from {url}")
    
    html = fetch_page(url)
    soup = BeautifulSoup(html, 'html.parser')
    
    event_urls = set()
    for link in soup.find_all('a', href=re.compile(r'/events/')):
        href = link.get('href', '')
        if href and not href.endswith('?format=ical'):
            # Normalize URL
            if href.startswith('/'):
                href = site_config['base_url'] + href
            # Remove query strings
            href = href.split('?')[0]
            event_urls.add(href)
    
    return list(event_urls)

def fetch_event_ical(event_url):
    """Fetch iCal data for a single event."""
    ical_url = event_url + '?format=ical'
    logger.info(f"Fetching iCal: {ical_url}")
    
    try:
        response = requests.get(ical_url, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.warning(f"Failed to fetch {ical_url}: {e}")
        return None

def parse_ical_event(ical_text):
    """Parse a single event from iCal text."""
    try:
        cal = Calendar.from_ical(ical_text)
        for component in cal.walk():
            if component.name == 'VEVENT':
                return {
                    'summary': str(component.get('summary', '')),
                    'dtstart': component.get('dtstart').dt if component.get('dtstart') else None,
                    'dtend': component.get('dtend').dt if component.get('dtend') else None,
                    'location': str(component.get('location', '')),
                    'description': str(component.get('description', '')),
                    'uid': str(component.get('uid', ''))
                }
    except Exception as e:
        logger.warning(f"Failed to parse iCal: {e}")
    return None

def scrape_site(site_key, target_year, target_month):
    """Scrape all events from a site for a target month."""
    if site_key not in SITES:
        raise ValueError(f"Unknown site: {site_key}")
    
    site_config = SITES[site_key]
    events = []
    
    event_urls = get_event_urls(site_config)
    logger.info(f"Found {len(event_urls)} event URLs")
    
    for event_url in event_urls:
        ical_text = fetch_event_ical(event_url)
        if not ical_text:
            continue
        
        event_data = parse_ical_event(ical_text)
        if not event_data or not event_data['dtstart']:
            continue
        
        # Handle date vs datetime
        dt = event_data['dtstart']
        if hasattr(dt, 'year'):
            event_year = dt.year
            event_month = dt.month
        else:
            continue
        
        # Filter by target month
        if event_year == target_year and event_month == target_month:
            event_data['url'] = event_url
            events.append(event_data)
            logger.info(f"Found event: {event_data['summary']} on {dt}")
        
        # Rate limiting
        time.sleep(0.5)
    
    return events, site_config

def create_calendar(events, site_config, year, month):
    """Create an iCalendar from parsed events."""
    cal = Calendar()
    cal.add('prodid', f'-//{site_config["name"]}//{site_config["base_url"]}//')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', f'{site_config["name"]} - {year}/{month:02d}')
    cal.add('x-wr-timezone', 'America/Los_Angeles')
    
    for event_data in events:
        event = Event()
        event.add('summary', event_data['summary'])
        event.add('dtstart', event_data['dtstart'])
        if event_data.get('dtend'):
            event.add('dtend', event_data['dtend'])
        if event_data.get('url'):
            event.add('url', event_data['url'])
        if event_data.get('location'):
            event.add('location', event_data['location'])
        if event_data.get('description'):
            event.add('description', event_data['description'])
        
        # Use original UID or generate one
        uid = event_data.get('uid') or hashlib.md5(
            f"{event_data['summary']}-{event_data['dtstart']}".encode()
        ).hexdigest()
        event.add('uid', uid)
        
        cal.add_component(event)
    
    return cal

def main():
    parser = argparse.ArgumentParser(description='Scrape Squarespace event sites')
    parser.add_argument('--site', type=str, required=True, 
                        choices=list(SITES.keys()),
                        help=f'Site to scrape: {list(SITES.keys())}')
    parser.add_argument('--year', type=int, required=True, help='Target year')
    parser.add_argument('--month', type=int, required=True, help='Target month (1-12)')
    parser.add_argument('--output', type=str, help='Output filename')
    args = parser.parse_args()
    
    events, site_config = scrape_site(args.site, args.year, args.month)
    
    logger.info(f"Found {len(events)} events for {args.year}-{args.month:02d}")
    
    cal = create_calendar(events, site_config, args.year, args.month)
    
    output_file = args.output or f'{args.site}_{args.year}_{args.month:02d}.ics'
    with open(output_file, 'wb') as f:
        f.write(cal.to_ical())
    
    logger.info(f"Written to {output_file}")
    return output_file

if __name__ == '__main__':
    main()
