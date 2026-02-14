#!/usr/bin/env python3
"""
Mercury Theater Petaluma - scrapes events via Squarespace JSON API

Mercury Theater is at 3333 Petaluma Blvd N (the former Cinnabar Theater space).
Their site is Squarespace, which exposes a JSON API at ?format=json-pretty.
"""

import json
import re
import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

from datetime import datetime, timezone
from typing import Any
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

from lib.base import BaseScraper

EVENTS_URL = "https://www.mercurytheater.org/mercury-theater-calendar?format=json-pretty"
VENUE_NAME = "Mercury Theater"
VENUE_ADDRESS = "3333 Petaluma Blvd N, Petaluma, CA 94952"


class MercuryTheaterScraper(BaseScraper):
    name = "Mercury Theater"
    domain = "mercurytheater.org"

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from Squarespace JSON API."""
        self.logger.info(f"Fetching {EVENTS_URL}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; CommunityCalendar/1.0)',
            'Accept': 'application/json',
        }
        req = Request(EVENTS_URL, headers=headers)
        try:
            with urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode('utf-8'))
        except (HTTPError, URLError, json.JSONDecodeError) as e:
            self.logger.error(f"Failed to fetch: {e}")
            return []

        events = []
        upcoming = data.get('upcoming', data.get('items', []))

        for item in upcoming:
            title = item.get('title', 'Untitled')
            start_ms = item.get('startDate')
            if not start_ms:
                continue

            dtstart = datetime.fromtimestamp(start_ms / 1000, tz=timezone.utc)

            end_ms = item.get('endDate')
            dtend = datetime.fromtimestamp(end_ms / 1000, tz=timezone.utc) if end_ms else None

            body = item.get('body', '') or ''
            desc = re.sub(r'<[^>]+>', ' ', body).strip()
            desc = re.sub(r'\s+', ' ', desc)

            location_data = item.get('location', {})
            if isinstance(location_data, dict):
                loc_str = location_data.get('addressLine1', VENUE_ADDRESS)
            else:
                loc_str = VENUE_ADDRESS

            full_url = item.get('fullUrl', '')
            if full_url and not full_url.startswith('http'):
                full_url = f"https://www.mercurytheater.org{full_url}"

            events.append({
                'title': title,
                'dtstart': dtstart,
                'dtend': dtend,
                'description': desc,
                'location': f"{VENUE_NAME}, {loc_str}",
                'url': full_url,
            })

        self.logger.info(f"Found {len(events)} upcoming events")
        return events


if __name__ == '__main__':
    MercuryTheaterScraper.main()
