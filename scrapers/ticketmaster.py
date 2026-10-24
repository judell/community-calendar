#!/usr/bin/env python3
"""
Scraper for Ticketmaster events via the Discovery API.

Requires a TICKETMASTER_API_KEY environment variable (or --api-key).
Free keys: https://developer.ticketmaster.com/products-and-docs/apis/getting-started/

Two modes:

  Per-venue (existing usage):
      python scrapers/ticketmaster.py \
          --venue-id KovZpa2X8e --name "DPAC" \
          --output cities/raleighdurham/dpac.ics

  City-level aggregator:
      python scrapers/ticketmaster.py \
          --city Washington --state DC --classification Music \
          --name "Ticketmaster DC Music" \
          --output cities/dc-music/ticketmaster_dc_music.ics
"""

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

import argparse
import json
import logging
import os
import time
from datetime import UTC, datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from lib.base import BaseScraper
from lib.timeutil import parse_naive_ics

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

API_BASE = "https://app.ticketmaster.com/discovery/v2"
PAGE_SIZE = 100  # max allowed by TM API


class TicketmasterScraper(BaseScraper):
    """Scraper for Ticketmaster events via the Discovery API.

    Supports per-venue queries (venue_id) or broader filters
    (city, stateCode, classificationName) for aggregator-style usage.
    """

    name = "Ticketmaster"
    domain = "ticketmaster.com"
    timezone = "America/New_York"

    def __init__(
        self,
        api_key: str,
        venue_id: str | None = None,
        city: str | None = None,
        state: str | None = None,
        classification: str | None = None,
        source_name: str | None = None,
        tz: str | None = None,
    ):
        super().__init__()
        if not venue_id and not (city or state or classification):
            raise ValueError("Provide either venue_id or city/state/classification")
        self.venue_id = venue_id
        self.city = city
        self.state = state
        self.classification = classification
        self.api_key = api_key
        if source_name:
            self.name = source_name
        if tz:
            self.timezone = tz

    def _query_params(self) -> dict[str, str]:
        """Build query params for the events endpoint."""
        params: dict[str, str] = {}
        if self.venue_id:
            params["venueId"] = self.venue_id
        if self.city:
            params["city"] = self.city
        if self.state:
            params["stateCode"] = self.state
        if self.classification:
            params["classificationName"] = self.classification
        # Bound the API window to our horizon to save quota and keep results focused.
        # TM expects yyyy-MM-ddTHH:mm:ssZ (no fractional seconds).
        now = datetime.now(UTC)
        end = self.horizon_cutoff(now)
        params["startDateTime"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        params["endDateTime"] = end.strftime("%Y-%m-%dT%H:%M:%SZ")
        return params

    def _fetch_page(self, page: int) -> dict:
        """Fetch one page of events from the Discovery API."""
        from urllib.parse import urlencode

        params = self._query_params()
        params["apikey"] = self.api_key
        params["size"] = str(PAGE_SIZE)
        params["page"] = str(page)
        params["sort"] = "date,asc"
        url = f"{API_BASE}/events.json?{urlencode(params)}"
        req = Request(url)
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch all matching events, paginating as needed."""
        events = []
        page = 0

        try:
            data = self._fetch_page(page)
        except (HTTPError, URLError) as e:
            self.logger.warning(f"Failed to fetch Ticketmaster events: {e}")
            return []
        self.mark_source_reached()

        total = data.get("page", {}).get("totalElements", 0)
        total_pages = data.get("page", {}).get("totalPages", 0)
        target = (
            self.venue_id or f"{self.city or ''}/{self.state or ''}/{self.classification or ''}"
        )
        self.logger.info(f"Ticketmaster: {total} events across {total_pages} pages for {target}")

        while True:
            for e in data.get("_embedded", {}).get("events", []):
                event = self._parse_event(e)
                if event:
                    events.append(event)

            page += 1
            if page >= total_pages:
                break

            # Rate limit: 5 req/sec
            time.sleep(0.25)
            try:
                data = self._fetch_page(page)
            except (HTTPError, URLError) as e:
                self.logger.warning(f"Failed on page {page}: {e}")
                break

        self.logger.info(f"Parsed {len(events)} events for {self.name}")
        return events

    def _parse_event(self, e: dict) -> dict | None:
        """Parse a single Ticketmaster event into our event dict format."""
        dates = e.get("dates", {})
        start = dates.get("start", {})

        local_date = start.get("localDate")
        if not local_date:
            return None

        local_time = start.get("localTime", "00:00:00")
        tz = ZoneInfo(dates.get("timezone", self.timezone))

        try:
            dtstart = parse_naive_ics(f"{local_date} {local_time}", "%Y-%m-%d %H:%M:%S")
            dtstart = dtstart.replace(tzinfo=tz)
        except ValueError:
            return None

        # Skip TBD/TBA
        if start.get("dateTBD") or start.get("dateTBA"):
            return None

        # Location from embedded venue
        venues = e.get("_embedded", {}).get("venues", [])
        if venues:
            v = venues[0]
            parts = [v.get("name", "")]
            addr = v.get("address", {})
            if addr.get("line1"):
                parts.append(addr["line1"])
            city = v.get("city", {}).get("name", "")
            state = v.get("state", {}).get("stateCode", "")
            if city:
                parts.append(f"{city}, {state}" if state else city)
            location = ", ".join(p for p in parts if p)
        else:
            location = ""

        return {
            "title": e.get("name", "Untitled"),
            "dtstart": dtstart,
            "url": e.get("url", ""),
            "location": location,
            "description": "",
        }


def main():
    parser = argparse.ArgumentParser(description="Scrape Ticketmaster events")
    parser.add_argument("--venue-id", help="Ticketmaster venue ID (per-venue mode)")
    parser.add_argument("--city", help="City name (aggregator mode)")
    parser.add_argument("--state", help="State code, e.g. DC (aggregator mode)")
    parser.add_argument(
        "--classification", help="Classification name, e.g. Music (aggregator mode)"
    )
    parser.add_argument("--name", default="Ticketmaster", help="Source name")
    parser.add_argument("--output", "-o", help="Output ICS file")
    parser.add_argument(
        "--api-key",
        default=os.environ.get("TICKETMASTER_API_KEY") or os.environ.get("TICKETMASTER_KEY"),
        help="API key (default: TICKETMASTER_API_KEY or TICKETMASTER_KEY env var)",
    )
    parser.add_argument("--timezone", default="America/New_York", help="Timezone")
    parser.add_argument("--default-url", help="Fallback URL when events have no per-event URL")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    if not args.api_key:
        print("Error: --api-key or TICKETMASTER_API_KEY env var required", file=sys.stderr)
        sys.exit(1)
    if not args.venue_id and not (args.city or args.state or args.classification):
        print(
            "Error: provide --venue-id, or one of --city/--state/--classification", file=sys.stderr
        )
        sys.exit(1)

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = TicketmasterScraper(
        api_key=args.api_key,
        venue_id=args.venue_id,
        city=args.city,
        state=args.state,
        classification=args.classification,
        source_name=args.name,
        tz=args.timezone,
    )
    if args.default_url:
        scraper.default_url = args.default_url
    scraper.run(args.output)


if __name__ == "__main__":
    main()
