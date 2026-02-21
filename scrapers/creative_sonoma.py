#!/usr/bin/env python3
"""
Scraper for Creative Sonoma (county arts agency) events.
https://creativesonoma.org/event/

Usage:
    python scrapers/creative_sonoma.py --output cities/santarosa/creative_sonoma.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import re
from datetime import datetime, timedelta
from typing import Any

import requests
from bs4 import BeautifulSoup

from lib.base import BaseScraper

# Creative Sonoma blocks the standard HEADERS User-Agent
HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'text/html,application/xhtml+xml',
}


class CreativeSonomaScraper(BaseScraper):
    """Scraper for Creative Sonoma arts events."""

    name = "Creative Sonoma"
    domain = "creativesonoma.org"

    BASE_URL = "https://creativesonoma.org/event/"

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from Creative Sonoma, paginated."""
        events = []

        for page in range(1, 10):  # Up to 10 pages, break when empty
            url = self.BASE_URL if page == 1 else f"{self.BASE_URL}?page={page}"
            self.logger.info(f"Fetching page {page}: {url}")

            response = requests.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.select('div.div-one')

            if not items:
                self.logger.info(f"No events on page {page}, stopping")
                break

            for item in items:
                event = self._parse_event(item)
                if event:
                    events.append(event)

        return events

    def _parse_event(self, item) -> dict[str, Any] | None:
        """Parse a single event from a div.div-one element."""
        title_el = item.select_one('span.ev-tt')
        if not title_el:
            return None
        title = title_el.get_text(strip=True)

        url = item.get('data-url', '')

        # Get venue
        venue_el = item.select_one('span.venue-event')
        location = venue_el.get_text(strip=True).lstrip('at').strip() if venue_el else ''

        # Get organization
        org_el = item.select_one('p.meta.auth a')
        org = org_el.get_text(strip=True) if org_el else ''

        # Get time slots from sibling div.show-events
        show_events = item.find_next('div', class_='show-events')
        if not show_events:
            return None

        time_items = show_events.select('.item')
        if not time_items:
            return None

        # Parse first time slot: "Feb 21, 2026 at 1:00pm - 4:00pm  (Sat)"
        dtstart, dtend = self._parse_time_slot(time_items[0].get_text(strip=True))
        if not dtstart:
            return None

        description = f"Presented by {org}" if org else ''

        self.logger.info(f"Found: {title} on {dtstart.strftime('%Y-%m-%d')}")

        return {
            'title': title,
            'dtstart': dtstart,
            'dtend': dtend or dtstart + timedelta(hours=2),
            'url': url,
            'location': location,
            'description': description,
        }

    @staticmethod
    def _parse_time_slot(text: str) -> tuple:
        """Parse 'Feb 21, 2026 at 1:00pm - 4:00pm  (Sat)' -> (dtstart, dtend)."""
        # Remove day-of-week suffix
        text = re.sub(r'\s*\([A-Za-z]+\)\s*$', '', text)

        # Pattern: "Mon DD, YYYY at H:MMam - H:MMpm"
        m = re.match(
            r'(\w+ \d+, \d{4})\s+at\s+(\d+:\d+\s*[ap]m)\s*-\s*(\d+:\d+\s*[ap]m)',
            text, re.IGNORECASE
        )
        if m:
            date_str, start_str, end_str = m.group(1), m.group(2), m.group(3)
            try:
                dtstart = datetime.strptime(f"{date_str} {start_str}", '%b %d, %Y %I:%M%p')
                dtend = datetime.strptime(f"{date_str} {end_str}", '%b %d, %Y %I:%M%p')
                return dtstart, dtend
            except ValueError:
                pass

        # Pattern: date only "Mon DD, YYYY at H:MMam" (no end time)
        m = re.match(r'(\w+ \d+, \d{4})\s+at\s+(\d+:\d+\s*[ap]m)', text, re.IGNORECASE)
        if m:
            try:
                dtstart = datetime.strptime(f"{m.group(1)} {m.group(2)}", '%b %d, %Y %I:%M%p')
                return dtstart, None
            except ValueError:
                pass

        # Pattern: date only "Mon DD, YYYY"
        m = re.match(r'(\w+ \d+, \d{4})', text)
        if m:
            try:
                dtstart = datetime.strptime(m.group(1), '%b %d, %Y')
                return dtstart, None
            except ValueError:
                pass

        return None, None


if __name__ == '__main__':
    CreativeSonomaScraper.main()
