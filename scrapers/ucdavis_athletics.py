#!/usr/bin/env python3
"""
Scraper for UC Davis Athletics events
https://ucdavisaggies.com/calendar

Sidearm Sports platform - provides ICS feed.
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

from datetime import datetime
from typing import Any

import requests
from icalendar import Calendar

from lib.base import BaseScraper


class UCDavisAthleticsScraper(BaseScraper):
    """Scraper for UC Davis Athletics events."""

    name = "UC Davis Athletics"
    domain = "ucdavisaggies.com"

    ICS_URL = "https://ucdavisaggies.com/calendar.ashx/calendar.ics"

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from ICS feed."""
        self.logger.info(f"Fetching {self.ICS_URL}")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        try:
            response = requests.get(self.ICS_URL, headers=headers, timeout=30)
            response.raise_for_status()
            return self._parse_ics(response.text)
        except Exception as e:
            self.logger.error(f"Error fetching ICS: {e}")
            return []

    def _parse_ics(self, ics_content: str) -> list[dict[str, Any]]:
        """Parse events from ICS content."""
        events = []
        try:
            cal = Calendar.from_ical(ics_content)
        except Exception as e:
            self.logger.warning(f"Error parsing ICS: {e}")
            return events

        for component in cal.walk():
            if component.name != "VEVENT":
                continue

            try:
                event = self._parse_event(component)
                if event:
                    events.append(event)
            except Exception as e:
                self.logger.warning(f"Error parsing event: {e}")
                continue

        return events

    def _parse_event(self, component) -> dict[str, Any] | None:
        """Parse a single VEVENT component."""
        summary = str(component.get('summary', ''))
        if not summary:
            return None

        dtstart = component.get('dtstart')
        if not dtstart:
            return None
        dtstart = dtstart.dt

        dtend = component.get('dtend')
        dtend = dtend.dt if dtend else dtstart

        location = str(component.get('location', '')) or 'UC Davis'
        description = str(component.get('description', ''))
        url = str(component.get('url', ''))
        
        # Clean up HTML entities in URL
        url = url.replace('&amp;', '&')

        uid = str(component.get('uid', ''))

        return {
            'title': summary,
            'dtstart': dtstart,
            'dtend': dtend,
            'location': location,
            'description': description,
            'url': url,
            'uid': uid,
        }


if __name__ == '__main__':
    UCDavisAthleticsScraper.main()
