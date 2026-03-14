#!/usr/bin/env python3
"""
Scraper for Sidearm Sports athletics schedules via JSON-LD.

Sidearm Sports is used by hundreds of NCAA athletics programs. Many expose
an ICS feed at /calendar.ashx/calendar.ics, but some disable it. This scraper
extracts SportsEvent JSON-LD from individual sport schedule pages, which is
always available.

Usage:
    # Single sport
    python scrapers/sidearm.py \
        --url "https://godiplomats.com" \
        --sports baseball \
        --name "F&M Baseball" \
        --output cities/lancaster/fandm_baseball.ics

    # All sports (auto-discovers from site navigation)
    python scrapers/sidearm.py \
        --url "https://godiplomats.com" \
        --name "F&M Athletics" \
        --output cities/lancaster/fandm_athletics.ics

    # Specific sports list
    python scrapers/sidearm.py \
        --url "https://godiplomats.com" \
        --sports baseball,football,mens-basketball,womens-basketball \
        --name "F&M Athletics" \
        --output cities/lancaster/fandm_athletics.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import json
import logging
import re
from datetime import datetime
from typing import Any
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from zoneinfo import ZoneInfo

from lib.base import BaseScraper
from lib.utils import DEFAULT_HEADERS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SidearmScraper(BaseScraper):
    """Scraper for Sidearm Sports athletics schedules."""

    name = "Sidearm Athletics"
    domain = "sidearm.com"
    timezone = "America/New_York"

    def __init__(self, base_url: str, sports: list[str] | None = None,
                 source_name: str | None = None, tz: str | None = None):
        super().__init__()
        self.base_url = base_url.rstrip('/')
        self.sports = sports
        if source_name:
            self.name = source_name
        self.domain = base_url.split('//')[1].split('/')[0]
        if tz:
            self.timezone = tz
        self.tz = ZoneInfo(self.timezone)

    def _fetch_page(self, url: str) -> str | None:
        """Fetch a page and return its text content."""
        try:
            req = Request(url, headers=DEFAULT_HEADERS)
            with urlopen(req, timeout=30) as resp:
                return resp.read().decode('utf-8', errors='replace')
        except (HTTPError, URLError) as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return None

    def _discover_sports(self) -> list[str]:
        """Discover available sports from the site's navigation."""
        html = self._fetch_page(self.base_url)
        if not html:
            return []

        # Match /sports/SLUG/schedule links
        slugs = re.findall(r'/sports/([\w-]+)/schedule', html)
        # Deduplicate while preserving order
        seen = set()
        unique = []
        for s in slugs:
            if s not in seen:
                seen.add(s)
                unique.append(s)

        logger.info(f"Discovered {len(unique)} sports: {', '.join(unique)}")
        return unique

    def _extract_jsonld(self, html: str) -> list[dict]:
        """Extract JSON-LD SportsEvent objects from HTML."""
        events = []
        for match in re.finditer(
            r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            html, re.DOTALL
        ):
            try:
                data = json.loads(match.group(1))
                if isinstance(data, list):
                    events.extend(e for e in data if e.get('@type') == 'SportsEvent')
                elif isinstance(data, dict) and data.get('@type') == 'SportsEvent':
                    events.append(data)
            except json.JSONDecodeError:
                continue
        return events

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from all sport schedule pages."""
        sports = self.sports or self._discover_sports()
        if not sports:
            logger.error("No sports found to scrape")
            return []

        all_events = []
        for sport in sports:
            url = f"{self.base_url}/sports/{sport}/schedule"
            logger.info(f"Fetching {sport}: {url}")
            html = self._fetch_page(url)
            if not html:
                continue

            jsonld_events = self._extract_jsonld(html)
            logger.info(f"  {sport}: {len(jsonld_events)} events")

            for je in jsonld_events:
                event = self._parse_event(je, sport)
                if event:
                    all_events.append(event)

        logger.info(f"Total: {len(all_events)} events across {len(sports)} sports")
        return all_events

    def _parse_event(self, data: dict, sport: str) -> dict[str, Any] | None:
        """Parse a JSON-LD SportsEvent into our event dict format."""
        title = data.get('name', '')
        if not title:
            return None

        start_str = data.get('startDate')
        if not start_str:
            return None

        try:
            # Sidearm uses format like "2026-02-21T11:00:00"
            dt = datetime.fromisoformat(start_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=self.tz)
        except ValueError:
            return None

        # Skip past events
        now = datetime.now(self.tz)
        if dt < now:
            return None

        # Location
        location = ''
        loc_data = data.get('location', {})
        if isinstance(loc_data, dict):
            location = loc_data.get('name', '')
            addr = loc_data.get('address', {})
            if isinstance(addr, dict):
                street = addr.get('streetAddress', '')
                if street and street != location:
                    location = f"{location}, {street}" if location else street

        # URL — Sidearm often has null here
        url = data.get('url') or ''

        # Description
        description = data.get('description', '')

        return {
            'title': title,
            'dtstart': dt,
            'dtend': dt,  # Sidearm typically sets endDate == startDate
            'location': location,
            'url': url,
            'description': description,
        }


def main():
    parser = argparse.ArgumentParser(description='Scrape Sidearm Sports athletics schedules')
    parser.add_argument('--url', required=True,
                        help='Base URL of the athletics site (e.g., https://godiplomats.com)')
    parser.add_argument('--sports', default=None,
                        help='Comma-separated sport slugs (default: auto-discover all)')
    parser.add_argument('--name', default='Sidearm Athletics',
                        help='Source name for the calendar')
    parser.add_argument('--timezone', default='America/New_York',
                        help='Timezone for events (default: America/New_York)')
    parser.add_argument('--output', '-o', required=True,
                        help='Output ICS file')

    args = parser.parse_args()

    sports = args.sports.split(',') if args.sports else None

    scraper = SidearmScraper(
        base_url=args.url,
        sports=sports,
        source_name=args.name,
        tz=args.timezone,
    )
    scraper.run(args.output)


if __name__ == '__main__':
    main()
