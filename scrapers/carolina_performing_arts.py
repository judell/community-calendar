#!/usr/bin/env python3
"""
Scraper for Carolina Performing Arts events.
https://carolinaperformingarts.org/calendar/

CPA uses a custom WordPress REST API endpoint that returns JSON:
/wp-json/cpa/v1/performances/?start=YYYY-MM-DD&end=YYYY-MM-DD

Usage:
    python scrapers/carolina_performing_arts.py --output cities/raleighdurham/carolina_performing_arts.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import os
from datetime import datetime, timedelta
from typing import Any

import requests

from lib.base import BaseScraper
from lib.utils import DEFAULT_HEADERS


class CarolinaPerformingArtsScraper(BaseScraper):
    """Scraper for Carolina Performing Arts via custom WP REST API."""

    name = "Carolina Performing Arts"
    domain = "carolinaperformingarts.org"
    timezone = "America/New_York"

    API_URL = "https://carolinaperformingarts.org/wp-json/cpa/v1/performances/"
    VENUE_ADDRESS = "Memorial Hall, 114 E Cameron Ave, Chapel Hill, NC 27514"

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from CPA REST API."""
        months_ahead = int(os.environ.get('SCRAPE_MONTHS', 6))
        now = datetime.now()
        start = now.strftime('%Y-%m-%d')
        end = (now + timedelta(days=months_ahead * 31)).strftime('%Y-%m-%d')

        self.logger.info(f"Fetching {self.API_URL} (start={start}, end={end})")
        response = requests.get(
            self.API_URL,
            params={'start': start, 'end': end},
            headers=DEFAULT_HEADERS,
            timeout=30
        )
        response.raise_for_status()

        data = response.json()
        self.logger.info(f"API returned {len(data)} events")

        events = []
        for item in data:
            event = self._parse_event(item)
            if event:
                events.append(event)

        return events

    def _parse_event(self, item: dict) -> dict[str, Any] | None:
        """Parse a single API event object."""
        title = item.get('title', '')
        start_str = item.get('start', '')
        if not title or not start_str:
            return None

        # Parse "2026-02-12 18:00"
        try:
            dtstart = datetime.strptime(start_str, '%Y-%m-%d %H:%M')
        except ValueError:
            return None

        # End time is usually null
        dtend = None
        end_str = item.get('end')
        if end_str:
            try:
                dtend = datetime.strptime(end_str, '%Y-%m-%d %H:%M')
            except ValueError:
                pass
        if not dtend:
            dtend = dtstart + timedelta(hours=2)

        url = item.get('url', '')
        tag = item.get('tag', '')

        description = f"Series: {tag}" if tag else ''

        return {
            'title': title,
            'dtstart': dtstart,
            'dtend': dtend,
            'url': url,
            'location': self.VENUE_ADDRESS,
            'description': description,
        }


if __name__ == '__main__':
    CarolinaPerformingArtsScraper.main()
