#!/usr/bin/env python3
"""Eventbrite organizer events with venue denylist + geo allowlist filters.

Discovers an Eventbrite organizer's events from the organizer page (/o/slug)
and per-event JSON-LD (same mechanism as scrapers/eventbrite.py), then
excludes events whose LOCATION matches any keyword in a denylist file and
(optionally) requires the LOCATION to match a geo allowlist.

Designed for publisher organizer feeds (Coach House, Cormorant, Penguin Random
House Canada, etc.) where most events are at indie venues we want to capture
but some are at big-box chains we want to exclude, and where the organizer
runs events far outside the city.

Historical note: this scraper originally fetched a ready-made ICS from
eb-to-ical.daylightpirates.org, which went dead in 2026 (HTTP 404). It now
scrapes Eventbrite directly via scrapers/eventbrite.py.

Usage:
    python scrapers/eventbrite_filtered.py \\
        --url "https://www.eventbrite.ca/o/coach-house-books-6007837525" \\
        --denylist cities/toronto/bookstore_venue_denylist.txt \\
        --geo-allowlist cities/toronto/geo_allowlist.txt \\
        --name "Coach House Books" \\
        -o cities/toronto/coach_house.ics

    # See what's being filtered out and what's passing through:
    python scrapers/eventbrite_filtered.py ... --report
"""

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

from eventbrite import EventbriteScraper


def load_keyword_file(path: Path) -> list[str]:
    """Load a keyword file: one keyword per line, # comments stripped."""
    keywords = []
    for line in path.read_text().splitlines():
        line = line.split('#')[0].strip()
        if line:
            keywords.append(line)
    return keywords


def matches_keyword(location: str, keywords: list[str]) -> str | None:
    """Return the matching keyword if location contains one, else None."""
    if not location or not keywords:
        return None
    loc_lower = location.lower()
    for kw in keywords:
        if re.search(rf'\b{re.escape(kw.lower())}\b', loc_lower):
            return kw
    return None


class EventbriteFilteredScraper(EventbriteScraper):
    """Eventbrite organizer events filtered by venue denylist + geo allowlist."""

    domain = "eventbrite.ca"
    timezone = "America/Toronto"

    def __init__(
        self,
        organizer_url: str,
        denylist: list[str],
        name: str,
        geo_allowlist: list[str] | None = None,
        report: bool = False,
    ):
        self.denylist = denylist
        self.geo_allowlist = geo_allowlist or []
        self.report = report
        super().__init__(organizer_url=organizer_url, source_name=name)

    def fetch_events(self) -> list[dict[str, Any]]:
        candidates = super().fetch_events()

        events: list[dict[str, Any]] = []
        denied_venues: list[str] = []
        out_of_area: list[str] = []
        passed_venues: list[str] = []

        for ev in candidates:
            location = (ev.get('location') or '').strip()

            denied_kw = matches_keyword(location, self.denylist)
            if denied_kw:
                denied_venues.append(f"[{denied_kw}] {location}")
                continue

            # Geo filter: if allowlist provided, location must contain at least
            # one keyword. Empty location passes (treated as online from a
            # Toronto org — see geo_allowlist.txt rationale).
            if self.geo_allowlist and location:
                if not matches_keyword(location, self.geo_allowlist):
                    out_of_area.append(location)
                    continue

            events.append(ev)
            passed_venues.append(location or '(no location)')

        self.logger.info(
            f"{self.name}: {len(events)} passed, {len(denied_venues)} denied, "
            f"{len(out_of_area)} out-of-area"
        )

        if self.report:
            if denied_venues:
                self.logger.info(f"--- DENIED ({len(denied_venues)}) ---")
                for v in sorted(set(denied_venues))[:30]:
                    self.logger.info(f"  {v}")
            if out_of_area:
                self.logger.info(f"--- OUT OF AREA ({len(out_of_area)}) ---")
                for v in sorted(set(out_of_area))[:30]:
                    self.logger.info(f"  {v}")
            if passed_venues:
                self.logger.info(f"--- PASSED VENUES (unique, first 50) ---")
                for v in sorted(set(passed_venues))[:50]:
                    self.logger.info(f"  {v}")

        return events


def main():
    parser = argparse.ArgumentParser(
        description="Scrape an Eventbrite organizer's events, filtered by venue denylist + geo allowlist"
    )
    parser.add_argument('--url', required=True, help='Eventbrite organizer URL (/o/slug)')
    parser.add_argument('--denylist', required=True, help='Path to venue denylist file')
    parser.add_argument('--geo-allowlist', help='Path to geo allowlist file (require LOCATION to contain at least one keyword)')
    parser.add_argument('--name', required=True, help='Source display name (X-SOURCE)')
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--report', action='store_true', help='Print denied + out-of-area + passed venue samples')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    EventbriteFilteredScraper.setup_logging()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    denylist = load_keyword_file(Path(args.denylist))
    geo_allowlist = load_keyword_file(Path(args.geo_allowlist)) if args.geo_allowlist else []
    scraper = EventbriteFilteredScraper(
        organizer_url=args.url,
        denylist=denylist,
        geo_allowlist=geo_allowlist,
        name=args.name,
        report=args.report,
    )
    scraper.run(args.output)


if __name__ == '__main__':
    main()
