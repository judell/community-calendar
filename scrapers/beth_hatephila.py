#!/usr/bin/env python3
"""
Scraper for Congregation Beth HaTephila (43 N Liberty St, Asheville NC).

The site (bethhatephila.org) is Weebly-hosted and returns 406 to curl
and the requests library (TLS fingerprint mismatch). urllib.request with
a Chrome User-Agent succeeds. The calendar page server-renders an
"Upcoming 10 events" list as <ul class="upcomingEvents …">.

Usage:
    python scrapers/beth_hatephila.py --output cities/asheville/beth_hatephila.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import html as html_mod
import logging
import re
import ssl
from datetime import datetime, timezone
from typing import Any
from urllib.request import urlopen, Request

from lib.base import BaseScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CALENDAR_URL = 'https://www.bethhatephila.org/cbht-calendar.html'
DEFAULT_LOCATION = 'Congregation Beth HaTephila, 43 N Liberty St, Asheville, NC 28801'

# urllib works; curl and requests get 406 (Weebly TLS fingerprint check).
HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

# Abbreviated AM/PM variants used by Weebly widget (e.g. "6:00p", "10:00a")
_TIME_RE = re.compile(r'(\d{1,2}):(\d{2})([ap])', re.I)
_MONTH_ABBR = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
    'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12,
}
_MONTH_FULL = {
    'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
    'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12,
}


def _parse_time(time_str: str) -> tuple[int, int]:
    """Parse a time string like '6:00p' or '10:00a' → (hour24, minute)."""
    m = _TIME_RE.match(time_str.strip())
    if not m:
        return (0, 0)
    hour, minute, meridiem = int(m.group(1)), int(m.group(2)), m.group(3).lower()
    if meridiem == 'p' and hour != 12:
        hour += 12
    elif meridiem == 'a' and hour == 12:
        hour = 0
    return hour, minute


class BethHaTephilaScraper(BaseScraper):
    """Scraper for Congregation Beth HaTephila upcoming events."""

    name = 'Congregation Beth HaTephila'
    domain = 'bethhatephila.org'
    timezone = 'America/New_York'
    default_url = CALENDAR_URL

    def _fetch_html(self) -> str:
        ctx = ssl.create_default_context()
        req = Request(CALENDAR_URL, headers=HEADERS)
        with urlopen(req, context=ctx, timeout=20) as r:
            return r.read().decode('utf-8')

    def fetch_events(self) -> list[dict[str, Any]]:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(self.timezone)
        now = datetime.now(tz)

        self.logger.info(f'Fetching {CALENDAR_URL}')
        html = self._fetch_html()

        # The widget renders: <ul class="upcomingEvents event_count_10">
        ul_match = re.search(
            r'<ul class="upcomingEvents[^"]*">(.*?)</ul>', html, re.DOTALL
        )
        if not ul_match:
            self.logger.error('Could not find upcomingEvents list')
            return []

        section = ul_match.group(1)
        # Split into <li> blocks
        items = re.split(r'<li\b', section)

        events: list[dict[str, Any]] = []
        for raw in items:
            if not raw.strip():
                continue
            item = '<li' + raw

            # Month (long form, e.g. "August")
            month_m = re.search(r'date_box_long_month">([^<]+)<', item)
            # Day of month
            day_m = re.search(r'date_box_day_of_month">(\d+)<', item)
            # Year
            year_m = re.search(r'event_widget_date_box_year">(\d+)<', item)
            if not (month_m and day_m and year_m):
                continue

            month_name = month_m.group(1).strip()
            month_num = _MONTH_FULL.get(month_name)
            if month_num is None:
                # Try abbreviated
                for abbr, num in _MONTH_ABBR.items():
                    if month_name.startswith(abbr):
                        month_num = num
                        break
            if month_num is None:
                self.logger.warning(f'Unknown month: {month_name!r}')
                continue

            day = int(day_m.group(1))
            year = int(year_m.group(1))

            # Time (optional) — Weebly widget uses "6:00p" / "10:00a" format
            time_m = re.search(r'event_start_time">\s*([^<]+)', item)
            if time_m:
                hour, minute = _parse_time(time_m.group(1))
            else:
                hour, minute = 0, 0

            try:
                dtstart = datetime(year, month_num, day, hour, minute, tzinfo=tz)
            except ValueError as e:
                self.logger.warning(f'Bad date {year}-{month_num}-{day}: {e}')
                continue

            if dtstart < now:
                continue

            # Title — may be blank for private events; skip those
            title_m = re.search(r'class="event_widget_title"[^>]*>\s*([^<]+)', item)
            title = html_mod.unescape(title_m.group(1).strip()) if title_m else ''
            if not title:
                # Try the anchor text
                anchor_m = re.search(r'href="/event/[^"]+">([^<]+)<', item)
                if anchor_m:
                    title = html_mod.unescape(anchor_m.group(1).strip())
            if not title:
                self.logger.debug('Skipping event with no title')
                continue

            # URL
            url_m = re.search(r'href="(/event/[^"]+)"', item)
            url = f'https://www.bethhatephila.org{url_m.group(1)}' if url_m else CALENDAR_URL

            # Description
            desc_m = re.search(r'class="d event_widget_desc"[^>]*>\s*(.*?)\s*</span>', item, re.DOTALL)
            description = ''
            if desc_m:
                description = re.sub(r'<[^>]+>', ' ', desc_m.group(1)).strip()
                description = html_mod.unescape(description)

            events.append({
                'title': title,
                'dtstart': dtstart,
                'location': DEFAULT_LOCATION,
                'description': description,
                'url': url,
            })

        self.logger.info(f'Found {len(events)} future events')
        return events


def main():
    parser = argparse.ArgumentParser(description='Scrape Congregation Beth HaTephila events')
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = BethHaTephilaScraper()
    scraper.run(args.output)


if __name__ == '__main__':
    main()
