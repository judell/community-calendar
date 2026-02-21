#!/usr/bin/env python3
"""
Scraper for Spreckels Performing Arts Center (Rohnert Park, CA)
Uses The Events Calendar REST API v1.

Usage:
    python scrapers/spreckels.py --output cities/santarosa/spreckels.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

from datetime import datetime
from typing import Any

import requests

from lib.base import BaseScraper
from lib.utils import DEFAULT_HEADERS


class SpreckelsScraper(BaseScraper):
    """Scraper for Spreckels Performing Arts Center via Tribe Events REST API."""

    name = "Spreckels Performing Arts Center"
    domain = "spreckelsonline.com"

    API_URL = "https://spreckelsonline.com/wp-json/tribe/events/v1/events"
    VENUE_ADDRESS = "Spreckels Performing Arts Center, 5409 Snyder Ln, Rohnert Park, CA 94928"

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from Tribe Events Calendar REST API."""
        params = {
            'start_date': '2025-01-01',
            'per_page': 50,
        }

        self.logger.info(f"Fetching {self.API_URL}")
        response = requests.get(self.API_URL, params=params, headers=DEFAULT_HEADERS, timeout=30)
        response.raise_for_status()

        data = response.json()
        events = []

        for item in data.get('events', []):
            title = item.get('title', '').strip()
            if not title:
                continue

            try:
                dtstart = datetime.strptime(item['start_date'], '%Y-%m-%d %H:%M:%S')
                dtend = datetime.strptime(item['end_date'], '%Y-%m-%d %H:%M:%S')
            except (KeyError, ValueError) as e:
                self.logger.warning(f"Skipping {title}: {e}")
                continue

            venue = item.get('venue', {})
            location = venue.get('venue', '')
            if venue.get('address'):
                location += f", {venue['address']}"
            if venue.get('city'):
                location += f", {venue['city']}"
            if not location:
                location = self.VENUE_ADDRESS

            # Strip HTML tags from description
            description = item.get('description', '')
            if description:
                import re
                description = re.sub(r'<[^>]+>', '', description).strip()
                # Collapse whitespace
                description = re.sub(r'\s+', ' ', description)

            events.append({
                'title': title,
                'dtstart': dtstart,
                'dtend': dtend,
                'url': item.get('url', ''),
                'location': location,
                'description': description[:500] if description else '',
            })

            self.logger.info(f"Found: {title} on {dtstart.strftime('%Y-%m-%d')}")

        return events


if __name__ == '__main__':
    SpreckelsScraper.main()
