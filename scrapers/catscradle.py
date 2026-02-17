#!/usr/bin/env python3
"""
Scraper for Cat's Cradle events (covers multiple venues).

The Cat's Cradle WordPress site uses the RHP Events plugin and publishes an RSS feed
at https://catscradle.com/events/feed/ covering events at:
- Cat's Cradle (main room)
- Cat's Cradle Back Room
- Haw River Ballroom
- Motorco Music Hall
- Lincoln Theatre
- Local 506

Each event detail page has JSON-LD (schema.org Event) with startDate, location, etc.

Usage:
    python scrapers/catscradle.py --output cities/raleighdurham/catscradle.ics
    python scrapers/catscradle.py --venue cats-cradle --output cities/raleighdurham/catscradle_main.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import json
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Any, Optional

import feedparser
import requests

from lib.base import BaseScraper
from lib.utils import DEFAULT_HEADERS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CatsCradleScraper(BaseScraper):
    """Scraper for Cat's Cradle and associated venues via RSS + JSON-LD."""

    name = "Cat's Cradle"
    domain = "catscradle.com"
    timezone = "America/New_York"

    RSS_URL = "https://catscradle.com/events/feed/"
    # RSS feed has paginated pages: /events/feed/?paged=2, etc.
    MAX_PAGES = 5

    VENUE_ADDRESSES = {
        "cats-cradle": "Cat's Cradle, 300 E Main St, Carrboro, NC 27510",
        "cats-cradle-back-room": "Cat's Cradle Back Room, 300 E Main St, Carrboro, NC 27510",
        "cats-cradle-back-yard": "Cat's Cradle Back Yard, 300 E Main St, Carrboro, NC 27510",
        "haw-river-ballroom": "Haw River Ballroom, 1711 Saxapahaw-Bethlehem Church Rd, Saxapahaw, NC 27340",
        "motorco-music-hall": "Motorco Music Hall, 723 Rigsbee Ave, Durham, NC 27701",
        "lincoln-theatre": "Lincoln Theatre, 126 E Cabarrus St, Raleigh, NC 27601",
        "local-506": "Local 506, 506 W Franklin St, Chapel Hill, NC 27516",
    }

    def __init__(self, venue_filter: Optional[str] = None):
        self.venue_filter = venue_filter
        super().__init__()

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from RSS feed, then get dates from JSON-LD on detail pages."""
        # Collect all RSS entries across pages
        all_entries = []
        for page in range(1, self.MAX_PAGES + 1):
            url = self.RSS_URL if page == 1 else f"{self.RSS_URL}?paged={page}"
            self.logger.info(f"Fetching RSS page {page}: {url}")
            feed = feedparser.parse(url)
            if not feed.entries:
                break
            all_entries.extend(feed.entries)
            self.logger.info(f"  Got {len(feed.entries)} entries (total: {len(all_entries)})")

        self.logger.info(f"Total RSS entries: {len(all_entries)}")

        events = []
        for entry in all_entries:
            link = entry.get('link', '')

            # Extract venue slug from URL path
            # URL format: /event/{slug}/{venue-slug}/{city-state}/
            venue_slug = self._extract_venue_slug(link)

            # Apply venue filter if specified
            if self.venue_filter and venue_slug != self.venue_filter:
                continue

            # Fetch JSON-LD from the event detail page
            event = self._fetch_event_jsonld(link, venue_slug)
            if not event:
                # Fall back to RSS entry data if JSON-LD missing/unparseable
                event = self._parse_rss_entry(entry, venue_slug)
            if event:
                events.append(event)
            time.sleep(0.3)

        return events

    def _extract_venue_slug(self, url: str) -> str:
        """Extract venue slug from event URL."""
        # URL: https://catscradle.com/event/{event-slug}/{venue-slug}/{city-state}/
        parts = url.rstrip('/').split('/')
        if len(parts) >= 5:
            return parts[-2]  # venue slug is second-to-last
        return "unknown"

    def _fetch_event_jsonld(self, url: str, venue_slug: str) -> Optional[dict[str, Any]]:
        """Fetch event detail page and extract JSON-LD Event data."""
        try:
            response = requests.get(url, headers=DEFAULT_HEADERS, timeout=30)
            response.raise_for_status()
        except Exception as e:
            self.logger.warning(f"Failed to fetch {url}: {e}")
            return None

        html = response.text

        # Extract JSON-LD blocks
        blocks = re.findall(
            r'<script type="application/ld\+json">(.*?)</script>',
            html, re.DOTALL
        )

        for block in blocks:
            try:
                data = json.loads(block)
            except json.JSONDecodeError:
                continue

            # Handle @graph wrapper
            if isinstance(data, dict) and '@graph' in data:
                for item in data['@graph']:
                    event = self._parse_jsonld_event(item, url, venue_slug)
                    if event:
                        return event
            elif isinstance(data, dict):
                event = self._parse_jsonld_event(data, url, venue_slug)
                if event:
                    return event

        self.logger.warning(f"No JSON-LD Event found at {url}")
        return None

    def _parse_rss_entry(self, entry, venue_slug: str) -> Optional[dict[str, Any]]:
        """Fall back to RSS entry data when JSON-LD is missing."""
        title = entry.get('title', '')
        if not title:
            return None
        published = entry.get('published_parsed')
        if not published:
            return None
        dtstart = datetime(*published[:6])
        return {
            'title': title,
            'dtstart': dtstart,
            'dtend': dtstart + timedelta(hours=3),
            'url': entry.get('link', ''),
            'location': self.VENUE_ADDRESSES.get(venue_slug, venue_slug),
            'description': '',
        }

    @staticmethod
    def _parse_iso_date(date_str: str) -> Optional[datetime]:
        """Parse ISO date string, handling offset formats like -0400 that
        Python < 3.11 fromisoformat() doesn't support."""
        # Insert colon in timezone offset if missing (e.g., -0400 -> -04:00)
        date_str = re.sub(r'([+-]\d{2})(\d{2})$', r'\1:\2', date_str)
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.replace(tzinfo=None)
        except ValueError:
            return None

    def _parse_jsonld_event(self, data: dict, url: str, venue_slug: str) -> Optional[dict[str, Any]]:
        """Parse a JSON-LD Event object into our event dict format."""
        event_type = data.get('@type', '')
        if event_type not in ('Event', 'MusicEvent'):
            return None

        title = data.get('name', '')
        if not title:
            return None

        # Clean HTML entities
        title = title.replace('&#8211;', '–').replace('&#8217;', "'").replace('&amp;', '&')

        # Parse startDate (ISO format: "2026-04-02T20:00:00-0400")
        start_str = data.get('startDate', '')
        if not start_str:
            return None

        dtstart = self._parse_iso_date(start_str)
        if not dtstart:
            self.logger.warning(f"Could not parse startDate: {start_str}")
            return None

        # Parse endDate if available
        dtend = None
        end_str = data.get('endDate', '')
        if end_str:
            dtend = self._parse_iso_date(end_str)
        if not dtend:
            dtend = dtstart + timedelta(hours=3)

        # Location
        location_data = data.get('location', {})
        if isinstance(location_data, dict):
            venue_name = location_data.get('name', '')
            address = location_data.get('address', '')
            if isinstance(address, dict):
                parts = [address.get('streetAddress', ''),
                         address.get('addressLocality', ''),
                         address.get('addressRegion', '')]
                address = ', '.join(p for p in parts if p)
            location = f"{venue_name}, {address}" if venue_name and address else (venue_name or address)
        else:
            location = self.VENUE_ADDRESSES.get(venue_slug, venue_slug)

        # Clean HTML from location
        location = re.sub(r'&#\d+;', '', location).strip(', ')

        # Description
        description = data.get('description', '')

        return {
            'title': title,
            'dtstart': dtstart,
            'dtend': dtend,
            'url': url,
            'location': location or self.VENUE_ADDRESSES.get(venue_slug, ''),
            'description': description[:500] if description else '',
        }


def main():
    parser = argparse.ArgumentParser(description="Scrape Cat's Cradle events")
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--venue', help='Filter by venue slug (e.g., cats-cradle, motorco-music-hall)')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = CatsCradleScraper(venue_filter=args.venue)
    scraper.run(args.output)


if __name__ == '__main__':
    main()
