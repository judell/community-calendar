#!/usr/bin/env python3
"""
Scraper for California Theatre (Cal Theatre) Santa Rosa events
https://www.caltheatre.com/calendar

This is a Wix site. The DOM scrape (BeautifulSoup) is broken because Wix requires
JavaScript to render the calendar widget. However, Wix server-renders all event
data inside <script type="application/json" id="wix-warmup-data"> on the initial
HTML response. We parse that JSON to extract events without a headless browser.

Event data path in warmupData:
  appsWarmupData
    -> "140603ad-af8d-84a5-2c80-a0f60cb47351"   (Wix Events app ID)
    -> widgetcomp-lsc1et6p                        (widget instance)
    -> events -> events                            (list of event dicts)
Each event has:
  - title
  - scheduling.config.startDate / endDate (UTC ISO)
  - scheduling.config.timeZoneId
  - location.address
  - description
  - slug (used for per-event URL)
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

from lib.base import BaseScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

# Wix Events app UUID (stable across sites using the app)
WIX_EVENTS_APP_ID = '140603ad-af8d-84a5-2c80-a0f60cb47351'


class CalTheatreScraper(BaseScraper):
    """Scraper for California Theatre Santa Rosa events."""

    name = "Cal Theatre"
    domain = "caltheatre.com"
    timezone = "America/Los_Angeles"

    BASE_URL = 'https://www.caltheatre.com'
    CALENDAR_URL = f'{BASE_URL}/calendar'
    VENUE_ADDRESS = "California Theatre, 528 7th St, Santa Rosa, CA 95401"

    def _fetch_page(self, url: str) -> Optional[str]:
        req = Request(url, headers=HEADERS)
        try:
            with urlopen(req, timeout=30) as resp:
                return resp.read().decode('utf-8')
        except (HTTPError, URLError) as e:
            self.logger.warning(f"Failed to fetch {url}: {e}")
            return None

    def _extract_wix_events(self, html: str) -> list[dict]:
        """Extract events from the Wix warmup data embedded in the page."""
        # Find the warmup data JSON script tag
        m = re.search(
            r'<script[^>]+type="application/json"[^>]+id="wix-warmup-data"[^>]*>(.*?)</script>',
            html, re.DOTALL
        )
        if not m:
            self.logger.error("Could not find wix-warmup-data script tag")
            return []

        try:
            warmup = json.loads(m.group(1))
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse warmup JSON: {e}")
            return []

        # Navigate to events
        apps = warmup.get('appsWarmupData', {})
        wix_events_app = apps.get(WIX_EVENTS_APP_ID, {})
        if not wix_events_app:
            self.logger.error(f"Wix Events app data not found (key: {WIX_EVENTS_APP_ID})")
            return []

        # The widget key can vary; iterate widgets to find events
        raw_events = []
        for widget_key, widget_data in wix_events_app.items():
            if not isinstance(widget_data, dict):
                continue
            events_container = widget_data.get('events', {})
            if isinstance(events_container, dict):
                event_list = events_container.get('events', [])
                if isinstance(event_list, list) and event_list:
                    self.logger.info(f"Found {len(event_list)} events in widget {widget_key!r}")
                    raw_events.extend(event_list)

        return raw_events

    def fetch_events(self) -> list[dict[str, Any]]:
        self.logger.info(f"Fetching {self.CALENDAR_URL}")
        html = self._fetch_page(self.CALENDAR_URL)
        if not html:
            self.logger.error("Could not fetch calendar page")
            return []

        raw_events = self._extract_wix_events(html)
        if not raw_events:
            self.logger.warning("No events found in Wix warmup data")
            return []

        self.logger.info(f"Parsing {len(raw_events)} raw events")
        now = datetime.now(timezone.utc)
        events = []

        for item in raw_events:
            event = self._parse_wix_event(item, now)
            if event:
                events.append(event)

        self.logger.info(f"Found {len(events)} future events")
        return events

    def _parse_wix_event(self, item: dict, now: datetime) -> Optional[dict[str, Any]]:
        """Parse a single Wix event dict."""
        title = item.get('title', '').strip()
        if not title:
            return None

        scheduling = item.get('scheduling', {})
        config = scheduling.get('config', {})

        start_str = config.get('startDate', '')
        if not start_str:
            return None

        try:
            dtstart = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        except ValueError:
            self.logger.debug(f"Bad startDate {start_str!r} for {title!r}")
            return None

        start_aware = dtstart if dtstart.tzinfo else dtstart.replace(tzinfo=timezone.utc)
        if start_aware < now:
            return None

        end_str = config.get('endDate', '')
        dtend = None
        if end_str:
            try:
                dtend = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
            except ValueError:
                pass

        # Location
        loc = item.get('location', {})
        address = loc.get('address', '') or loc.get('formattedAddress', '') or ''
        if not address:
            full_addr = loc.get('fullAddress', {})
            if isinstance(full_addr, dict):
                address = full_addr.get('formattedAddress', '') or ''
        location = address.strip() or self.VENUE_ADDRESS

        # Description (strip HTML)
        description = item.get('description', '') or ''
        description = re.sub(r'<[^>]+>', ' ', description).strip()
        description = re.sub(r'\s+', ' ', description)

        # URL from slug
        slug = item.get('slug', '')
        event_id = item.get('id', '')
        if slug:
            url = f"{self.BASE_URL}/event-details/{slug}"
        else:
            url = self.CALENDAR_URL

        return {
            'title': title,
            'dtstart': dtstart,
            'dtend': dtend or dtstart,
            'location': location,
            'description': description[:500],
            'url': url,
        }


if __name__ == '__main__':
    CalTheatreScraper.main()
