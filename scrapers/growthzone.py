#!/usr/bin/env python3
"""
Scraper for GrowthZone/ChamberMaster event calendars.

GrowthZone is a common platform for Chamber of Commerce websites.
They expose an XML API at /api/events that returns event data.

Usage:
    python scrapers/growthzone.py --site petalumachamber --output events.ics
    python scrapers/growthzone.py --url https://business.example.com/api/events --output events.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import html
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import requests

from lib.base import BaseScraper
from lib.utils import DEFAULT_HEADERS


# Known GrowthZone sites
KNOWN_SITES = {
    'petalumachamber': {
        'name': 'Petaluma Chamber of Commerce',
        'api_url': 'https://business.petalumachamber.us/api/events',
        'base_url': 'https://business.petalumachamber.us',
        'timezone': 'America/Los_Angeles',
        'location': 'Petaluma, CA',
    },
    # Add more chambers as discovered
}


class GrowthZoneScraper(BaseScraper):
    """Scraper for GrowthZone/ChamberMaster event calendars."""

    name = "GrowthZone"
    domain = "growthzone.com"

    def __init__(self, site_config: dict):
        super().__init__()
        self.config = site_config
        self.name = site_config.get('name', 'GrowthZone Events')
        self.api_url = site_config['api_url']
        self.base_url = site_config.get('base_url', '')
        self.tz = ZoneInfo(site_config.get('timezone', 'America/Los_Angeles'))
        self.default_location = site_config.get('location', '')

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from GrowthZone XML API."""
        self.logger.info(f"Fetching {self.api_url}")
        
        response = requests.get(self.api_url, headers=DEFAULT_HEADERS, timeout=30)
        response.raise_for_status()
        
        return self._parse_xml(response.text)

    def _parse_xml(self, xml_content: str) -> list[dict[str, Any]]:
        """Parse events from GrowthZone XML response."""
        events = []
        
        root = ET.fromstring(xml_content)
        
        for event_elem in root.findall('EventDisplay'):
            try:
                event = self._parse_event(event_elem)
                if event:
                    events.append(event)
                    self.logger.info(f"Found event: {event['title']} on {event['dtstart']}")
            except Exception as e:
                self.logger.warning(f"Error parsing event: {e}")
                continue
        
        return events

    def _parse_event(self, elem: ET.Element) -> dict[str, Any] | None:
        """Parse a single EventDisplay element."""
        # Required fields
        name_elem = elem.find('Name')
        start_elem = elem.find('StartDate')
        
        if name_elem is None or start_elem is None:
            return None
        
        title = name_elem.text
        if not title:
            return None
        
        # Parse dates
        start_str = start_elem.text  # Format: 2026-02-16T00:00:00
        end_elem = elem.find('EndDate')
        end_str = end_elem.text if end_elem is not None else None
        
        try:
            dtstart = datetime.fromisoformat(start_str).replace(tzinfo=self.tz)
            dtend = datetime.fromisoformat(end_str).replace(tzinfo=self.tz) if end_str else None
        except (ValueError, TypeError):
            return None
        
        # Skip events too far in the past or future
        now = datetime.now(self.tz)
        if dtstart < now.replace(year=now.year - 1):
            return None
        if dtstart > now.replace(year=now.year + 2):
            return None
        
        # Optional fields
        description = ''
        desc_elem = elem.find('Description')
        if desc_elem is not None and desc_elem.text:
            # Clean HTML entities and tags
            description = html.unescape(desc_elem.text)
            description = re.sub(r'<[^>]+>', '', description)
            description = re.sub(r'\s+', ' ', description).strip()
        
        # Build URL from slug
        url = ''
        slug_elem = elem.find('Slug')
        if slug_elem is not None and slug_elem.text and self.base_url:
            url = f"{self.base_url}/events/details/{slug_elem.text}"
        
        # Location - GrowthZone doesn't always include location in API
        location = self.default_location
        
        # Check if all-day event
        is_all_day = elem.find('IsAllDayEvent')
        if is_all_day is not None and is_all_day.text == 'true':
            # For all-day events, use date only
            pass
        
        return {
            'title': title.strip(),
            'dtstart': dtstart,
            'dtend': dtend,
            'description': description[:1000] if description else '',
            'location': location,
            'url': url,
        }


def main():
    parser = argparse.ArgumentParser(description='Scrape GrowthZone/ChamberMaster events')
    parser.add_argument('--site', choices=list(KNOWN_SITES.keys()),
                        help='Known site to scrape')
    parser.add_argument('--url', help='Custom API URL (overrides --site)')
    parser.add_argument('--name', default='GrowthZone Events',
                        help='Calendar name for custom URL')
    parser.add_argument('--timezone', default='America/Los_Angeles',
                        help='Timezone for events')
    parser.add_argument('--output', '-o', required=True,
                        help='Output ICS file')
    
    args = parser.parse_args()
    
    if args.url:
        config = {
            'name': args.name,
            'api_url': args.url,
            'base_url': args.url.rsplit('/api/', 1)[0] if '/api/' in args.url else '',
            'timezone': args.timezone,
        }
    elif args.site:
        config = KNOWN_SITES[args.site]
    else:
        parser.error('Either --site or --url is required')
    
    scraper = GrowthZoneScraper(config)
    scraper.run(args.output)


if __name__ == '__main__':
    main()
