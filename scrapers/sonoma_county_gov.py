#!/usr/bin/env python3
"""
Scraper for Sonoma County Government calendar
https://sonomacounty.gov/sonoma-county-calendar

Uses JSON API endpoint - includes county meetings, parks events, and more.
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

from datetime import datetime, timedelta
from typing import Any

import requests

from lib.base import BaseScraper


class SonomaCountyGovScraper(BaseScraper):
    """Scraper for Sonoma County Government calendar."""

    name = "Sonoma County Government"
    domain = "sonomacounty.gov"

    API_URL = 'https://sonomacounty.gov/api/FeedData/CalendarEvents'
    PAGE_ID = 'x116193'
    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from the JSON API."""
        results = []
        seen_urls = set()

        # Fetch from today to N months ahead
        now = datetime.now()
        start_date = now.replace(day=1)

        for i in range(self.months_ahead + 1):
            # Calculate month boundaries
            year = start_date.year + (start_date.month + i - 1) // 12
            month = (start_date.month + i - 1) % 12 + 1

            month_start = f"{year}-{month:02d}-01"
            if month == 12:
                month_end = f"{year + 1}-01-01"
            else:
                month_end = f"{year}-{month + 1:02d}-01"

            params = {
                'pageId': self.PAGE_ID,
                'start': month_start,
                'end': month_end
            }

            self.logger.info(f"Fetching events from {month_start} to {month_end}")
            response = requests.get(self.API_URL, params=params, timeout=30)
            response.raise_for_status()

            for event_data in response.json():
                parsed = self._parse_event(event_data, seen_urls)
                if parsed:
                    results.append(parsed)

        return results

    def _parse_event(self, event_data: dict, seen_urls: set) -> dict[str, Any] | None:
        """Parse a single event from JSON data."""
        title = event_data.get('title', '').strip()
        if not title:
            return None

        # Skip canceled events
        if event_data.get('className') == 'canceled':
            return None
        if title.upper().startswith('CANCELED'):
            return None

        url = event_data.get('url', '')

        # Dedupe by URL
        if url in seen_urls:
            return None
        seen_urls.add(url)

        # Parse start time
        start_str = event_data.get('start', '')
        if not start_str:
            return None

        try:
            dt_start = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                dt_start = datetime.strptime(start_str, "%Y-%m-%d")
            except ValueError:
                self.logger.warning(f"Could not parse date: {start_str}")
                return None

        # Parse end time
        end_str = event_data.get('end', '')
        if end_str:
            try:
                dt_end = datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                dt_end = dt_start
        else:
            dt_end = dt_start

        self.logger.info(f"Found event: {title} on {dt_start}")

        return {
            'title': title,
            'url': url,
            'dtstart': dt_start,
            'dtend': dt_end,
            'description': event_data.get('abstract', ''),
            'location': 'Sonoma County, CA'
        }


if __name__ == '__main__':
    SonomaCountyGovScraper.main()
