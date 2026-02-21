#!/usr/bin/env python3
"""
Scraper for MaxPreps high school athletics events.

MaxPreps embeds event data in __NEXT_DATA__ JSON. This scraper extracts
the initSchoolContests data which contains upcoming and recent games.

Usage:
    # Using known school shortnames:
    python scrapers/maxpreps.py --school petaluma-trojans --output events.ics
    python scrapers/maxpreps.py --school casa-grande-gauchos --output events.ics
    
    # Using any MaxPreps school URL:
    python scrapers/maxpreps.py --url "https://www.maxpreps.com/ca/davis/davis-blue-devils/events/" --name "Davis High" -o davis.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import json
import re
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import requests

from lib.base import BaseScraper
from lib.utils import DEFAULT_HEADERS


PACIFIC = ZoneInfo('America/Los_Angeles')
EASTERN = ZoneInfo('America/Indiana/Indianapolis')

# Known schools - add more as needed
# URL pattern: https://www.maxpreps.com/{state}/{city}/{school-mascot}/events/
KNOWN_SCHOOLS = {
    # Petaluma
    'petaluma-trojans': {
        'name': 'Petaluma High School',
        'url': 'https://www.maxpreps.com/ca/petaluma/petaluma-trojans/events/',
        'location': 'Petaluma High School, 201 Fair St, Petaluma, CA 94952',
        'timezone': PACIFIC,
    },
    'casa-grande-gauchos': {
        'name': 'Casa Grande High School', 
        'url': 'https://www.maxpreps.com/ca/petaluma/casa-grande-gauchos/events/',
        'location': 'Casa Grande High School, 333 Casa Grande Rd, Petaluma, CA 94954',
        'timezone': PACIFIC,
    },
    # Santa Rosa
    'santa-rosa-panthers': {
        'name': 'Santa Rosa High School',
        'url': 'https://www.maxpreps.com/ca/santa-rosa/santa-rosa-panthers/events/',
        'location': 'Santa Rosa High School, 1235 Mendocino Ave, Santa Rosa, CA',
        'timezone': PACIFIC,
    },
    'montgomery-vikings': {
        'name': 'Montgomery High School',
        'url': 'https://www.maxpreps.com/ca/santa-rosa/montgomery-vikings/events/',
        'location': 'Montgomery High School, 1250 Hahman Dr, Santa Rosa, CA',
        'timezone': PACIFIC,
    },
    'maria-carrillo-pumas': {
        'name': 'Maria Carrillo High School',
        'url': 'https://www.maxpreps.com/ca/santa-rosa/maria-carrillo-pumas/events/',
        'location': 'Maria Carrillo High School, 6975 Montecito Blvd, Santa Rosa, CA',
        'timezone': PACIFIC,
    },
    'piner-prospectors': {
        'name': 'Piner High School',
        'url': 'https://www.maxpreps.com/ca/santa-rosa/piner-prospectors/events/',
        'location': 'Piner High School, 1700 Fulton Rd, Santa Rosa, CA',
        'timezone': PACIFIC,
    },
    'elsie-allen-lobos': {
        'name': 'Elsie Allen High School',
        'url': 'https://www.maxpreps.com/ca/santa-rosa/elsie-allen-lobos/events/',
        'location': 'Elsie Allen High School, 599 Bellevue Ave, Santa Rosa, CA',
        'timezone': PACIFIC,
    },
    'cardinal-newman-cardinals': {
        'name': 'Cardinal Newman High School',
        'url': 'https://www.maxpreps.com/ca/santa-rosa/cardinal-newman-cardinals/events/',
        'location': 'Cardinal Newman High School, 50 Ursuline Rd, Santa Rosa, CA',
        'timezone': PACIFIC,
    },
    # Davis
    'davis-blue-devils': {
        'name': 'Davis Senior High School',
        'url': 'https://www.maxpreps.com/ca/davis/davis-blue-devils/events/',
        'location': 'Davis Senior High School, 315 W 14th St, Davis, CA',
        'timezone': PACIFIC,
    },
    # Bloomington
    'bloomington-south-panthers': {
        'name': 'Bloomington South High School',
        'url': 'https://www.maxpreps.com/in/bloomington/bloomington-south-panthers/events/',
        'location': 'Bloomington South High School, 1965 S Walnut St, Bloomington, IN',
        'timezone': EASTERN,
    },
    'bloomington-north-cougars': {
        'name': 'Bloomington North High School',
        'url': 'https://www.maxpreps.com/in/bloomington/bloomington-north-cougars/events/',
        'location': 'Bloomington North High School, 10750 N Kinser Pike, Bloomington, IN',
        'timezone': EASTERN,
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
        self.timezone = school_config.get('timezone', PACIFIC)

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from MaxPreps school page."""
        self.logger.info(f"Fetching {self.url}")
        
        response = requests.get(self.url, headers=DEFAULT_HEADERS, timeout=30)
        response.raise_for_status()
        
        return self._parse_next_data(response.text)

    def _parse_next_data(self, html: str) -> list[dict[str, Any]]:
        """Extract events from __NEXT_DATA__ JSON."""
        events = []
        
        # Find __NEXT_DATA__ script
        match = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>([^<]+)</script>', html)
        if not match:
            self.logger.warning("No __NEXT_DATA__ found in page")
            return events
        
        try:
            data = json.loads(match.group(1))
            page_props = data.get('props', {}).get('pageProps', {})
            contests = page_props.get('initSchoolContests', [])
            
            self.logger.info(f"Found {len(contests)} contests in __NEXT_DATA__")
            
            for contest in contests:
                parsed = self._parse_contest(contest)
                if parsed:
                    events.append(parsed)
                    self.logger.info(f"Found event: {parsed['title']} on {parsed['dtstart']}")
                    
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse __NEXT_DATA__ JSON: {e}")
        
        return events

    def _parse_contest(self, contest: dict) -> dict[str, Any] | None:
        """Parse a single contest from initSchoolContests."""
        # Get the title (e.g., "Santa Rosa Girls Varsity Basketball vs. Branson")
        title = contest.get('title', '')
        if not title:
            return None
        
        # Get date - format: "2026-02-21T19:00:00" (local time)
        date_str = contest.get('date')
        if not date_str:
            return None
        
        # Parse datetime (local time, no timezone info)
        try:
            # The date is in local time for the school
            dtstart = datetime.fromisoformat(date_str)
            dtstart = dtstart.replace(tzinfo=self.timezone)
        except (ValueError, TypeError):
            return None
        
        # Filter out past events (only include future or today's events)
        now = datetime.now(self.timezone)
        if dtstart.date() < now.date():
            return None
        
        # End time - use contestLength (minutes) if available
        contest_length = contest.get('contestLength', 90)  # default 90 min
        dtend = dtstart + timedelta(minutes=contest_length)
        
        # Location
        location = contest.get('location', self.default_location)
        if not location or location == 'TBA':
            location = self.default_location
        
        # Build description
        description_parts = []
        
        # Sport and level
        sport = contest.get('sport', '')
        gender = contest.get('gender', '')
        level = contest.get('teamLevel', '')
        if sport:
            sport_str = f"{gender} {level} {sport}".strip()
            description_parts.append(sport_str)
        
        # Tournament info
        tournament = contest.get('tournamentName', '')
        if tournament:
            description_parts.append(f"Tournament: {tournament}")
        
        # Contest description from MaxPreps
        desc = contest.get('description', '')
        if desc:
            description_parts.append(desc)
        
        description = '\n'.join(description_parts)
        
        # URL
        url = contest.get('canonicalUrl', '')
        
        # Tickets (GoFan)
        gofan_url = contest.get('goFanUrl', '')
        if gofan_url:
            description += f"\n\nTickets: {gofan_url}"
        
        return {
            'title': title,
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
    parser.add_argument('--list-schools', action='store_true',
                        help='List all known schools')
    
    args = parser.parse_args()
    
    if args.list_schools:
        print("Known schools:")
        for key, config in KNOWN_SCHOOLS.items():
            print(f"  {key}: {config['name']}")
        return
    
    if args.url:
        config = {
            'name': args.name,
            'url': args.url,
            'location': '',
            'timezone': PACIFIC,
        }
    elif args.school:
        config = KNOWN_SCHOOLS[args.school]
    else:
        parser.error('Either --school or --url is required')
    
    scraper = MaxPrepsScraper(config)
    scraper.run(args.output)


if __name__ == '__main__':
    main()
