#!/usr/bin/env python3
"""
Scraper for Carolina Theatre (Durham) events.
https://carolinatheatre.org/events/

The Carolina Theatre uses a custom WordPress theme with an AJAX event filter.
Events are loaded via wp-admin/admin-ajax.php?action=event_filter&events=all&paged=1
and returned as HTML fragments with structured CSS classes.

Usage:
    python scrapers/carolina_theatre.py --output cities/raleighdurham/carolina_theatre.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import re
import subprocess
from datetime import datetime, timedelta
from typing import Any, Optional

from bs4 import BeautifulSoup

from lib.base import BaseScraper
from lib.utils import MONTH_MAP


class CarolinaTheatreScraper(BaseScraper):
    """Scraper for Carolina Theatre Durham events via AJAX endpoint."""

    name = "Carolina Theatre"
    domain = "carolinatheatre.org"
    timezone = "America/New_York"

    AJAX_URL = "https://carolinatheatre.org/wp-admin/admin-ajax.php"
    VENUE_ADDRESS = "Carolina Theatre, 309 W Morgan St, Durham, NC 27701"
    MAX_PAGES = 3

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from AJAX endpoint."""
        all_events = []

        for page in range(1, self.MAX_PAGES + 1):
            url = f"{self.AJAX_URL}?action=event_filter&events=all&paged={page}"
            self.logger.info(f"Fetching page {page}: {url}")
            result = subprocess.run(
                ['curl', '-sL', '-A', 'Mozilla/5.0', url],
                capture_output=True, text=True, timeout=30
            )
            html = result.stdout

            if not html.strip():
                break

            events = self._parse_event_cards(html)
            if not events:
                break

            all_events.extend(events)
            self.logger.info(f"  Got {len(events)} events (total: {len(all_events)})")

        return all_events

    def _parse_event_cards(self, html: str) -> list[dict[str, Any]]:
        """Parse event cards from AJAX HTML response."""
        soup = BeautifulSoup(html, 'html.parser')
        cards = soup.select('.eventCard')
        events = []

        for card in cards:
            event = self._parse_card(card)
            if event:
                events.append(event)

        return events

    def _parse_card(self, card) -> Optional[dict[str, Any]]:
        """Parse a single event card."""
        # Title
        title_el = card.select_one('.card__title')
        if not title_el:
            return None
        title = title_el.get_text(strip=True)

        # Date: .day and .month elements
        day_el = card.select_one('.day')
        month_el = card.select_one('.month')
        if not day_el or not month_el:
            return None

        day = int(day_el.get_text(strip=True))
        month_str = month_el.get_text(strip=True).lower()
        month = MONTH_MAP.get(month_str)
        if not month:
            return None

        # Time and hall from .card__info
        info_el = card.select_one('.card__info')
        time_str = ''
        hall = ''
        if info_el:
            info_text = info_el.get_text(strip=True)
            # Format: "8:00pmFletcher Hall" or "2:00pm, 6:00pmFletcher Hall"
            time_match = re.match(r'([\d:,\s]+(?:am|pm)(?:,\s*[\d:]+(?:am|pm))?)', info_text, re.IGNORECASE)
            if time_match:
                time_str = time_match.group(1).strip()
                hall = info_text[time_match.end():].strip()

        # Category
        cat_el = card.select_one('.event__categories')
        category = cat_el.get_text(strip=True) if cat_el else ''

        # Link
        link_el = card.select_one('a[href]')
        url = link_el.get('href', '') if link_el else ''

        # Parse datetime
        dtstart = self._parse_datetime(day, month, time_str)
        if not dtstart:
            return None

        dtend = dtstart + timedelta(hours=2)

        # Location
        location = f"{hall}, {self.VENUE_ADDRESS}" if hall else self.VENUE_ADDRESS

        # Description
        desc_parts = []
        if category:
            desc_parts.append(f"Category: {category}")
        if hall:
            desc_parts.append(f"Venue: {hall}")
        description = '\n'.join(desc_parts)

        return {
            'title': title,
            'dtstart': dtstart,
            'dtend': dtend,
            'url': url,
            'location': location,
            'description': description,
        }

    def _parse_datetime(self, day: int, month: int, time_str: str) -> Optional[datetime]:
        """Parse date components and time string into datetime."""
        now = datetime.now()
        year = now.year

        # If month is before current month, assume next year
        if month < now.month or (month == now.month and day < now.day - 14):
            year += 1

        # Parse time - take first time if multiple (e.g., "2:00pm, 6:00pm")
        hour, minute = 20, 0  # default 8pm
        if time_str:
            first_time = time_str.split(',')[0].strip()
            time_match = re.match(r'(\d{1,2}):(\d{2})\s*(am|pm)', first_time, re.IGNORECASE)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
                ampm = time_match.group(3).lower()
                if ampm == 'pm' and hour != 12:
                    hour += 12
                elif ampm == 'am' and hour == 12:
                    hour = 0

        try:
            return datetime(year, month, day, hour, minute)
        except ValueError:
            return None


if __name__ == '__main__':
    CarolinaTheatreScraper.main()
