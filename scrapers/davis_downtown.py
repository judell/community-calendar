#!/usr/bin/env python3
"""
Scraper for Davis Downtown events
https://davisdowntown.com/events/

WordPress site with The Events Calendar plugin - provides ICS feed.
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

from datetime import datetime
from typing import Any

import requests
from icalendar import Calendar

from lib.base import BaseScraper


class DavisDowntownScraper(BaseScraper):
    """Scraper for Davis Downtown events."""

    name = "Davis Downtown"
    domain = "davisdowntown.com"

    ICS_URL = "https://davisdowntown.com/events/?ical=1"

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from ICS feed."""
        self.logger.info(f"Fetching {self.ICS_URL}")

        try:
            response = requests.get(self.ICS_URL, timeout=30)
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
            if component.name == "VEVENT":
                try:
                    title = str(component.get('summary', ''))
                    if not title:
                        continue

                    dtstart = component.get('dtstart')
                    dtend = component.get('dtend')
                    
                    if dtstart:
                        dt_start = dtstart.dt
                    else:
                        continue

                    dt_end = dtend.dt if dtend else None

                    location = str(component.get('location', '')) or None
                    description = str(component.get('description', '')) or None
                    url = str(component.get('url', '')) or None

                    events.append({
                        'title': title,
                        'dtstart': dt_start,
                        'dtend': dt_end,
                        'location': location,
                        'description': description,
                        'url': url,
                    })

                    self.logger.info(f"Found event: {title}")

                except Exception as e:
                    self.logger.warning(f"Error parsing event: {e}")
                    continue

        return events


if __name__ == '__main__':
    DavisDowntownScraper.main()
