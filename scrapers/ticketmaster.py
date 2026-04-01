#!/usr/bin/env python3
"""
Scraper for Ticketmaster venue events via the Discovery API.

Requires a TICKETMASTER_API_KEY environment variable (or --api-key).
Free keys: https://developer.ticketmaster.com/products-and-docs/apis/getting-started/

Usage:
    python scrapers/ticketmaster.py \
        --venue-id KovZpa2X8e --name "DPAC" \
        --output cities/raleighdurham/dpac.ics

    python scrapers/ticketmaster.py \
        --venue-id KovZpZAJledA --name "Martin Marietta Center" \
        --output cities/raleighdurham/martin_marietta.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Optional
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from zoneinfo import ZoneInfo

from lib.base import BaseScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_BASE = "https://app.ticketmaster.com/discovery/v2"
PAGE_SIZE = 100  # max allowed by TM API


class TicketmasterScraper(BaseScraper):
    """Scraper for Ticketmaster venues via the Discovery API."""

    name = "Ticketmaster"
    domain = "ticketmaster.com"
    timezone = "America/New_York"

    def __init__(self, venue_id: str, api_key: str, source_name: Optional[str] = None,
                 tz: Optional[str] = None):
        super().__init__()
        self.venue_id = venue_id
        self.api_key = api_key
        if source_name:
            self.name = source_name
        if tz:
            self.timezone = tz

    def _fetch_page(self, page: int) -> dict:
        """Fetch one page of events from the Discovery API."""
        url = (f"{API_BASE}/events.json?apikey={self.api_key}"
               f"&venueId={self.venue_id}&size={PAGE_SIZE}&page={page}"
               f"&sort=date,asc")
        req = Request(url)
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8'))

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch all events for the venue, paginating as needed."""
        events = []
        page = 0

        try:
            data = self._fetch_page(page)
        except (HTTPError, URLError) as e:
            self.logger.warning(f"Failed to fetch Ticketmaster events: {e}")
            return []

        total = data.get('page', {}).get('totalElements', 0)
        total_pages = data.get('page', {}).get('totalPages', 0)
        self.logger.info(f"Ticketmaster: {total} events across {total_pages} pages for venue {self.venue_id}")

        while True:
            for e in data.get('_embedded', {}).get('events', []):
                event = self._parse_event(e)
                if event:
                    events.append(event)

            page += 1
            if page >= total_pages:
                break

            # Rate limit: 5 req/sec
            time.sleep(0.25)
            try:
                data = self._fetch_page(page)
            except (HTTPError, URLError) as e:
                self.logger.warning(f"Failed on page {page}: {e}")
                break

        self.logger.info(f"Parsed {len(events)} events for {self.name}")
        return events

    def _parse_event(self, e: dict) -> Optional[dict]:
        """Parse a single Ticketmaster event into our event dict format."""
        dates = e.get('dates', {})
        start = dates.get('start', {})

        local_date = start.get('localDate')
        if not local_date:
            return None

        local_time = start.get('localTime', '00:00:00')
        tz = ZoneInfo(dates.get('timezone', self.timezone))

        try:
            dtstart = datetime.strptime(f"{local_date} {local_time}", "%Y-%m-%d %H:%M:%S")
            dtstart = dtstart.replace(tzinfo=tz)
        except ValueError:
            return None

        # Skip TBD/TBA
        if start.get('dateTBD') or start.get('dateTBA'):
            return None

        # Location from embedded venue
        venues = e.get('_embedded', {}).get('venues', [])
        if venues:
            v = venues[0]
            parts = [v.get('name', '')]
            addr = v.get('address', {})
            if addr.get('line1'):
                parts.append(addr['line1'])
            city = v.get('city', {}).get('name', '')
            state = v.get('state', {}).get('stateCode', '')
            if city:
                parts.append(f"{city}, {state}" if state else city)
            location = ', '.join(p for p in parts if p)
        else:
            location = ''

        return {
            'title': e.get('name', 'Untitled'),
            'dtstart': dtstart,
            'url': e.get('url', ''),
            'location': location,
            'description': '',
        }


def main():
    parser = argparse.ArgumentParser(description="Scrape Ticketmaster venue events")
    parser.add_argument('--venue-id', required=True, help='Ticketmaster venue ID')
    parser.add_argument('--name', default='Ticketmaster', help='Source name')
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--api-key', default=os.environ.get('TICKETMASTER_API_KEY'),
                        help='API key (default: TICKETMASTER_API_KEY env var)')
    parser.add_argument('--timezone', default='America/New_York', help='Timezone')
    parser.add_argument('--default-url', help='Fallback URL when events have no per-event URL')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if not args.api_key:
        print("Error: --api-key or TICKETMASTER_API_KEY env var required", file=sys.stderr)
        sys.exit(1)

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = TicketmasterScraper(
        venue_id=args.venue_id,
        api_key=args.api_key,
        source_name=args.name,
        tz=args.timezone,
    )
    if args.default_url:
        scraper.default_url = args.default_url
    scraper.run(args.output)


if __name__ == '__main__':
    main()
