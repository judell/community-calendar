"""The Events Calendar (Tribe) REST API scraper library.

WordPress sites using The Events Calendar plugin expose a JSON REST API at
`/wp-json/tribe/events/v1/events/`. This works even when ICS export is
blocked by WAFs, since the API endpoint isn't typically firewalled.

Usage:
    from lib.tribe_events import TribeEventsScraper

    class MyEventsScraper(TribeEventsScraper):
        name = "My Events"
        domain = "example.org"
        api_url = "https://example.org/wp-json/tribe/events/v1/events/"
        default_location = "Anytown, USA"

    if __name__ == '__main__':
        MyEventsScraper.main()
"""

import re
from datetime import datetime
from typing import Any, Optional
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from .base import BaseScraper

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; CommunityCalendar/1.0)',
    'Accept': 'application/json',
}


class TribeEventsScraper(BaseScraper):
    """Base class for scrapers targeting The Events Calendar REST API.

    Subclasses should set:
        name: str - Source name
        domain: str - Domain for UIDs
        api_url: str - Tribe Events API URL (e.g. https://example.org/wp-json/tribe/events/v1/events/)
        timezone: str - IANA timezone

    Optional:
        default_location: str - Fallback location string
        max_pages: int - Maximum pages to fetch (default 10)
        per_page: int - Events per page (default 50)
    """

    api_url: str = ''
    default_location: str = ''
    max_pages: int = 10
    per_page: int = 50

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from the Tribe Events REST API."""
        all_events = []
        tz = ZoneInfo(self.timezone)

        for page in range(1, self.max_pages + 1):
            url = f"{self.api_url}?per_page={self.per_page}&page={page}"
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
            if page >= total_pages:
                break

        self.logger.info(f"Found {len(all_events)} events")
        return all_events

    def _parse_event(self, item: dict, tz: ZoneInfo) -> Optional[dict[str, Any]]:
        """Parse a single event from the Tribe Events API."""
        title = item.get('title', '')
        if not title:
            return None

        start_str = item.get('start_date', '')
        if not start_str:
            return None

        try:
            dtstart = datetime.fromisoformat(start_str).replace(tzinfo=tz)
        except ValueError:
            return None

        dtend = None
        end_str = item.get('end_date', '')
        if end_str:
            try:
                dtend = datetime.fromisoformat(end_str).replace(tzinfo=tz)
            except ValueError:
                pass

        # Location
        venue = item.get('venue', {}) or {}
        location_parts = [
            venue.get('venue', ''),
            venue.get('address', ''),
            venue.get('city', ''),
            venue.get('state', ''),
        ]
        location = ', '.join(p for p in location_parts if p) or self.default_location

        # Description — strip HTML
        desc_html = item.get('description', '') or ''
        desc = BeautifulSoup(desc_html, 'html.parser').get_text(strip=True)
        desc = re.sub(r'\s+', ' ', desc)[:500]

        # URL
        url = item.get('url', '')

        # UID
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
