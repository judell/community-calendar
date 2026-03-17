#!/usr/bin/env python3
"""
Scraper for guild.host group event pages.

guild.host is a JS-rendered SPA with no ICS feeds. However, individual event
pages include JSON-LD Event schema with full structured data. The listing page
at /events embeds event slugs in an Apollo Client cache, and event links appear
as standard href="/events/{slug}" anchors in the HTML.

Usage:
    python scrapers/guildhost.py \
        --group civic-tech-toronto \
        --name "Civic Tech Toronto" \
        -o cities/toronto/guildhost_civic_tech.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import json
import logging
import re
import time
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

from lib.base import BaseScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
}

BASE_URL = 'https://guild.host'


class GuildHostScraper(BaseScraper):
    """Scraper for guild.host group event pages via JSON-LD Event data."""

    name = "Guild.host"
    domain = "guild.host"
    timezone = "America/Toronto"

    def __init__(self, group: str, source_name: Optional[str] = None):
        super().__init__()
        self.group = group
        if source_name:
            self.name = source_name

    def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch a page with error handling."""
        req = Request(url, headers=HEADERS)
        try:
            with urlopen(req, timeout=30) as resp:
                return resp.read().decode('utf-8')
        except (HTTPError, URLError) as e:
            self.logger.warning(f"Failed to fetch {url}: {e}")
            return None

    def _extract_event_slugs(self, html: str) -> list[str]:
        """Extract unique event slugs from the listing page HTML."""
        # Event links appear as href="/events/{slug}"
        slugs = re.findall(r'href="/events/([^"]+)"', html)
        # Deduplicate while preserving order
        seen = set()
        unique = []
        for slug in slugs:
            if slug not in seen:
                seen.add(slug)
                unique.append(slug)
        return unique

    def _parse_jsonld_event(self, html: str, event_url: str) -> Optional[dict[str, Any]]:
        """Extract Event JSON-LD from an individual event page."""
        blocks = re.findall(
            r'<script\s+type="application/ld\+json">(.*?)</script>',
            html, re.DOTALL
        )

        for block_str in blocks:
            try:
                data = json.loads(block_str)
            except json.JSONDecodeError:
                continue

            items = data if isinstance(data, list) else [data]
            for item in items:
                if not isinstance(item, dict) or item.get('@type') != 'Event':
                    continue

                start_str = item.get('startDate', '')
                if not start_str:
                    continue

                try:
                    dtstart = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                except ValueError:
                    continue

                # End date
                dtend = None
                end_str = item.get('endDate', '')
                if end_str:
                    try:
                        dtend = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
                    except ValueError:
                        pass

                title = item.get('name', 'Untitled')

                # Location — guild.host uses an array with VirtualLocation and Place
                location_parts = []
                locations = item.get('location', [])
                if isinstance(locations, dict):
                    locations = [locations]
                for loc in locations:
                    if not isinstance(loc, dict):
                        continue
                    loc_type = loc.get('@type', '')
                    if loc_type == 'Place':
                        place_name = loc.get('name', '')
                        addr = loc.get('address', {})
                        if isinstance(addr, dict):
                            addr_parts = [
                                addr.get('streetAddress'),
                                addr.get('addressLocality'),
                                addr.get('addressRegion'),
                                addr.get('postalCode'),
                            ]
                            addr_str = ', '.join(p for p in addr_parts if p)
                            if place_name and addr_str:
                                location_parts.append(f"{place_name}, {addr_str}")
                            elif place_name:
                                location_parts.append(place_name)
                            elif addr_str:
                                location_parts.append(addr_str)
                    elif loc_type == 'VirtualLocation':
                        virtual_url = loc.get('url', '')
                        if virtual_url:
                            location_parts.append(f"Online: {virtual_url}")

                location = ' / '.join(location_parts)

                description = item.get('description', '')

                return {
                    'title': title,
                    'dtstart': dtstart,
                    'dtend': dtend,
                    'location': location,
                    'description': description,
                    'url': event_url,
                }

        return None

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch the group listing page, then each event page for JSON-LD."""
        listing_url = f"{BASE_URL}/{self.group}/events"
        self.logger.info(f"Fetching listing page: {listing_url}")

        html = self._fetch_page(listing_url)
        if not html:
            return []

        slugs = self._extract_event_slugs(html)
        self.logger.info(f"Found {len(slugs)} event slugs on listing page")

        if not slugs:
            return []

        now = datetime.now(timezone.utc)
        events = []

        for i, slug in enumerate(slugs):
            event_url = f"{BASE_URL}/events/{slug}"
            self.logger.info(f"Fetching event {i + 1}/{len(slugs)}: {event_url}")

            event_html = self._fetch_page(event_url)
            if not event_html:
                continue

            event = self._parse_jsonld_event(event_html, event_url)
            if event:
                # Skip past events
                dtstart = event['dtstart']
                start_aware = dtstart if dtstart.tzinfo else dtstart.replace(tzinfo=timezone.utc)
                if start_aware < now:
                    self.logger.debug(f"Skipping past event: {event['title']}")
                    continue
                events.append(event)

            # Be polite — small delay between requests
            if i < len(slugs) - 1:
                time.sleep(0.5)

        self.logger.info(f"Found {len(events)} future events from {self.name}")
        return events


def main():
    parser = argparse.ArgumentParser(description="Scrape guild.host group events")
    parser.add_argument('--group', required=True, help='Guild.host group slug (e.g., civic-tech-toronto)')
    parser.add_argument('--name', default='Guild.host', help='Source display name')
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = GuildHostScraper(group=args.group, source_name=args.name)
    scraper.run(args.output)


if __name__ == '__main__':
    main()
