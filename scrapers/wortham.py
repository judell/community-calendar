#!/usr/bin/env python3
"""
Scraper for Wortham Center for the Performing Arts (18 Biltmore Ave, Asheville NC).

The site (worthamarts.org) runs WordPress + Toolset Blocks custom CPT.
There is no Tribe/MEC plugin, no usable RSS dates, and JSON-LD is
WebPage-type without startDate — so we scrape HTML directly.

Strategy:
  1. Walk paginated listing at /events/, /events/page/2/, /events/page/3/, …
     until an empty page is found.
  2. From the listing, extract event URLs and their date text (rendered in
     a <div class="tb-fields-and-text"> block below each <h3> link).
     Date text examples:
       "Saturday August 15, 2026"
       "August 6, 2026 — August 8, 2026"   (multi-day; use start date)
       "Friday July 24, 2026"
  3. Fetch each individual event page to extract the h4 date/time block:
       "Sat, Aug 15, 2026 • 7:30 pm"
       "August 6–8, 2026 • 7:30 pm"
       "Fri & Sat, Sep 18 & 19 • 7:30 pm"
     Fall back to listing-page date + 7:30 pm default when the h4 is absent
     or the show has already been filtered.

Usage:
    python scrapers/wortham.py --output cities/asheville/wortham.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import html as html_mod
import logging
import re
import ssl
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.request import urlopen, Request

from lib.base import BaseScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

LISTING_URL = 'https://www.worthamarts.org/events/'
DEFAULT_LOCATION = 'Wortham Center for the Performing Arts, 18 Biltmore Ave, Asheville, NC 28801'
DEFAULT_SHOW_HOUR = 19   # 7 pm
DEFAULT_SHOW_MINUTE = 30

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

_MONTHS = {
    'Jan': 1, 'January': 1, 'Feb': 2, 'February': 2,
    'Mar': 3, 'March': 3, 'Apr': 4, 'April': 4,
    'May': 5, 'Jun': 6, 'June': 6,
    'Jul': 7, 'July': 7, 'Aug': 8, 'August': 8,
    'Sep': 9, 'Sept': 9, 'September': 9, 'Oct': 10, 'October': 10,
    'Nov': 11, 'November': 11, 'Dec': 12, 'December': 12,
}
# Match "July 24, 2026" or "August 15, 2026"
_DATE_FULL = re.compile(
    r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})(?:,\s*(\d{4}))?',
    re.I
)
# Match "7:30 pm" or "1:30 pm"
_TIME_RE = re.compile(r'(\d{1,2}):(\d{2})\s*(am|pm)', re.I)


def _month_num(name: str) -> Optional[int]:
    for key, val in _MONTHS.items():
        if name.lower().startswith(key.lower()):
            return val
    return None


def _parse_listing_date(text: str) -> Optional[tuple[int, int, int]]:
    """Parse listing-page date text → (year, month, day) for the start date."""
    text = html_mod.unescape(text).strip()
    # For ranges like "August 6, 2026 — August 8, 2026", take first date
    m = _DATE_FULL.search(text)
    if not m:
        return None
    month = _month_num(m.group(1))
    if month is None:
        return None
    day = int(m.group(2))
    year = int(m.group(3)) if m.group(3) else datetime.now().year
    return year, month, day


def _parse_event_page_time(h4_text: str) -> Optional[tuple[int, int]]:
    """Extract hour/minute from individual event page h4, e.g. '7:30 pm' → (19, 30)."""
    m = _TIME_RE.search(h4_text)
    if not m:
        return None
    hour, minute = int(m.group(1)), int(m.group(2))
    meridiem = m.group(3).lower()
    if meridiem == 'pm' and hour != 12:
        hour += 12
    elif meridiem == 'am' and hour == 12:
        hour = 0
    return hour, minute


def _fetch(url: str) -> Optional[str]:
    ctx = ssl.create_default_context()
    req = Request(url, headers=HEADERS)
    try:
        with urlopen(req, context=ctx, timeout=20) as r:
            return r.read().decode('utf-8')
    except Exception as e:
        logger.warning(f'Failed to fetch {url}: {e}')
        return None


def _parse_listing_page(html: str) -> list[tuple[str, str, str]]:
    """Return list of (url, title, date_text) from a listing page."""
    pattern = (
        r'<h3[^>]+tb-heading[^>]*>'
        r'<a href="(https://www\.worthamarts\.org/events/[^"]+)">([^<]+)</a></h3>'
        r'.*?'
        r'<div class="tb-fields-and-text[^"]*"[^>]*>(.*?)</div>'
    )
    matches = re.findall(pattern, html, re.DOTALL)
    results = []
    for url, title, date_div in matches:
        title = html_mod.unescape(title.strip())
        date_text = re.sub(r'<[^>]+>', ' ', date_div)
        date_text = re.sub(r'\s+', ' ', date_text).strip()
        results.append((url, title, date_text))
    return results


def _enrich_with_event_page(url: str, fallback_date: tuple[int, int, int]) -> Optional[dict[str, Any]]:
    """Fetch individual event page and extract time; returns event dict or None."""
    from zoneinfo import ZoneInfo
    tz = ZoneInfo('America/New_York')
    now = datetime.now(tz)

    html = _fetch(url)
    if not html:
        return None

    # Look for the h4 field with date/time
    h4s = re.findall(r'<h4[^>]*>(.*?)</h4>', html, re.DOTALL)
    hour, minute = DEFAULT_SHOW_HOUR, DEFAULT_SHOW_MINUTE
    for h in h4s:
        clean = html_mod.unescape(re.sub(r'<[^>]+>', '', h)).strip()
        time_result = _parse_event_page_time(clean)
        if time_result:
            hour, minute = time_result
            break

    year, month, day = fallback_date
    try:
        dtstart = datetime(year, month, day, hour, minute, tzinfo=tz)
    except ValueError:
        return None

    if dtstart < now:
        return None

    return {'hour': hour, 'minute': minute, 'dtstart': dtstart}


class WorthamScraper(BaseScraper):
    """Scraper for Wortham Center for the Performing Arts."""

    name = 'Wortham Center for the Performing Arts'
    domain = 'worthamarts.org'
    timezone = 'America/New_York'
    default_url = LISTING_URL

    def _collect_listing_events(self) -> list[tuple[str, str, tuple[int, int, int]]]:
        """Walk all listing pages and return (url, title, (year, month, day)) tuples."""
        collected = []
        page_num = 1
        while True:
            url = LISTING_URL if page_num == 1 else f'{LISTING_URL}page/{page_num}/'
            self.logger.info(f'Fetching listing page {page_num}: {url}')
            html = _fetch(url)
            if not html:
                break

            page_events = _parse_listing_page(html)
            if not page_events:
                self.logger.info(f'No events on page {page_num}, stopping pagination')
                break

            for event_url, title, date_text in page_events:
                parsed = _parse_listing_date(date_text)
                if parsed is None:
                    self.logger.warning(f'Could not parse date {date_text!r} for {title!r}')
                    continue
                collected.append((event_url, title, parsed))

            # Check if there is a "next page" link; if this page had fewer events
            # than a full page that's also a stop signal, but safest: try next page
            # and break when empty (done above).
            if len(page_events) < 16:
                # Fewer than a full grid — this is the last page
                break
            page_num += 1
            time.sleep(0.3)

        return collected

    def fetch_events(self) -> list[dict[str, Any]]:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(self.timezone)
        now = datetime.now(tz)

        listing = self._collect_listing_events()
        self.logger.info(f'Found {len(listing)} events on listing pages')

        # Pre-filter obviously past events before fetching detail pages
        future_listing = []
        for url, title, (year, month, day) in listing:
            try:
                # Use midnight as lower bound; we'll get the real time from detail page
                cutoff = datetime(year, month, day, 23, 59, tzinfo=tz)
            except ValueError:
                continue
            if cutoff >= now:
                future_listing.append((url, title, (year, month, day)))

        self.logger.info(f'{len(future_listing)} events are potentially future')

        events: list[dict[str, Any]] = []

        def _fetch_one(args):
            url, title, date_tuple = args
            result = _enrich_with_event_page(url, date_tuple)
            if result is None:
                return None
            return {
                'title': title,
                'dtstart': result['dtstart'],
                'location': DEFAULT_LOCATION,
                'url': url,
                'description': '',
            }

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(_fetch_one, args): args for args in future_listing}
            for future in as_completed(futures):
                ev = future.result()
                if ev:
                    events.append(ev)
                time.sleep(0.1)

        events.sort(key=lambda e: e['dtstart'])
        self.logger.info(f'Found {len(events)} future events')
        return events


def main():
    parser = argparse.ArgumentParser(description='Scrape Wortham Center for the Performing Arts events')
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = WorthamScraper()
    scraper.run(args.output)


if __name__ == '__main__':
    main()
