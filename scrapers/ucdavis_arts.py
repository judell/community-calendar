#!/usr/bin/env python3
"""
Scraper for UC Davis Arts calendar
https://arts.ucdavis.edu/calendar

Provides ICS feed at monthly URLs.
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

from datetime import datetime
from typing import Any

import requests
from icalendar import Calendar

from lib.base import BaseScraper


class UCDavisArtsScraper(BaseScraper):
    """Scraper for UC Davis Arts calendar."""

    name = "UC Davis Arts"
    domain = "arts.ucdavis.edu"

    BASE_URL = "https://arts.ucdavis.edu/calendar/ical"

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from monthly ICS feeds."""
        all_events = []
        now = datetime.now()

        for i in range(self.months_ahead + 1):
            year = now.year + (now.month + i - 1) // 12
            month = (now.month + i - 1) % 12 + 1

            url = f"{self.BASE_URL}/{year}-{month:02d}"
            self.logger.info(f"Fetching {url}")

            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                events = self._parse_ics(response.text)
                all_events.extend(events)
            except Exception as e:
                self.logger.warning(f"Error fetching {url}: {e}")

        return all_events

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
    UCDavisArtsScraper.main()
