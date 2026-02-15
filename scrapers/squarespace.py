#!/usr/bin/env python3
"""
Generic scraper for Squarespace event pages.

Squarespace sites expose individual event iCal files via ?format=ical.
This scraper finds event links on a listing page and fetches each one.

Usage:
    python scrapers/squarespace.py --url https://nativeearth.ca/shows/all-shows --name "Native Earth Performing Arts" -o native_earth.ics
    python scrapers/squarespace.py --url https://sjshbg.org/events --name "St. John the Baptist" -o sjshbg.ics
"""

import argparse
import logging
import re
import time
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

import requests
from icalendar import Calendar

import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from scrapers.lib.base import BaseScraper


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SquarespaceScraper(BaseScraper):
    """Generic scraper for Squarespace event pages."""

    name = "Squarespace"
    domain = "squarespace.com"

    def __init__(self, url, source_name):
        self.listing_url = url
        parsed = urlparse(url)
        self.base_url = f"{parsed.scheme}://{parsed.netloc}"
        self.events_path = parsed.path.rstrip('/')
        self.name = source_name
        self.domain = parsed.netloc.replace('www.', '')
        super().__init__()

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events by finding links and getting their iCal data."""
        event_urls = self._get_event_urls()
        logger.info(f"Found {len(event_urls)} event URLs")

        events = []
        for url in event_urls:
            event = self._fetch_event_ical(url)
            if event:
                events.append(event)
            time.sleep(0.5)

        return events

    def _get_event_urls(self) -> list[str]:
        """Find event links on the listing page."""
        logger.info(f"Fetching event list from {self.listing_url}")

        response = requests.get(self.listing_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }, timeout=30)
        response.raise_for_status()

        # Find all links under the listing path
        prefix = self.events_path + '/'
        urls = set()
        for match in re.finditer(r'href="([^"]*)"', response.text):
            href = match.group(1)
            if href.startswith(prefix) and href != prefix:
                # Strip query strings and fragments
                clean = href.split('?')[0].split('#')[0]
                urls.add(self.base_url + clean)

        return sorted(urls)

    def _fetch_event_ical(self, event_url: str) -> dict[str, Any] | None:
        """Fetch iCal for a single event and parse it."""
        ical_url = event_url + '?format=ical'
        logger.info(f"Fetching iCal: {ical_url}")

        try:
            response = requests.get(ical_url, timeout=30)
            response.raise_for_status()

            cal = Calendar.from_ical(response.content)
            for component in cal.walk():
                if component.name == 'VEVENT':
                    dtstart = component.get('dtstart')
                    if not dtstart:
                        continue
                    return {
                        'title': str(component.get('summary', '')),
                        'dtstart': dtstart.dt,
                        'dtend': component.get('dtend').dt if component.get('dtend') else None,
                        'location': str(component.get('location', '')),
                        'description': str(component.get('description', '')),
                        'url': event_url,
                        'uid': str(component.get('uid', ''))
                    }
        except Exception as e:
            logger.warning(f"Failed to fetch {ical_url}: {e}")

        return None


def main():
    parser = argparse.ArgumentParser(description='Scrape Squarespace event pages')
    parser.add_argument('--url', required=True, help='Events listing page URL')
    parser.add_argument('--name', required=True, help='Source name')
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = SquarespaceScraper(args.url, args.name)
    scraper.run(args.output)


if __name__ == '__main__':
    main()
