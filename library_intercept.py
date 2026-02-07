#!/usr/bin/env python3
"""
Scraper for library events (Sonoma County Library, Bloomington Library)
Fetches all upcoming events from the library event pages.
"""

import sys
sys.path.insert(0, 'scrapers')

import argparse
import re
from datetime import datetime
from typing import Any

import requests
from bs4 import BeautifulSoup
from zoneinfo import ZoneInfo

from lib.base import BaseScraper


class LibraryScraper(BaseScraper):
    """Scraper for library events."""

    # These will be set based on location
    name = "Library"
    domain = "library.org"
    base_url = ""
    url_prefix = ""
    timezone = "America/Los_Angeles"

    # Library-specific configurations
    CONFIGS = {
        'santarosa': {
            'name': 'Sonoma County Library',
            'domain': 'sonomalibrary.org',
            'base_url': 'https://events.sonomalibrary.org/events/list?page=',
            'url_prefix': 'https://events.sonomalibrary.org',
            'timezone': 'America/Los_Angeles',
        },
        'bloomington': {
            'name': 'Bloomington Library',
            'domain': 'bloomingtonlibrary.org',
            'base_url': 'https://www.bloomingtonlibrary.org/events/list?page=',
            'url_prefix': 'https://www.bloomingtonlibrary.org',
            'timezone': 'America/Indiana/Indianapolis',
        }
    }

    def __init__(self, location: str = 'santarosa'):
        super().__init__()
        config = self.CONFIGS.get(location)
        if not config:
            raise ValueError(f"Unsupported location: {location}. Use: {list(self.CONFIGS.keys())}")

        self.location = location
        self.name = config['name']
        self.domain = config['domain']
        self.base_url = config['base_url']
        self.url_prefix = config['url_prefix']
        self.timezone = config['timezone']

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch all events from the library event pages."""
        page = 1
        all_events = []

        while True:
            url = self.base_url + str(page)
            self.logger.info(f"Scraping page {page}")

            events = self._scrape_page(url)
            if not events:
                break

            parsed_events = [self._parse_event(e) for e in events]
            parsed_events = [e for e in parsed_events if e is not None]

            if not parsed_events:
                break

            all_events.extend(parsed_events)
            page += 1

        return all_events

    def _scrape_page(self, url: str) -> list:
        """Scrape events from a single page."""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup.find_all('div', class_='lc-list-event-content-container')
        except Exception as e:
            self.logger.warning(f"Error scraping {url}: {e}")
            return []

    def _parse_event(self, event) -> dict[str, Any] | None:
        """Parse a single event."""
        try:
            title_element = event.find('h2')
            if not title_element or not title_element.find('a'):
                return None

            title = title_element.text.strip()
            url = self.url_prefix + title_element.find('a')['href']

            date_element = event.find('div', class_='lc-list-event-info-item--date')
            if not date_element:
                return None

            date_str = ' '.join(date_element.text.strip().split())

            location_element = event.find('div', class_='lc-list-event-location')
            location = location_element.text.strip() if location_element else "Location not specified"

            description_element = event.find('div', class_='lc-list-event-description')
            description = description_element.text.strip() if description_element else ""

            # Parse date and time
            date_pattern = r'(\w+, \w+ \d{1,2}, \d{4}) at (\d{1,2}:\d{2}(?:am|pm)) - (\d{1,2}:\d{2}(?:am|pm))'
            match = re.match(date_pattern, date_str)

            if not match:
                self.logger.debug(f"Failed to parse date: {date_str}")
                return None

            date_str, start_time_str, end_time_str = match.groups()

            date = datetime.strptime(date_str, '%A, %B %d, %Y')
            start_time = datetime.strptime(start_time_str, '%I:%M%p')
            end_time = datetime.strptime(end_time_str, '%I:%M%p')

            tz = ZoneInfo(self.timezone)
            dt_start = date.replace(hour=start_time.hour, minute=start_time.minute, tzinfo=tz)
            dt_end = date.replace(hour=end_time.hour, minute=end_time.minute, tzinfo=tz)

            self.logger.info(f"Found event: {title} on {dt_start}")

            return {
                'title': title,
                'description': description,
                'location': location,
                'dtstart': dt_start,
                'dtend': dt_end,
                'url': url
            }
        except Exception as e:
            self.logger.debug(f"Error parsing event: {e}")
            return None

    def default_output_filename(self) -> str:
        """Generate default output filename including location."""
        return f"{self.location}/library_intercept.ics"


def main():
    parser = argparse.ArgumentParser(description='Scrape library events.')
    parser.add_argument('--location', type=str, required=True,
                        choices=['santarosa', 'bloomington'],
                        help='Library to scrape')
    parser.add_argument('--output', '-o', type=str, help='Output filename')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()

    LibraryScraper.setup_logging()
    if args.debug:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = LibraryScraper(args.location)
    scraper.run(args.output)


if __name__ == '__main__':
    main()
