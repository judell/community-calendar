#!/usr/bin/env python3
"""Scraper for Feed & Seed (Fletcher NC) events using MF Gig Calendar plugin.

The music page at https://feedandseednc.com/music/ uses the MF Gig Calendar
WordPress plugin, rendering events as <li class="event"> elements inside
<ul class="mfgigcal mfgigcal_list">. Each event has structured date divs
(.weekday, .day, .month, .year) and an artist name in the first <strong>
inside the .location block.
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Optional
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from lib.base import BaseScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

MONTHS = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
}

MUSIC_URL = 'https://feedandseednc.com/music/'
DEFAULT_LOCATION = 'Feed & Seed, 3715 Hendersonville Rd, Fletcher, NC 28732'
DOMAIN = 'feedandseednc.com'


def _parse_time(time_str: str) -> tuple[int, int]:
    """Parse a time string like '7-9PM', '7:00PM', '7 p.m.' into (hour, minute)."""
    time_str = time_str.strip().lower().replace('.', '').replace(' ', '')
    # Match leading hour of a range like "7-9pm" → take the start
    m = re.match(r'(\d{1,2})(?::(\d{2}))?(?:-\d{1,2}(?::\d{2})?)?\s*(am|pm)', time_str)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2) or 0)
        period = m.group(3)
        if period == 'pm' and hour != 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0
        return hour, minute
    return 19, 0  # default 7pm


class FeedAndSeedScraper(BaseScraper):
    """Scraper for Feed & Seed live music events."""

    name = "Feed & Seed"
    domain = DOMAIN
    timezone = "America/New_York"
    default_location = DEFAULT_LOCATION

    def fetch_events(self) -> list[dict[str, Any]]:
        self.logger.info(f"Fetching {MUSIC_URL}")
        response = requests.get(MUSIC_URL, headers=HEADERS, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        tz = ZoneInfo(self.timezone)
        now = datetime.now(tz)
        events = []

        for li in soup.select('li.event'):
            parsed = self._parse_event(li, now, tz)
            if parsed:
                events.append(parsed)

        self.logger.info(f"Found {len(events)} future events")
        return events

    def _parse_event(self, li, now: datetime, tz: ZoneInfo) -> Optional[dict[str, Any]]:
        """Parse a single MF Gig Calendar <li class="event"> element."""
        # Date from structured divs
        weekday_el = li.select_one('.weekday')
        day_el = li.select_one('.day')
        month_el = li.select_one('.month')
        year_el = li.select_one('.year')

        if not (day_el and month_el and year_el):
            return None

        day_str = day_el.get_text(strip=True)
        month_str = month_el.get_text(strip=True).lower()[:3]
        year_str = year_el.get_text(strip=True)

        try:
            day = int(day_str)
            month = MONTHS.get(month_str)
            year = int(year_str)
            if not month:
                return None
        except (ValueError, TypeError):
            return None

        # Time from .time span
        time_el = li.select_one('.time')
        hour, minute = 19, 0  # default 7pm
        if time_el:
            time_text = time_el.get_text(strip=True)
            if time_text:
                hour, minute = _parse_time(time_text)

        try:
            dtstart = datetime(year, month, day, hour, minute, tzinfo=tz)
        except ValueError:
            return None

        # Skip past events
        if dtstart < now:
            return None

        dtend = dtstart + timedelta(hours=2)

        # Artist name: first <strong> in .location block that isn't a date/venue label
        location_el = li.select_one('.location')
        artist = ''
        if location_el:
            strongs = location_el.select('strong')
            for s in strongs:
                text = s.get_text(strip=True)
                # Skip strings that look like date stamps or venue labels
                if re.search(r'\d{2}/\d{2}/', text) or text in ('Venue', 'Cost'):
                    continue
                if text:
                    artist = text
                    break

        # Title: use artist if available, else fall back to h3
        title_el = li.select_one('h3')
        title_base = title_el.get_text(strip=True) if title_el else 'Live Music'

        if artist:
            title = artist
        else:
            title = title_base

        # Description: include artist + time range info if both present
        desc_parts = []
        if artist and title_base and artist != title_base:
            desc_parts.append(title_base)
        if time_el:
            desc_parts.append(f"Show time: {time_el.get_text(strip=True)}")
        description = ' | '.join(desc_parts)

        slug = re.sub(r'[^a-z0-9]+', '-', title.lower())[:40]
        uid = f"feedandseed-{dtstart.strftime('%Y%m%d')}-{slug}@{self.domain}"

        return {
            'title': title,
            'dtstart': dtstart,
            'dtend': dtend,
            'url': MUSIC_URL,
            'location': DEFAULT_LOCATION,
            'description': description,
            'uid': uid,
        }


def main():
    parser = argparse.ArgumentParser(description="Scrape Feed & Seed (Fletcher NC) live music events")
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = FeedAndSeedScraper()
    scraper.run(args.output)


if __name__ == '__main__':
    main()
