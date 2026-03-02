#!/usr/bin/env python3
"""
Scraper for Eventbrite organizer pages.

Discovers event URLs from an organizer page (/o/slug), then fetches each
individual event page for JSON-LD structured data (schema.org Event).

Eventbrite blocks API access and organizer-page scraping, but individual
event pages are public and contain clean JSON-LD with startDate, endDate,
location, and description.

Usage:
    python scrapers/eventbrite.py \
        --url "https://www.eventbrite.com/o/montclair-brewery-17088451648" \
        --name "Montclair Brewery" \
        --output cities/montclair/eventbrite_montclair_brewery.ics

    python scrapers/eventbrite.py \
        --url "https://www.eventbrite.com/o/montclair-book-center-76893048773" \
        --name "Montclair Book Center" \
        --output cities/montclair/eventbrite_montclair_book_center.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Optional

from lib.base import BaseScraper
from lib.jsonld import extract_jsonld_blocks, extract_events_from_blocks, parse_location

import html as html_mod
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


class EventbriteScraper(BaseScraper):
    """Scraper for Eventbrite organizer pages via JSON-LD on individual event pages."""

    domain = "eventbrite.com"
    timezone = "America/New_York"

    def __init__(self, organizer_url: str, source_name: str):
        self.organizer_url = organizer_url
        self.name = source_name
        super().__init__()

    def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch a URL and return HTML."""
        req = Request(url, headers=HEADERS)
        try:
            with urlopen(req, timeout=30) as resp:
                return resp.read().decode('utf-8')
        except (HTTPError, URLError) as e:
            self.logger.warning(f"Failed to fetch {url}: {e}")
            return None

    def _discover_event_urls(self) -> list[str]:
        """Fetch organizer page and extract individual event URLs."""
        html = self._fetch_page(self.organizer_url)
        if not html:
            self.logger.error(f"Could not fetch organizer page: {self.organizer_url}")
            return []

        # Extract /e/ event URLs (both absolute and relative)
        pattern = r'(?:https://www\.eventbrite\.com)?(/e/[^"?\s]+)'
        paths = set(re.findall(pattern, html))
        urls = [f"https://www.eventbrite.com{p}" if p.startswith('/') else p for p in paths]
        self.logger.info(f"Discovered {len(urls)} event URLs from organizer page")
        return urls

    def _fetch_event_jsonld(self, url: str) -> Optional[dict[str, Any]]:
        """Fetch an individual event page and extract JSON-LD Event data."""
        html = self._fetch_page(url)
        if not html:
            return None

        blocks = extract_jsonld_blocks(html)
        events = extract_events_from_blocks(blocks)

        if not events:
            self.logger.warning(f"No JSON-LD Event found at {url}")
            return None

        item = events[0]

        title = html_mod.unescape(item.get('name', 'Untitled'))
        start_str = item.get('startDate', '')
        if not start_str:
            return None

        try:
            dtstart = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        except ValueError:
            self.logger.debug(f"Skipping {title}: bad startDate {start_str}")
            return None

        # Skip past events
        now = datetime.now(timezone.utc)
        start_aware = dtstart if dtstart.tzinfo else dtstart.replace(tzinfo=timezone.utc)
        if start_aware < now:
            return None

        # End time
        dtend = None
        end_str = item.get('endDate', '')
        if end_str:
            try:
                dtend = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
            except ValueError:
                pass

        # Location
        location = parse_location(item.get('location'), '')

        # Description
        desc = item.get('description', '') or ''
        desc = html_mod.unescape(desc)
        desc = re.sub(r'<[^>]+>', ' ', desc).strip()
        desc = re.sub(r'\s+', ' ', desc)

        return {
            'title': title,
            'dtstart': dtstart,
            'dtend': dtend,
            'location': location,
            'description': desc[:500] if desc else '',
            'url': url,
        }

    def fetch_events(self) -> list[dict[str, Any]]:
        """Discover events from organizer page, then fetch each for JSON-LD."""
        event_urls = self._discover_event_urls()
        if not event_urls:
            return []

        events = []
        self.logger.info(f"Fetching {len(event_urls)} event pages (parallel)...")

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self._fetch_event_jsonld, url): url for url in event_urls}
            for future in as_completed(futures):
                event = future.result()
                if event:
                    events.append(event)

        self.logger.info(f"Got {len(events)} future events")
        return events


def main():
    parser = argparse.ArgumentParser(description="Scrape Eventbrite organizer events via JSON-LD")
    parser.add_argument('--url', required=True, help='Eventbrite organizer URL (/o/slug)')
    parser.add_argument('--name', required=True, help='Source name')
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = EventbriteScraper(organizer_url=args.url, source_name=args.name)
    scraper.run(args.output)


if __name__ == '__main__':
    main()
