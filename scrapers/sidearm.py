#!/usr/bin/env python3
"""
Scraper for Sidearm Sports athletics schedules.

Tries the v3 Calendar API first (/api/v2/Calendar), which provides structured
game data with home/away indicators. Falls back to JSON-LD SportsEvent
scraping from schedule pages for older Sidearm installations.

Usage:
    # All sports, home games only (v3 API):
    python scrapers/sidearm.py \
        --base-url https://iuhoosiers.com \
        --name "IU Athletics" \
        --timezone America/Indiana/Indianapolis \
        --home-only \
        --output cities/bloomington/iu_athletics.ics

    # All sports via JSON-LD fallback:
    python scrapers/sidearm.py \
        --base-url https://godiplomats.com \
        --name "F&M Athletics" \
        --home-only \
        --output cities/lancaster/fandm_athletics.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Optional
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from zoneinfo import ZoneInfo

from lib.base import BaseScraper
from lib.utils import DEFAULT_HEADERS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SidearmScraper(BaseScraper):
    """Scraper for Sidearm Sports athletics schedules."""

    domain = "sidearm"

    def __init__(self, base_url: str, source_name: str, tz: str = "America/New_York",
                 home_only: bool = False):
        self.base_url = base_url.rstrip('/')
        self.name = source_name
        self.domain = base_url.split('/')[2]
        self.timezone = tz
        self.home_only = home_only
        self.tz = ZoneInfo(tz)
        super().__init__()

    def fetch_events(self) -> list[dict[str, Any]]:
        """Try v3 API first, fall back to JSON-LD scraping."""
        events = self._fetch_v3_api()
        if events is not None:
            return events
        self.logger.info("v3 API not available, falling back to JSON-LD scraping")
        return self._fetch_jsonld()

    # ── v3 Calendar API path ──────────────────────────────────────────

    def _fetch_v3_api(self) -> Optional[list[dict[str, Any]]]:
        """Fetch from /api/v2/Calendar. Returns None if endpoint doesn't exist."""
        now = datetime.now(self.tz)
        end = now + timedelta(days=180)
        start_str = now.strftime("%-m-%-d-%Y")
        end_str = end.strftime("%-m-%-d-%Y")

        url = f"{self.base_url}/api/v2/Calendar/from/{start_str}/to/{end_str}"
        self.logger.info(f"Trying v3 API: {url}")

        try:
            req = Request(url, headers={
                'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0 (compatible; community-calendar/1.0)',
            })
            with urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
        except (HTTPError, URLError):
            return None

        events = []
        for day in data:
            for e in day.get('events', []):
                parsed = self._parse_api_event(e, day.get('date', ''))
                if parsed:
                    events.append(parsed)

        self.logger.info(f"v3 API: {len(events)} events")
        return events

    def _parse_api_event(self, e: dict, day_date: str) -> Optional[dict[str, Any]]:
        """Parse a v3 API game event."""
        opponent = e.get('opponent', {})
        opponent_name = opponent.get('title', '')
        sport_data = e.get('sport', {})
        sport = sport_data.get('title', '') if isinstance(sport_data, dict) else ''
        location_indicator = e.get('locationIndicator', '')

        if self.home_only and location_indicator == 'A':
            return None
        if e.get('status') != 'A':
            return None

        at_vs = e.get('atVs', 'vs')
        if sport and opponent_name:
            title = f"{sport} {at_vs} {opponent_name}"
        elif sport:
            title = sport
        elif opponent_name:
            title = f"{at_vs} {opponent_name}"
        else:
            return None

        dtstart = self._parse_api_datetime(day_date, e.get('time', ''))
        if not dtstart:
            return None

        location = e.get('location', '')
        url = ''
        opponent_website = opponent.get('website', '')
        if location_indicator != 'A' and opponent_website:
            url = opponent_website

        image_url = e.get('gameImageUrl', '') or ''
        event = {
            'title': title,
            'dtstart': dtstart,
            'url': url,
            'location': location,
            'description': '',
        }
        if image_url:
            event['image_url'] = image_url
        return event

    def _parse_api_datetime(self, day_date: str, time_str: str) -> Optional[datetime]:
        """Parse date from API and time string like '7 p.m.'."""
        try:
            dt = datetime.fromisoformat(day_date.replace('Z', '+00:00'))
            dt = dt.replace(tzinfo=None)
        except (ValueError, AttributeError):
            return None

        if time_str:
            time_str = time_str.strip().lower()
            if time_str in ('noon', '12 p.m.'):
                dt = dt.replace(hour=12, minute=0)
            elif time_str in ('tba', 'tbd', ''):
                dt = dt.replace(hour=12, minute=0)
            else:
                time_str = time_str.replace('.', '').replace(' ', '')
                try:
                    if ':' in time_str:
                        t = datetime.strptime(time_str, "%I:%M%p")
                    else:
                        t = datetime.strptime(time_str, "%I%p")
                    dt = dt.replace(hour=t.hour, minute=t.minute)
                except ValueError:
                    dt = dt.replace(hour=12, minute=0)

        return dt.replace(tzinfo=self.tz)

    # ── JSON-LD fallback path ─────────────────────────────────────────

    def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch a page and return its text content."""
        try:
            req = Request(url, headers=DEFAULT_HEADERS)
            with urlopen(req, timeout=30) as resp:
                return resp.read().decode('utf-8', errors='replace')
        except (HTTPError, URLError) as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return None

    def _discover_sports(self) -> list[str]:
        """Discover available sports from the site's navigation."""
        html = self._fetch_page(self.base_url)
        if not html:
            return []
        slugs = re.findall(r'/sports/([\w-]+)/schedule', html)
        seen = set()
        unique = []
        for s in slugs:
            if s not in seen:
                seen.add(s)
                unique.append(s)
        logger.info(f"Discovered {len(unique)} sports: {', '.join(unique)}")
        return unique

    def _extract_jsonld(self, html: str) -> list[dict]:
        """Extract JSON-LD SportsEvent objects from HTML."""
        events = []
        for match in re.finditer(
            r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            html, re.DOTALL
        ):
            try:
                data = json.loads(match.group(1))
                if isinstance(data, list):
                    events.extend(e for e in data if e.get('@type') == 'SportsEvent')
                elif isinstance(data, dict) and data.get('@type') == 'SportsEvent':
                    events.append(data)
            except json.JSONDecodeError:
                continue
        return events

    def _fetch_jsonld(self) -> list[dict[str, Any]]:
        """Fetch events by scraping JSON-LD from schedule pages."""
        sports = self._discover_sports()
        if not sports:
            logger.error("No sports found to scrape")
            return []

        all_events = []
        for sport in sports:
            url = f"{self.base_url}/sports/{sport}/schedule"
            logger.info(f"Fetching {sport}: {url}")
            html = self._fetch_page(url)
            if not html:
                continue
            jsonld_events = self._extract_jsonld(html)
            logger.info(f"  {sport}: {len(jsonld_events)} events")
            for je in jsonld_events:
                event = self._parse_jsonld_event(je)
                if event:
                    all_events.append(event)

        logger.info(f"JSON-LD: {len(all_events)} events across {len(sports)} sports")
        return all_events

    def _parse_jsonld_event(self, data: dict) -> Optional[dict[str, Any]]:
        """Parse a JSON-LD SportsEvent into our event dict format."""
        title = data.get('name', '')
        if not title:
            return None

        start_str = data.get('startDate')
        if not start_str:
            return None

        try:
            dt = datetime.fromisoformat(start_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=self.tz)
        except ValueError:
            return None

        if dt < datetime.now(self.tz):
            return None

        # Home/away detection for JSON-LD: homeTeam name matches site domain,
        # and home games have the school listed as homeTeam with local address
        if self.home_only:
            home_team = data.get('homeTeam', {})
            away_team = data.get('awayTeam', {})
            home_name = home_team.get('name', '') if isinstance(home_team, dict) else ''
            away_name = away_team.get('name', '') if isinstance(away_team, dict) else ''
            # If our team is listed as awayTeam, skip (we're visiting)
            # Sidearm always lists the site's school as homeTeam for home games
            # For away games, the school is still homeTeam but location is elsewhere
            # Best heuristic: check if location address matches a different city
            loc_data = data.get('location', {})
            if isinstance(loc_data, dict):
                addr = loc_data.get('address', {})
                if isinstance(addr, dict):
                    street = addr.get('streetAddress', '')
                    # Away games have location like "City, State" that differs from home
                    loc_name = loc_data.get('name', '')
                    # If location name doesn't contain a campus venue name,
                    # it's likely an away game (e.g., "Hampden Sydney, Va.")
                    # Skip if the location looks like "City, State" (no comma in venue names)
                    if loc_name and ',' not in loc_name:
                        pass  # Looks like a venue name = home game
                    elif loc_name and home_name and home_name.lower() not in loc_name.lower():
                        return None  # Away game

        location = ''
        loc_data = data.get('location', {})
        if isinstance(loc_data, dict):
            location = loc_data.get('name', '')
            addr = loc_data.get('address', {})
            if isinstance(addr, dict):
                street = addr.get('streetAddress', '')
                if street and street != location:
                    location = f"{location}, {street}" if location else street

        url = data.get('url') or ''
        description = data.get('description', '')

        return {
            'title': title,
            'dtstart': dt,
            'dtend': dt,
            'location': location,
            'url': url,
            'description': description,
        }


def main():
    parser = argparse.ArgumentParser(description="Scrape Sidearm Sports athletics schedules")
    parser.add_argument('--base-url', required=True, help='Athletics site base URL')
    parser.add_argument('--name', default='Athletics', help='Source name')
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--timezone', default='America/New_York', help='Timezone')
    parser.add_argument('--home-only', action='store_true', help='Only include home games')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = SidearmScraper(
        base_url=args.base_url,
        source_name=args.name,
        tz=args.timezone,
        home_only=args.home_only,
    )
    scraper.run(args.output)


if __name__ == '__main__':
    main()
