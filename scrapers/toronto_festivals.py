#!/usr/bin/env python3
"""
Scraper for City of Toronto Festivals & Events.
Data from Toronto Open Data CKAN portal (direct JSON download).
https://open.toronto.ca/dataset/festivals-events/
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

from datetime import datetime
from typing import Any, Optional
from zoneinfo import ZoneInfo

import requests

from lib.base import BaseScraper

TZ = ZoneInfo("America/Toronto")
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; community-calendar/1.0)'}

DATA_URL = (
    "https://ckan0.cf.opendata.inter.prod-toronto.ca/dataset/"
    "9201059e-43ed-4369-885e-0b867652feac/resource/"
    "8900fdb2-7f6c-4f50-8581-b463311ff05d/download/file.json"
)


class TorontoFestivalsScraper(BaseScraper):
    name = "City of Toronto Festivals & Events"
    domain = "toronto.ca"
    timezone = "America/Toronto"

    def fetch_events(self) -> list[dict[str, Any]]:
        self.logger.info(f"Fetching {DATA_URL}")
        resp = requests.get(DATA_URL, headers=HEADERS, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        # Data is {"value": [...]}
        records = data.get('value', data) if isinstance(data, dict) else data
        self.logger.info(f"Got {len(records)} records")

        now = datetime.now(TZ)
        events = []
        for record in records:
            event = self._map_record(record, now)
            if event:
                events.append(event)

        self.logger.info(f"Total: {len(events)} future events")
        return events

    def _map_record(self, record: dict, now: datetime) -> Optional[dict[str, Any]]:
        name = record.get('event_name') or record.get('short_name', '')
        if not name:
            return None

        # Parse dates
        start_str = record.get('event_startdate', '')
        end_str = record.get('event_enddate', '')

        dtstart = self._parse_iso(start_str)
        dtend = self._parse_iso(end_str)

        if not dtstart:
            return None

        # Filter to future events
        if dtend and dtend < now:
            return None
        elif not dtend and dtstart < now:
            return None

        # Location from event_locations array
        location = self._extract_location(record)

        # Build description
        desc_parts = []
        desc = record.get('event_description') or record.get('short_description', '')
        if desc:
            desc_parts.append(desc)
        categories = record.get('event_category', [])
        if categories:
            desc_parts.append(f"Categories: {', '.join(categories)}")
        price = record.get('event_price')
        if record.get('free_event') == 'Yes':
            desc_parts.append("Free event")
        elif price:
            desc_parts.append(f"Price: {price}")

        url = record.get('event_website', '')

        return {
            'title': name,
            'dtstart': dtstart,
            'dtend': dtend,
            'location': location,
            'url': url,
            'description': '\n'.join(desc_parts),
        }

    def _parse_iso(self, s: str) -> Optional[datetime]:
        if not s:
            return None
        try:
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=TZ)
            return dt
        except ValueError:
            self.logger.warning(f"Unparseable date: {s}")
            return None

    def _extract_location(self, record: dict) -> str:
        locations = record.get('event_locations', [])
        if not locations:
            return ''
        loc = locations[0]
        parts = []
        name = loc.get('location_name', '')
        addr = loc.get('location_address', '')
        if name:
            parts.append(name)
        if addr and addr != name:
            parts.append(addr)
        return ', '.join(parts) if parts else ''


if __name__ == '__main__':
    TorontoFestivalsScraper.main()
