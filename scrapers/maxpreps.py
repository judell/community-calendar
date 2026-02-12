#!/usr/bin/env python3
"""
Scraper for MaxPreps high school athletics events.

MaxPreps embeds JSON-LD structured data (schema.org HighSchool with events)
in their school pages. This scraper extracts that data.

Usage:
    python scrapers/maxpreps.py --school petaluma-trojans --output events.ics
    python scrapers/maxpreps.py --school casa-grande-gauchos --output events.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import json
import re
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import requests

from lib.base import BaseScraper
from lib.utils import DEFAULT_HEADERS


PACIFIC = ZoneInfo('America/Los_Angeles')

# Known schools
KNOWN_SCHOOLS = {
    'petaluma-trojans': {
        'name': 'Petaluma High School',
        'url': 'https://www.maxpreps.com/ca/petaluma/petaluma-trojans/events/',
        'location': 'Petaluma High School, 201 Fair St, Petaluma, CA 94952',
    },
    'casa-grande-gauchos': {
        'name': 'Casa Grande High School', 
        'url': 'https://www.maxpreps.com/ca/petaluma/casa-grande-gauchos/events/',
        'location': 'Casa Grande High School, 333 Casa Grande Rd, Petaluma, CA 94954',
    },
}


class MaxPrepsScraper(BaseScraper):
    """Scraper for MaxPreps high school athletics."""

    name = "MaxPreps"
    domain = "maxpreps.com"

    def __init__(self, school_config: dict):
        super().__init__()
        self.config = school_config
        self.name = school_config.get('name', 'MaxPreps')
        self.url = school_config['url']
        self.default_location = school_config.get('location', '')

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from MaxPreps school page."""
        self.logger.info(f"Fetching {self.url}")
        
        response = requests.get(self.url, headers=DEFAULT_HEADERS, timeout=30)
        response.raise_for_status()
        
        return self._parse_jsonld(response.text)

    def _parse_jsonld(self, html: str) -> list[dict[str, Any]]:
        """Extract events from JSON-LD structured data."""
        events = []
        
        # Find all JSON-LD blocks
        matches = re.findall(r'<script type="application/ld\+json">(.+?)</script>', html, re.DOTALL)
        
        for match in matches:
            try:
                data = json.loads(match)
                if data.get('@type') == 'HighSchool':
                    school_events = data.get('event', [])
                    for e in school_events:
                        parsed = self._parse_event(e)
                        if parsed:
                            events.append(parsed)
                            self.logger.info(f"Found event: {parsed['title']} on {parsed['dtstart']}")
            except json.JSONDecodeError:
                continue
        
        return events

    def _parse_event(self, event_data: dict) -> dict[str, Any] | None:
        """Parse a single event from JSON-LD."""
        name = event_data.get('name')
        start_str = event_data.get('startDate')
        
        if not name or not start_str:
            return None
        
        # Parse datetime
        try:
            # Format: 2026-02-14T19:00:00+00:00
            dtstart = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
            # Convert to Pacific time
            dtstart = dtstart.astimezone(PACIFIC)
        except (ValueError, TypeError):
            return None
        
        # End time
        end_str = event_data.get('endDate')
        if end_str:
            try:
                dtend = datetime.fromisoformat(end_str.replace('Z', '+00:00')).astimezone(PACIFIC)
            except (ValueError, TypeError):
                dtend = None
        else:
            dtend = None
        
        # Location
        location_data = event_data.get('location', {})
        if isinstance(location_data, dict):
            location = location_data.get('name', self.default_location)
            address = location_data.get('address', {})
            if isinstance(address, dict):
                addr_parts = [address.get('streetAddress', ''), 
                              address.get('addressLocality', ''),
                              address.get('addressRegion', '')]
                addr_str = ', '.join(p for p in addr_parts if p)
                if addr_str:
                    location = f"{location}, {addr_str}"
        else:
            location = self.default_location
        
        # Description
        description = event_data.get('description', '')
        sport = event_data.get('sport', '')
        if sport and sport not in description:
            description = f"[{sport}] {description}"
        
        # URL
        url = event_data.get('url', '')
        
        return {
            'title': name,
            'dtstart': dtstart,
            'dtend': dtend,
            'location': location,
            'description': description,
            'url': url,
        }


def main():
    parser = argparse.ArgumentParser(description='Scrape MaxPreps high school athletics')
    parser.add_argument('--school', choices=list(KNOWN_SCHOOLS.keys()),
                        help='Known school to scrape')
    parser.add_argument('--url', help='Custom MaxPreps events URL')
    parser.add_argument('--name', default='MaxPreps School',
                        help='School name for custom URL')
    parser.add_argument('--output', '-o', required=True,
                        help='Output ICS file')
    
    args = parser.parse_args()
    
    if args.url:
        config = {
            'name': args.name,
            'url': args.url,
            'location': '',
        }
    elif args.school:
        config = KNOWN_SCHOOLS[args.school]
    else:
        parser.error('Either --school or --url is required')
    
    scraper = MaxPrepsScraper(config)
    scraper.run(args.output)


if __name__ == '__main__':
    main()
