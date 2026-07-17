#!/usr/bin/env python3
"""
Scraper for Where Y'at AVL Music (whereyatavlmusic.com), an Asheville NC
live-music aggregator with an open JSON API.

A single request to /api/events returns every event (past and future)
with an embedded venue object (name, street address). The API covers
~50 venues, including many small bars and breweries that have no
machine-readable calendar of their own (5 Walnut, Fleetwood's, Double
Crown, Sovereign Kava, One World Brewing, ...).

This is an aggregator source — list it in AGGREGATORS in
scripts/combine_ics.py so primary sources win the card ordering.

Usage:
    python scrapers/whereyat.py --output cities/asheville/whereyat.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import html as html_mod
import json
import logging
import re
from datetime import datetime, date
from typing import Any
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from zoneinfo import ZoneInfo

from lib.base import BaseScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_URL = "https://whereyatavlmusic.com/api/events"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
}


def strip_html(text: str) -> str:
    text = html_mod.unescape(text or '')
    text = re.sub(r'<[^>]+>', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


class WhereYatScraper(BaseScraper):
    """Scraper for the Where Y'at AVL Music JSON API."""

    name = "Where Y'at AVL Music"
    domain = "whereyatavlmusic.com"
    timezone = "America/New_York"
    default_url = "https://whereyatavlmusic.com"

    def fetch_events(self) -> list[dict[str, Any]]:
        req = Request(API_URL, headers=HEADERS)
        try:
            with urlopen(req, timeout=60) as resp:
                payload = json.load(resp)
        except (HTTPError, URLError, json.JSONDecodeError) as e:
            self.logger.error(f"Failed to fetch {API_URL}: {e}")
            return []

        items = payload.get('events', [])
        self.logger.info(f"API returned {len(items)} events (past and future)")

        tz = ZoneInfo(self.timezone)
        today = datetime.now(tz).date()
        events = []
        for item in items:
            venue = item.get('venue') or {}
            if str(venue.get('hidden', '')).lower() == 'true':
                continue

            title = strip_html(item.get('title', ''))
            date_str = item.get('date', '')
            if not title or not date_str:
                continue
            try:
                event_date = date.fromisoformat(date_str)
            except ValueError:
                continue
            if event_date < today:
                continue

            time_str = (item.get('time') or '').strip()
            dtstart: Any
            if re.match(r'^\d{1,2}:\d{2}$', time_str):
                hour, minute = map(int, time_str.split(':'))
                dtstart = datetime(event_date.year, event_date.month, event_date.day,
                                   hour, minute, tzinfo=tz)
            else:
                dtstart = event_date  # all-day fallback when no time given

            location_parts = [venue.get('name', ''), venue.get('streetAddress', '')]
            location = ', '.join(p for p in location_parts if p)

            events.append({
                'title': title,
                'dtstart': dtstart,
                'location': location,
                'description': '',
                'url': item.get('ticketUrl') or venue.get('website') or self.default_url,
            })

        self.logger.info(f"Got {len(events)} future events")
        return events


def main():
    parser = argparse.ArgumentParser(description="Scrape Where Y'at AVL Music events")
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = WhereYatScraper()
    scraper.run(args.output)


if __name__ == '__main__':
    main()
