#!/usr/bin/env python3
"""
Scraper for Sebastopol Center for the Arts events
https://www.sebarts.org/classes-and-events
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import re
import time
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from lib.base import BaseScraper
from lib.utils import fetch_with_retry


class SebArtsScraper(BaseScraper):
    """Scraper for Sebastopol Center for the Arts events."""

    name = "Sebastopol Center for the Arts"
    domain = "sebarts.org"

    BASE_URL = 'https://www.sebarts.org'
    EVENTS_URL = f'{BASE_URL}/classes-and-events'

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch and parse events from the events page."""
        self.logger.info(f"Fetching {self.EVENTS_URL}")
        main_page = fetch_with_retry(self.EVENTS_URL)

        events = []
        event_links = self._parse_event_links(main_page)

        for event_link in event_links:
            try:
                event_page = fetch_with_retry(event_link['url'])
                event = self._parse_event_details(event_page, event_link)
                if event:
                    events.append(event)
                    self.logger.info(f"Found event: {event['title']} on {event['dtstart']}")
                time.sleep(2)  # Rate limiting
            except Exception as e:
                self.logger.warning(f"Error fetching {event_link['url']}: {e}")

        return events

    def _parse_event_links(self, html_content: str) -> list[dict]:
        """Parse event links from the main page."""
        soup = BeautifulSoup(html_content, 'html.parser')
        seen_urls = set()
        events = []

        for event_elem in soup.find_all('a', href=re.compile(r'/classes-lectures/')):
            url = urljoin(self.BASE_URL, event_elem['href'])
            if url not in seen_urls:
                seen_urls.add(url)
                events.append({
                    'url': url,
                    'title': event_elem.text.strip()
                })

        return events

    def _parse_event_details(self, html_content: str, event_link: dict) -> dict[str, Any] | None:
        """Parse event details from the event page."""
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find title
        title_elem = soup.find('h1', class_='page-title')
        if title_elem:
            title = title_elem.text.strip()
        else:
            meta_title = soup.find('meta', property='og:title')
            title = meta_title['content'].strip() if meta_title else event_link['title']

        # Find description
        description_elem = soup.find('div', class_='sqs-block-content')
        description = description_elem.text.strip() if description_elem else ""

        # Find date and time
        date_elem = soup.find('time', class_='event-date')
        if not date_elem:
            return None

        date_str = date_elem.text.strip()
        date_str = re.sub(r'^[A-Za-z]+,\s*', '', date_str)  # Remove day of week

        try:
            date_obj = datetime.strptime(date_str, "%B %d, %Y")
        except ValueError:
            return None

        time_elem = soup.find('time', class_='event-time')
        if time_elem:
            time_str = time_elem.text.strip()
            try:
                start_time, end_time = time_str.split(' - ')
                dt_start = datetime.strptime(f"{date_str} {start_time}", "%B %d, %Y %I:%M%p")
                dt_end = datetime.strptime(f"{date_str} {end_time}", "%B %d, %Y %I:%M%p")
            except ValueError:
                dt_start = date_obj
                dt_end = date_obj + timedelta(days=1)
        else:
            dt_start = date_obj
            dt_end = date_obj + timedelta(days=1)

        return {
            'title': title,
            'url': event_link['url'],
            'dtstart': dt_start,
            'dtend': dt_end,
            'description': description,
            'location': 'Sebastopol Center for the Arts, 282 S High St, Sebastopol, CA 95472'
        }


if __name__ == '__main__':
    SebArtsScraper.main()
