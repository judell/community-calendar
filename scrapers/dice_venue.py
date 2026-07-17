#!/usr/bin/env python3
"""
Parameterized scraper for the DICE partner events API.

Unlike scrapers/lib/dice.py (which scrapes a venue's own website for
link.dice.fm short links, then fetches each DICE event page for JSON-LD),
this scraper talks directly to DICE's partner API:

    https://events-api.dice.fm/v1/events

which returns full structured event JSON (name, ISO dates, venue,
address, ticket URL) in one paginated request — no per-event page
fetches. The API requires an `x-api-key` header. A public client-side
partner key is embedded in pages that use DICE's event-list widget
(e.g. https://ayurpranalisteningroom.com/events, as
`"apiKey":"..."` in the widget config). By default we extract the key
at runtime from such a page (--key-url) so a key rotation doesn't
break the scraper; --api-key overrides for a known-good key.

Kept self-contained rather than extending lib/dice.py: the two share
no fetching or parsing logic (widget API vs. link-scrape + JSON-LD).

Usage:
    python scrapers/dice_venue.py \
        --venue "Eulogy" --name "Eulogy" \
        --output cities/asheville/dice_eulogy.ics

    python scrapers/dice_venue.py \
        --venue "AyurPrana Listening Room" --name "AyurPrana Listening Room" \
        --output cities/asheville/dice_ayurprana.ics

    # Or all Asheville events on DICE:
    python scrapers/dice_venue.py --city Asheville --name "DICE Asheville"
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

from lib.base import BaseScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_URL = 'https://events-api.dice.fm/v1/events'
DEFAULT_KEY_URL = 'https://ayurpranalisteningroom.com/events'
# Widget config embeds the partner key as "apiKey":"..."
API_KEY_PATTERN = re.compile(r'"apiKey"\s*:\s*"([A-Za-z0-9]{20,})"')
PAGE_SIZE = 100
MAX_PAGES = 10  # safety cap

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/html;q=0.9, */*;q=0.8',
}


class DiceApiScraper(BaseScraper):
    """Scraper for DICE partner events API, filtered by venue(s) or city."""

    def __init__(self, source_name: str, venues: list[str], city: Optional[str],
                 api_key: Optional[str], key_url: str, tz: str = 'America/New_York'):
        self.name = source_name
        self.domain = 'dice.fm'
        self.timezone = tz
        self.venues = venues
        self.city = city
        self.api_key = api_key
        self.key_url = key_url
        super().__init__()

    def _fetch(self, url: str, headers: Optional[dict] = None) -> Optional[str]:
        req = Request(url, headers={**HEADERS, **(headers or {})})
        try:
            with urlopen(req, timeout=30) as resp:
                return resp.read().decode('utf-8')
        except (HTTPError, URLError) as e:
            self.logger.warning(f"Failed to fetch {url}: {e}")
            return None

    def _get_api_key(self) -> Optional[str]:
        """Return the API key, extracting it from the key-url page if needed."""
        if self.api_key:
            return self.api_key
        self.logger.info(f"Extracting DICE API key from {self.key_url}")
        html = self._fetch(self.key_url)
        if not html:
            self.logger.error(f"Could not fetch key page {self.key_url}")
            return None
        m = API_KEY_PATTERN.search(html)
        if not m:
            self.logger.error(f"No apiKey found in {self.key_url}")
            return None
        self.api_key = m.group(1)
        self.logger.info(f"Extracted API key ...{self.api_key[-6:]}")
        return self.api_key

    def _build_url(self) -> str:
        params = [('page[size]', str(PAGE_SIZE))]
        for venue in self.venues:
            params.append(('filter[venues][]', venue))
        if self.city:
            params.append(('filter[cities][]', self.city))
        return f"{API_URL}?{urlencode(params)}"

    def _parse_event(self, item: dict[str, Any]) -> Optional[dict[str, Any]]:
        title = (item.get('name') or '').strip()
        start_str = item.get('date') or ''
        if not title or not start_str:
            return None

        try:
            dtstart = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        except ValueError:
            self.logger.debug(f"Bad date {start_str!r} for {title}")
            return None
        if dtstart.tzinfo is None:
            dtstart = dtstart.replace(tzinfo=timezone.utc)

        # Skip past events
        if dtstart < datetime.now(timezone.utc):
            return None

        dtend = None
        end_str = item.get('date_end') or ''
        if end_str:
            try:
                dtend = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
                if dtend.tzinfo is None:
                    dtend = dtend.replace(tzinfo=timezone.utc)
            except ValueError:
                pass

        # Location: "<venue name>, <full address>"
        venue_name = item.get('venue') or ''
        venues = item.get('venues') or []
        if not venue_name and venues:
            venue_name = venues[0].get('name', '')
        address = item.get('address') or ''
        location = ', '.join(p for p in (venue_name, address) if p)

        desc = (item.get('raw_description') or item.get('description') or '').strip()
        desc = re.sub(r'\s+', ' ', desc)

        event: dict[str, Any] = {
            'title': title,
            'dtstart': dtstart,
            'dtend': dtend,
            'location': location,
            'description': desc[:500],
            'url': item.get('url') or '',
        }
        images = item.get('images') or []
        if images:
            event['image_url'] = images[0]
        return event

    def fetch_events(self) -> list[dict[str, Any]]:
        api_key = self._get_api_key()
        if not api_key:
            return []

        events: list[dict[str, Any]] = []
        url: Optional[str] = self._build_url()
        pages = 0
        while url and pages < MAX_PAGES:
            body = self._fetch(url, headers={'x-api-key': api_key})
            if not body:
                break
            try:
                payload = json.loads(body)
            except json.JSONDecodeError as e:
                self.logger.error(f"Bad JSON from {url}: {e}")
                break
            data = payload.get('data') or []
            self.logger.info(f"Page {pages + 1}: {len(data)} events")
            for item in data:
                event = self._parse_event(item)
                if event:
                    events.append(event)
            url = (payload.get('links') or {}).get('next')
            pages += 1

        self.logger.info(f"Got {len(events)} future events")
        return events


def main():
    parser = argparse.ArgumentParser(description="Scrape events from the DICE partner API")
    parser.add_argument('--venue', action='append', default=[],
                        help='Venue name filter (repeatable), e.g. --venue "Eulogy"')
    parser.add_argument('--city', help='City filter, e.g. --city Asheville')
    parser.add_argument('--name', required=True, help='Source display name')
    parser.add_argument('--api-key', help='DICE partner API key (overrides --key-url extraction)')
    parser.add_argument('--key-url', default=DEFAULT_KEY_URL,
                        help=f'Page embedding a DICE widget apiKey (default: {DEFAULT_KEY_URL})')
    parser.add_argument('--timezone', default='America/New_York',
                        help='IANA timezone (default: America/New_York)')
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if not args.venue and not args.city:
        parser.error('Provide at least one --venue or a --city')

    scraper = DiceApiScraper(args.name, args.venue, args.city,
                             args.api_key, args.key_url, args.timezone)
    scraper.run(args.output)


if __name__ == '__main__':
    main()
