#!/usr/bin/env python3
"""Scraper for Monroe County History Center events (EventON via WP REST API).

Parses dates from the listing API content field instead of fetching
individual detail pages — reduces ~250 HTTP requests to ~5.
"""

import re
from datetime import datetime, timedelta
from typing import Any, Optional
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from lib.base import BaseScraper

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; CommunityCalendar/1.0)',
    'Accept': 'application/json',
}

MONTHS = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12,
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
    'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9,
    'oct': 10, 'nov': 11, 'dec': 12,
}

# Pattern for structured eelisttime: "Thursday, July 16: 5:30pm – 6:30pm"
STRUCTURED_DATE = re.compile(
    r'(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday),?\s+'
    r'(\w+)\s+(\d{1,2}):\s*'
    r'(\d{1,2}:\d{2}\s*[ap]m)\s*'
    r'(?:–|-)\s*'
    r'(\d{1,2}:\d{2}\s*[ap]m)',
    re.IGNORECASE
)

# Pattern for inline prose dates: "on April 25th" or "on March 28th"
PROSE_DATE = re.compile(
    r'(?:on|from)\s+(\w+)\s+(\d{1,2})(?:st|nd|rd|th)?\b',
    re.IGNORECASE
)

# Pattern for "Month Day, Time" in plain text
PLAIN_DATE = re.compile(
    r'(\w+)\s+(\d{1,2})(?:st|nd|rd|th)?\s*(?:,\s*\d{4})?\s*'
    r'(?:from\s+)?(\d{1,2}(?::\d{2})?\s*[ap]m)',
    re.IGNORECASE
)

# Inline EventON format from old scraper: "28mar1:00 pm2:30 pm"
EVENTON_INLINE = re.compile(
    r'(\d{1,2})(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)'
    r'(\d{1,2}:\d{2}\s*[ap]m)'
    r'(\d{1,2}:\d{2}\s*[ap]m)',
    re.IGNORECASE
)


class HistoryCenterScraper(BaseScraper):
    """Scraper for Monroe County History Center."""

    name = "Monroe County History Center"
    domain = "monroehistory.org"
    api_url = "https://monroehistory.org/wp-json/wp/v2/ajde_events"
    timezone = "America/Indiana/Indianapolis"

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events via WP REST API, parsing dates from content field."""
        self.logger.info(f"Fetching event list from {self.api_url}")
        tz = ZoneInfo(self.timezone)
        events = []
        seen_slugs = set()

        page = 1
        while True:
            response = requests.get(f"{self.api_url}?per_page=50&page={page}",
                                    headers=HEADERS, timeout=30)
            if response.status_code != 200:
                break

            items = response.json()
            if not items:
                break

            for item in items:
                slug = item.get('slug', '')
                if slug in seen_slugs:
                    continue
                seen_slugs.add(slug)

                title = item.get('title', {}).get('rendered', '')
                url = item.get('link', '')
                if not title or not url:
                    continue

                content = item.get('content', {}).get('rendered', '')
                parsed = self._parse_from_content(content, title, url, tz)
                if parsed:
                    events.append(parsed)

            page += 1
            if page > 5:
                break

        self.logger.info(f"Found {len(events)} events")
        return events

    def _parse_from_content(self, content: str, title: str, url: str,
                            tz: ZoneInfo) -> Optional[dict[str, Any]]:
        """Parse event date/time/location from API content field."""
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text(' ', strip=True)

        dtstart = None
        dtend = None
        now = datetime.now(tz)

        # Try structured eelisttime div first
        time_div = soup.select_one('.eelisttime')
        if time_div:
            time_text = time_div.get_text(strip=True)
            m = STRUCTURED_DATE.search(time_text)
            if m:
                month = MONTHS.get(m.group(1).lower())
                day = int(m.group(2))
                if month:
                    year = self._infer_year(month, day, now)
                    dtstart = self._make_dt(year, month, day, m.group(3), tz)
                    dtend = self._make_dt(year, month, day, m.group(4), tz)

        # Try EventON inline format: "28mar1:00 pm2:30 pm"
        if not dtstart:
            m = EVENTON_INLINE.search(text)
            if m:
                day = int(m.group(1))
                month = MONTHS.get(m.group(2).lower())
                if month:
                    year = self._infer_year(month, day, now)
                    dtstart = self._make_dt(year, month, day, m.group(3), tz)
                    dtend = self._make_dt(year, month, day, m.group(4), tz)

        # Try plain date with time: "January 31st from 10 am"
        if not dtstart:
            m = PLAIN_DATE.search(text)
            if m:
                month = MONTHS.get(m.group(1).lower())
                day = int(m.group(2))
                if month:
                    year = self._infer_year(month, day, now)
                    dtstart = self._make_dt(year, month, day, m.group(3), tz)

        # Try prose date without time: "on April 25th"
        if not dtstart:
            m = PROSE_DATE.search(text)
            if m:
                month = MONTHS.get(m.group(1).lower())
                day = int(m.group(2))
                if month:
                    year = self._infer_year(month, day, now)
                    dtstart = datetime(year, month, day, 17, 0, tzinfo=tz)

        if not dtstart:
            return None

        # Location
        loc_div = soup.select_one('.eelocation')
        location = loc_div.get_text(strip=True) if loc_div else 'Monroe County History Center, 202 E 6th St, Bloomington, IN'

        # Description
        desc_div = soup.select_one('.eelistdesc')
        desc = desc_div.get_text(strip=True)[:300] if desc_div else ''
        if not desc:
            # Fall back to first substantial paragraph
            for p in soup.select('p'):
                pt = p.get_text(strip=True)
                if len(pt) > 30:
                    desc = pt[:300]
                    break

        slug = re.sub(r'[^a-z0-9]+', '-', title.lower())[:40]
        uid = f"mchc-{dtstart.strftime('%Y%m%d')}-{slug}@monroehistory.org"

        return {
            'title': title,
            'dtstart': dtstart,
            'dtend': dtend or dtstart + timedelta(hours=2),
            'url': url,
            'location': location,
            'description': desc,
            'uid': uid,
        }

    @staticmethod
    def _infer_year(month: int, day: int, now: datetime) -> int:
        if month < now.month or (month == now.month and day < now.day):
            return now.year + 1
        return now.year

    @staticmethod
    def _make_dt(year, month, day, time_str, tz):
        time_str = time_str.strip().lower()
        # Handle "10 am" (no colon) and "1:30pm"
        m = re.match(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)', time_str)
        if not m:
            return None
        hour = int(m.group(1))
        minute = int(m.group(2) or 0)
        if m.group(3) == 'pm' and hour != 12:
            hour += 12
        elif m.group(3) == 'am' and hour == 12:
            hour = 0
        return datetime(year, month, day, hour, minute, tzinfo=tz)


if __name__ == '__main__':
    HistoryCenterScraper.main()
