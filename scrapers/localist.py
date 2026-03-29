#!/usr/bin/env python3
"""
Scraper for Localist-powered event calendars (e.g., events.in.gov).

Localist provides a JSON API at /api/2/events with filtering by venue_id,
group_id, or other parameters. Each event has instances (dates) and full
metadata including location, description, and geo coordinates.

Usage:
    python scrapers/localist.py \
        --base-url "https://events.in.gov" \
        --venue-id 35217665860404 \
        --name "McCormick's Creek State Park" \
        --output cities/bloomington/localist_mccormicks_creek.ics

    python scrapers/localist.py \
        --base-url "https://events.in.gov" \
        --venue-id 35217662417669 \
        --name "Brown County State Park" \
        --output cities/bloomington/localist_brown_county_sp.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import json
import logging
import re
from datetime import datetime
from typing import Any, Optional
from urllib.parse import urlencode
from urllib.request import urlopen, Request

from lib.base import BaseScraper


class LocalistScraper(BaseScraper):
    name = "Localist"
    domain = "localist.com"
    timezone = "America/Indiana/Indianapolis"

    def __init__(self, base_url: str, name: str, venue_id: str = None,
                 group_id: str = None, days: int = 90):
        super().__init__()
        self.base_url = base_url.rstrip('/')
        self.name = name
        self.domain = re.sub(r'https?://', '', base_url).split('/')[0]
        self.venue_id = venue_id
        self.group_id = group_id
        self.days = days

    def _fetch_api(self, page: int = 1) -> dict:
        """Fetch one page of events from the Localist API."""
        params = {
            'pp': 100,
            'page': page,
            'days': self.days,
        }
        if self.venue_id:
            params['venue_id'] = self.venue_id
        if self.group_id:
            params['group_id'] = self.group_id

        url = f"{self.base_url}/api/2/events?{urlencode(params)}"
        self.logger.debug(f"Fetching {url}")
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0 CommunityCalendar/1.0'})
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())

    def _clean_html(self, html: str) -> str:
        """Strip HTML tags to plain text."""
        if not html:
            return ''
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def fetch_events(self) -> list[dict[str, Any]]:
        events = []
        page = 1

        while True:
            data = self._fetch_api(page)
            raw_events = data.get('events', [])
            if not raw_events:
                break

            for item in raw_events:
                evt = item.get('event', {})
                title = evt.get('title', '').strip()
                if not title:
                    continue

                # Each event can have multiple instances (dates)
                for inst_wrapper in evt.get('event_instances', []):
                    inst = inst_wrapper.get('event_instance', {})
                    start_str = inst.get('start')
                    end_str = inst.get('end')
                    if not start_str:
                        continue

                    dtstart = datetime.fromisoformat(start_str)
                    dtend = datetime.fromisoformat(end_str) if end_str else dtstart

                    # Build location string
                    location_parts = []
                    if evt.get('location_name'):
                        location_parts.append(evt['location_name'])
                    if evt.get('room_number'):
                        location_parts.append(evt['room_number'])
                    if evt.get('address'):
                        location_parts.append(evt['address'])
                    location = ', '.join(location_parts)

                    # Description
                    description = self._clean_html(evt.get('description', ''))

                    # URL
                    url = evt.get('url') or evt.get('localist_url', '')

                    events.append({
                        'title': title,
                        'dtstart': dtstart,
                        'dtend': dtend,
                        'url': url,
                        'location': location,
                        'description': description,
                    })

            # Check for more pages
            page_info = data.get('page', {})
            total = page_info.get('total', 0)
            current = page_info.get('current', page)
            size = page_info.get('size', 100)
            if current * size >= total:
                break
            page += 1

        return events


def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    parser = argparse.ArgumentParser(description='Scrape Localist events')
    parser.add_argument('--base-url', required=True, help='Localist base URL (e.g., https://events.in.gov)')
    parser.add_argument('--venue-id', help='Filter by venue ID')
    parser.add_argument('--group-id', help='Filter by group ID')
    parser.add_argument('--name', required=True, help='Source display name')
    parser.add_argument('--days', type=int, default=90, help='Days ahead to fetch (default: 90)')
    parser.add_argument('--output', '-o', required=True, help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = LocalistScraper(
        base_url=args.base_url,
        name=args.name,
        venue_id=args.venue_id,
        group_id=args.group_id,
        days=args.days,
    )
    scraper.run(args.output)


if __name__ == '__main__':
    main()
