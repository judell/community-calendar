#!/usr/bin/env python3
"""
Scraper for Raleigh Little Theatre shows.
https://raleighlittletheatre.org/shows-and-events/

RLT lists current/upcoming shows on their main page. Each show page has a
date range (e.g., "March 27 - April 19, 2026") and show time rules
(e.g., "Fridays and Saturdays at 8:00pm", "Sundays at 3:00pm"). This
scraper generates individual performance events from those rules.

Usage:
    python scrapers/raleigh_little_theatre.py --output cities/raleighdurham/raleigh_little_theatre.ics
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

# Day name to weekday number (Monday=0)
DAY_MAP = {
    'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
    'friday': 4, 'saturday': 5, 'sunday': 6,
    'mondays': 0, 'tuesdays': 1, 'wednesdays': 2, 'thursdays': 3,
    'fridays': 4, 'saturdays': 5, 'sundays': 6,
}

MONTH_MAP = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12,
}


class RaleighLittleTheatreScraper(BaseScraper):
    """Scraper for Raleigh Little Theatre via show page parsing."""

    name = "Raleigh Little Theatre"
    domain = "raleighlittletheatre.org"
    timezone = "America/New_York"

    SHOWS_URL = "https://raleighlittletheatre.org/shows-and-events/"
    VENUE_ADDRESS = "Raleigh Little Theatre, 301 Pogue St, Raleigh, NC 27607"

    # "March 27 - April 19, 2026" or "May 2 - 10, 2026" or "February 6 - 22, 2026"
    DATE_RANGE_RE = re.compile(
        r'(\w+)\s+(\d{1,2})\s*[-–]\s*(?:(\w+)\s+)?(\d{1,2}),?\s*(\d{4})'
    )

    # "Fridays and Saturdays (plus Thursday, April 2) at 8:00pm"
    # "Sundays at 3:00pm"
    # "Saturdays and Sundays at 1:00pm & 3:00pm"
    # "Wednesdays, Thursdays, and Fridays at 10:00am & 11:15am"
    TIME_RULE_RE = re.compile(
        r'((?:(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)s?'
        r'(?:\s*,\s*|\s+and\s+|\s*\*+\s*)?)+'
        r')'
        r'.*?at\s+'
        r'([\d:]+\s*[ap]m(?:\s*[&,]\s*[\d:]+\s*[ap]m)*)',
        re.IGNORECASE
    )

    # "plus Thursday, April 2" or "plus Thursday, Feb. 12"
    PLUS_DAY_RE = re.compile(
        r'plus\s+\w+day,?\s+(\w+\.?)\s+(\d{1,2})',
        re.IGNORECASE
    )

    # "**No performances on Saturday, March 14"
    NO_PERF_RE = re.compile(
        r'No performances?\s+on\s+\w+day,?\s+(\w+\.?)\s+(\d{1,2})',
        re.IGNORECASE
    )

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from Raleigh Little Theatre."""
        self.logger.info(f"Fetching {self.SHOWS_URL}")
        response = requests.get(
            self.SHOWS_URL,
            headers=DEFAULT_HEADERS,
            timeout=30
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Get current shows (before "Past Shows" heading)
        show_urls = self._get_current_shows(soup)
        self.logger.info(f"Found {len(show_urls)} current/upcoming shows")

        events = []
        for title, url in show_urls:
            show_events = self._scrape_show(title, url)
            events.extend(show_events)

        return events

    def _get_current_shows(self, soup) -> list[tuple[str, str]]:
        """Get current/upcoming show titles and URLs."""
        shows = []
        all_h3 = soup.find_all('h3')

        # Find "Past Shows" divider
        past_idx = len(all_h3)
        for i, h3 in enumerate(all_h3):
            if 'Past Shows' in h3.get_text():
                past_idx = i
                break

        for h3 in all_h3[:past_idx]:
            title = h3.get_text().strip()
            # Find link
            a = h3.find('a') or h3.find_parent('a')
            href = a.get('href', '') if a else ''
            if not href:
                parent = h3.parent
                if parent:
                    a = parent.find('a', href=True)
                    if a:
                        href = a.get('href', '')

            # Only include /shows/ pages (skip /events/ which are one-offs)
            if href and '/shows/' in href:
                shows.append((title, href))

        return shows

    def _scrape_show(self, title: str, url: str) -> list[dict[str, Any]]:
        """Scrape a single show page for performance dates."""
        self.logger.info(f"Scraping show: {title} ({url})")
        try:
            response = requests.get(url, headers=DEFAULT_HEADERS, timeout=30)
            response.raise_for_status()
        except Exception as e:
            self.logger.warning(f"Failed to fetch {url}: {e}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')

        # Get date range from meta
        meta = soup.find('p', class_='meta')
        if not meta:
            self.logger.warning(f"No meta date found for {title}")
            return []

        meta_text = ' '.join(meta.get_text().split())
        date_range = self._parse_date_range(meta_text)
        if not date_range:
            self.logger.warning(f"Could not parse date range: {meta_text}")
            return []

        start_date, end_date, year = date_range

        # Get show time rules from list items
        rules = []
        excluded_dates = set()
        extra_dates = []

        # Find list items near the "Show Times:" section
        show_times_found = False
        for el in soup.find_all(['p', 'li']):
            text = el.get_text().strip()
            if 'Show Time' in text:
                show_times_found = True
                continue
            if not show_times_found:
                continue
            # Stop when we hit accessibility info or other sections
            if any(kw in text.lower() for kw in ['wheelchair', 'assistive listening',
                                                   'audio description', 'sensory',
                                                   'cast list', 'click here']):
                continue

            # Check for exclusions
            no_match = self.NO_PERF_RE.search(text)
            if no_match:
                exc_date = self._parse_month_day(no_match.group(1), no_match.group(2), year)
                if exc_date:
                    excluded_dates.add(exc_date)
                continue

            # Check for time rules
            time_match = self.TIME_RULE_RE.search(text)
            if time_match:
                days_str = time_match.group(1)
                times_str = time_match.group(2)
                weekdays = self._parse_days(days_str)
                times = self._parse_times(times_str)
                if weekdays and times:
                    rules.append((weekdays, times))

                # Check for "plus" extra dates
                plus_match = self.PLUS_DAY_RE.search(text)
                if plus_match:
                    extra_d = self._parse_month_day(plus_match.group(1), plus_match.group(2), year)
                    if extra_d and times:
                        extra_dates.append((extra_d, times))

        if not rules:
            self.logger.warning(f"No time rules found for {title}")
            return []

        # Generate performance events
        events = []
        current = start_date
        while current <= end_date:
            if current not in excluded_dates:
                for weekdays, times in rules:
                    if current.weekday() in weekdays:
                        for t in times:
                            dt = current.replace(hour=t[0], minute=t[1])
                            events.append({
                                'title': title,
                                'dtstart': dt,
                                'dtend': dt + timedelta(hours=2),
                                'url': url,
                                'location': self.VENUE_ADDRESS,
                                'description': '',
                            })
            current += timedelta(days=1)

        # Add extra dates (e.g., "plus Thursday, April 2")
        for extra_d, times in extra_dates:
            if extra_d not in excluded_dates:
                for t in times:
                    dt = extra_d.replace(hour=t[0], minute=t[1])
                    events.append({
                        'title': title,
                        'dtstart': dt,
                        'dtend': dt + timedelta(hours=2),
                        'url': url,
                        'location': self.VENUE_ADDRESS,
                        'description': '',
                    })

        self.logger.info(f"  {title}: {len(events)} performances")
        return events

    def _parse_date_range(self, text: str):
        """Parse 'March 27 - April 19, 2026' into (start_date, end_date, year)."""
        m = self.DATE_RANGE_RE.search(text)
        if not m:
            return None

        start_month_str = m.group(1)
        start_day = int(m.group(2))
        end_month_str = m.group(3)  # May be None if same month
        end_day = int(m.group(4))
        year = int(m.group(5))

        start_month = MONTH_MAP.get(start_month_str.lower())
        if not start_month:
            return None

        if end_month_str:
            end_month = MONTH_MAP.get(end_month_str.lower())
            if not end_month:
                return None
        else:
            end_month = start_month

        try:
            start_date = datetime(year, start_month, start_day)
            end_date = datetime(year, end_month, end_day)
            return start_date, end_date, year
        except ValueError:
            return None

    def _parse_month_day(self, month_str: str, day_str: str, year: int):
        """Parse month name + day into a datetime date."""
        month_str = month_str.rstrip('.')
        month = MONTH_MAP.get(month_str.lower())
        if not month:
            return None
        try:
            return datetime(year, month, int(day_str))
        except ValueError:
            return None

    def _parse_days(self, text: str) -> list[int]:
        """Parse day names into weekday numbers."""
        weekdays = []
        # Clean up asterisks
        text = re.sub(r'\*+', '', text)
        for word in re.split(r'[,\s]+', text):
            word = word.strip().lower()
            if word in DAY_MAP:
                weekdays.append(DAY_MAP[word])
        return weekdays

    def _parse_times(self, text: str) -> list[tuple[int, int]]:
        """Parse time strings like '8:00pm' or '1:00pm & 3:00pm'."""
        times = []
        for m in re.finditer(r'(\d{1,2}):(\d{2})\s*(am|pm)', text, re.IGNORECASE):
            hour = int(m.group(1))
            minute = int(m.group(2))
            ampm = m.group(3).lower()
            if ampm == 'pm' and hour != 12:
                hour += 12
            elif ampm == 'am' and hour == 12:
                hour = 0
            times.append((hour, minute))
        return times


if __name__ == '__main__':
    RaleighLittleTheatreScraper.main()
