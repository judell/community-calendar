#!/usr/bin/env python3
"""
Scraper for Creative Sonoma events
https://creativesonoma.org/event/

Fetches RSS feed then scrapes each event page for JSON-LD structured data.
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])  # Add scrapers/ to path

import requests
import feedparser
import json
import re
import argparse
from datetime import datetime
from icalendar import Calendar, Event
import logging
import time
from html import unescape

from lib.utils import DEFAULT_HEADERS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

RSS_URL = 'https://creativesonoma.org/event/feed/'
TIMEZONE = 'America/Los_Angeles'


def fetch_rss():
    """Fetch and parse the RSS feed."""
    logger.info(f"Fetching RSS feed: {RSS_URL}")
    feed = feedparser.parse(RSS_URL)
    logger.info(f"Found {len(feed.entries)} entries in RSS feed")
    return feed.entries


def extract_jsonld(html_content):
    """Extract JSON-LD Event data from HTML."""
    # Look for JSON-LD script with Event type
    pattern = r'<script type="application/ld\+json">({[^<]*"@type":\s*"Event"[^<]*})</script>'
    match = re.search(pattern, html_content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return None


def fetch_event_details(url):
    """Fetch event page and extract JSON-LD data."""
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=30)
        response.raise_for_status()
        return extract_jsonld(response.text)
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None


def parse_datetime(dt_str):
    """Parse ISO datetime string."""
    if not dt_str:
        return None
    try:
        # Handle various ISO formats
        dt_str = dt_str.replace('Z', '+00:00')
        if '+' in dt_str:
            dt_str = dt_str.split('+')[0]
        return datetime.fromisoformat(dt_str)
    except ValueError:
        return None


def clean_text(text):
    """Clean HTML entities and extra whitespace from text."""
    if not text:
        return ''
    text = unescape(text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def create_ics(events, year, month):
    """Create ICS calendar from events."""
    cal = Calendar()
    cal.add('prodid', '-//Creative Sonoma Events//creativesonoma.org//')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', f'Creative Sonoma Events - {year}/{month:02d}')
    cal.add('x-wr-timezone', TIMEZONE)
    
    count = 0
    for event_data in events:
        start_dt = parse_datetime(event_data.get('startDate'))
        if not start_dt:
            continue
            
        # Filter by target month
        if start_dt.year != year or start_dt.month != month:
            continue
        
        event = Event()
        event.add('summary', clean_text(event_data.get('name', 'Untitled Event')))
        event.add('dtstart', start_dt)
        
        end_dt = parse_datetime(event_data.get('endDate'))
        if end_dt:
            event.add('dtend', end_dt)
        else:
            event.add('dtend', start_dt)
        
        if event_data.get('description'):
            event.add('description', clean_text(event_data['description']))
        
        if event_data.get('url'):
            event.add('url', event_data['url'])
        
        # Extract location
        location = event_data.get('location', {})
        if isinstance(location, dict):
            loc_parts = []
            if location.get('name'):
                loc_parts.append(location['name'])
            addr = location.get('address', {})
            if isinstance(addr, dict):
                if addr.get('streetAddress'):
                    loc_parts.append(addr['streetAddress'].strip())
                city_state = []
                if addr.get('addressLocality'):
                    city_state.append(addr['addressLocality'])
                if addr.get('addressRegion'):
                    city_state.append(addr['addressRegion'])
                if city_state:
                    loc_parts.append(', '.join(city_state))
            if loc_parts:
                event.add('location', ', '.join(loc_parts))
        
        cal.add_component(event)
        count += 1
    
    return cal, count


def main(year, month, output=None):
    """Main function to scrape events and create ICS."""
    entries = fetch_rss()
    
    events = []
    for i, entry in enumerate(entries):
        url = entry.get('link')
        if not url:
            continue
        
        logger.info(f"Fetching event {i+1}/{len(entries)}: {entry.get('title', 'Unknown')[:50]}")
        event_data = fetch_event_details(url)
        
        if event_data:
            event_data['url'] = url
            events.append(event_data)
        
        # Be nice to the server
        time.sleep(0.5)
    
    logger.info(f"Successfully fetched {len(events)} events with structured data")
    
    cal, count = create_ics(events, year, month)
    
    filename = output or f'creative_sonoma_{year}_{month:02d}.ics'
    with open(filename, 'wb') as f:
        f.write(cal.to_ical())
    
    logger.info(f"Wrote {count} events to {filename}")
    return filename


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scrape Creative Sonoma events to ICS')
    parser.add_argument('--year', type=int, required=True, help='Target year')
    parser.add_argument('--month', type=int, required=True, help='Target month (1-12)')
    parser.add_argument('--output', '-o', help='Output filename')
    args = parser.parse_args()
    
    main(args.year, args.month, args.output)
