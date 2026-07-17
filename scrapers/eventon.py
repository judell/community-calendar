#!/usr/bin/env python3
"""Parameterized EventON scraper.

Targets WordPress sites using the EventON plugin (ajde_events CPT).
Fetches event pages individually to parse the structured time row:
  "August 11, 2026 10:00 am – 12:00 pm"

Usage:
    python scrapers/eventon.py \\
        --url https://whitehorseblackmountain.org \\
        --name "White Horse Black Mountain" \\
        --default-location "White Horse Black Mountain, 105C Montreat Rd, Black Mountain, NC 28711" \\
        --output cities/asheville/white_horse_black_mountain.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import html as html_mod
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Any, Optional
from urllib.parse import urlparse
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

API_HEADERS = {
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

# Matches "August 11, 2026 10:00 am – 12:00 pm" (with optional "Time" prefix)
TIME_PATTERN = re.compile(
    r'(\w+)\s+(\d{1,2}),\s+(\d{4})\s+'
    r'(\d{1,2}:\d{2}\s*[ap]m)\s*[–\-]+\s*(\d{1,2}:\d{2}\s*[ap]m)',
    re.IGNORECASE
)

# Fallback: EventON inline "11aug10:00 am12:00 pm"
EVENTON_INLINE = re.compile(
    r'(\d{1,2})(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)'
    r'(\d{1,2}:\d{2}\s*[ap]m)'
    r'(\d{1,2}:\d{2}\s*[ap]m)',
    re.IGNORECASE
)


def _parse_time(time_str: str) -> tuple[int, int]:
    """Parse '10:00 am' or '2:30 pm' into (hour, minute)."""
    time_str = time_str.strip().lower()
    m = re.match(r'(\d{1,2}):(\d{2})\s*(am|pm)', time_str)
    if not m:
        return 0, 0
    hour = int(m.group(1))
    minute = int(m.group(2))
    period = m.group(3)
    if period == 'pm' and hour != 12:
        hour += 12
    elif period == 'am' and hour == 12:
        hour = 0
    return hour, minute


class EventOnScraper(BaseScraper):
    """Scraper for WordPress sites using the EventON plugin."""

    def __init__(self, site_url: str, source_name: str,
                 tz: str = 'America/New_York', default_location: str = ''):
        self.site_url = site_url.rstrip('/')
        self.name = source_name
        self.domain = urlparse(site_url).netloc.removeprefix('www.')
        self.timezone = tz
        self.default_location = default_location
        super().__init__()

    def _api_url(self) -> str:
        return f"{self.site_url}/wp-json/wp/v2/ajde_events?per_page=100"

    def _fetch_event_items(self) -> list[dict]:
        """Fetch all ajde_events from WP REST API."""
        items = []
        page = 1
        while True:
            url = f"{self._api_url()}&page={page}"
            try:
                r = requests.get(url, headers=API_HEADERS, timeout=30)
                if r.status_code != 200:
                    break
                batch = r.json()
                if not batch:
                    break
                items.extend(batch)
                page += 1
                if page > 10:
                    break
            except Exception as e:
                self.logger.warning(f"API fetch error page {page}: {e}")
                break
        self.logger.info(f"Got {len(items)} items from REST API")
        return items

    def _fetch_event_page(self, url: str, title: str, tz: ZoneInfo, now: datetime) -> Optional[dict[str, Any]]:
        """Fetch an event detail page and parse the EventON time row."""
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            r.raise_for_status()
        except Exception as e:
            self.logger.debug(f"Could not fetch {url}: {e}")
            return None

        soup = BeautifulSoup(r.text, 'html.parser')
        dtstart = None
        dtend = None

        # Primary: parse the structured time row
        for el in soup.select('.evo_metarow_time .evcal_evdata_cell'):
            text = el.get_text(' ', strip=True)
            m = TIME_PATTERN.search(text)
            if m:
                month_name = m.group(1).lower()
                month = MONTHS.get(month_name)
                day = int(m.group(2))
                year = int(m.group(3))
                if month:
                    sh, sm = _parse_time(m.group(4))
                    eh, em = _parse_time(m.group(5))
                    dtstart = datetime(year, month, day, sh, sm, tzinfo=tz)
                    dtend = datetime(year, month, day, eh, em, tzinfo=tz)
                break

        # Fallback: EventON inline format "11aug10:00 am12:00 pm"
        if not dtstart:
            for el in soup.select('.evoet_dayblock, .evcal_cblock'):
                text = el.get_text(strip=True)
                m = EVENTON_INLINE.search(text)
                if m:
                    day = int(m.group(1))
                    month = MONTHS.get(m.group(2).lower())
                    if month:
                        # Infer year
                        year = now.year
                        if month < now.month or (month == now.month and day < now.day):
                            year += 1
                        sh, sm = _parse_time(m.group(3))
                        eh, em = _parse_time(m.group(4))
                        dtstart = datetime(year, month, day, sh, sm, tzinfo=tz)
                        dtend = datetime(year, month, day, eh, em, tzinfo=tz)
                    break

        if not dtstart:
            return None

        # Skip past events
        if dtstart < now:
            return None

        # Location from event details — prefer specific name+address elements
        location = self.default_location
        loc_cell = soup.select_one('.evo_metarow_time_location .evcal_evdata_cell')
        if loc_cell:
            name_el = loc_cell.select_one('.evo_location_name, p.evo_location_name')
            addr_el = loc_cell.select_one('.evo_location_address')
            if name_el:
                parts = [name_el.get_text(strip=True)]
                if addr_el:
                    # Strip map link text
                    addr_text = addr_el.get_text(' ', strip=True).split('↗')[0].strip()
                    addr_text = re.sub(r'\s*↗.*', '', addr_text).strip()
                    if addr_text:
                        parts.append(addr_text)
                loc_candidate = ', '.join(p for p in parts if p)
                if loc_candidate:
                    location = loc_candidate

        # Description from event card
        desc = ''
        for el in soup.select('.event_description .evcal_evdata_cell, .evo_metarow_details .evcal_evdata_cell'):
            desc = el.get_text(' ', strip=True)
            if desc and 'Event Details' in desc:
                desc = desc.replace('Event Details', '').strip()
            if desc:
                break
        if not desc:
            # Fallback: first meaningful paragraph in content
            for p in soup.select('article p, .entry-content p'):
                pt = p.get_text(strip=True)
                if len(pt) > 30:
                    desc = pt[:400]
                    break

        clean_title = html_mod.unescape(title)
        slug = re.sub(r'[^a-z0-9]+', '-', clean_title.lower())[:40]
        uid = f"eventon-{dtstart.strftime('%Y%m%d')}-{slug}@{self.domain}"

        return {
            'title': clean_title,
            'dtstart': dtstart,
            'dtend': dtend or dtstart + timedelta(hours=2),
            'url': url,
            'location': location,
            'description': desc[:400],
            'uid': uid,
        }

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch all EventON events and filter to future ones."""
        items = self._fetch_event_items()
        if not items:
            return []

        tz = ZoneInfo(self.timezone)
        now = datetime.now(tz)

        # Deduplicate by slug (EventON creates repeat entries for recurring events)
        seen_slugs: set[str] = set()
        unique_items = []
        for item in items:
            slug = item.get('slug', '')
            # Strip trailing -2, -3 etc for dedup
            base_slug = re.sub(r'-\d+$', '', slug)
            if base_slug not in seen_slugs:
                seen_slugs.add(base_slug)
                unique_items.append(item)

        self.logger.info(f"Fetching {len(unique_items)} unique event pages (parallel)...")
        events = []

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(
                    self._fetch_event_page,
                    item.get('link', ''),
                    item.get('title', {}).get('rendered', 'Untitled'),
                    tz,
                    now,
                ): item
                for item in unique_items
                if item.get('link')
            }
            for future in as_completed(futures):
                result = future.result()
                if result:
                    events.append(result)

        self.logger.info(f"Got {len(events)} future events")
        return events


def main():
    parser = argparse.ArgumentParser(description="Scrape an EventON (WordPress) site")
    parser.add_argument('--url', required=True,
                        help='Site base URL (e.g. https://whitehorseblackmountain.org)')
    parser.add_argument('--name', required=True, help='Source name')
    parser.add_argument('--timezone', default='America/New_York',
                        help='IANA timezone (default: America/New_York)')
    parser.add_argument('--default-location', default='',
                        help='Fallback location string')
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = EventOnScraper(
        site_url=args.url,
        source_name=args.name,
        tz=args.timezone,
        default_location=args.default_location,
    )
    scraper.run(args.output)


if __name__ == '__main__':
    main()
