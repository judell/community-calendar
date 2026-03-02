#!/usr/bin/env python3
"""
Scraper for Montclair Film showtimes (Clairidge & Bellevue theaters).

Montclair Film uses WordPress with a custom mc_event post type and the
groundplan-pro plugin. Individual event pages contain JSON-LD with a
subEvent array — each subEvent is a screening with its own startDate,
endDate, and location.

Strategy:
1. Fetch /all-event/ listing page to discover currently-showing film URLs (~15)
2. Fetch each film page in parallel
3. Extract JSON-LD Event → subEvent array for individual showtimes
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

from lib.base import BaseScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

LISTING_URL = "https://montclairfilm.org/all-event/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
}


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
        """Scrape /all-event/ listing page for currently-showing film URLs."""
        html = self._fetch_page(LISTING_URL)
        if not html:
            return []
        urls = list(set(re.findall(
            r'href="(https://www\.montclairfilm\.org/events/[^"?#]+/)"', html
        )))
        self.logger.info(f"Found {len(urls)} current films on listing page")
        return urls

    def _extract_screenings(self, event_url: str) -> list[dict[str, Any]]:
        """Fetch an event page and extract individual screenings from JSON-LD subEvents."""
        html = self._fetch_page(event_url)
        if not html:
            return []

        now = datetime.now(timezone.utc)
        screenings = []

        # Extract JSON-LD blocks
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

            film_title = html_mod.unescape(data.get('name', 'Untitled'))
            film_desc = data.get('description', '') or ''
            film_url = data.get('url', event_url)

            for sub in data.get('subEvent', []):
                start_str = sub.get('startDate', '')
                if not start_str:
                    continue

                try:
                    dtstart = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                except ValueError:
                    continue

                # Skip past screenings
                start_aware = dtstart if dtstart.tzinfo else dtstart.replace(tzinfo=timezone.utc)
                if start_aware < now:
                    continue

                # End time
                dtend = None
                end_str = sub.get('endDate', '')
                if end_str:
                    try:
                        dtend = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
                    except ValueError:
                        pass

                # Location (theater + screen)
                loc_data = sub.get('location', {})
                if isinstance(loc_data, dict):
                    loc_name = loc_data.get('name', '')
                    addr = loc_data.get('address', '')
                    if isinstance(addr, str):
                        addr = addr.replace('\r\n', ', ')
                    location = f"{loc_name}, {addr}" if loc_name and addr else (loc_name or addr)
                else:
                    location = "Montclair Film, 505 Bloomfield Ave, Montclair, NJ 07042"

                # Ticket URL from subEvent
                ticket_url = sub.get('url', film_url)

                screenings.append({
                    'title': film_title,
                    'dtstart': dtstart,
                    'dtend': dtend,
                    'location': location,
                    'description': film_desc[:500] if film_desc else '',
                    'url': ticket_url,
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
