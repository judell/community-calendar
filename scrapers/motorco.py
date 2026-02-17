#!/usr/bin/env python3
"""
Scraper for Motorco Music Hall events.
https://motorcomusic.com/calendar/

Motorco uses the Total Calendar WordPress plugin which renders a FullCalendar.js
calendar with all events embedded inline in the HTML as JavaScript objects.

Usage:
    python scrapers/motorco.py --output cities/raleighdurham/motorco.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import re
from datetime import datetime, timedelta
from typing import Any

import requests

from lib.base import BaseScraper
from lib.utils import DEFAULT_HEADERS


class MotorcoScraper(BaseScraper):
    """Scraper for Motorco Music Hall events from inline FullCalendar data."""

    name = "Motorco Music Hall"
    domain = "motorcomusic.com"
    timezone = "America/New_York"

    CALENDAR_URL = "https://motorcomusic.com/calendar/"
    VENUE_ADDRESS = "Motorco Music Hall, 723 Rigsbee Ave, Durham, NC 27701"

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from inline FullCalendar JavaScript data."""
        self.logger.info(f"Fetching {self.CALENDAR_URL}")
        response = requests.get(self.CALENDAR_URL, headers=DEFAULT_HEADERS, timeout=30)
        response.raise_for_status()

        events = self._parse_fullcalendar_events(response.text)

        if not events:
            self.logger.warning("No events found - page structure may have changed")

        return events

    def _parse_fullcalendar_events(self, html: str) -> list[dict[str, Any]]:
        """Extract events from inline FullCalendar JavaScript initialization."""
        # Match individual event objects:
        # title: 'EVENT NAME', start: '2026-03-12 18:00', end: '...', url: '...'
        raw_events = re.findall(
            r"title:\s*'((?:[^'\\]|\\.)*)'"
            r",\s*start:\s*'([^']*)'"
            r",\s*end:\s*'([^']*)'"
            r",\s*url:\s*'([^']*)'",
            html
        )

        self.logger.info(f"Found {len(raw_events)} raw events in FullCalendar data")

        events = []
        now = datetime.now()

        for title, start_str, end_str, url in raw_events:
            # Unescape title
            title = title.replace("\\'", "'").replace("\\\\", "\\")

            # Parse start datetime: "2026-03-12 18:00"
            try:
                dtstart = datetime.strptime(start_str, "%Y-%m-%d %H:%M")
            except ValueError:
                self.logger.warning(f"Could not parse start date: {start_str}")
                continue

            # Skip past events
            if dtstart < now - timedelta(days=1):
                continue

            # Parse end datetime
            dtend = None
            if end_str:
                try:
                    dtend = datetime.strptime(end_str, "%Y-%m-%d %H:%M")
                except ValueError:
                    pass
            if not dtend:
                dtend = dtstart + timedelta(hours=3)

            events.append({
                'title': title,
                'dtstart': dtstart,
                'dtend': dtend,
                'url': url,
                'location': self.VENUE_ADDRESS,
                'description': '',
            })

        return events


if __name__ == '__main__':
    MotorcoScraper.main()
