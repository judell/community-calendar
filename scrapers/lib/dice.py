"""DICE venue-page scraper library.

Many independent music venues ticket through DICE. Their /events/ pages
embed `link.dice.fm/<id>` URLs (one per show); each redirects to a DICE
event page with full schema.org MusicEvent JSON-LD (name, startDate,
location with address+geo, canonical url).

This pattern works when:
- Venue's events page is HTML-rendered (not behind heavy JS)
- Venue uses link.dice.fm short links to deep-link DICE event pages
- DICE has the venue's full slate of upcoming shows

When it doesn't work, fall back to the venue's own custom HTML format
or to a per-platform alternative (Songkick for touring acts, etc.).

Usage:
    from lib.dice import DiceVenueScraper

    class MyVenueScraper(DiceVenueScraper):
        name = "My Venue"
        domain = "myvenue.com"
        timezone = "America/New_York"
        venue_url = "https://myvenue.com/events/"
        default_location = "My Venue, 123 Main St, Anytown, US"

    if __name__ == '__main__':
        MyVenueScraper.main()
"""

import html as html_mod
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

from .base import BaseScraper
from .jsonld import (
    extract_jsonld_blocks,
    extract_events_from_blocks,
    parse_location,
)

logger = logging.getLogger(__name__)

LINK_PATTERN = re.compile(r'https://link\.dice\.fm/[A-Za-z0-9]+')


class DiceVenueScraper(BaseScraper):
    """Scraper for venues that ticket through DICE.

    Subclasses set:
        name, domain, timezone (from BaseScraper)
        venue_url: URL of the venue's events listing page
        default_location: fallback location string for events without one

    Optional:
        max_workers: parallelism for DICE event-page fetches (default: 8)
        headers: HTTP headers for both venue and DICE fetches
    """

    venue_url: str = ''
    default_location: str = ''
    max_workers: int = 8
    headers: dict = {
        'User-Agent': 'Mozilla/5.0 (compatible; CommunityCalendar/1.0)',
        'Accept': 'text/html,application/xhtml+xml',
    }

    def _fetch(self, url: str) -> Optional[str]:
        """Fetch a URL; return decoded body or None on error."""
        req = Request(url, headers=self.headers)
        try:
            with urlopen(req, timeout=20) as resp:
                return resp.read().decode('utf-8', errors='replace')
        except (HTTPError, URLError) as e:
            self.logger.warning(f"Failed to fetch {url}: {e}")
            return None

    def _discover_dice_links(self) -> list[str]:
        """Fetch the venue page and extract unique link.dice.fm URLs."""
        if not self.venue_url:
            self.logger.error("venue_url not set")
            return []
        html = self._fetch(self.venue_url)
        if not html:
            return []
        links = sorted(set(LINK_PATTERN.findall(html)))
        self.logger.info(f"Found {len(links)} DICE links on {self.venue_url}")
        return links

    def _extract_event(self, dice_url: str) -> Optional[dict[str, Any]]:
        """Fetch one DICE event page and parse its MusicEvent JSON-LD."""
        html = self._fetch(dice_url)
        if not html:
            return None

        blocks = extract_jsonld_blocks(html)
        events = extract_events_from_blocks(blocks)
        if not events:
            self.logger.debug(f"No JSON-LD events on {dice_url}")
            return None

        item = events[0]
        title = html_mod.unescape(item.get('name', 'Untitled'))
        start_str = item.get('startDate', '')
        if not start_str:
            return None

        try:
            dtstart = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        except ValueError:
            self.logger.debug(f"Bad startDate {start_str!r} on {dice_url}")
            return None

        # Skip past events
        now = datetime.now(timezone.utc)
        start_aware = dtstart if dtstart.tzinfo else dtstart.replace(tzinfo=timezone.utc)
        if start_aware < now:
            return None

        dtend = None
        end_str = item.get('endDate', '')
        if end_str:
            try:
                dtend = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
            except ValueError:
                pass

        location = parse_location(item.get('location'), self.default_location)

        desc = item.get('description', '') or ''
        desc = html_mod.unescape(desc)
        desc = re.sub(r'<[^>]+>', ' ', desc).strip()
        desc = re.sub(r'\s+', ' ', desc)

        # Prefer the canonical DICE event URL over the link.dice.fm short
        url = item.get('url', dice_url)

        return {
            'title': title,
            'dtstart': dtstart,
            'dtend': dtend,
            'location': location,
            'description': desc,
            'url': url,
        }

    def fetch_events(self) -> list[dict[str, Any]]:
        """Discover DICE links from venue page, then extract each in parallel."""
        links = self._discover_dice_links()
        if not links:
            return []

        events: list[dict[str, Any]] = []
        self.logger.info(f"Fetching {len(links)} DICE event pages (parallel)...")

        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = {pool.submit(self._extract_event, url): url for url in links}
            for fut in as_completed(futures):
                ev = fut.result()
                if ev:
                    events.append(ev)

        self.logger.info(f"Got {len(events)} future events")
        return events
