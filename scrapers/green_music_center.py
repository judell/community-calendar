#!/usr/bin/env python3
"""
Scraper for Green Music Center at Sonoma State University.

Usage:
    python scrapers/green_music_center.py --output cities/santarosa/green_music_center.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import re
from datetime import datetime, timedelta
from typing import Any

import requests
from bs4 import BeautifulSoup

from lib.base import BaseScraper
from lib.utils import DEFAULT_HEADERS


MONTH_MAP = {
    'jan': 1, 'january': 1, 'feb': 2, 'february': 2,
    'mar': 3, 'march': 3, 'apr': 4, 'april': 4,
    'may': 5, 'jun': 6, 'june': 6,
    'jul': 7, 'july': 7, 'aug': 8, 'august': 8,
    'sep': 9, 'september': 9, 'oct': 10, 'october': 10,
    'nov': 11, 'november': 11, 'dec': 12, 'december': 12,
}


class GreenMusicCenterScraper(BaseScraper):
    """Scraper for Green Music Center events."""

    name = "Green Music Center"
    domain = "gmc.sonoma.edu"

    URL = "https://gmc.sonoma.edu/all-events/"
    VENUE_ADDRESS = "Green Music Center, 1801 E Cotati Ave, Rohnert Park, CA 94928"

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from GMC events page (first page only, static HTML)."""
        self.logger.info(f"Fetching {self.URL}")
        response = requests.get(self.URL, headers=DEFAULT_HEADERS, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        events = []

        for container in soup.select('div.event_container'):
            event = self._parse_event(container)
            if event:
                events.append(event)

        return events

    def _parse_event(self, container) -> dict[str, Any] | None:
        """Parse a single event_container div."""
        month_el = container.select_one('.e_month')
        date_el = container.select_one('.e_date')
        title_el = container.select_one('.title a')
        time_el = container.select_one('.e_time')
        loc_el = container.select_one('.e_location')
        desc_el = container.select_one('.summary a')

        if not title_el or not month_el or not date_el:
            return None

        title = title_el.get_text(strip=True)
        url = title_el.get('href', self.URL)
        month_str = month_el.get_text(strip=True).lower()
        date_str = date_el.get_text(strip=True)

        month = MONTH_MAP.get(month_str)
        if not month:
            self.logger.warning(f"Unknown month '{month_str}' for {title}")
            return None

        # Determine year — assume current or next year
        now = datetime.now()
        year = now.year
        if month < now.month - 1:
            year += 1

        # Date can be "26" or "21-23" (range)
        date_parts = re.split(r'[-–]', date_str)
        try:
            start_day = int(date_parts[0].strip())
        except ValueError:
            self.logger.warning(f"Bad date '{date_str}' for {title}")
            return None

        # Parse time: "7:30 p.m." or "Various Times"
        time_text = time_el.get_text(strip=True) if time_el else ''
        hour, minute = self._parse_time(time_text)

        dtstart = datetime(year, month, start_day, hour, minute)

        if len(date_parts) > 1:
            try:
                end_day = int(date_parts[1].strip())
                dtend = datetime(year, month, end_day, hour, minute)
            except ValueError:
                dtend = dtstart + timedelta(hours=3)
        else:
            dtend = dtstart + timedelta(hours=3)

        location = loc_el.get_text(strip=True) if loc_el else ''
        if location and 'Hall' in location:
            location = f"{location}, {self.VENUE_ADDRESS}"
        elif not location:
            location = self.VENUE_ADDRESS

        description = desc_el.get_text(strip=True)[:500] if desc_el else ''

        self.logger.info(f"Found: {title} on {dtstart.strftime('%Y-%m-%d')}")

        return {
            'title': title,
            'dtstart': dtstart,
            'dtend': dtend,
            'url': url,
            'location': location,
            'description': description,
        }

    @staticmethod
    def _parse_time(text: str) -> tuple[int, int]:
        """Parse '7:30 p.m.' -> (19, 30). Returns (20, 0) as default for evening events."""
        m = re.match(r'(\d+):(\d+)\s*(a\.?m\.?|p\.?m\.?)', text, re.IGNORECASE)
        if m:
            hour = int(m.group(1))
            minute = int(m.group(2))
            ampm = m.group(3).replace('.', '').lower()
            if ampm == 'pm' and hour != 12:
                hour += 12
            elif ampm == 'am' and hour == 12:
                hour = 0
            return hour, minute
        return 20, 0  # Default to 8pm for performing arts


if __name__ == '__main__':
    GreenMusicCenterScraper.main()
