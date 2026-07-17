#!/usr/bin/env python3
"""
Scraper for sites running the Simpleview CMS tourism/events platform.

The RSS feed at <base>/event/rss/ lists upcoming events.  Each RSS item
carries category tags (which may include town names) and a <pubDate> that
is the event's END date at 23:59:59 — NOT a publication date.  We use it
only as a cheap past-filter hint (if pubDate is in the past the event has
already ended).

Each item's detail page embeds schema.org Event JSON-LD with date-only
startDate / endDate values and a location object.  We parse those for
accurate dates; we never trust the RSS <description> HTML for dates.

Date-only events are emitted as all-day iCal events (DATE values).
Multi-day events use DTEND = endDate + 1 day (iCal exclusive convention).

Known venues on this platform:
  - Monroe Convention Center  (https://www.bloomingtonconvention.com)
  - Visit Morgan County        (https://www.visitmorgancountyin.com)

Usage:
    python scrapers/simpleview.py \\
        --url "https://www.bloomingtonconvention.com" \\
        --name "Monroe Convention Center" \\
        --default-location "Monroe Convention Center, 302 S College Ave, Bloomington, IN 47403" \\
        --output cities/bloomington/simpleview_mcc.ics

    python scrapers/simpleview.py \\
        --url "https://www.visitmorgancountyin.com" \\
        --name "Visit Morgan County" \\
        --towns Martinsville \\
        --output cities/bloomington/simpleview_morgan.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import html as html_mod
import logging
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Optional
from urllib.parse import urlparse
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from zoneinfo import ZoneInfo

from lib.base import BaseScraper
from lib.jsonld import extract_jsonld_blocks, extract_events_from_blocks, parse_location

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


class SimpleviewScraper(BaseScraper):
    """Scraper for Simpleview CMS tourism/event sites via RSS + JSON-LD."""

    def __init__(
        self,
        base_url: str,
        source_name: str,
        tz: str = 'America/Indiana/Indianapolis',
        default_location: str = '',
        towns: Optional[list[str]] = None,
    ):
        self.base_url = base_url.rstrip('/')
        self.name = source_name
        self.domain = urlparse(base_url).netloc.removeprefix('www.')
        self.timezone = tz
        self.default_location = default_location
        # Normalise town filter to lower-case for case-insensitive matching.
        self.towns = [t.strip().lower() for t in towns] if towns else []
        super().__init__()

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    def _fetch(self, url: str) -> Optional[str]:
        req = Request(url, headers=HEADERS)
        try:
            with urlopen(req, timeout=30) as resp:
                return resp.read().decode('utf-8', errors='replace')
        except (HTTPError, URLError) as exc:
            self.logger.warning(f"Failed to fetch {url}: {exc}")
            return None

    # ------------------------------------------------------------------
    # RSS discovery
    # ------------------------------------------------------------------

    def _discover_items(self) -> list[dict]:
        """Fetch RSS and return list of {url, categories} dicts.

        Filters out items whose pubDate (= event end date) is in the past,
        and optionally filters by town category.
        """
        rss_url = f"{self.base_url}/event/rss/"
        content = self._fetch(rss_url)
        if not content:
            self.logger.error("Could not fetch RSS feed")
            return []

        try:
            root = ET.fromstring(content)
        except ET.ParseError as exc:
            self.logger.error(f"Failed to parse RSS: {exc}")
            return []

        now_utc = datetime.now(timezone.utc)
        items = []
        skipped_past = 0
        skipped_town = 0

        for item in root.findall('.//item'):
            link_el = item.find('link')
            if link_el is None or not link_el.text:
                continue
            url = link_el.text.strip()

            # pubDate is the event END date (23:59:59).  If it's in the past
            # the event has ended — skip without fetching the detail page.
            pub_el = item.find('pubDate')
            if pub_el is not None and pub_el.text:
                try:
                    pub_dt = parsedate_to_datetime(pub_el.text)
                    if pub_dt < now_utc:
                        skipped_past += 1
                        continue
                except (ValueError, TypeError):
                    pass  # malformed date — include and let detail page decide

            # Categories: used for town filtering.
            categories = []
            for cat_el in item.findall('category'):
                text = cat_el.text or ''
                categories.append(text.strip().lower())

            # Town filter: keep item if ANY category matches ANY requested town.
            if self.towns:
                if not any(town in cat for cat in categories for town in self.towns):
                    skipped_town += 1
                    continue

            items.append({'url': url, 'categories': categories})

        self.logger.info(
            f"RSS: {len(items)} items kept "
            f"(skipped {skipped_past} past, {skipped_town} town-filtered)"
        )
        return items

    # ------------------------------------------------------------------
    # Detail-page JSON-LD parsing
    # ------------------------------------------------------------------

    def _parse_detail(self, item: dict) -> Optional[dict[str, Any]]:
        """Fetch a detail page and return an event dict, or None."""
        url = item['url']
        html = self._fetch(url)
        if not html:
            return None

        blocks = extract_jsonld_blocks(html)
        events = extract_events_from_blocks(blocks)
        if not events:
            self.logger.debug(f"No JSON-LD Event found at {url}")
            return None

        data = events[0]

        title = html_mod.unescape(data.get('name', 'Untitled'))
        start_str = data.get('startDate', '')
        if not start_str:
            self.logger.debug(f"No startDate at {url}")
            return None

        # Simpleview JSON-LD uses date-only strings (YYYY-MM-DD).
        # If a time component ever appears, fromisoformat handles it.
        try:
            dtstart = _parse_date_or_datetime(start_str)
        except ValueError:
            self.logger.debug(f"Bad startDate '{start_str}' at {url}")
            return None

        # Past-event guard (works for both date and datetime).
        if _is_past(dtstart):
            return None

        dtend: Optional[date] = None
        end_str = data.get('endDate', '')
        if end_str:
            try:
                dtend_raw = _parse_date_or_datetime(end_str)
                # Simpleview endDate is the last day (inclusive).
                # iCal DATE-type DTEND must be exclusive → add 1 day.
                if isinstance(dtend_raw, date) and not isinstance(dtend_raw, datetime):
                    dtend = dtend_raw + timedelta(days=1)
                else:
                    dtend = dtend_raw
            except ValueError:
                pass

        location = parse_location(data.get('location'), self.default_location)

        desc_raw = data.get('description', '') or ''
        desc = html_mod.unescape(desc_raw)
        desc = re.sub(r'<[^>]+>', ' ', desc).strip()
        desc = re.sub(r'\s+', ' ', desc)

        return {
            'title': title,
            'dtstart': dtstart,
            'dtend': dtend,
            'location': location,
            'description': desc[:500] if desc else '',
            'url': url,
        }

    # ------------------------------------------------------------------
    # BaseScraper interface
    # ------------------------------------------------------------------

    def fetch_events(self) -> list[dict[str, Any]]:
        items = self._discover_items()
        if not items:
            return []

        self.logger.info(f"Fetching {len(items)} detail pages (parallel)…")
        events = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self._parse_detail, it): it for it in items}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    events.append(result)

        self.logger.info(f"Got {len(events)} future events after detail parse")
        return events


# ------------------------------------------------------------------
# Date helpers
# ------------------------------------------------------------------

def _parse_date_or_datetime(s: str):
    """Return a date or datetime from an ISO string.

    Simpleview uses date-only (YYYY-MM-DD).  Handles full ISO datetimes too.
    """
    s = s.strip()
    if 'T' in s or ' ' in s:
        return datetime.fromisoformat(s.replace('Z', '+00:00'))
    # date-only
    return date.fromisoformat(s)


def _is_past(dt) -> bool:
    """True if dt (date or datetime) is strictly in the past."""
    today = datetime.now(timezone.utc).date()
    if isinstance(dt, datetime):
        return dt.astimezone(timezone.utc) < datetime.now(timezone.utc)
    # date object
    return dt < today


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Scrape a Simpleview CMS tourism/events site via RSS + JSON-LD'
    )
    parser.add_argument(
        '--url', required=True,
        help='Site base URL (e.g. https://www.bloomingtonconvention.com)'
    )
    parser.add_argument('--name', required=True, help='Display name for the source')
    parser.add_argument(
        '--timezone', default='America/Indiana/Indianapolis',
        help='IANA timezone (default: America/Indiana/Indianapolis)'
    )
    parser.add_argument(
        '--default-location', default='',
        help='Fallback location string when JSON-LD has none'
    )
    parser.add_argument(
        '--towns', default='',
        help='Comma-separated town names to keep (matched against RSS category values, case-insensitive). '
             'Omit to keep all events.'
    )
    parser.add_argument('--output', '-o', help='Output ICS file path')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    towns = [t.strip() for t in args.towns.split(',') if t.strip()] if args.towns else []

    scraper = SimpleviewScraper(
        base_url=args.url,
        source_name=args.name,
        tz=args.timezone,
        default_location=args.default_location,
        towns=towns or None,
    )
    scraper.run(args.output)


if __name__ == '__main__':
    main()
