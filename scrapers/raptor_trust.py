#!/usr/bin/env python3
"""
Scraper for The Raptor Trust events.

The Raptor Trust is a Squarespace site with per-event ICS files.
Strategy: scrape /events listing for event slugs, fetch each ?format=ical.

Usage:
    python scrapers/raptor_trust.py --output cities/montclair/raptor_trust.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

from icalendar import Calendar as ICalendar

from lib.base import BaseScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = "https://www.theraptortrust.org"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
}


class RaptorTrustScraper(BaseScraper):
    """Scraper for The Raptor Trust via Squarespace per-event ICS."""

    name = "The Raptor Trust"
    domain = "theraptortrust.org"
    timezone = "America/New_York"

    def _fetch(self, url: str) -> bytes | None:
        req = Request(url, headers=HEADERS)
        try:
            with urlopen(req, timeout=30) as resp:
                return resp.read()
        except (HTTPError, URLError) as e:
            self.logger.warning(f"Failed to fetch {url}: {e}")
            return None

    def _get_event_slugs(self) -> list[str]:
        html = self._fetch(f"{BASE_URL}/events")
        if not html:
            return []
        text = html.decode('utf-8')
        slugs = list(set(re.findall(r'href="(/events/[^"?#]+)"', text)))
        # Filter out the listing page itself
        slugs = [s for s in slugs if s != '/events' and s != '/events/']
        self.logger.info(f"Found {len(slugs)} event slugs")
        return slugs

    def _fetch_event_ics(self, slug: str) -> list[dict[str, Any]]:
        url = f"{BASE_URL}{slug}?format=ical"
        data = self._fetch(url)
        if not data:
            return []

        now = datetime.now(timezone.utc)
        events = []
        try:
            cal = ICalendar.from_ical(data)
        except Exception:
            return []

        for comp in cal.walk('VEVENT'):
            dtstart = comp.get('dtstart')
            if not dtstart:
                continue
            dt = dtstart.dt
            if hasattr(dt, 'hour'):
                start_aware = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            else:
                start_aware = datetime.combine(dt, datetime.min.time()).replace(tzinfo=timezone.utc)

            if start_aware < now:
                continue

            dtend = comp.get('dtend')
            end_dt = dtend.dt if dtend else None

            events.append({
                'title': str(comp.get('summary', 'Untitled')),
                'dtstart': dt,
                'dtend': end_dt,
                'location': str(comp.get('location', '')),
                'description': str(comp.get('description', '')),
                'url': f"{BASE_URL}{slug}",
            })

        return events

    def fetch_events(self) -> list[dict[str, Any]]:
        slugs = self._get_event_slugs()
        if not slugs:
            return []

        all_events = []
        self.logger.info(f"Fetching {len(slugs)} event pages...")

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self._fetch_event_ics, s): s for s in slugs}
            for future in as_completed(futures):
                events = future.result()
                if events:
                    all_events.extend(events)

        self.logger.info(f"Found {len(all_events)} future events")
        return all_events


def main():
    parser = argparse.ArgumentParser(description="Scrape The Raptor Trust events")
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    scraper = RaptorTrustScraper()
    scraper.run(args.output)


if __name__ == '__main__':
    main()
