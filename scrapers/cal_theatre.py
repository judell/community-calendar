#!/usr/bin/env python3
"""
Scraper for California Theatre (Cal Theatre) Santa Rosa events
https://www.caltheatre.com/calendar

This is a Wix site with a calendar widget.
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import re
import time
from datetime import datetime, timedelta
from typing import Any

import requests
from bs4 import BeautifulSoup

from lib.base import BaseScraper
from lib.utils import DEFAULT_HEADERS


class CalTheatreScraper(BaseScraper):
    """Scraper for California Theatre Santa Rosa events."""

    name = "Cal Theatre"
    domain = "caltheatre.com"

    BASE_URL = 'https://www.caltheatre.com'
    CALENDAR_URL = f'{BASE_URL}/calendar'
    VENUE_ADDRESS = "California Theatre, 528 7th St, Santa Rosa, CA 95401"
    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events using static request or Selenium."""
        # Try static first
        self.logger.info(f"Fetching {self.CALENDAR_URL}")
        response = requests.get(self.CALENDAR_URL, headers=DEFAULT_HEADERS, timeout=30)
        response.raise_for_status()

        events = self._parse_wix_calendar(response.text)

        # If no events found, could try Selenium as fallback
        if not events:
            self.logger.warning("No events found with static fetch - Wix may require JavaScript")

        return events

    def _parse_wix_calendar(self, html_content: str) -> list[dict[str, Any]]:
        """Parse events from Wix calendar text content."""
        soup = BeautifulSoup(html_content, 'html.parser')
        events = []

        month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                       'July', 'August', 'September', 'October', 'November', 'December']

        # Try to find calendar day cells with events
        calendar_cells = soup.find_all(attrs={'data-hook': re.compile(r'calendar-day-\d+')})

        for cell in calendar_cells:
            try:
                cell_text = cell.get_text(' ', strip=True)

                # Extract day number from data-hook
                hook = cell.get('data-hook', '')
                day_match = re.search(r'calendar-day-(\d+)', hook)
                if not day_match:
                    continue
                day = int(day_match.group(1))

                # Find events - format: "15 7:30 PM Event Title +1 more"
                event_patterns = re.findall(
                    r'(\d{1,2}:\d{2}\s*(?:AM|PM))\s+([^+]+?)(?:\s*\+|$)',
                    cell_text, re.IGNORECASE
                )

                for time_str, title in event_patterns:
                    title = title.strip()
                    if not title or len(title) < 3:
                        continue

                    # Try to determine year and month from context
                    now = datetime.now()
                    year = now.year
                    month = now.month

                    # If day is less than current day, might be next month
                    if day < now.day:
                        month += 1
                        if month > 12:
                            month = 1
                            year += 1

                    try:
                        month_name = month_names[month - 1]
                        date_str = f"{month_name} {day}, {year}"
                        dt_start = datetime.strptime(f"{date_str} {time_str}", "%B %d, %Y %I:%M %p")
                    except ValueError:
                        continue

                    dt_end = dt_start + timedelta(hours=3)

                    events.append({
                        'title': title,
                        'url': self.CALENDAR_URL,
                        'dtstart': dt_start,
                        'dtend': dt_end,
                        'location': self.VENUE_ADDRESS,
                        'description': f'Event at California Theatre. See {self.CALENDAR_URL} for details.'
                    })

                    self.logger.info(f"Found event: {title} on {dt_start}")

            except Exception as e:
                self.logger.warning(f"Error parsing cell: {e}")
                continue

        return events


if __name__ == '__main__':
    CalTheatreScraper.main()
