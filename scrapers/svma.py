#!/usr/bin/env python3
"""
Scraper for Sonoma Valley Museum of Art (SVMA) events
https://www.svma.org/events
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


class SVMAScraper(BaseScraper):
    """Scraper for Sonoma Valley Museum of Art events."""

    name = "Sonoma Valley Museum of Art"
    domain = "svma.org"

    BASE_URL = 'https://svma.org'
    EVENTS_URL = f'{BASE_URL}/events'
    VENUE_ADDRESS = "Sonoma Valley Museum of Art, 551 Broadway, Sonoma, CA 95476"

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch and parse events from the events page."""
        self.logger.info(f"Fetching {self.EVENTS_URL}")
        response = requests.get(self.EVENTS_URL, headers=DEFAULT_HEADERS, timeout=30)
        response.raise_for_status()

        return self._parse_events(response.text)

    def _parse_events(self, html_content: str) -> list[dict[str, Any]]:
        """Parse events from the events page."""
        soup = BeautifulSoup(html_content, 'html.parser')
        events = []
        seen_urls = set()

        for link in soup.find_all('a', href=re.compile(r'/event/')):
            try:
                href = link.get('href', '')
                if not href or href in seen_urls:
                    continue

                parent = link.find_parent(['div', 'article', 'section'])
                if not parent:
                    continue

                parent_text = parent.get_text(' ', strip=True)

                # Parse date: "02.07.26 | 4:00PM" format
                date_match = re.search(
                    r'(\d{2})\.(\d{2})\.(\d{2})\s*\|\s*(\d{1,2}:\d{2}\s*(?:AM|PM)?)',
                    parent_text, re.IGNORECASE
                )
                if not date_match:
                    # Try date range format: "04.09.26 - 04.24.26"
                    date_match = re.search(r'(\d{2})\.(\d{2})\.(\d{2})', parent_text)
                    if date_match:
                        month, day, year = date_match.groups()
                        year = 2000 + int(year)
                        month = int(month)
                        day = int(day)
                        dt_start = datetime(year, month, day, 10, 0)
                        dt_end = dt_start + timedelta(hours=2)
                    else:
                        continue
                else:
                    month, day, year, time_str = date_match.groups()
                    year = 2000 + int(year)
                    month = int(month)
                    day = int(day)

                    # Parse time
                    time_str = time_str.strip().upper()
                    try:
                        if 'AM' in time_str or 'PM' in time_str:
                            time_obj = datetime.strptime(time_str, "%I:%M%p")
                        else:
                            time_obj = datetime.strptime(time_str, "%H:%M")
                        dt_start = datetime(year, month, day, time_obj.hour, time_obj.minute)
                    except ValueError:
                        dt_start = datetime(year, month, day, 18, 0)

                    dt_end = dt_start + timedelta(hours=2)

                # Get title from link text
                title = link.get_text(strip=True)
                if not title or title in ['more info', '.st1{fill:url(#SVGID_1_);}']:
                    h_tag = parent.find(['h2', 'h3', 'h4'])
                    if h_tag:
                        title = h_tag.get_text(strip=True)
                    else:
                        continue

                if not title or len(title) < 3:
                    continue

                seen_urls.add(href)

                full_url = href if href.startswith('http') else self.BASE_URL + href

                events.append({
                    'title': title,
                    'url': full_url,
                    'dtstart': dt_start,
                    'dtend': dt_end,
                    'location': self.VENUE_ADDRESS,
                    'description': f'Event at Sonoma Valley Museum of Art. More info: {full_url}'
                })

                self.logger.info(f"Found event: {title} on {dt_start}")

            except Exception as e:
                self.logger.warning(f"Error parsing event: {e}")
                continue

        return events


if __name__ == '__main__':
    SVMAScraper.main()
