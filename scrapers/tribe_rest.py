#!/usr/bin/env python3
"""
Parameterized scraper for WordPress "The Events Calendar" (Tribe) sites
whose ?ical=1 is blocked/410 but whose REST API works.

Usage:
    python scrapers/tribe_rest.py \
        --api-base "https://www.weavervillenc.org" \
        --name "Town of Weaverville" \
        --output cities/asheville/weaverville.ics

    python scrapers/tribe_rest.py \
        --api-base "https://www.fletchernc.org" \
        --name "Town of Fletcher" \
        --output cities/asheville/fletcher.ics

The REST endpoint is discovered as:
    {api-base}/wp-json/tribe/events/v1/events/

Pagination is automatic. By default fetches up to 6 months ahead
(controlled by SCRAPE_MONTHS env var, inherited from BaseScraper.run()).
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import logging
import re
from datetime import datetime
from typing import Any, Optional
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from lib.base import BaseScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; CommunityCalendar/1.0)',
    'Accept': 'application/json',
}


class TribeRestScraper(BaseScraper):
    """
    Thin parameterized wrapper around the Tribe Events REST API.

    Accepts api_base at runtime so a single file handles multiple sites.
    Heavy lifting (pagination, field parsing, HTML stripping) is here
    rather than delegating to lib/tribe_events.py so we can add the
    start_date filter without modifying the shared lib.
    """

    per_page: int = 50
    max_pages: int = 300  # hard cap; BaseScraper.run() filters by date

    def __init__(
        self,
        api_base: str,
        source_name: str,
        tz: str = "America/New_York",
        default_location: str = "",
    ):
        self.api_base = api_base.rstrip('/')
        self.name = source_name
        self.domain = urlparse(self.api_base).netloc.removeprefix('www.')
        self.timezone = tz
        self.default_location = default_location
        self.api_url = f"{self.api_base}/wp-json/tribe/events/v1/events/"
        super().__init__()

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch future events from the Tribe Events REST API."""
        all_events: list[dict[str, Any]] = []
        tz = ZoneInfo(self.timezone)
        from datetime import timedelta
        now = datetime.now(tz)
        today = now.strftime('%Y-%m-%d')
        # Cap API fetch at SCRAPE_MONTHS (default 6) to avoid fetching thousands
        # of recurring events — the BaseScraper.run() cutoff will prune anything
        # beyond that window anyway.
        end_date = (now + timedelta(days=self.months_ahead * 31)).strftime('%Y-%m-%d')

        for page in range(1, self.max_pages + 1):
            url = (
                f"{self.api_url}"
                f"?per_page={self.per_page}"
                f"&page={page}"
                f"&start_date={today}"
                f"&end_date={end_date}"
            )
            self.logger.info(f"Fetching page {page}: {url}")

            try:
                response = requests.get(url, headers=HEADERS, timeout=30)
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                self.logger.warning(f"Error fetching page {page}: {e}")
                break

            events = data.get('events', [])
            if not events:
                break

            for item in events:
                parsed = self._parse_event(item, tz)
                if parsed:
                    all_events.append(parsed)

            total_pages = data.get('total_pages', 1)
            self.logger.info(
                f"  Page {page}/{total_pages} — {len(events)} events, "
                f"running total {len(all_events)}"
            )
            if page >= total_pages:
                break

        self.logger.info(f"Found {len(all_events)} events total")
        return all_events

    def _parse_event(self, item: dict, tz: ZoneInfo) -> Optional[dict[str, Any]]:
        """Parse a single event from the Tribe Events API response."""
        title = item.get('title', '')
        if not title:
            return None

        start_str = item.get('start_date', '')
        if not start_str:
            return None

        try:
            dtstart = datetime.fromisoformat(start_str).replace(tzinfo=tz)
        except ValueError:
            self.logger.debug(f"Skipping event with bad start_date: {start_str!r}")
            return None

        dtend: Optional[datetime] = None
        end_str = item.get('end_date', '')
        if end_str:
            try:
                dtend = datetime.fromisoformat(end_str).replace(tzinfo=tz)
            except ValueError:
                pass

        # Location from venue sub-object
        venue = item.get('venue') or {}
        location_parts = [
            venue.get('venue', ''),
            venue.get('address', ''),
            venue.get('city', ''),
            venue.get('state', ''),
        ]
        location = ', '.join(p for p in location_parts if p) or self.default_location

        # Description — strip HTML tags
        desc_html = item.get('description', '') or ''
        desc = BeautifulSoup(desc_html, 'html.parser').get_text(strip=True)
        desc = re.sub(r'\s+', ' ', desc)[:500]

        # URL
        url = item.get('url', '')

        # Stable UID based on Tribe event id
        event_id = item.get('id', '')
        uid = f"tribe-{event_id}@{self.domain}" if event_id else None

        return {
            'title': title,
            'dtstart': dtstart,
            'dtend': dtend,
            'url': url,
            'location': location,
            'description': desc,
            'uid': uid,
        }


def main():
    parser = argparse.ArgumentParser(
        description="Scrape a Tribe Events Calendar REST API (WordPress)"
    )
    parser.add_argument(
        '--api-base', required=True,
        help='Base site URL, e.g. https://www.weavervillenc.org'
    )
    parser.add_argument('--name', required=True, help='Calendar/source display name')
    parser.add_argument(
        '--timezone', default='America/New_York',
        help='IANA timezone (default: America/New_York)'
    )
    parser.add_argument(
        '--default-location', default='',
        help='Fallback location when the API venue is empty'
    )
    parser.add_argument('--output', '-o', help='Output ICS file path')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = TribeRestScraper(
        api_base=args.api_base,
        source_name=args.name,
        tz=args.timezone,
        default_location=args.default_location,
    )
    scraper.run(args.output)


if __name__ == '__main__':
    main()
