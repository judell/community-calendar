#!/usr/bin/env python3
"""
Scraper for Redwood Cafe Cotati events
https://redwoodcafecotati.com/events/

Uses WordPress "My Calendar" plugin - fetches multiple months.
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import re
from datetime import datetime, timedelta
from typing import Any

import requests
from bs4 import BeautifulSoup

from lib.base import BaseScraper


class RedwoodCafeScraper(BaseScraper):
    """Scraper for Redwood Cafe Cotati events."""

    name = "Redwood Cafe"
    domain = "redwoodcafecotati.com"

    BASE_URL = 'https://redwoodcafecotati.com'
    EVENTS_URL = f'{BASE_URL}/events/'
    VENUE_ADDRESS = "Redwood Cafe, 8240 Old Redwood Hwy, Cotati, CA 94931"
    months_ahead = 3

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events for current and upcoming months."""
        all_events = []
        now = datetime.now()

        for i in range(self.months_ahead + 1):
            year = now.year + (now.month + i - 1) // 12
            month = (now.month + i - 1) % 12 + 1

            url = f"{self.EVENTS_URL}?month={month:02d}&yr={year}"
            self.logger.info(f"Fetching {url}")

            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                events = self._parse_events(response.text, year, month)
                all_events.extend(events)
            except Exception as e:
                self.logger.warning(f"Error fetching {url}: {e}")

        return all_events

    def _parse_events(self, html_content: str, year: int, month: int) -> list[dict[str, Any]]:
        """Parse events from the calendar HTML."""
        soup = BeautifulSoup(html_content, 'html.parser')
        events = []

        for article in soup.find_all('article', class_='calendar-event'):
            try:
                # Get event title from button data-modal-title attribute
                button = article.find('button', class_='mc-modal')
                if not button:
                    continue

                title = button.get('data-modal-title', '')
                if not title:
                    continue

                title = title.replace('&amp;', '&')

                # Get time from button text
                button_text = button.get_text(' ', strip=True)
                time_match = re.search(r'(\d{1,2}:\d{2})\s*(AM|PM)', button_text, re.IGNORECASE)

                # Parse day from article ID
                article_id = article.get('id', '')
                day_match = re.search(r'mc_calendar_(\d{2})_', article_id)
                if not day_match:
                    continue

                day = int(day_match.group(1))

                try:
                    event_date = datetime(year, month, day)
                except ValueError:
                    self.logger.warning(f"Invalid date: {year}-{month}-{day}")
                    continue

                # Parse time
                if time_match:
                    time_str = f"{time_match.group(1)} {time_match.group(2)}"
                    try:
                        time_obj = datetime.strptime(time_str, "%I:%M %p")
                        dt_start = event_date.replace(hour=time_obj.hour, minute=time_obj.minute)
                    except ValueError:
                        dt_start = event_date.replace(hour=18, minute=0)
                else:
                    dt_start = event_date.replace(hour=18, minute=0)

                dt_end = dt_start + timedelta(hours=3)

                events.append({
                    'title': title,
                    'url': self.EVENTS_URL,
                    'dtstart': dt_start,
                    'dtend': dt_end,
                    'location': self.VENUE_ADDRESS,
                    'description': 'Live music at Redwood Cafe Cotati.'
                })

                self.logger.info(f"Found event: {title} on {dt_start}")

            except Exception as e:
                self.logger.warning(f"Error parsing event: {e}")
                continue

        return events


if __name__ == '__main__':
    RedwoodCafeScraper.main()
