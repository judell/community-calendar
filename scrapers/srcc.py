#!/usr/bin/env python3
"""
Scraper for Santa Rosa Cycling Club events
https://srcc.com/Calendar

Uses RSS feed at https://srcc.com/Calendar/RSS
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])  # Add scrapers/ to path

import re
import argparse
import logging
from datetime import datetime
from html import unescape
from zoneinfo import ZoneInfo

import feedparser
from bs4 import BeautifulSoup
from icalendar import Calendar, Event

from lib.utils import generate_uid, append_source

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

RSS_URL = 'https://srcc.com/Calendar/RSS'
SOURCE_NAME = 'Santa Rosa Cycling Club'
DOMAIN = 'srcc.com'
TIMEZONE = ZoneInfo('America/Los_Angeles')


def fetch_rss():
    """Fetch and parse the RSS feed."""
    logger.info(f"Fetching RSS feed: {RSS_URL}")
    feed = feedparser.parse(RSS_URL)
    logger.info(f"Found {len(feed.entries)} entries in RSS feed")
    return feed.entries


def clean_html(html_text):
    """Strip HTML tags and clean up text."""
    if not html_text:
        return ''
    soup = BeautifulSoup(html_text, 'html.parser')
    text = soup.get_text(' ', strip=True)
    text = unescape(text)
    # Collapse multiple whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_location(description_html):
    """Extract location from the description HTML."""
    if not description_html:
        return None
    
    soup = BeautifulSoup(description_html, 'html.parser')
    
    # Look for "Starts at" followed by a link
    text = soup.get_text(' ', strip=True)
    
    # Common patterns: "Starts at Esposti Park, Windsor" or "Starts at Healdsburg City Hall"
    match = re.search(r'Starts? at\s+([^.]+?)(?:\s*\d{4,}|\s*Led by|\s*Route:|$)', text, re.IGNORECASE)
    if match:
        location = match.group(1).strip()
        # Clean up
        location = re.sub(r'\s+', ' ', location)
        if len(location) > 10 and len(location) < 200:
            return location
    
    return None


def parse_event(entry, target_year, target_month):
    """Parse a single RSS entry into event data."""
    # Parse pubDate: "Sat, 07 Feb 2026 16:30:00 GMT"
    pub_date = entry.get('published')
    if not pub_date:
        return None
    
    try:
        # feedparser usually parses this into published_parsed
        if entry.get('published_parsed'):
            dt_tuple = entry.published_parsed
            dt_utc = datetime(*dt_tuple[:6], tzinfo=ZoneInfo('UTC'))
        else:
            # Manual parse
            dt_utc = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
            dt_utc = dt_utc.replace(tzinfo=ZoneInfo('UTC'))
        
        # Convert to Pacific
        dt_start = dt_utc.astimezone(TIMEZONE)
    except Exception as e:
        logger.warning(f"Could not parse date '{pub_date}': {e}")
        return None
    
    # Filter by target month
    if dt_start.year != target_year or dt_start.month != target_month:
        return None
    
    # Parse title - format: "Event Name (Day, Month DD, YYYY)"
    title = entry.get('title', '')
    # Remove the date suffix
    title = re.sub(r'\s*\([^)]+\d{4}\)\s*$', '', title)
    title = title.strip()
    
    if not title:
        return None
    
    # Get URL
    url = entry.get('link', '')
    
    # Get description and extract location
    description_html = entry.get('description', '')
    location = extract_location(description_html)
    
    # Clean description for display (truncate the verbose boilerplate)
    description = clean_html(description_html)
    # Truncate at common boilerplate phrases
    for cutoff in ['PLEASE arrive at LEAST', 'Visitors are welcome', 'All riders MUST wear']:
        idx = description.find(cutoff)
        if idx > 0:
            description = description[:idx].strip()
            break
    
    # Limit description length
    if len(description) > 500:
        description = description[:500] + '...'
    
    # Assume rides are ~3 hours
    dt_end = dt_start.replace(hour=dt_start.hour + 3) if dt_start.hour < 21 else dt_start
    
    return {
        'title': title,
        'dtstart': dt_start,
        'dtend': dt_end,
        'url': url,
        'location': location,
        'description': description,
    }


def create_calendar(events, year, month):
    """Create an iCalendar from parsed events."""
    cal = Calendar()
    cal.add('prodid', f'-//{SOURCE_NAME}//{DOMAIN}//')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', f'{SOURCE_NAME} - {year}/{month:02d}')
    cal.add('x-wr-timezone', 'America/Los_Angeles')
    
    for event_data in events:
        event = Event()
        event.add('summary', event_data['title'])
        event.add('dtstart', event_data['dtstart'])
        event.add('dtend', event_data['dtend'])
        
        if event_data.get('url'):
            event.add('url', event_data['url'])
        
        if event_data.get('location'):
            event.add('location', event_data['location'])
        
        event.add('description', append_source(event_data.get('description', ''), SOURCE_NAME))
        event.add('uid', generate_uid(event_data['title'], event_data['dtstart'], DOMAIN))
        event.add('x-source', SOURCE_NAME)
        
        cal.add_component(event)
    
    return cal


def main():
    parser = argparse.ArgumentParser(description='Scrape Santa Rosa Cycling Club events')
    parser.add_argument('--year', type=int, required=True, help='Target year')
    parser.add_argument('--month', type=int, required=True, help='Target month (1-12)')
    parser.add_argument('--output', '-o', type=str, help='Output filename')
    args = parser.parse_args()
    
    entries = fetch_rss()
    
    events = []
    for entry in entries:
        event = parse_event(entry, args.year, args.month)
        if event:
            events.append(event)
            logger.info(f"Found event: {event['title']} on {event['dtstart']}")
    
    logger.info(f"Found {len(events)} events for {args.year}-{args.month:02d}")
    
    cal = create_calendar(events, args.year, args.month)
    
    output_file = args.output or f'srcc_{args.year}_{args.month:02d}.ics'
    with open(output_file, 'wb') as f:
        f.write(cal.to_ical())
    
    logger.info(f"Written to {output_file}")
    return output_file


if __name__ == '__main__':
    main()
