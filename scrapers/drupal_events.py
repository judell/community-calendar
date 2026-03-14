#!/usr/bin/env python3
"""
Scraper for Drupal library/community calendar JSON feeds.

Many public library systems run Drupal with the Library Calendar module,
which exposes a JSON feed at /events/feed/json with start/end date filtering.

The JSON returns an array of event objects with fields like:
  title, start_date, end_date, timezone, branch, room, url, description,
  program_type, age_group, registration_enabled, image, etc.

Usage:
    # Lancaster County Libraries
    python scrapers/drupal_events.py \
        --url "https://calendar.lancasterlibraries.org/events/feed/json" \
        --name "Lancaster Libraries" \
        --output cities/lancaster/lancaster_libraries.ics

    # Any Drupal site with the same JSON feed structure
    python scrapers/drupal_events.py \
        --url "https://example.org/events/feed/json" \
        --name "Example Library" \
        --timezone America/Chicago \
        --output example_library.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any
from urllib.request import urlopen, Request
from zoneinfo import ZoneInfo

from lib.base import BaseScraper
from lib.utils import DEFAULT_HEADERS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DrupalEventsScraper(BaseScraper):
    """Scraper for Drupal library/community calendar JSON feeds."""

    name = "Drupal Events"
    domain = "example.org"
    timezone = "America/New_York"

    def __init__(self, feed_url: str, source_name: str | None = None,
                 tz: str | None = None):
        super().__init__()
        self.feed_url = feed_url
        if source_name:
            self.name = source_name
        # Extract domain from feed URL
        self.domain = feed_url.split('//')[1].split('/')[0]
        if tz:
            self.timezone = tz
        self.tz = ZoneInfo(self.timezone)

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from the Drupal JSON feed."""
        start = datetime.now().strftime("%Y-%m-%d")
        end = (datetime.now() + timedelta(days=self.months_ahead * 31)).strftime("%Y-%m-%d")
        url = f"{self.feed_url}?start={start}&end={end}"

        self.logger.info(f"Fetching {url}")
        req = Request(url, headers=DEFAULT_HEADERS)
        resp = urlopen(req, timeout=60)
        data = json.loads(resp.read())
        self.logger.info(f"Got {len(data)} raw events")

        events = []
        for item in data:
            parsed = self._parse_event(item)
            if parsed:
                events.append(parsed)

        self.logger.info(f"Parsed {len(events)} events")
        return events

    def _parse_event(self, item: dict) -> dict[str, Any] | None:
        """Parse a single event from the Drupal JSON feed."""
        title = item.get('title', '').strip()
        if not title:
            return None

        # Parse start/end dates — format: "2026-03-13 09:00:00"
        start_str = item.get('start_date', '')
        if not start_str:
            return None

        try:
            dtstart = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
            # Use event-level timezone if provided, otherwise default
            event_tz_str = item.get('timezone', self.timezone)
            event_tz = ZoneInfo(event_tz_str) if event_tz_str else self.tz
            dtstart = dtstart.replace(tzinfo=event_tz)
        except (ValueError, KeyError):
            return None

        end_str = item.get('end_date', '')
        if end_str:
            try:
                dtend = datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")
                dtend = dtend.replace(tzinfo=event_tz)
            except ValueError:
                dtend = dtstart
        else:
            dtend = dtstart

        # Location — combine branch and room
        location = self._build_location(item)

        # URL
        url = item.get('url', '')

        # Description — strip HTML tags for plain text
        description = self._strip_html(item.get('description', '') or '')

        # Add program type and age group as context
        meta_parts = []
        program_types = item.get('program_type', {})
        if isinstance(program_types, dict):
            meta_parts.extend(program_types.values())
        age_groups = item.get('age_group', {})
        if isinstance(age_groups, dict):
            meta_parts.extend(age_groups.values())
        if meta_parts:
            description = f"{', '.join(meta_parts)}\n\n{description}".strip()

        return {
            'title': title,
            'dtstart': dtstart,
            'dtend': dtend,
            'location': location,
            'url': url,
            'description': description,
        }

    @staticmethod
    def _build_location(item: dict) -> str:
        """Build location string from branch, room, and offsite address."""
        parts = []

        # Branch name (dict: {"101": "Lancaster"})
        branch = item.get('branch', {})
        if isinstance(branch, dict):
            branch_names = list(branch.values())
            if branch_names:
                parts.append(branch_names[0])

        # Room (dict: {"349": "LPL Community Room"})
        room = item.get('room', {})
        if isinstance(room, dict):
            room_names = list(room.values())
            if room_names:
                parts.append(room_names[0])

        # Offsite address overrides branch/room
        offsite = item.get('offsite_address')
        if offsite:
            return offsite

        return ', '.join(parts)

    @staticmethod
    def _strip_html(html: str) -> str:
        """Strip HTML tags and decode entities for plain text."""
        text = re.sub(r'<[^>]+>', '', html)
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        # Collapse whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        return text.strip()


def main():
    parser = argparse.ArgumentParser(
        description='Scrape Drupal library/community calendar JSON feeds'
    )
    parser.add_argument('--url', required=True,
                        help='JSON feed URL (e.g., https://calendar.lancasterlibraries.org/events/feed/json)')
    parser.add_argument('--name', default='Drupal Events',
                        help='Source name for the calendar')
    parser.add_argument('--timezone', default='America/New_York',
                        help='Default timezone (default: America/New_York)')
    parser.add_argument('--output', '-o', required=True,
                        help='Output ICS file')

    args = parser.parse_args()

    scraper = DrupalEventsScraper(
        feed_url=args.url,
        source_name=args.name,
        tz=args.timezone,
    )
    scraper.run(args.output)


if __name__ == '__main__':
    main()
