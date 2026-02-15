#!/usr/bin/env python3
"""
Scraper for University of Toronto events
https://www.utoronto.ca/events

Drupal site with HTML tables organized by department.
Each table has rows: title+link, date, optional department.
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import re
from datetime import datetime
from typing import Any, Optional
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from lib.base import BaseScraper


class UofTEventsScraper(BaseScraper):
    """Scraper for University of Toronto events page."""

    name = "University of Toronto"
    domain = "utoronto.ca"
    timezone = "America/Toronto"

    EVENTS_URL = "https://www.utoronto.ca/events"

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from the UofT events page."""
        self.logger.info(f"Fetching {self.EVENTS_URL}")

        resp = requests.get(self.EVENTS_URL, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; community-calendar/1.0)'
        }, timeout=30)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, 'html.parser')
        tables = soup.find_all('table')
        self.logger.info(f"Found {len(tables)} tables")

        events = []
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if not cells:
                    continue
                event = self._parse_row(cells)
                if event:
                    events.append(event)

        self.logger.info(f"Parsed {len(events)} events")
        return events

    def _parse_row(self, cells) -> Optional[dict[str, Any]]:
        """Parse a table row into an event dict."""
        try:
            # First cell: title + link
            link = cells[0].find('a')
            if not link:
                return None
            title = link.get_text(strip=True)
            url = link.get('href', '')

            # Second cell: date
            if len(cells) < 2:
                return None
            date_text = cells[1].get_text(strip=True)
            dtstart, dtend = self._parse_date(date_text)
            if not dtstart:
                return None

            # Third cell (optional): department
            department = ''
            if len(cells) >= 3:
                department = cells[2].get_text(strip=True)

            location = 'University of Toronto'
            if department:
                location = f"{department}, University of Toronto"

            return {
                'title': title,
                'dtstart': dtstart,
                'dtend': dtend,
                'url': url,
                'location': location,
                'description': f"Department: {department}" if department else '',
            }

        except Exception as e:
            self.logger.warning(f"Error parsing row: {e}")
            return None

    def _parse_date(self, text: str) -> tuple[Optional[datetime], Optional[datetime]]:
        """Parse date text into start and optional end datetimes.

        Formats:
          February 14, 2026
          Feb 21 2026
          February 13 to 15, 2026
          February 13 to February 15, 2026
          February 10 to March 10, 2026
          January 2 to March 3, 2026
          February 25, to August 1, 2026
        """
        tz = ZoneInfo(self.timezone)
        # Clean up stray commas before "to"
        text = re.sub(r',\s*to\s', ' to ', text)

        # Range: "Month D to Month D, YYYY" or "Month D to D, YYYY"
        m = re.match(
            r'(\w+)\s+(\d+)\s+to\s+(\w+)\s+(\d+),?\s+(\d{4})', text
        )
        if m:
            start_month, start_day, end_month, end_day, year = m.groups()
            dtstart = self._make_dt(start_month, start_day, year, tz)
            dtend = self._make_dt(end_month, end_day, year, tz)
            return dtstart, dtend

        # Range same month: "Month D to D, YYYY"
        m = re.match(r'(\w+)\s+(\d+)\s+to\s+(\d+),?\s+(\d{4})', text)
        if m:
            month, start_day, end_day, year = m.groups()
            dtstart = self._make_dt(month, start_day, year, tz)
            dtend = self._make_dt(month, end_day, year, tz)
            return dtstart, dtend

        # Single date: "Month D, YYYY" or "Month D YYYY"
        m = re.match(r'(\w+)\s+(\d+),?\s+(\d{4})', text)
        if m:
            month, day, year = m.groups()
            dtstart = self._make_dt(month, day, year, tz)
            return dtstart, None

        self.logger.warning(f"Unparseable date: {text}")
        return None, None

    def _make_dt(self, month: str, day: str, year: str, tz) -> Optional[datetime]:
        """Create a datetime from month name, day, year."""
        for fmt in ('%B %d %Y', '%b %d %Y'):
            try:
                dt = datetime.strptime(f"{month} {day} {year}", fmt)
                return dt.replace(tzinfo=tz)
            except ValueError:
                continue
        self.logger.warning(f"Cannot parse date parts: {month} {day} {year}")
        return None


if __name__ == '__main__':
    UofTEventsScraper.main()
