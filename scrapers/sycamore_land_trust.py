#!/usr/bin/env python3
"""
Scraper for Sycamore Land Trust events calendar.

Custom WordPress theme with ACF fields rendered as structured HTML.
All events on a single page, no pagination needed.

Usage:
    python scrapers/sycamore_land_trust.py --output cities/bloomington/sycamore_land_trust.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import logging
import re
import subprocess
from datetime import datetime
from typing import Any

from lib.base import BaseScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

EVENTS_URL = 'https://sycamorelandtrust.org/bulletin-board/events-calendar/'

MONTHS = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12,
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
    'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
}


def parse_date_time(date_str: str) -> tuple[datetime, datetime | None]:
    """Parse date string like 'Saturday, March 29, 9:00 am - 12:00 pm'."""
    # Clean up HTML entities
    date_str = date_str.replace('\xa0', ' ').replace('&nbsp;', ' ').strip()

    # Remove day name prefix
    date_str = re.sub(r'^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s*', '', date_str, flags=re.IGNORECASE)

    # Match: "Month Day, Time - Time" or "Month Day"
    m = re.match(
        r'(\w+)\s+(\d{1,2}),?\s*(?:(\d{1,2}):(\d{2})\s*(am|pm))?\s*(?:-\s*(\d{1,2}):(\d{2})\s*(am|pm))?',
        date_str, re.IGNORECASE
    )
    if not m:
        return None, None

    month_name = m.group(1).lower()
    day = int(m.group(2))
    month = MONTHS.get(month_name)
    if not month:
        return None, None

    # Infer year
    now = datetime.now()
    year = now.year
    try:
        dt = datetime(year, month, day)
    except ValueError:
        return None, None
    if dt.date() < now.date():
        dt = datetime(year + 1, month, day)

    dtstart = dt
    dtend = None

    # Parse start time
    if m.group(3):
        hour = int(m.group(3))
        minute = int(m.group(4))
        ampm = m.group(5).lower()
        if ampm == 'pm' and hour != 12:
            hour += 12
        if ampm == 'am' and hour == 12:
            hour = 0
        dtstart = dtstart.replace(hour=hour, minute=minute)

    # Parse end time
    if m.group(6):
        hour = int(m.group(6))
        minute = int(m.group(7))
        ampm = m.group(8).lower()
        if ampm == 'pm' and hour != 12:
            hour += 12
        if ampm == 'am' and hour == 12:
            hour = 0
        dtend = dt.replace(hour=hour, minute=minute)

    return dtstart, dtend


class SycamoreLandTrustScraper(BaseScraper):
    """Scraper for Sycamore Land Trust events."""

    name = "Sycamore Land Trust"
    domain = "sycamorelandtrust.org"

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch and parse events from the calendar page."""
        logger.info(f"Fetching {EVENTS_URL}")
        result = subprocess.run(
            ['curl', '-sL', EVENTS_URL],
            capture_output=True, text=True, timeout=30
        )
        html = result.stdout

        # Parse event items
        events = []
        # Split on event items
        items = re.split(r'<div class="item">', html)[1:]  # skip before first

        for item in items:
            # Extract title and URL
            title_m = re.search(r'<h1><a href="([^"]*)">(.*?)</a></h1>', item, re.DOTALL)
            if not title_m:
                continue
            url = title_m.group(1)
            title = re.sub(r'<[^>]+>', '', title_m.group(2)).strip()

            # Extract location
            loc_m = re.search(r'<span class="location"></span>\s*<a[^>]*>(.*?)</a>', item, re.DOTALL)
            location = re.sub(r'<[^>]+>', '', loc_m.group(1)).strip() if loc_m else ''

            # Extract date/time
            date_m = re.search(r'<span class="date"></span>(.*?)</li>', item, re.DOTALL)
            if not date_m:
                continue
            date_text = re.sub(r'<[^>]+>', '', date_m.group(1)).strip()

            dtstart, dtend = parse_date_time(date_text)
            if not dtstart:
                logger.warning(f"Could not parse date: {date_text!r} for {title}")
                continue

            # Extract description
            desc_m = re.search(r'</ul>\s*<p>(.*?)</p>', item, re.DOTALL)
            description = re.sub(r'<[^>]+>', '', desc_m.group(1)).strip() if desc_m else ''

            events.append({
                'title': title,
                'dtstart': dtstart,
                'dtend': dtend,
                'location': location,
                'description': description,
                'url': url,
            })

        return events


def main():
    parser = argparse.ArgumentParser(description='Scrape Sycamore Land Trust events')
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = SycamoreLandTrustScraper()
    scraper.run(args.output)


if __name__ == '__main__':
    main()
