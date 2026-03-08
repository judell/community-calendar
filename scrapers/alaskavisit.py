#!/usr/bin/env python3
"""
Scraper for alaskavisit.com (Mat-Su Convention & Visitors Bureau).

Fetches the RSS feed to discover event URLs, then extracts JSON-LD
structured data from each event page.

Usage:
    python scrapers/alaskavisit.py --output cities/matsu/alaskavisit.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import json
import logging
import re
import time
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from typing import Any, Optional
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

from lib.base import BaseScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

RSS_URL = 'https://www.alaskavisit.com/event/rss/'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,*/*',
}

KNOWN_EVENT_TYPES = {
    'Event', 'SportsEvent', 'EventSeries', 'MusicEvent',
    'TheaterEvent', 'EducationEvent', 'FoodEvent', 'SocialEvent',
    'BusinessEvent', 'PublicEvent',
}


def fetch_url(url: str, delay: float = 0.5) -> Optional[str]:
    """Fetch a URL and return its text content."""
    time.sleep(delay)
    req = Request(url, headers=HEADERS)
    try:
        with urlopen(req, timeout=20) as resp:
            return resp.read().decode('utf-8', errors='replace')
    except (HTTPError, URLError) as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None


def parse_dt(dt_str: str, tz: timezone) -> Optional[datetime]:
    """Parse ISO date or datetime string into an aware datetime."""
    if not dt_str:
        return None
    try:
        # Date-only: "2026-03-08"
        if re.match(r'^\d{4}-\d{2}-\d{2}$', dt_str):
            d = date.fromisoformat(dt_str)
            return datetime(d.year, d.month, d.day, tzinfo=tz)
        # Datetime: "2026-03-08T09:00:00"
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tz)
        return dt
    except ValueError:
        return None


def extract_event_urls(rss_text: str) -> list[str]:
    """Extract event page URLs from the RSS feed."""
    root = ET.fromstring(rss_text)
    urls = []
    for item in root.findall('.//item'):
        link = item.find('link')
        if link is not None and link.text:
            urls.append(link.text.strip())
    return urls


def extract_json_ld(html: str) -> Optional[dict]:
    """Find the first schema.org Event-type JSON-LD block in the page."""
    blocks = re.findall(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html, re.DOTALL
    )
    for block_str in blocks:
        try:
            obj = json.loads(block_str)
        except json.JSONDecodeError:
            continue
        items = obj if isinstance(obj, list) else [obj]
        for item in items:
            if isinstance(item, dict) and item.get('@type') in KNOWN_EVENT_TYPES:
                return item
    return None


def build_location(loc: Any) -> str:
    """Build a location string from a schema.org Place object."""
    if not isinstance(loc, dict):
        return str(loc) if loc else ''
    parts = []
    name = loc.get('name', '')
    if name:
        parts.append(name)
    addr = loc.get('address', {})
    if isinstance(addr, dict):
        for field in ('streetAddress', 'addressLocality', 'addressRegion', 'postalCode'):
            val = addr.get(field, '')
            if val:
                parts.append(val)
    return ', '.join(parts)


class AlaskaVisitScraper(BaseScraper):
    """Scraper for alaskavisit.com Mat-Su CVB event listings."""

    name = 'Mat-Su Convention & Visitors Bureau'
    domain = 'alaskavisit.com'
    timezone = 'America/Anchorage'

    def fetch_events(self) -> list[dict[str, Any]]:
        import pytz
        tz = pytz.timezone(self.timezone)

        logger.info(f"Fetching RSS from {RSS_URL}")
        rss_text = fetch_url(RSS_URL, delay=0)
        if not rss_text:
            logger.error("Could not fetch RSS feed")
            return []

        urls = extract_event_urls(rss_text)
        logger.info(f"Found {len(urls)} event URLs in RSS")

        now = datetime.now(timezone.utc)
        events = []

        for url in urls:
            logger.debug(f"Fetching {url}")
            html = fetch_url(url)
            if not html:
                continue

            ld = extract_json_ld(html)
            if not ld:
                logger.debug(f"No JSON-LD found at {url}")
                continue

            start_str = ld.get('startDate', '')
            dtstart = parse_dt(start_str, tz)
            if not dtstart:
                logger.debug(f"No valid startDate at {url}")
                continue

            # Skip past events
            start_aware = dtstart if dtstart.tzinfo else dtstart.replace(tzinfo=timezone.utc)
            if start_aware < now:
                logger.debug(f"Skipping past event: {ld.get('name')} ({start_str})")
                continue

            end_str = ld.get('endDate', '')
            dtend = parse_dt(end_str, tz) if end_str else None

            location = build_location(ld.get('location'))
            description = ld.get('description', '')
            event_url = ld.get('url', url)

            events.append({
                'title': ld.get('name', 'Untitled'),
                'dtstart': dtstart,
                'dtend': dtend,
                'location': location,
                'description': description,
                'url': event_url,
            })
            logger.info(f"  + {ld.get('name')} ({start_str})")

        logger.info(f"Scraped {len(events)} future events from alaskavisit.com")
        return events


def main():
    parser = argparse.ArgumentParser(description='Scrape alaskavisit.com Mat-Su CVB events')
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = AlaskaVisitScraper()
    scraper.run(args.output)


if __name__ == '__main__':
    main()
