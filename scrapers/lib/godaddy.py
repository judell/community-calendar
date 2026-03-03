"""GoDaddy Website Builder calendar scraper library.

GoDaddy Website Builder sites with a calendar widget serve event data from a
JSON API at calendar.apps.secureserver.net. The API returns structured events
with title, description, location, start/end times, and allDay flag.

API URL pattern:
    https://calendar.apps.secureserver.net/v1/events/{website_id}/{section_id}/{widget_id}

To find IDs: open the site's calendar page in a browser, check network requests
for a GET to calendar.apps.secureserver.net.

Usage:
    from lib.godaddy import GoDaddyScraper

    class MyVenueScraper(GoDaddyScraper):
        name = "My Venue"
        domain = "myvenue.com"
        website_id = "850abeb2-..."
        section_id = "9c296a07-..."
        widget_id = "f33a9bca-..."
        default_location = "My Venue, 123 Main St, Anytown, CA"

    if __name__ == '__main__':
        MyVenueScraper.main()
"""

import html as html_mod
import re
from datetime import datetime, timezone
from typing import Any, Optional
from zoneinfo import ZoneInfo

import requests

from .base import BaseScraper
from .utils import DEFAULT_HEADERS


API_BASE = "https://calendar.apps.secureserver.net/v1/events"


class GoDaddyScraper(BaseScraper):
    """Base class for scrapers targeting GoDaddy Website Builder calendar widgets.

    Subclasses should set:
        name: str - Source name
        domain: str - Domain for UIDs
        website_id: str - GoDaddy website UUID
        section_id: str - Calendar section UUID
        widget_id: str - Calendar widget UUID
        default_location: str - Fallback location string
    """

    website_id: str = ''
    section_id: str = ''
    widget_id: str = ''
    default_location: str = ''

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from GoDaddy calendar API."""
        url = f"{API_BASE}/{self.website_id}/{self.section_id}/{self.widget_id}"
        self.logger.info(f"Fetching {url}")

        try:
            resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError) as e:
            self.logger.error(f"Failed to fetch: {e}")
            return []

        raw_events = data.get('events', [])
        self.logger.info(f"API returned {len(raw_events)} events")

        events = []
        for item in raw_events:
            parsed = self._parse_event(item)
            if parsed:
                events.append(parsed)

        self.logger.info(f"Parsed {len(events)} events")
        return events

    def _parse_event(self, item: dict) -> Optional[dict[str, Any]]:
        """Parse a single event from the GoDaddy API response."""
        title = item.get('title', '').strip()
        if not title:
            return None

        start_str = item.get('start', '')
        if not start_str:
            return None

        try:
            dtstart = datetime.fromisoformat(start_str)
        except (ValueError, TypeError):
            return None

        # Localize naive datetimes to the scraper's configured timezone
        if dtstart.tzinfo is None:
            tz = ZoneInfo(self.timezone) if isinstance(self.timezone, str) else self.timezone
            dtstart = dtstart.replace(tzinfo=tz)

        # Skip past events
        now = datetime.now(timezone.utc)
        if dtstart < now:
            return None

        dtend = None
        end_str = item.get('end', '')
        if end_str:
            try:
                dtend = datetime.fromisoformat(end_str)
                if dtend.tzinfo is None:
                    tz = ZoneInfo(self.timezone) if isinstance(self.timezone, str) else self.timezone
                    dtend = dtend.replace(tzinfo=tz)
            except (ValueError, TypeError):
                pass

        # Clean description: strip HTML tags, unescape entities
        desc = item.get('desc', '') or ''
        desc = html_mod.unescape(desc)
        desc = re.sub(r'<[^>]+>', ' ', desc).strip()
        desc = re.sub(r'\s+', ' ', desc)
        # Truncate very long descriptions (some GoDaddy calendar entries can be huge)
        if len(desc) > 500:
            desc = desc[:497] + '...'

        location = item.get('location', '').strip() or self.default_location

        return {
            'title': title,
            'dtstart': dtstart,
            'dtend': dtend,
            'location': location,
            'description': desc,
        }
