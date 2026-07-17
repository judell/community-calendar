#!/usr/bin/env python3
"""
Scraper for MountainTrue (mountaintrue.org), a western-NC environmental
nonprofit — river cleanups, hikes, workshops, member gatherings.

The WP REST CPT list at /wp-json/wp/v2/event provides titles and links,
but the ACF date/location fields are not exposed via REST (acf: []).
So we list events via REST, then fetch each event page (throttled
serial — the site 429s parallel bursts) and parse the
Elementor-rendered detail block:

    <h3 ...>Start:</h3> ... <div ...>October 8, 2026 5:30 pm</div>
    <h3 ...>End:</h3>   ... <div ...>October 8, 2026 8:00 pm</div>
    <h2 ...>Location</h2> <h3 ...>Venue Name</h3> <div ...>Address</div>

MountainTrue's events span all of western NC (Boone, Brevard, Murphy...).
We keep only events whose location matches the Asheville area
(Buncombe/Henderson county towns); events with no location default to
the MountainTrue Asheville office.

Usage:
    python scrapers/mountaintrue.py --output cities/asheville/mountaintrue.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import html as html_mod
import json
import logging
import re
import time
from datetime import datetime
from typing import Any, Optional
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from zoneinfo import ZoneInfo

from lib.base import BaseScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_URL = 'https://mountaintrue.org/wp-json/wp/v2/event'
PER_PAGE = 100
MAX_PAGES = 5

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8',
}

# Elementor heading value that follows a label heading
HEADING_VALUE = re.compile(
    r'<(?:div|h3)[^>]*class="[^"]*elementor-heading-title[^"]*"[^>]*>\s*([^<]+?)\s*</(?:div|h3)>'
)
START_LABEL = re.compile(r'>\s*Start:\s*</h3>')
END_LABEL = re.compile(r'>\s*End:\s*</h3>')
LOCATION_LABEL = re.compile(r'>\s*Location\s*</h2>')

# Asheville-area (Buncombe/Henderson) location filter
AREA_PATTERN = re.compile(
    r'\b(Asheville|Black Mountain|Weaverville|Woodfin|Arden|Fletcher|Candler|'
    r'Swannanoa|Fairview|Leicester|Enka|Hendersonville|Mills River|Montreat|'
    r'Mars Hill|Biltmore|Buncombe|Henderson County)\b',
    re.IGNORECASE,
)

DEFAULT_LOCATION = 'MountainTrue, Asheville, NC'
TZ = ZoneInfo('America/New_York')


class MountainTrueScraper(BaseScraper):
    """Scraper for MountainTrue events (WP REST list + event-page details)."""

    name = 'MountainTrue'
    domain = 'mountaintrue.org'
    timezone = 'America/New_York'

    def _fetch(self, url: str, retries: int = 3) -> Optional[str]:
        """Fetch a URL; retry with backoff on 429 (site rate-limits bursts)."""
        for attempt in range(retries):
            req = Request(url, headers=HEADERS)
            try:
                with urlopen(req, timeout=30) as resp:
                    return resp.read().decode('utf-8')
            except HTTPError as e:
                if e.code == 429 and attempt < retries - 1:
                    wait = 2 * (attempt + 1)
                    self.logger.debug(f"429 on {url}, retrying in {wait}s")
                    time.sleep(wait)
                    continue
                self.logger.warning(f"Failed to fetch {url}: {e}")
                return None
            except URLError as e:
                self.logger.warning(f"Failed to fetch {url}: {e}")
                return None
        return None

    def _list_events(self) -> list[dict[str, Any]]:
        """List all published events via WP REST (title, link, excerpt)."""
        items: list[dict[str, Any]] = []
        for page in range(1, MAX_PAGES + 1):
            url = (f'{API_URL}?per_page={PER_PAGE}&page={page}'
                   f'&_fields=id,link,title,excerpt,status')
            body = self._fetch(url)
            if not body:
                break
            try:
                batch = json.loads(body)
            except json.JSONDecodeError as e:
                self.logger.error(f"Bad JSON from {url}: {e}")
                break
            if not isinstance(batch, list) or not batch:
                break
            items.extend(batch)
            if len(batch) < PER_PAGE:
                break
        self.logger.info(f"Listed {len(items)} events from WP REST")
        return items

    @staticmethod
    def _value_after(html: str, label: re.Pattern) -> str:
        """Return the next Elementor heading value after a label heading."""
        m = label.search(html)
        if not m:
            return ''
        v = HEADING_VALUE.search(html, m.end())
        return html_mod.unescape(v.group(1)).strip() if v else ''

    @staticmethod
    def _parse_dt(text: str) -> Optional[datetime]:
        """Parse 'October 8, 2026 5:30 pm' as tz-aware America/New_York."""
        text = re.sub(r'\s+', ' ', text).strip()
        for fmt in ('%B %d, %Y %I:%M %p', '%B %d, %Y'):
            try:
                return datetime.strptime(text, fmt).replace(tzinfo=TZ)
            except ValueError:
                continue
        return None

    def _fetch_event(self, item: dict[str, Any]) -> Optional[dict[str, Any]]:
        url = item.get('link') or ''
        title = html_mod.unescape((item.get('title') or {}).get('rendered', '')).strip()
        if not url or not title:
            return None

        page = self._fetch(url)
        if not page:
            return None

        start_text = self._value_after(page, START_LABEL)
        dtstart = self._parse_dt(start_text) if start_text else None
        if not dtstart:
            self.logger.debug(f"No start date on {url} ({start_text!r})")
            return None

        # Skip past events
        if dtstart < datetime.now(TZ):
            return None

        end_text = self._value_after(page, END_LABEL)
        dtend = self._parse_dt(end_text) if end_text else None

        # Location: venue h3 + address div after the Location h2
        location = ''
        loc = LOCATION_LABEL.search(page)
        if loc:
            venue_m = HEADING_VALUE.search(page, loc.end())
            venue = html_mod.unescape(venue_m.group(1)).strip() if venue_m else ''
            addr = ''
            if venue_m:
                addr_m = HEADING_VALUE.search(page, venue_m.end())
                addr = html_mod.unescape(addr_m.group(1)).strip() if addr_m else ''
            location = ', '.join(p for p in (venue, addr) if p)

        if location:
            # Keep only Asheville-area events
            if not AREA_PATTERN.search(location):
                self.logger.debug(f"Outside Asheville area, dropping: {title} @ {location}")
                return None
        else:
            location = DEFAULT_LOCATION

        desc = (item.get('excerpt') or {}).get('rendered', '') or ''
        desc = html_mod.unescape(re.sub(r'<[^>]+>', ' ', desc))
        desc = re.sub(r'\s+', ' ', desc).strip()

        return {
            'title': title,
            'dtstart': dtstart,
            'dtend': dtend,
            'location': location,
            'description': desc[:500],
            'url': url,
        }

    def fetch_events(self) -> list[dict[str, Any]]:
        items = self._list_events()
        if not items:
            return []

        # Serial with a small delay: mountaintrue.org 429s parallel bursts.
        events: list[dict[str, Any]] = []
        self.logger.info(f"Fetching {len(items)} event pages (throttled serial)...")
        for item in items:
            event = self._fetch_event(item)
            if event:
                events.append(event)
            time.sleep(0.4)

        self.logger.info(f"Got {len(events)} future Asheville-area events")
        return events


def main():
    parser = argparse.ArgumentParser(description="Scrape MountainTrue (Asheville-area) events")
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = MountainTrueScraper()
    scraper.run(args.output)


if __name__ == '__main__':
    main()
