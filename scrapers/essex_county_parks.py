#!/usr/bin/env python3
"""
Scraper for Essex County Parks calendar.

The Essex County Parks website uses a FullCalendar JSON endpoint that accepts
start/end date parameters and returns structured event data.

Usage:
    python scrapers/essex_county_parks.py --output cities/montclair/essex_county_parks.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Optional
from urllib.request import urlopen, Request

from lib.base import BaseScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "https://essexcountyparks.org"
CALENDAR_URL = f"{BASE_URL}/calendar.json/general"


class EssexCountyParksScraper(BaseScraper):
    """Scraper for Essex County Parks via FullCalendar JSON API."""

    name = "Essex County Parks"
    domain = "essexcountyparks.org"
    timezone = "America/New_York"

    # Skip "Golf Course Closed/Open" and "NO PUBLIC SESSIONS" non-events
    SKIP_PATTERNS = [
        "golf course closed",
        "golf course id unit",
        "no public session",
        "no learn to skate",
        "no 11:45",
    ]

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from the FullCalendar JSON endpoint."""
        start = datetime.now().strftime("%Y-%m-%d")
        end = (datetime.now() + timedelta(days=self.months_ahead * 31)).strftime("%Y-%m-%d")
        url = f"{CALENDAR_URL}?start={start}&end={end}"

        self.logger.info(f"Fetching {url}")
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urlopen(req, timeout=30)
        data = json.loads(resp.read())
        self.logger.info(f"Got {len(data)} raw events")

        events = []
        for item in data:
            title = item.get("title", "").strip()

            # Skip non-event entries
            if any(pat in title.lower() for pat in self.SKIP_PATTERNS):
                continue

            start_str = item.get("start", "")
            if not start_str:
                continue

            dtstart = datetime.fromisoformat(start_str)

            end_str = item.get("end", "")
            dtend = datetime.fromisoformat(end_str) if end_str else None

            # Build full URL from relative path
            rel_url = item.get("url", "")
            event_url = f"{BASE_URL}/{rel_url}" if rel_url else BASE_URL

            # Derive location from className
            class_name = item.get("className", "")
            location = self._location_from_class(class_name)

            events.append({
                "title": title,
                "dtstart": dtstart,
                "dtend": dtend,
                "url": event_url,
                "location": location,
                "description": "",
            })

        self.logger.info(f"Filtered to {len(events)} events")
        return events

    @staticmethod
    def _location_from_class(class_name: str) -> str:
        """Map CSS class names to human-readable locations."""
        loc_map = {
            "loc-codey-arena": "Codey Arena, South Mountain Recreation Complex, West Orange, NJ",
            "loc-environmental-center": "Essex County Environmental Center, 621 Eagle Rock Ave, Roseland, NJ",
            "loc-branch-brook-park": "Branch Brook Park, Newark/Belleville, NJ",
            "loc-turtle-back-zoo": "Turtle Back Zoo, West Orange, NJ",
            "loc-south-mountain": "South Mountain Reservation, West Orange/Millburn, NJ",
            "loc-eagle-rock": "Eagle Rock Reservation, West Orange, NJ",
        }
        for part in class_name.split():
            if part in loc_map:
                return loc_map[part]
        return "Essex County Parks, NJ"


def main():
    parser = argparse.ArgumentParser(description="Scrape Essex County Parks events")
    parser.add_argument("--output", "-o", help="Output ICS file")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = EssexCountyParksScraper()
    scraper.run(args.output)


if __name__ == "__main__":
    main()
