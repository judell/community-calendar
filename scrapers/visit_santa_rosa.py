#!/usr/bin/env python3
"""
Scraper for Visit Santa Rosa events via Algolia search API.

Visit Santa Rosa (visitsantarosa.com) embeds Algolia credentials in page JS
and indexes events in an Algolia index. We extract credentials at runtime
from the homepage, then query the Algolia API directly.

This is a tourism-aggregator source: events from many local venues appear here.

Usage:
    python scrapers/visit_santa_rosa.py --output cities/santarosa/visit_santa_rosa.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional
from zoneinfo import ZoneInfo
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

from lib.base import BaseScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

HOMEPAGE_URL = 'https://www.visitsantarosa.com/events/'
INDEX_NAME = 'prod-visit-santa-rosa-listings'


class VisitSantaRosaScraper(BaseScraper):
    """Scraper for Visit Santa Rosa events via Algolia API."""

    name = "Visit Santa Rosa"
    domain = "visitsantarosa.com"
    timezone = "America/Los_Angeles"

    def __init__(self):
        super().__init__()

    def _fetch_page(self, url: str, headers: Optional[dict] = None) -> Optional[str]:
        req = Request(url, headers=headers or HEADERS)
        try:
            with urlopen(req, timeout=30) as resp:
                return resp.read().decode('utf-8')
        except (HTTPError, URLError) as e:
            self.logger.warning(f"Failed to fetch {url}: {e}")
            return None

    def _extract_algolia_credentials(self) -> tuple[Optional[str], Optional[str]]:
        """Extract Algolia app ID and API key from homepage JS."""
        html = self._fetch_page(HOMEPAGE_URL)
        if not html:
            return None, None

        app_id_match = re.search(r"window\.searchAppId\s*=\s*['\"]([^'\"]+)['\"]", html)
        api_key_match = re.search(r"window\.searchApiKey\s*=\s*['\"]([^'\"]+)['\"]", html)

        if not app_id_match or not api_key_match:
            # Fallback: look in data-info attributes
            app_id_match = re.search(r'"appId"\s*:\s*"([^"]+)"', html)
            api_key_match = re.search(r'"apiKey"\s*:\s*"([^"]+)"', html)

        app_id = app_id_match.group(1) if app_id_match else None
        api_key = api_key_match.group(1) if api_key_match else None

        if app_id and api_key:
            self.logger.info(f"Extracted Algolia credentials: appId={app_id}")
        else:
            self.logger.error("Could not extract Algolia credentials from homepage")

        return app_id, api_key

    def _query_algolia(self, app_id: str, api_key: str, page: int = 0) -> Optional[dict]:
        """Query Algolia for events."""
        url = f"https://{app_id}-dsn.algolia.net/1/indexes/{INDEX_NAME}/query"

        now_epoch = int(datetime.now(timezone.utc).timestamp())
        params = f"filters=sectionName:Events AND endDate >= {now_epoch}&hitsPerPage=1000&page={page}"

        payload = json.dumps({"params": params}).encode('utf-8')
        headers = {
            **HEADERS,
            'X-Algolia-Application-Id': app_id,
            'X-Algolia-API-Key': api_key,
            'Content-Type': 'application/json',
        }

        req = Request(url, data=payload, headers=headers, method='POST')
        try:
            with urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except (HTTPError, URLError) as e:
            self.logger.error(f"Algolia query failed: {e}")
            return None

    def fetch_events(self) -> list[dict[str, Any]]:
        app_id, api_key = self._extract_algolia_credentials()
        if not app_id or not api_key:
            return []

        all_hits = []
        page = 0
        while True:
            self.logger.info(f"Querying Algolia page {page}...")
            result = self._query_algolia(app_id, api_key, page)
            if not result:
                break

            hits = result.get('hits', [])
            all_hits.extend(hits)

            nb_pages = result.get('nbPages', 1)
            self.logger.info(f"Page {page}/{nb_pages - 1}, {len(hits)} hits (total so far: {len(all_hits)})")
            if page >= nb_pages - 1:
                break
            page += 1

        self.logger.info(f"Total hits from Algolia: {len(all_hits)}")

        now = datetime.now(timezone.utc)
        events = []
        for hit in all_hits:
            event = self._parse_hit(hit, now)
            if event:
                events.append(event)

        self.logger.info(f"Parsed {len(events)} future events")
        return events

    def _parse_hit(self, hit: dict, now: datetime) -> Optional[dict[str, Any]]:
        """Parse an Algolia hit into an event dict."""
        title = hit.get('title', '').strip()
        if not title:
            return None

        start_epoch = hit.get('startDate')
        if not start_epoch:
            return None

        try:
            # Simpleview encodes local wall time as a fake-UTC epoch:
            # the UTC fields ARE the local wall clock — relabel, don't convert
            dtstart = datetime.fromtimestamp(int(start_epoch), tz=timezone.utc) \
                .replace(tzinfo=ZoneInfo(self.timezone))
        except (ValueError, TypeError):
            return None

        # Skip past events
        end_epoch = hit.get('endDate')
        if end_epoch:
            try:
                dtend = datetime.fromtimestamp(int(end_epoch), tz=timezone.utc) \
                    .replace(tzinfo=ZoneInfo(self.timezone))
            except (ValueError, TypeError):
                dtend = dtstart
            # Skip if end is in the past
            if dtend < now:
                return None
        else:
            dtend = dtstart
            if dtstart < now:
                return None

        # Handle all-day events
        is_all_day = hit.get('isAllDay', False)
        if is_all_day:
            from datetime import date
            dtstart_val = dtstart.astimezone(__import__('zoneinfo').ZoneInfo(self.timezone)).date()
            dtend_val = dtend.astimezone(__import__('zoneinfo').ZoneInfo(self.timezone)).date()
        else:
            dtstart_val = dtstart
            dtend_val = dtend

        # Location from address array or _geoloc
        address_parts = hit.get('address', [])
        if address_parts:
            location = ', '.join(str(p) for p in address_parts if p)
        else:
            location = ''

        # URL
        uri = hit.get('uri', '')
        # Algolia's uri is a bare slug; the site serves event pages under /events/
        url = f"https://www.visitsantarosa.com/events{uri}" if uri.startswith('/') else uri

        # Description from content (first 500 chars)
        content = hit.get('content', '') or hit.get('snippet', '') or ''
        # Extract just the first paragraph before URLs/prices
        desc_lines = content.split('\n')
        desc_parts = []
        for line in desc_lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith('URLs:') or line.startswith('Prices:') or line.startswith('Date and Time:') or line.startswith('Venue Details:') or line.startswith('Category:'):
                break
            desc_parts.append(line)
        description = ' '.join(desc_parts)[:500]

        # Categories
        categories = hit.get('eventCategories', [])
        if categories:
            description = (description + '\n\nCategories: ' + ', '.join(categories)).strip()

        return {
            'title': title,
            'dtstart': dtstart_val,
            'dtend': dtend_val,
            'location': location,
            'description': description[:500],
            'url': url,
        }


def main():
    parser = argparse.ArgumentParser(description="Scrape Visit Santa Rosa events via Algolia API")
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = VisitSantaRosaScraper()
    scraper.run(args.output)


if __name__ == '__main__':
    main()
