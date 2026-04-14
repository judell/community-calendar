#!/usr/bin/env python3
"""Eventbrite organizer feed with venue denylist filter.

Fetches an Eventbrite organizer's ICS feed via eb-to-ical and excludes events
whose LOCATION matches any keyword in a denylist file. Everything else passes
through as a plausible candidate.

Designed for publisher organizer feeds (Coach House, Cormorant, Penguin Random
House Canada, etc.) where most events are at indie venues we want to capture
but some are at big-box chains we want to exclude.

Usage:
    python scrapers/eventbrite_filtered.py \\
        --organizer 6007837525 \\
        --denylist cities/toronto/bookstore_venue_denylist.txt \\
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
import urllib.request

sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

from icalendar import Calendar

from lib.base import BaseScraper

EB_TO_ICAL_URL = "https://eb-to-ical.daylightpirates.org/eventbrite-organizer-ical?organizer={}"


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


class EventbriteFilteredScraper(BaseScraper):
    """Eventbrite organizer feed filtered by venue denylist + geo allowlist."""

    domain = "eventbrite.ca"
    timezone = "America/Toronto"

    def __init__(
        self,
        organizer_id: str,
        denylist: list[str],
        name: str,
        geo_allowlist: list[str] | None = None,
        report: bool = False,
    ):
        super().__init__()
        self.organizer_id = organizer_id
        self.denylist = denylist
        self.geo_allowlist = geo_allowlist or []
        self.name = name
        self.report = report

    def fetch_events(self) -> list[dict[str, Any]]:
        url = EB_TO_ICAL_URL.format(self.organizer_id)
        try:
            data = urllib.request.urlopen(url, timeout=30).read()
        except Exception as exc:
            self.logger.error(f"Failed to fetch {url}: {exc}")
            return []

        try:
            cal = Calendar.from_ical(data)
        except Exception as exc:
            self.logger.error(f"Failed to parse ICS: {exc}")
            return []

        events: list[dict[str, Any]] = []
        denied_venues: list[str] = []
        out_of_area: list[str] = []
        passed_venues: list[str] = []

        for ev in cal.walk('VEVENT'):
            location = str(ev.get('location') or '').strip()

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

            dtstart = ev.get('dtstart')
            if not dtstart:
                continue

            dtend = ev.get('dtend')
            dt_start_value = dtstart.dt if hasattr(dtstart, 'dt') else dtstart
            dt_end_value = (dtend.dt if (dtend and hasattr(dtend, 'dt')) else dt_start_value)

            events.append({
                'uid': str(ev.get('uid') or ''),
                'title': str(ev.get('summary') or ''),
                'dtstart': dt_start_value,
                'dtend': dt_end_value,
                'location': location,
                'description': str(ev.get('description') or ''),
                'url': str(ev.get('url') or ''),
            })
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
        description="Filter an Eventbrite organizer feed by venue denylist"
    )
    parser.add_argument('--organizer', required=True, help='Eventbrite organizer ID')
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
        organizer_id=args.organizer,
        denylist=denylist,
        geo_allowlist=geo_allowlist,
        name=args.name,
        report=args.report,
    )
    scraper.run(args.output)


if __name__ == '__main__':
    main()
