"""JSON-LD Event scraper library.

Many websites embed schema.org Event structured data as JSON-LD in their HTML.
This library extracts and parses that data into calendar events.

Handles common quirks:
- Malformed JSON from WordPress MEC plugin (unescaped HTML in description)
- HTML entities in titles/descriptions
- Various @type values (Event, MusicEvent, SocialEvent, Festival)
- Nested location/address objects

Usage:
    from lib.jsonld import JsonLdScraper

    class MyVenueScraper(JsonLdScraper):
        name = "My Venue"
        domain = "myvenue.com"
        url = "https://myvenue.com/events/"
        default_location = "My Venue, 123 Main St, Anytown, CA"

    if __name__ == '__main__':
        MyVenueScraper.main()
"""

import html as html_mod
import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

from .base import BaseScraper

logger = logging.getLogger(__name__)

EVENT_TYPES = {'Event', 'MusicEvent', 'SocialEvent', 'Festival', 'TheaterEvent',
               'DanceEvent', 'ScreeningEvent', 'LiteraryEvent', 'ExhibitionEvent'}


def fix_malformed_description(raw: str) -> str:
    """Fix JSON-LD where description contains unescaped HTML with quotes.

    Common with WordPress Modern Events Calendar (MEC) plugin which dumps
    raw HTML into the JSON description field without escaping quotes.
    """
    def escape_desc(m):
        prefix = m.group(1)
        content = m.group(2)
        suffix = m.group(3)
        fixed = content.replace('"', '\\"')
        return f'{prefix}{fixed}{suffix}'

    pattern = r'("description":\s*")(.+?)("\s*[,}])'
    return re.sub(pattern, escape_desc, raw)


def extract_jsonld_blocks(html: str) -> list[dict]:
    """Extract all JSON-LD blocks from HTML, with malformed-JSON recovery."""
    pattern = r'<script\s+type="application/ld\+json"[^>]*>(.*?)</script>'
    matches = re.findall(pattern, html, re.DOTALL)

    blocks = []
    for match in matches:
        try:
            data = json.loads(match)
            blocks.append(data)
        except json.JSONDecodeError:
            # Try fixing malformed description fields
            try:
                fixed = fix_malformed_description(match)
                data = json.loads(fixed)
                blocks.append(data)
            except json.JSONDecodeError:
                logger.debug(f"Skipping unparseable JSON-LD block: {match[:100]}...")
    return blocks


def extract_events_from_blocks(blocks: list[dict], event_types: set[str] = EVENT_TYPES) -> list[dict]:
    """Extract Event objects from JSON-LD blocks.

    Handles:
    - Top-level Event objects
    - Arrays of objects
    - @graph arrays
    - Events nested under other types (e.g., HighSchool.event)
    """
    events = []
    for data in blocks:
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get('@type') in event_types:
                    events.append(item)
        elif isinstance(data, dict):
            if data.get('@type') in event_types:
                events.append(data)
            # Check @graph
            for item in data.get('@graph', []):
                if isinstance(item, dict) and item.get('@type') in event_types:
                    events.append(item)
            # Check nested event arrays (e.g., HighSchool.event)
            for item in data.get('event', []):
                if isinstance(item, dict):
                    events.append(item)
    return events


def parse_location(loc_data: Any, default_location: str = '') -> str:
    """Parse schema.org location into a string."""
    if not loc_data or not isinstance(loc_data, dict):
        return default_location

    loc_name = loc_data.get('name', '')
    addr = loc_data.get('address', {})

    if isinstance(addr, dict):
        parts = [
            addr.get('streetAddress', ''),
            addr.get('addressLocality', ''),
            addr.get('addressRegion', ''),
        ]
        addr_str = ', '.join(p for p in parts if p)
        if loc_name and addr_str:
            return f"{loc_name}, {addr_str}"
        return loc_name or addr_str or default_location
    elif isinstance(addr, str):
        if loc_name:
            return f"{loc_name}, {addr}"
        return addr

    return loc_name or default_location


class JsonLdScraper(BaseScraper):
    """Base class for scrapers that extract JSON-LD Event data from web pages.

    Subclasses should set:
        name: str - Source name
        domain: str - Domain for UIDs
        url: str - URL to fetch events from
        default_location: str - Fallback location string

    Optional overrides:
        event_types: set[str] - Schema.org types to match (default: common Event types)
        location_filter: str - Only include events with this string in location (case-insensitive)
        urls: list[str] - Multiple pages to scrape (overrides url)
    """

    url: str = ''
    urls: list[str] = []
    default_location: str = ''
    event_types: set[str] = EVENT_TYPES
    location_filter: Optional[str] = None
    headers: dict = {
        'User-Agent': 'Mozilla/5.0 (compatible; CommunityCalendar/1.0)',
        'Accept': 'text/html,application/xhtml+xml',
    }

    def fetch_html(self, url: str) -> Optional[str]:
        """Fetch a URL and return HTML. Uses urllib to avoid WAF issues."""
        req = Request(url, headers=self.headers)
        try:
            with urlopen(req, timeout=15) as resp:
                return resp.read().decode('utf-8')
        except (HTTPError, URLError) as e:
            self.logger.error(f"Failed to fetch {url}: {e}")
            return None

    def get_urls(self) -> list[str]:
        """Return list of URLs to scrape. Override for dynamic URL generation."""
        if self.urls:
            return list(self.urls)
        if self.url:
            return [self.url]
        return []

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch and parse JSON-LD events from configured URLs."""
        all_events = []

        for page_url in self.get_urls():
            self.logger.info(f"Fetching {page_url}")
            html = self.fetch_html(page_url)
            if not html:
                continue

            blocks = extract_jsonld_blocks(html)
            jsonld_events = extract_events_from_blocks(blocks, self.event_types)
            self.logger.info(f"Found {len(jsonld_events)} JSON-LD events on {page_url}")

            for item in jsonld_events:
                parsed = self._parse_event(item)
                if parsed:
                    all_events.append(parsed)

        self.logger.info(f"Total: {len(all_events)} events")
        return all_events

    def _parse_event(self, item: dict) -> Optional[dict[str, Any]]:
        """Parse a single JSON-LD Event into BaseScraper event dict format."""
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
        location = parse_location(item.get('location'), self.default_location)

        # Location filter
        if self.location_filter and self.location_filter.lower() not in location.lower():
            self.logger.debug(f"Filtered out {title}: location '{location}' doesn't match '{self.location_filter}'")
            return None

        # Description — strip HTML, unescape entities
        desc = item.get('description', '') or ''
        desc = html_mod.unescape(desc)
        desc = re.sub(r'<[^>]+>', ' ', desc).strip()
        desc = re.sub(r'\s+', ' ', desc)

        url = item.get('url', '')

        return {
            'title': title,
            'dtstart': dtstart,
            'dtend': dtend,
            'location': location,
            'description': desc,
            'url': url,
        }
