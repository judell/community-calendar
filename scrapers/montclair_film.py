#!/usr/bin/env python3
"""
Scraper for Montclair Film showtimes (Clairidge & Bellevue theaters).

As of the 2026-08-07 montclairfilm.org redesign, individual event pages no
longer carry a JSON-LD subEvent array with every showtime — the JSON-LD
Event block now carries only a single representative startDate/endDate.
The full multi-date, multi-venue, multi-time showtimes grid is server-
rendered directly in the page HTML instead, as nested
`.venue[data-venue]` > `.date[data-date]` > `<elevent-ticket-button-widget>`
blocks (one button per showtime). This scraper walks that HTML structure
positionally (venue/date markers in document order) to recover every
showtime, and falls back to the single JSON-LD startDate/endDate only if
that HTML grid is absent for a given page (defensive, not currently
expected to trigger).

Strategy:
1. Fetch /cinemas/now-playing/ listing page to discover currently-showing
   film URLs (~12)
2. Fetch each film page in parallel
3. Extract title/description from JSON-LD Event; extract every showtime
   (venue, date, time) from the rendered showtimes grid
This is much cheaper than paginating the WP REST API (1021 total posts).

Usage:
    python scrapers/montclair_film.py --output cities/montclair/montclair_film.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import html as html_mod
import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from zoneinfo import ZoneInfo

from lib.base import BaseScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

LISTING_URL = "https://www.montclairfilm.org/cinemas/now-playing/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
}
EASTERN = ZoneInfo("America/New_York")

# Per-venue street addresses, read from the site's own JSON-LD Place data
# (2026-08-07); used since the showtimes grid only gives a bare venue name.
VENUE_ADDRESSES = {
    "The Clairidge": "486 Bloomfield Avenue, Montclair, NJ 07042",
    "The Bellevue": "260 Bellevue Avenue, Montclair, NJ 07043",
}

VENUE_RE = re.compile(r'<div class="venue" data-venue="([^"]+)">')
DATE_RE = re.compile(r'<div class="date" data-date="([^"]+)">')
TIME_RE = re.compile(r'<button>([\d: ]+(?:AM|PM))')


class MontclairFilmScraper(BaseScraper):
    """Scraper for Montclair Film showtimes via listing page + JSON-LD subEvents."""

    name = "Montclair Film"
    domain = "montclairfilm.org"
    timezone = "America/New_York"

    def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch a URL and return content."""
        req = Request(url, headers=HEADERS)
        try:
            with urlopen(req, timeout=30) as resp:
                return resp.read().decode('utf-8')
        except (HTTPError, URLError) as e:
            self.logger.warning(f"Failed to fetch {url}: {e}")
            return None

    def _get_event_urls(self) -> list[str]:
        """Scrape /cinemas/now-playing/ listing page for currently-showing film URLs."""
        html = self._fetch_page(LISTING_URL)
        if not html:
            return []
        urls = list(set(re.findall(
            r'href="(https://www\.montclairfilm\.org/events/[^"?#]+/)"', html
        )))
        self.logger.info(f"Found {len(urls)} current films on listing page")
        return urls

    @staticmethod
    def _film_meta(html: str, event_url: str) -> dict[str, Any]:
        """Extract title/description/url from the page's JSON-LD Event block."""
        blocks = re.findall(
            r'<script\s+type="application/ld\+json"[^>]*>(.*?)</script>',
            html, re.DOTALL
        )
        for block_str in blocks:
            try:
                data = json.loads(block_str)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict) and data.get('@type') == 'Event':
                return {
                    'title': html_mod.unescape(data.get('name', 'Untitled')),
                    'description': (data.get('description') or '')[:500],
                    'url': data.get('url', event_url),
                }
        return {'title': 'Untitled', 'description': '', 'url': event_url}

    @staticmethod
    def _parse_showtimes(html: str) -> list[dict[str, str]]:
        """Walk the rendered showtimes grid: venue[data-venue] > date[data-date] >
        one or more <button>TIME</button> ticket widgets, in document order.
        Returns a flat list of {venue, date, time} dicts."""
        markers: list[tuple[int, str, str]] = []
        markers.extend((m.start(), 'venue', m.group(1)) for m in VENUE_RE.finditer(html))
        markers.extend((m.start(), 'date', m.group(1)) for m in DATE_RE.finditer(html))
        markers.sort(key=lambda t: t[0])

        showtimes = []
        current_venue = None
        for i, (pos, kind, value) in enumerate(markers):
            if kind == 'venue':
                current_venue = value
                continue
            next_pos = markers[i + 1][0] if i + 1 < len(markers) else pos + 8000
            chunk = html[pos:next_pos]
            for time_str in TIME_RE.findall(chunk):
                showtimes.append({'venue': current_venue, 'date': value, 'time': time_str})
        return showtimes

    def _extract_screenings(self, event_url: str) -> list[dict[str, Any]]:
        """Fetch an event page and extract every screening from the rendered
        showtimes grid, falling back to the single JSON-LD startDate/endDate
        if the grid is absent."""
        html = self._fetch_page(event_url)
        if not html:
            return []

        now = datetime.now(EASTERN)
        meta = self._film_meta(html, event_url)
        screenings = []

        for st in self._parse_showtimes(html):
            try:
                dtstart = datetime.strptime(
                    f"{st['date']} {st['time']}", "%Y-%m-%d %I:%M %p"
                ).replace(tzinfo=EASTERN)
            except ValueError:
                continue

            if dtstart < now:
                continue

            venue = st['venue'] or ''
            addr = VENUE_ADDRESSES.get(venue, 'Montclair, NJ')
            location = f"{venue}, {addr}" if venue else addr

            screenings.append({
                'title': meta['title'],
                'dtstart': dtstart,
                'dtend': None,
                'location': location,
                'description': meta['description'],
                'url': meta['url'],
            })

        if screenings:
            return screenings

        # Fallback: no showtimes grid found, use the single JSON-LD date if present.
        blocks = re.findall(
            r'<script\s+type="application/ld\+json"[^>]*>(.*?)</script>',
            html, re.DOTALL
        )
        for block_str in blocks:
            try:
                data = json.loads(block_str)
            except json.JSONDecodeError:
                continue
            if not isinstance(data, dict) or data.get('@type') != 'Event':
                continue
            start_str = data.get('startDate', '')
            if not start_str:
                continue
            try:
                dtstart = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
            except ValueError:
                continue
            start_aware = dtstart if dtstart.tzinfo else dtstart.replace(tzinfo=EASTERN)
            if start_aware < now:
                continue
            dtend = None
            end_str = data.get('endDate', '')
            if end_str:
                try:
                    dtend = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
                except ValueError:
                    pass
            loc_data = data.get('location', {})
            if isinstance(loc_data, dict):
                loc_name = loc_data.get('name', '')
                addr = loc_data.get('address', {})
                addr_str = addr.get('name', '') if isinstance(addr, dict) else (addr or '')
                location = f"{loc_name}, {addr_str}" if loc_name and addr_str else (loc_name or addr_str)
            else:
                location = 'Montclair, NJ'
            screenings.append({
                'title': meta['title'],
                'dtstart': start_aware,
                'dtend': dtend,
                'location': location,
                'description': meta['description'],
                'url': meta['url'],
            })
        return screenings

    def fetch_events(self) -> list[dict[str, Any]]:
        """Discover current films from listing page, then extract screenings."""
        event_urls = self._get_event_urls()
        if not event_urls:
            return []

        all_screenings = []
        self.logger.info(f"Fetching {len(event_urls)} film pages (parallel)...")

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self._extract_screenings, url): url
                for url in event_urls
            }
            for future in as_completed(futures):
                screenings = future.result()
                if screenings:
                    all_screenings.extend(screenings)

        self.logger.info(f"Got {len(all_screenings)} future screenings")
        return all_screenings


def main():
    parser = argparse.ArgumentParser(description="Scrape Montclair Film showtimes")
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = MontclairFilmScraper()
    scraper.run(args.output)


if __name__ == '__main__':
    main()
