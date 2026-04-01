#!/usr/bin/env python3
"""
Scraper for Spektrix ticketing platforms.

Spektrix exposes a public JSON API (v3, Web mode, no auth) with events
and individual performance instances.

Usage:
    python scrapers/spektrix.py \
        --base-url "https://tickets.seeconstellation.org/constellation" \
        --name "Constellation Stage & Screen" \
        --output cities/bloomington/constellation.ics
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


class SpektrixScraper(BaseScraper):
    """Scraper for Spektrix ticketing API."""

    def __init__(self, base_url, source_name):
        self.base_url = base_url.rstrip('/')
        self.name = source_name
        self.domain = base_url.split('/')[2]
        super().__init__()

    def _api_get(self, endpoint):
        """Fetch JSON from Spektrix API."""
        url = f"{self.base_url}/api/v3/{endpoint}"
        logger.info(f"Fetching {url}")
        req = Request(url, headers={'Accept': 'application/json'})
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events and instances from Spektrix API."""
        events_data = self._api_get('events')
        instances_data = self._api_get('instances?filter=startFrom%3Dnow')

        # Build event lookup
        event_map = {}
        for e in events_data:
            event_map[e['id']] = e

        events = []
        for inst in instances_data:
            if inst.get('cancelled'):
                continue
            event_id = inst.get('event', {}).get('id')
            event_info = event_map.get(event_id, {})

            start = inst.get('start', '')
            if not start:
                continue

            dt = datetime.fromisoformat(start)

            # Build description from event info
            desc_parts = []
            if event_info.get('description'):
                desc_parts.append(event_info['description'])
            subtitle = event_info.get('attribute_EventSubtitle', '')
            if subtitle:
                desc_parts.append(subtitle)

            venue = event_info.get('attribute_PerformanceVenue', '')

            events.append({
                'title': event_info.get('name', 'Unknown'),
                'dtstart': dt,
                'dtend': None,  # Spektrix doesn't expose end times per instance
                'location': venue,
                'description': '\n'.join(desc_parts),
                'url': '',
                'uid': f"spektrix-{inst['id']}@{self.domain}",
            })

        return events


def main():
    parser = argparse.ArgumentParser(description='Scrape Spektrix ticketing API')
    parser.add_argument('--base-url', required=True, help='Spektrix base URL (e.g. https://tickets.example.org/org)')
    parser.add_argument('--name', required=True, help='Source name')
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--default-url', help='Fallback URL when events have no per-event URL')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = SpektrixScraper(args.base_url, args.name)
    if args.default_url:
        scraper.default_url = args.default_url
    scraper.run(args.output)


if __name__ == '__main__':
    main()
