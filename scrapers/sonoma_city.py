#!/usr/bin/env python3
"""
Scraper for City of Sonoma calendar
https://www.sonomacity.org/calendar

Includes city council meetings, commission meetings, and special events.
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import re
from datetime import datetime, timedelta
from typing import Any

import requests
from bs4 import BeautifulSoup

from lib.base import BaseScraper
from lib.utils import DEFAULT_HEADERS, MONTH_MAP


class SonomaCityScraper(BaseScraper):
    """Scraper for City of Sonoma calendar."""

    name = "City of Sonoma"
    domain = "sonomacity.org"

    BASE_URL = 'https://www.sonomacity.org'
    CALENDAR_URL = f'{BASE_URL}/calendar'
    DEFAULT_LOCATION = "City Council Chambers, 177 First St. West, Sonoma, CA 95476"

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch and parse events from the calendar page."""
        self.logger.info(f"Fetching {self.CALENDAR_URL}")
        response = requests.get(self.CALENDAR_URL, headers=DEFAULT_HEADERS, timeout=30)
        response.raise_for_status()

        return self._parse_events(response.text)

    def _parse_events(self, html_content: str) -> list[dict[str, Any]]:
        """Parse events from the calendar page."""
        soup = BeautifulSoup(html_content, 'html.parser')
        events = []
        seen_urls = set()

        for link in soup.find_all('a', href=re.compile(r'/event/')):
            try:
                href = link.get('href', '')
                if not href or href in seen_urls:
                    continue

                title = link.get_text(strip=True)
                if not title or len(title) < 3:
                    continue

                parent = link.find_parent(['article', 'div', 'li'])
                if not parent:
                    continue

                parent_text = parent.get_text(' ', strip=True)

                # Parse date: "Feb 4 2026" or "Feb 4, 2026"
                date_match = re.search(
                    r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})',
                    parent_text, re.IGNORECASE
                )
                if not date_match:
                    continue

                month_name, day, year = date_match.groups()
                year = int(year)
                day = int(day)

                month = MONTH_MAP.get(month_name.lower())
                if not month:
                    continue

                # Parse time: "6:00pm - 9:00pm" or "6:00pm"
                time_match = re.search(r'(\d{1,2}:\d{2})\s*(am|pm)', parent_text, re.IGNORECASE)
                if time_match:
                    time_str = f"{time_match.group(1)} {time_match.group(2)}"
                    try:
                        time_obj = datetime.strptime(time_str, "%I:%M %p")
                        dt_start = datetime(year, month, day, time_obj.hour, time_obj.minute)
                    except ValueError:
                        dt_start = datetime(year, month, day, 18, 0)
                elif 'all day' in parent_text.lower():
                    dt_start = datetime(year, month, day, 0, 0)
                else:
                    dt_start = datetime(year, month, day, 18, 0)

                # Parse end time
                end_match = re.search(r'-\s*(\d{1,2}:\d{2})\s*(am|pm)', parent_text, re.IGNORECASE)
                if end_match:
                    end_time_str = f"{end_match.group(1)} {end_match.group(2)}"
                    try:
                        end_time_obj = datetime.strptime(end_time_str, "%I:%M %p")
                        dt_end = datetime(year, month, day, end_time_obj.hour, end_time_obj.minute)
                    except ValueError:
                        dt_end = dt_start + timedelta(hours=2)
                else:
                    dt_end = dt_start + timedelta(hours=2)

                seen_urls.add(href)

                full_url = href if href.startswith('http') else self.BASE_URL + href

                # Get location if mentioned
                location = self.DEFAULT_LOCATION

                events.append({
                    'title': title,
                    'url': full_url,
                    'dtstart': dt_start,
                    'dtend': dt_end,
                    'location': location,
                    'description': f'City of Sonoma event. More info: {full_url}'
                })

                self.logger.info(f"Found event: {title} on {dt_start}")

            except Exception as e:
                self.logger.warning(f"Error parsing event: {e}")
                continue

        return events


if __name__ == '__main__':
    SonomaCityScraper.main()
