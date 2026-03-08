#!/usr/bin/env python3
"""
Scraper for Sweetwater Music Hall events via RSS feed + JSON-LD.

The RSS feed at /events/feed/ provides event URLs and descriptions.
Each event page has JSON-LD with startDate, location, etc.
The RSS pubDate is the publish date, NOT the event date — so we
fetch individual pages for accurate dates.

Usage:
    python scrapers/sweetwater.py --output cities/santarosa/sweetwater.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import html as html_mod
import logging
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Optional
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

from lib.base import BaseScraper
from lib.jsonld import extract_jsonld_blocks, extract_events_from_blocks, parse_location

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

RSS_URL = "https://sweetwatermusichall.org/events/feed/"
DEFAULT_LOCATION = "Sweetwater Music Hall, 19 Corte Madera Avenue, Mill Valley, CA"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


class SweetwaterScraper(BaseScraper):
    """Scraper for Sweetwater Music Hall via RSS + JSON-LD."""

    name = "Sweetwater Music Hall"
    domain = "sweetwatermusichall.org"
    timezone = "America/Los_Angeles"

    def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch a URL and return content."""
        req = Request(url, headers=HEADERS)
        try:
            with urlopen(req, timeout=30) as resp:
                return resp.read().decode('utf-8')
        except (HTTPError, URLError) as e:
            self.logger.warning(f"Failed to fetch {url}: {e}")
            return None

    def _discover_event_urls(self) -> list[str]:
        """Fetch RSS feed and extract event URLs."""
        content = self._fetch_page(RSS_URL)
        if not content:
            self.logger.error("Could not fetch RSS feed")
            return []

        try:
            root = ET.fromstring(content)
        except ET.ParseError as e:
            self.logger.error(f"Failed to parse RSS: {e}")
            return []

        # Only fetch items published recently — older ones are almost certainly past events.
        # pubDate is publish date, not event date, but recently published = likely upcoming.
        cutoff = datetime.now(timezone.utc) - timedelta(days=60)
        urls = []
        skipped = 0
        for item in root.findall('.//item'):
            link = item.find('link')
            if link is None or not link.text:
                continue
            pub = item.find('pubDate')
            if pub is not None and pub.text:
                try:
                    pub_dt = parsedate_to_datetime(pub.text)
                    if pub_dt < cutoff:
                        skipped += 1
                        continue
                except (ValueError, TypeError):
                    pass
            urls.append(link.text.strip())

        self.logger.info(f"Discovered {len(urls)} recent event URLs from RSS feed (skipped {skipped} older)")
        return urls

    def _fetch_event_jsonld(self, url: str) -> Optional[dict[str, Any]]:
        """Fetch an individual event page and extract JSON-LD Event data."""
        html = self._fetch_page(url)
        if not html:
            return None

        blocks = extract_jsonld_blocks(html)
        events = extract_events_from_blocks(blocks)

        if not events:
            self.logger.debug(f"No JSON-LD Event found at {url}")
            return None

        item = events[0]

        title = html_mod.unescape(item.get('name', 'Untitled'))
        start_str = item.get('startDate', '')
        if not start_str:
            return None

        try:
            dtstart = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        except ValueError:
            self.logger.debug(f"Skipping {title}: bad startDate {start_str}")
            return None

        # Skip past events
        now = datetime.now(timezone.utc)
        start_aware = dtstart if dtstart.tzinfo else dtstart.replace(tzinfo=timezone.utc)
        if start_aware < now:
            return None

        # End time
        dtend = None
        end_str = item.get('endDate', '')
        if end_str:
            try:
                dtend = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
            except ValueError:
                pass

        # Location
        location = parse_location(item.get('location'), DEFAULT_LOCATION)

        # Description
        desc = item.get('description', '') or ''
        desc = html_mod.unescape(desc)
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

    def fetch_events(self) -> list[dict[str, Any]]:
        """Discover events from RSS, then fetch each for JSON-LD."""
        event_urls = self._discover_event_urls()
        if not event_urls:
            return []

        events = []
        self.logger.info(f"Fetching {len(event_urls)} event pages (parallel)...")

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self._fetch_event_jsonld, url): url for url in event_urls}
            for future in as_completed(futures):
                event = future.result()
                if event:
                    events.append(event)

        self.logger.info(f"Got {len(events)} future events")
        return events


def main():
    parser = argparse.ArgumentParser(description="Scrape Sweetwater Music Hall events")
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = SweetwaterScraper()
    scraper.run(args.output)


if __name__ == '__main__':
    main()
