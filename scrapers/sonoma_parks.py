#!/usr/bin/env python3
"""
Scraper for Sonoma County Regional Parks calendar
https://parks.sonomacounty.ca.gov/play/calendar
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import re
from datetime import datetime
from typing import Any

import requests
from bs4 import BeautifulSoup

from lib.base import BaseScraper


class SonomaParksScraper(BaseScraper):
    """Scraper for Sonoma County Regional Parks calendar."""

    name = "Sonoma County Parks"
    domain = "parks.sonomacounty.ca.gov"

    CALENDAR_URL = 'https://parks.sonomacounty.ca.gov/play/calendar'

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch and parse events from the calendar page."""
        self.logger.info(f"Fetching {self.CALENDAR_URL}")
        response = requests.get(self.CALENDAR_URL, timeout=30)
        response.raise_for_status()

        return self._parse_events(response.text)

    def _parse_events(self, html_content: str) -> list[dict[str, Any]]:
        """Parse events from the calendar HTML."""
        soup = BeautifulSoup(html_content, 'html.parser')
        events = []

        for listing in soup.find_all('div', class_='listing'):
            try:
                # Get title and URL
                title_link = listing.find('h3') or listing.find('h4')
                if not title_link:
                    continue

                anchor = title_link.find('a')
                if not anchor:
                    continue

                title = anchor.get_text(strip=True)
                # Clean up "sold out |" prefix
                title = re.sub(r'^sold out\s*\|\s*', '', title, flags=re.IGNORECASE)
                url = anchor.get('href', '')

                # Get event content div
                content = listing.find('div', class_='content')
                if not content:
                    continue

                text = content.get_text(' ', strip=True)

                # Parse date - format: "February 3, 2026"
                date_match = re.search(r'(\w+)\s+(\d{1,2}),\s+(\d{4})', text)
                if not date_match:
                    continue

                month_name, day, year = date_match.groups()

                # Parse time - format: "4:00 pm - 5:30 pm"
                time_match = re.search(
                    r'(\d{1,2}:\d{2})\s*(am|pm)\s*-\s*(\d{1,2}:\d{2})\s*(am|pm)',
                    text, re.IGNORECASE
                )

                if time_match:
                    start_time_str = f"{time_match.group(1)} {time_match.group(2)}"
                    end_time_str = f"{time_match.group(3)} {time_match.group(4)}"
                else:
                    single_time = re.search(r'(\d{1,2}:\d{2})\s*(am|pm)', text, re.IGNORECASE)
                    if single_time:
                        start_time_str = f"{single_time.group(1)} {single_time.group(2)}"
                        end_time_str = None
                    else:
                        start_time_str = "12:00 pm"
                        end_time_str = None

                # Parse the datetime
                try:
                    date_str = f"{month_name} {day}, {year}"
                    dt_start = datetime.strptime(f"{date_str} {start_time_str}", "%B %d, %Y %I:%M %p")
                    if end_time_str:
                        dt_end = datetime.strptime(f"{date_str} {end_time_str}", "%B %d, %Y %I:%M %p")
                    else:
                        dt_end = dt_start
                except ValueError as e:
                    self.logger.warning(f"Could not parse date/time for '{title}': {e}")
                    continue

                # Get location if present
                location_match = re.search(r'\|\s*([^|]+?)\s*(?:$|PETALUMA|Description)', text)
                location = None
                if location_match:
                    loc_text = location_match.group(1).strip()
                    if any(word in loc_text.lower() for word in ['park', 'trail', 'regional', 'preserve']):
                        location = loc_text

                # Get description
                desc_elem = listing.find('p')
                description = desc_elem.get_text(strip=True) if desc_elem else ''

                events.append({
                    'title': title,
                    'url': url,
                    'dtstart': dt_start,
                    'dtend': dt_end,
                    'location': location,
                    'description': description
                })

                self.logger.info(f"Found event: {title} on {dt_start}")

            except Exception as e:
                self.logger.warning(f"Error parsing event: {e}")
                continue

        return events


if __name__ == '__main__':
    SonomaParksScraper.main()
