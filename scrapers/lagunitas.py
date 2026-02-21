#!/usr/bin/env python3
"""
Scraper for Lagunitas Brewing Company Petaluma Taproom events.

Usage:
    python scrapers/lagunitas.py --output cities/santarosa/lagunitas.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

from datetime import datetime, timedelta
from typing import Any

import requests
from bs4 import BeautifulSoup

from lib.base import BaseScraper
from lib.utils import DEFAULT_HEADERS


class LagunitasScraper(BaseScraper):
    """Scraper for Lagunitas Taproom Petaluma events."""

    name = "Lagunitas Brewing Company"
    domain = "lagunitas.com"

    URL = "https://lagunitas.com/taproom/petaluma/"
    VENUE_ADDRESS = "Lagunitas Brewing Company, 1280 N McDowell Blvd, Petaluma, CA 94954"

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from Lagunitas taproom page."""
        self.logger.info(f"Fetching {self.URL}")
        response = requests.get(self.URL, headers=DEFAULT_HEADERS, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        events = []

        for row in soup.select('.event-row'):
            date_el = row.select_one('.date')
            title_el = row.select_one('.desc h2')

            if not date_el or not title_el:
                continue

            title = title_el.get_text(strip=True)
            date_str = date_el.get_text(strip=True)

            # Parse date: MM/DD/YYYY
            try:
                event_date = datetime.strptime(date_str, '%m/%d/%Y')
            except ValueError:
                self.logger.warning(f"Skipping {title}: bad date '{date_str}'")
                continue

            # Parse start/end times from .time-wrap .time elements
            times = row.select('.time-wrap .time')
            if times:
                start_time = self._parse_time(times[0].get_text(strip=True))
                end_time = self._parse_time(times[1].get_text(strip=True)) if len(times) > 1 else None
            else:
                start_time = None
                end_time = None

            if start_time:
                dtstart = event_date.replace(hour=start_time[0], minute=start_time[1])
            else:
                dtstart = event_date

            if end_time:
                dtend = event_date.replace(hour=end_time[0], minute=end_time[1])
                if dtend < dtstart:
                    dtend += timedelta(days=1)
            else:
                dtend = dtstart + timedelta(hours=2)

            # Optional "More Info" link
            link_el = row.select_one('.buy-btn a')
            url = link_el['href'] if link_el and link_el.get('href') else self.URL

            events.append({
                'title': title,
                'dtstart': dtstart,
                'dtend': dtend,
                'url': url,
                'location': self.VENUE_ADDRESS,
            })

            self.logger.info(f"Found: {title} on {dtstart.strftime('%Y-%m-%d %H:%M')}")

        return events

    @staticmethod
    def _parse_time(time_str: str) -> tuple[int, int] | None:
        """Parse '3:30 PM' -> (15, 30)."""
        try:
            dt = datetime.strptime(time_str.strip(), '%I:%M %p')
            return (dt.hour, dt.minute)
        except ValueError:
            return None


if __name__ == '__main__':
    LagunitasScraper.main()
