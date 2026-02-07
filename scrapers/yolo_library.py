#!/usr/bin/env python3
"""
Scraper for Yolo County Library events (includes Davis branch)
https://events.yolocountylibrary.org/

LibCal platform - RSS feed with custom namespace.
Filters to Davis-area branches only.
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import html
import re
from datetime import datetime
from typing import Any, Optional
from zoneinfo import ZoneInfo

import feedparser

from lib.base import BaseScraper


# Davis-area branches to include
DAVIS_BRANCHES = {
    'Mary L Stephens Davis Branch Library',
    'Davis Branch Library',
    'Davis',
}


class YoloLibraryScraper(BaseScraper):
    """Scraper for Yolo County Library events."""

    name = "Yolo Library"
    domain = "events.yolocountylibrary.org"
    timezone = "America/Los_Angeles"

    RSS_URL = "https://events.yolocountylibrary.org/rss.php?iid=6754&m=month&cid=21064"

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from RSS feed."""
        self.logger.info(f"Fetching {self.RSS_URL}")
        
        feed = feedparser.parse(self.RSS_URL)
        self.logger.info(f"Found {len(feed.entries)} entries in RSS feed")

        events = []
        for entry in feed.entries:
            event = self._parse_entry(entry)
            if event:
                events.append(event)

        self.logger.info(f"Filtered to {len(events)} Davis-area events")
        return events

    def _parse_entry(self, entry: dict) -> Optional[dict[str, Any]]:
        """Parse a single RSS entry into event data."""
        try:
            # Get campus/branch from libcal namespace
            campus = getattr(entry, 'libcal_campus', '') or ''
            
            # Filter to Davis-area branches
            is_davis = any(branch.lower() in campus.lower() for branch in DAVIS_BRANCHES)
            if not is_davis and 'davis' not in campus.lower():
                return None

            title = entry.get('title', '')
            if not title:
                return None

            # Parse date and time from libcal namespace
            date_str = getattr(entry, 'libcal_date', '')
            start_str = getattr(entry, 'libcal_start', '')
            end_str = getattr(entry, 'libcal_end', '')

            if not date_str or not start_str:
                return None

            tz = ZoneInfo(self.timezone)
            dt_start = datetime.strptime(f"{date_str} {start_str}", "%Y-%m-%d %H:%M:%S")
            dt_start = dt_start.replace(tzinfo=tz)

            dt_end = None
            if end_str:
                dt_end = datetime.strptime(f"{date_str} {end_str}", "%Y-%m-%d %H:%M:%S")
                dt_end = dt_end.replace(tzinfo=tz)

            # Location
            location_room = getattr(entry, 'libcal_location', '') or ''
            location = f"{location_room}, {campus}" if location_room else campus

            # Description - use libcal description, clean HTML
            description = getattr(entry, 'libcal_description', '') or ''
            description = html.unescape(description)
            description = re.sub(r'<[^>]+>', '', description)  # Strip HTML tags
            description = description.strip()

            url = entry.get('link', '')

            event = {
                'title': title,
                'dtstart': dt_start,
                'dtend': dt_end,
                'location': location,
                'description': description,
                'url': url,
            }

            self.logger.info(f"Found event: {title} at {campus}")
            return event

        except Exception as e:
            self.logger.warning(f"Error parsing entry: {e}")
            return None


if __name__ == '__main__':
    YoloLibraryScraper.main()
