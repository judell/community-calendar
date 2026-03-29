#!/usr/bin/env python3
"""Scraper for FAR Center for Contemporary Arts events (Craft CMS)."""

import re
import sys
from datetime import datetime, timedelta
from typing import Any, Optional
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from lib.base import BaseScraper


class FARCenterScraper(BaseScraper):
    """Scraper for FAR Center for Contemporary Arts in Bloomington."""

    name = "FAR Center for Contemporary Arts"
    domain = "thefar.org"
    events_url = "https://www.thefar.org/events/list"
    timezone = "America/Indiana/Indianapolis"

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }

    # Day-of-week names to strip from date strings
    DAYS = r'(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s*'

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from the FAR Center events list."""
        self.logger.info(f"Fetching {self.events_url}")
        response = requests.get(self.events_url, headers=self.HEADERS, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        tz = ZoneInfo(self.timezone)
        events = []

        main = soup.select_one('.entry-main')
        if not main:
            return events

        for card in main.select('div.mb-8'):
            parsed = self._parse_card(card, tz)
            if parsed:
                events.append(parsed)

        self.logger.info(f"Found {len(events)} events")
        return events

    def _parse_card(self, card, tz: ZoneInfo) -> Optional[dict[str, Any]]:
        """Parse a single event card."""
        title_el = card.select_one('h3 a')
        if not title_el:
            return None

        title = title_el.get_text(strip=True)
        url = title_el.get('href', '')
        if url and not url.startswith('http'):
            url = f"https://www.thefar.org{url}"

        # Find date/time in the second p.text-sm.mb-1
        paragraphs = card.select('p.text-sm.mb-1')
        description = ''
        dtstart = None
        dtend = None

        for p in paragraphs:
            text = p.get_text(strip=True)
            # Check if this paragraph contains a date pattern
            if not dtstart and re.search(r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d', text):
                start, end = self._parse_datetime(text, tz)
                if start:
                    dtstart, dtend = start, end
            elif not dtstart:
                description = text

        if not dtstart:
            return None

        if not dtend:
            dtend = dtstart + timedelta(hours=2)

        slug = re.sub(r'[^a-z0-9]+', '-', title.lower())[:40]
        uid = f"far-{dtstart.strftime('%Y%m%d')}-{slug}@thefar.org"

        return {
            'title': title,
            'dtstart': dtstart,
            'dtend': dtend,
            'url': url,
            'location': 'FAR Center for Contemporary Arts, 505 W 4th St, Bloomington, IN',
            'description': description,
            'uid': uid,
        }

    def _parse_datetime(self, text: str, tz: ZoneInfo):
        """Parse date/time from strings like 'Friday, April 3 | 5:00pm - 8:00pm'."""
        # Strip day-of-week
        text = re.sub(self.DAYS, '', text, flags=re.IGNORECASE)

        # Match: "April 3 | 5:00pm - 8:00pm" or "April 9 2:30pm - April 10 9:30pm"
        # Simple case: single date with time range
        m = re.match(
            r'(\w+ \d{1,2})\s*\|\s*(\d{1,2}:\d{2}\s*[ap]m)\s*[-–]\s*(\d{1,2}:\d{2}\s*[ap]m)',
            text, re.IGNORECASE
        )
        if m:
            year = datetime.now().year
            dtstart = self._make_dt(m.group(1), m.group(2), year, tz)
            dtend = self._make_dt(m.group(1), m.group(3), year, tz)
            if dtstart and dtend and dtend < dtstart:
                dtend += timedelta(days=1)
            return dtstart, dtend

        # Multi-day: "April 9 2:30pm - April 10 9:30pm"
        m = re.match(
            r'(\w+ \d{1,2})\s+(\d{1,2}:\d{2}\s*[ap]m)\s*[-–]\s*(\w+ \d{1,2})\s+(\d{1,2}:\d{2}\s*[ap]m)',
            text, re.IGNORECASE
        )
        if m:
            year = datetime.now().year
            dtstart = self._make_dt(m.group(1), m.group(2), year, tz)
            dtend = self._make_dt(m.group(3), m.group(4), year, tz)
            return dtstart, dtend

        # Date only, no time: "April 3"
        m = re.match(r'(\w+ \d{1,2})', text)
        if m:
            year = datetime.now().year
            dtstart = self._make_dt(m.group(1), '12:00 pm', year, tz)
            return dtstart, None

        return None, None

    @staticmethod
    def _make_dt(date_str: str, time_str: str, year: int, tz: ZoneInfo) -> Optional[datetime]:
        """Combine 'April 3' + '5:00pm' into a datetime."""
        try:
            dt = datetime.strptime(f"{date_str} {year}", '%B %d %Y')
        except ValueError:
            return None

        time_str = time_str.strip().lower()
        m = re.match(r'(\d{1,2}):(\d{2})\s*(am|pm)', time_str)
        if not m:
            return None

        hour = int(m.group(1))
        minute = int(m.group(2))
        if m.group(3) == 'pm' and hour != 12:
            hour += 12
        elif m.group(3) == 'am' and hour == 12:
            hour = 0

        return datetime(dt.year, dt.month, dt.day, hour, minute, tzinfo=tz)


if __name__ == '__main__':
    FARCenterScraper.main()
