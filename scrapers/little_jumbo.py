#!/usr/bin/env python3
"""
Scraper for Little Jumbo (cocktail bar + live music, 241 Broadway St, Asheville NC).

Little Jumbo's website exposes a bespoke JSON API at:
    https://www.littlejumbobar.com/events?format=json

Response is a plain list of objects with fields:
    date        "2026-07-20"          (ISO date, no time)
    title       "Mike Holstein trio"
    location    "Little Jumbo: 241 Broadway St., Asheville, NC 28801"
    description (long text)
    link        "https://www.littlejumbobar.com/events/1880/..."
    updated_at  "2026-07-07T10:34:38.873-04:00"

Shows typically start at 8 pm when no time is given.
The standard Squarespace scraper (squarespace.py) fails on this site
because it returns 0 events from the iCal path — the JSON endpoint
is the correct approach.

Usage:
    python scrapers/little_jumbo.py --output cities/asheville/little_jumbo.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import json
import logging
from datetime import datetime, timezone
from typing import Any
from urllib.request import urlopen, Request

from lib.base import BaseScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

EVENTS_URL = 'https://www.littlejumbobar.com/events?format=json'
DEFAULT_LOCATION = 'Little Jumbo, 241 Broadway St, Asheville, NC 28801'
DEFAULT_SHOW_HOUR = 20  # 8 pm

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
    ),
    'Accept': 'application/json, text/html, */*',
    'Accept-Language': 'en-US,en;q=0.9',
}


class LittleJumboScraper(BaseScraper):
    """Scraper for Little Jumbo bar events via bespoke JSON API."""

    name = 'Little Jumbo'
    domain = 'littlejumbobar.com'
    timezone = 'America/New_York'
    default_url = 'https://www.littlejumbobar.com/events'

    def fetch_events(self) -> list[dict[str, Any]]:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(self.timezone)
        now = datetime.now(tz)

        self.logger.info(f'Fetching {EVENTS_URL}')
        req = Request(EVENTS_URL, headers=HEADERS)
        with urlopen(req, timeout=20) as r:
            raw = r.read().decode('utf-8')

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            self.logger.error(f'JSON parse error: {e}')
            return []

        if not isinstance(data, list):
            self.logger.error(f'Unexpected JSON shape: {type(data)}')
            return []

        events: list[dict[str, Any]] = []
        for item in data:
            if not isinstance(item, dict):
                continue

            title = (item.get('title') or '').strip()
            if not title:
                continue

            date_str = (item.get('date') or '').strip()
            if not date_str:
                continue

            # Parse ISO date — no time component in the API response
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                self.logger.warning(f'Unexpected date format: {date_str!r}')
                continue

            # Default to 8 pm show time
            dtstart = datetime(
                date_obj.year, date_obj.month, date_obj.day,
                DEFAULT_SHOW_HOUR, 0, tzinfo=tz
            )

            if dtstart < now:
                continue

            # Location: use API value if present, else default
            location = (item.get('location') or '').strip() or DEFAULT_LOCATION

            description = (item.get('description') or '').strip()
            # Trim very long descriptions
            if len(description) > 800:
                description = description[:797] + '...'

            url = (item.get('link') or self.default_url).strip()

            events.append({
                'title': title,
                'dtstart': dtstart,
                'location': location,
                'description': description,
                'url': url,
            })

        self.logger.info(f'Found {len(events)} future events')
        return events


def main():
    parser = argparse.ArgumentParser(description='Scrape Little Jumbo bar events')
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = LittleJumboScraper()
    scraper.run(args.output)


if __name__ == '__main__':
    main()
