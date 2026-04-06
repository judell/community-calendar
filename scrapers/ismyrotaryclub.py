#!/usr/bin/env python3
"""
Scraper for Rotary club events via the ismyrotaryclub.com / DACdb API.

The API returns FullCalendar-compatible JSON with title, start, end,
Speaker, Topic, Location, and event URL.

Usage:
    python scrapers/ismyrotaryclub.py \
        --club-id 3430 --account-id 6580 --name "Bloomington Rotary Club" \
        --output cities/bloomington/bloomington_rotary.ics

    python scrapers/ismyrotaryclub.py \
        --club-id 52230 --account-id 6580 --name "Bloomington Sunrise Rotary" \
        --output cities/bloomington/bloomington_sunrise_rotary.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import json
import logging
import re
from datetime import datetime
from typing import Any, Optional
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

from lib.base import BaseScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_BASE = "https://www.ismyrotaryclub.com/wp_api_prod_1-1"


def strip_html(text: str) -> str:
    """Remove HTML tags and collapse whitespace."""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


class IsMyRotaryClubScraper(BaseScraper):
    """Scraper for Rotary club events via ismyrotaryclub.com JSON API."""

    name = "Rotary Club"
    domain = "ismyrotaryclub.com"
    timezone = "America/Indiana/Indianapolis"

    def __init__(self, club_id: str, account_id: str, source_name: Optional[str] = None,
                 tz: Optional[str] = None):
        super().__init__()
        self.club_id = club_id
        self.account_id = account_id
        if source_name:
            self.name = source_name
        if tz:
            self.timezone = tz

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from the ismyrotaryclub.com JSON API."""
        url = (f"{API_BASE}/R_GetEvents.cfm"
               f"?AccountID={self.account_id}"
               f"&ClubID={self.club_id}"
               f"&fixImages=0&fixTables=0"
               f"&EventCategoryIDs=1,2,3,4,5,6,7")

        req = Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; CommunityCalendar/1.0)',
        })

        try:
            with urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode('utf-8'))
        except (HTTPError, URLError) as e:
            self.logger.warning(f"Failed to fetch events: {e}")
            return []

        self.logger.info(f"Fetched {len(data)} events for club {self.club_id}")

        events = []
        for item in data:
            event = self._parse_event(item)
            if event:
                events.append(event)

        return events

    def _parse_event(self, item: dict) -> Optional[dict[str, Any]]:
        """Parse a single event from the API response."""
        title = item.get('title', '').strip()
        if not title:
            return None

        start_str = item.get('start')
        if not start_str:
            return None

        try:
            dtstart = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            return None

        dtend = None
        end_str = item.get('end')
        if end_str:
            try:
                dtend = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                pass

        # Build description from Speaker and Topic
        parts = []
        speaker = item.get('Speaker', '').strip()
        topic = item.get('Topic', '').strip()
        if speaker:
            parts.append(f"Speaker: {speaker}")
        if topic:
            parts.append(f"Topic: {topic}")
        description = '\n'.join(parts)

        # Clean HTML from location
        location = strip_html(item.get('Location', '')) or None

        event_url = item.get('url')

        return {
            'title': title,
            'dtstart': dtstart,
            'dtend': dtend,
            'description': description,
            'location': location,
            'url': event_url,
        }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scrape Rotary club events from ismyrotaryclub.com')
    parser.add_argument('--club-id', required=True, help='DACdb Club ID')
    parser.add_argument('--account-id', required=True, help='DACdb Account ID')
    parser.add_argument('--name', required=True, help='Source name (e.g. "Bloomington Rotary Club")')
    parser.add_argument('--output', '-o', type=str, help='Output filename')
    parser.add_argument('--default-url', type=str, help='Fallback URL for events without per-event URLs')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = IsMyRotaryClubScraper(
        club_id=args.club_id,
        account_id=args.account_id,
        source_name=args.name,
    )
    if args.default_url:
        scraper.default_url = args.default_url

    scraper.run(output=args.output)
