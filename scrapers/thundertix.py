#!/usr/bin/env python3
"""
Parameterized scraper for ThunderTix-hosted venue ticketing pages.

ThunderTix pages embed schema.org Event data as JSON-LD in an ItemList block.
We extract events from the ItemList, skip past events, and emit ICS.

Known venues on this platform:
  - Raven Performing Arts Theater (Healdsburg CA)
    https://ravenperformingartstheater.thundertix.com/

Usage:
    python scrapers/thundertix.py \\
        --url "https://ravenperformingartstheater.thundertix.com/" \\
        --name "Raven Performing Arts Theater" \\
        --default-location "Raven Performing Arts Theater, 115 North St, Healdsburg, CA 95448" \\
        --output cities/santarosa/raven_theater.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import html as html_mod
import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

from lib.base import BaseScraper
from lib.jsonld import extract_jsonld_blocks, parse_location

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


class ThunderTixScraper(BaseScraper):
    """Scraper for ThunderTix venue pages via schema.org JSON-LD ItemList."""

    def __init__(self, url: str, source_name: str, tz: str = "America/Los_Angeles",
                 default_location: str = ""):
        self.url = url
        self.name = source_name
        # Derive domain from URL
        m = re.search(r'https?://([^/]+)', url)
        self.domain = m.group(1) if m else 'thundertix.com'
        self.timezone = tz
        self.default_location = default_location
        super().__init__()

    def _fetch_page(self, url: str) -> Optional[str]:
        req = Request(url, headers=HEADERS)
        try:
            with urlopen(req, timeout=30) as resp:
                return resp.read().decode('utf-8')
        except (HTTPError, URLError) as e:
            self.logger.warning(f"Failed to fetch {url}: {e}")
            return None

    def _extract_events_from_item_list(self, blocks: list[dict]) -> list[dict]:
        """Extract Event items from JSON-LD ItemList blocks."""
        events = []
        for block in blocks:
            if isinstance(block, dict):
                # Top-level ItemList
                if block.get('@type') == 'ItemList':
                    for item in block.get('itemListElement', []):
                        event = item.get('item', {})
                        if isinstance(event, dict) and event.get('@type', '').endswith('Event') or \
                           (isinstance(event, dict) and event.get('@type') == 'Event'):
                            events.append(event)
                # @graph
                for node in block.get('@graph', []):
                    if isinstance(node, dict) and node.get('@type') == 'ItemList':
                        for item in node.get('itemListElement', []):
                            event = item.get('item', {})
                            if isinstance(event, dict):
                                events.append(event)
        return events

    def fetch_events(self) -> list[dict[str, Any]]:
        self.logger.info(f"Fetching {self.url}")
        html = self._fetch_page(self.url)
        if not html:
            return []

        blocks = extract_jsonld_blocks(html)
        raw_events = self._extract_events_from_item_list(blocks)
        self.logger.info(f"Found {len(raw_events)} events in JSON-LD")

        now = datetime.now(timezone.utc)
        events = []

        for item in raw_events:
            parsed = self._parse_event(item, now)
            if parsed:
                events.append(parsed)

        self.logger.info(f"Total future events: {len(events)}")
        return events

    def _parse_event(self, item: dict, now: datetime) -> Optional[dict[str, Any]]:
        """Parse a single schema.org Event dict."""
        title = html_mod.unescape(item.get('name', 'Untitled')).strip()
        start_str = item.get('startDate', '')
        if not start_str:
            return None

        try:
            dtstart = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        except ValueError:
            self.logger.debug(f"Bad startDate {start_str!r} for {title!r}")
            return None

        start_aware = dtstart if dtstart.tzinfo else dtstart.replace(tzinfo=timezone.utc)
        if start_aware < now:
            return None

        end_str = item.get('endDate', '')
        dtend = None
        if end_str:
            try:
                dtend = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
            except ValueError:
                pass

        location = parse_location(item.get('location'), self.default_location)

        desc = html_mod.unescape(item.get('description', '') or '')
        desc = re.sub(r'<[^>]+>', ' ', desc).strip()
        desc = re.sub(r'\s+', ' ', desc)

        url = item.get('url', self.url)

        return {
            'title': title,
            'dtstart': dtstart,
            'dtend': dtend or dtstart,
            'location': location,
            'description': desc[:500],
            'url': url,
        }


def main():
    parser = argparse.ArgumentParser(description="Scrape a ThunderTix venue page")
    parser.add_argument('--url', required=True, help='ThunderTix venue base URL')
    parser.add_argument('--name', required=True, help='Venue display name')
    parser.add_argument('--timezone', default='America/Los_Angeles', help='IANA timezone')
    parser.add_argument('--default-location', default='', help='Fallback location string')
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = ThunderTixScraper(
        url=args.url,
        source_name=args.name,
        tz=args.timezone,
        default_location=args.default_location,
    )
    scraper.run(args.output)


if __name__ == '__main__':
    main()
