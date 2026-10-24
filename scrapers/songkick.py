#!/usr/bin/env python3
"""
Scraper for Songkick venue pages.

Songkick serves clean JSON-LD MusicEvent data on venue pages — artist-sourced
tour dates aggregated in one place. Single page fetch per venue.

Usage:
    python scrapers/songkick.py \
        --url "https://www.songkick.com/venues/32209-wellmont-theater" \
        --name "Wellmont Theater" \
        --output cities/montclair/songkick_wellmont.ics
"""

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

import argparse
import json
import logging
import re
from datetime import UTC, datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from lib.base import BaseScraper
from lib.timeutil import assume_utc

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml",
}


class SongkickScraper(BaseScraper):
    """Scraper for Songkick venue pages via JSON-LD MusicEvent data."""

    name = "Songkick"
    domain = "songkick.com"
    timezone = "America/New_York"

    def __init__(self, url: str, source_name: str | None = None):
        super().__init__()
        self.url = url
        if source_name:
            self.name = source_name

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch venue page and extract MusicEvent JSON-LD."""
        req = Request(self.url, headers=HEADERS)
        try:
            with urlopen(req, timeout=30) as resp:
                html = resp.read().decode("utf-8")
        except (HTTPError, URLError) as e:
            self.logger.warning(f"Failed to fetch {self.url}: {e}")
            return []
        self.mark_source_reached()

        now = datetime.now(UTC)
        events = []

        blocks = re.findall(
            r'<script\s+type="application/ld\+json">(.*?)</script>', html, re.DOTALL
        )

        for block_str in blocks:
            try:
                data = json.loads(block_str)
            except json.JSONDecodeError:
                continue

            items = data if isinstance(data, list) else [data]
            for item in items:
                if not isinstance(item, dict) or item.get("@type") != "MusicEvent":
                    continue

                start_str = item.get("startDate", "")
                if not start_str:
                    continue

                try:
                    dtstart = datetime.fromisoformat(start_str)
                except ValueError:
                    continue

                # Skip past events
                start_aware = assume_utc(dtstart)
                if start_aware < now:
                    continue

                # Build title from performer names (cleaner than "Artist @ Venue")
                performers = item.get("performer", [])
                if performers:
                    title = ", ".join(p.get("name", "") for p in performers if p.get("name"))
                else:
                    # Fall back to event name, strip " @ Venue" suffix
                    title = re.sub(r"\s*@\s*.+$", "", item.get("name", "Untitled"))

                # Location
                loc = item.get("location", {})
                if isinstance(loc, dict):
                    loc_name = loc.get("name", "")
                    addr = loc.get("address", {})
                    if isinstance(addr, dict):
                        parts = [
                            addr.get("streetAddress", ""),
                            addr.get("addressLocality", ""),
                            addr.get("addressRegion", ""),
                            addr.get("postalCode", ""),
                        ]
                        addr_str = ", ".join(p for p in parts if p)
                    else:
                        addr_str = str(addr)
                    location = (
                        f"{loc_name}, {addr_str}"
                        if loc_name and addr_str
                        else (loc_name or addr_str)
                    )
                else:
                    location = ""

                # URL — prefer offers URL (links to ticket purchase)
                event_url = item.get("url", "")
                offers = item.get("offers", [])
                if offers and isinstance(offers[0], dict):
                    event_url = offers[0].get("url", event_url)

                events.append(
                    {
                        "title": title,
                        "dtstart": dtstart,
                        "dtend": None,
                        "location": location,
                        "description": item.get("description", ""),
                        "url": event_url,
                    }
                )

        self.logger.info(f"Found {len(events)} future events from Songkick")
        return events


def main():
    parser = argparse.ArgumentParser(description="Scrape Songkick venue page")
    parser.add_argument("--url", required=True, help="Songkick venue URL")
    parser.add_argument("--name", default="Songkick", help="Source name")
    parser.add_argument("--output", "-o", help="Output ICS file")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = SongkickScraper(url=args.url, source_name=args.name)
    scraper.run(args.output)


if __name__ == "__main__":
    main()
