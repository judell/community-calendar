#!/usr/bin/env python3
"""
Scraper for Owen County Public Library events.

The library runs Payload CMS at owenlib.org. The JSON API at
/api/events returns all events with title, date, location, and
rich-text description. Pagination is supported via ?limit=&page=.

Usage:
    python scrapers/owen_county_library.py --output cities/bloomington/owen_county_library.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import json
import logging
from datetime import datetime, timezone
from typing import Any
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from zoneinfo import ZoneInfo

from lib.base import BaseScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "https://owenlib.org"
API_URL = f"{BASE_URL}/api/events"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
}
DEFAULT_LOCATION = "Owen County Public Library, 10 S Montgomery St, Spencer, IN 47460"
TZ = ZoneInfo("America/Indiana/Indianapolis")


def _extract_text(node: Any) -> str:
    """Recursively extract plain text from a Payload CMS rich-text node tree."""
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, dict):
        if node.get("type") == "text":
            return node.get("text", "")
        children = node.get("children", [])
        parts = [_extract_text(child) for child in children]
        return " ".join(p for p in parts if p)
    if isinstance(node, list):
        return " ".join(_extract_text(item) for item in node)
    return ""


class OwenCountyLibraryScraper(BaseScraper):
    """Scraper for Owen County Public Library via Payload CMS JSON API."""

    name = "Owen County Public Library"
    domain = "owenlib.org"
    timezone = "America/Indiana/Indianapolis"

    def _fetch_page(self, page: int) -> dict:
        url = f"{API_URL}?limit=100&page={page}"
        req = Request(url, headers=HEADERS)
        try:
            with urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except (HTTPError, URLError) as e:
            self.logger.warning(f"Failed to fetch page {page}: {e}")
            return {}

    def fetch_events(self) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc)
        events = []
        page = 1

        while True:
            data = self._fetch_page(page)
            docs = data.get('docs', [])
            if not docs:
                break

            for doc in docs:
                date_str = doc.get('date')
                if not date_str:
                    continue

                try:
                    # Dates come in as ISO 8601 UTC strings
                    dtstart = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                except ValueError:
                    self.logger.debug(f"Bad date: {date_str}")
                    continue

                # Skip past events
                start_aware = dtstart if dtstart.tzinfo else dtstart.replace(tzinfo=timezone.utc)
                if start_aware < now:
                    continue

                # Convert to local timezone
                dtstart_local = dtstart.astimezone(TZ)

                # End date
                dtend = None
                end_str = doc.get('endDate')
                if end_str:
                    try:
                        dtend = datetime.fromisoformat(end_str.replace('Z', '+00:00')).astimezone(TZ)
                    except ValueError:
                        pass

                # Location: use the room field if available, fall back to default
                location = doc.get('location') or ''
                room = doc.get('room') or ''
                if location and room:
                    location = f"{location}, {room.replace('-', ' ').title()}"
                elif not location:
                    location = DEFAULT_LOCATION

                # Description: extract from Payload's Lexical rich-text tree
                desc_node = doc.get('description')
                desc = _extract_text(desc_node).strip() if desc_node else ''
                if not desc:
                    # Fallback: cost + registration info
                    parts = []
                    if doc.get('cost'):
                        parts.append(f"Cost: {doc['cost']}")
                    if doc.get('registrationRequired'):
                        parts.append("Registration required.")
                        if doc.get('registrationUrl'):
                            parts.append(doc['registrationUrl'])
                    desc = ' '.join(parts)

                # Event URL (slug-based)
                slug = doc.get('slug', '')
                url = f"{BASE_URL}/events/{slug}" if slug else BASE_URL

                events.append({
                    'title': doc.get('title', 'Untitled'),
                    'dtstart': dtstart_local,
                    'dtend': dtend,
                    'location': location,
                    'description': desc[:500],
                    'url': url,
                })

            has_next = data.get('hasNextPage', False)
            if not has_next:
                break
            page += 1

        self.logger.info(f"Found {len(events)} future events")
        return events


def main():
    parser = argparse.ArgumentParser(description="Scrape Owen County Public Library events")
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    scraper = OwenCountyLibraryScraper()
    scraper.run(args.output)


if __name__ == '__main__':
    main()
