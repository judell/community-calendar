#!/usr/bin/env python3
"""
Scraper for Mobilize.us organization event pages.

Extracts events from the embedded window.__MLZ_EMBEDDED_DATA__ JSON
that Mobilize.us renders server-side into each organization's event feed page.

Usage:
    python scrapers/mobilize.py \
        --url "https://www.mobilize.us/indivisiblesonomacounty/" \
        --name "Indivisible Sonoma County" \
        --output cities/santarosa/mobilize_indivisible_sonoma.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

from lib.base import BaseScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


class MobilizeScraper(BaseScraper):
    """Scraper for Mobilize.us organization pages via embedded JSON data."""

    domain = "mobilize.us"

    def __init__(self, page_url: str, source_name: str):
        self.page_url = page_url.rstrip('/')  + '/'
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

    def _extract_embedded_data(self, html: str) -> Optional[dict]:
        """Extract window.__MLZ_EMBEDDED_DATA__ JSON from HTML."""
        match = re.search(r'__MLZ_EMBEDDED_DATA__\s*=\s*', html)
        if not match:
            self.logger.error("Could not find __MLZ_EMBEDDED_DATA__ in page")
            return None
        # Brace-count to find the complete JSON object
        start = match.end()
        depth = 0
        i = start
        while i < len(html):
            if html[i] == '{':
                depth += 1
            elif html[i] == '}':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        try:
            return json.loads(html[start:i + 1])
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse embedded JSON: {e}")
            return None

    def _parse_event(self, item: dict) -> list[dict[str, Any]]:
        """Parse a Mobilize event item into one or more event dicts (one per timeslot)."""
        title = (item.get('name') or '').strip()
        if not title:
            return []

        # Build description
        description = item.get('description', '') or ''
        # Clean HTML from description
        description = re.sub(r'<[^>]+>', ' ', description).strip()
        description = re.sub(r'\s+', ' ', description)
        if description:
            description = description[:500]

        # Location
        location = item.get('location_one_line', '') or ''
        if not location:
            parts = [p for p in [
                item.get('location_name', ''),
                item.get('address_line1', ''),
                item.get('city', ''),
                item.get('state', ''),
            ] if p]
            location = ', '.join(parts)
        if item.get('is_virtual'):
            location = location or 'Virtual'

        # Event URL: build from org slug + event id
        event_id = item.get('id')
        org = item.get('organization') or {}
        org_slug = org.get('slug', '') if isinstance(org, dict) else ''
        event_url = f"https://www.mobilize.us/{org_slug}/event/{event_id}/" if org_slug and event_id else ''

        # Image
        image_url = item.get('image_url', '')

        # Each timeslot becomes a separate event
        times = item.get('times') or []
        now = datetime.now(timezone.utc)
        events = []

        for slot in times:
            start_str = slot.get('start', '')
            end_str = slot.get('end', '')
            if not start_str:
                continue

            try:
                dtstart = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
            except ValueError:
                continue

            # Skip past events
            if dtstart < now:
                continue

            dtend = None
            if end_str:
                try:
                    dtend = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
                except ValueError:
                    pass

            events.append({
                'title': title,
                'dtstart': dtstart,
                'dtend': dtend,
                'location': location,
                'description': description,
                'url': event_url,
                'image_url': image_url if image_url else None,
            })

        return events

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch the organization page and extract all events."""
        html = self._fetch_page(self.page_url)
        if not html:
            return []

        data = self._extract_embedded_data(html)
        if not data:
            return []

        # Navigate: top-level has data.events
        events_list = []
        raw_events = []
        try:
            raw_events = data['data']['events']
        except (KeyError, TypeError):
            self.logger.error(f"Unexpected data structure, top keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")
            return []

        self.logger.info(f"Found {len(raw_events)} raw events in embedded data")

        for item in raw_events:
            if isinstance(item, dict):
                events_list.extend(self._parse_event(item))

        self.logger.info(f"Parsed {len(events_list)} future event timeslots")
        return events_list


def main():
    parser = argparse.ArgumentParser(description="Scrape Mobilize.us organization events")
    parser.add_argument('--url', required=True, help='Mobilize.us organization page URL')
    parser.add_argument('--name', required=True, help='Source name')
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = MobilizeScraper(page_url=args.url, source_name=args.name)
    scraper.run(args.output)


if __name__ == '__main__':
    main()
