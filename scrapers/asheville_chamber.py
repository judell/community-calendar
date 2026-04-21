#!/usr/bin/env python3
"""
Scraper for Asheville Area Chamber of Commerce events via RSS.

ChamberMaster's RSS embeds event dates inside the title field rather than
using standard RSS date fields (pubDate is the listing date, not the event date).

Title format: "Event Name MM/DD/YYYY [HH:MM AM/PM/Noon] [- MM/DD/YYYY [HH:MM AM/PM]]"

Usage:
    python scrapers/asheville_chamber.py --output cities/asheville/asheville_chamber.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import html as html_mod
import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional
from zoneinfo import ZoneInfo

import feedparser

from lib.base import BaseScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

RSS_URL = "https://web.ashevillechamber.org/cwt/external/wcpages/wcevents/events_communitystartpage.aspx?rss=true"
DEFAULT_LOCATION = "Asheville, NC"
TZ = ZoneInfo("America/New_York")

# Matches date(s) and optional times at the end of a Chamber RSS title.
# Handles: "4/21/2026 5:30 PM - 4/21/2026 7:00 PM", "4/20/2026 12:00 Noon - 4/26/2026 10:00 PM",
#          "3/18/2026  - 6/30/2026", "4/23/2026 6:30 PM"
DATE_RE = re.compile(
    r'\s+(\d{1,2}/\d{1,2}/\d{4})'
    r'(?:\s+(\d{1,2}:\d{2}\s*(?:AM|PM|Noon)))?'
    r'(?:\s*-\s*(\d{1,2}/\d{1,2}/\d{4})'
    r'(?:\s+(\d{1,2}:\d{2}\s*(?:AM|PM|Noon)))?)?'
    r'\s*$',
    re.IGNORECASE,
)


def _parse_time(time_str: str) -> tuple[int, int]:
    time_str = time_str.strip()
    if 'noon' in time_str.lower():
        return 12, 0
    try:
        dt = datetime.strptime(time_str.upper(), '%I:%M %p')
        return dt.hour, dt.minute
    except ValueError:
        return 0, 0


def _parse_title(title: str) -> tuple[str, Optional[datetime], Optional[datetime]]:
    """Split a Chamber RSS title into (event_name, dtstart, dtend)."""
    m = DATE_RE.search(title)
    if not m:
        return title.strip(), None, None

    name = title[:m.start()].strip()
    start_date_str, start_time_str, end_date_str, end_time_str = m.groups()

    try:
        start_date = datetime.strptime(start_date_str, '%m/%d/%Y')
    except ValueError:
        return title.strip(), None, None

    if start_time_str:
        h, mn = _parse_time(start_time_str)
        dtstart = start_date.replace(hour=h, minute=mn, tzinfo=TZ)
    else:
        dtstart = start_date.replace(hour=9, minute=0, tzinfo=TZ)

    dtend = None
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%m/%d/%Y')
        except ValueError:
            end_date = None
        if end_date:
            if end_time_str:
                h, mn = _parse_time(end_time_str)
                dtend = end_date.replace(hour=h, minute=mn, tzinfo=TZ)
            else:
                dtend = end_date.replace(hour=17, minute=0, tzinfo=TZ)

    return name, dtstart, dtend


class AshevilleChamberScraper(BaseScraper):
    """Scraper for Asheville Area Chamber of Commerce events."""

    name = "Asheville Area Chamber of Commerce"
    domain = "ashevillechamber.org"
    timezone = "America/New_York"

    def fetch_events(self) -> list[dict[str, Any]]:
        self.logger.info(f"Fetching Chamber RSS: {RSS_URL}")
        feed = feedparser.parse(RSS_URL)
        self.logger.info(f"Found {len(feed.entries)} entries")

        now = datetime.now(TZ)
        events = []
        skipped_past = 0

        for entry in feed.entries:
            title = entry.get('title', '').strip()
            name, dtstart, dtend = _parse_title(title)

            if dtstart is None:
                self.logger.debug(f"Could not parse date from title: {title!r}")
                continue

            # Skip events that are completely in the past.
            # For multi-day events, keep if end is still upcoming.
            effective_end = dtend or dtstart
            if effective_end < now:
                skipped_past += 1
                continue

            desc = entry.get('summary', '') or ''
            desc = html_mod.unescape(desc)
            desc = re.sub(r'<[^>]+>', ' ', desc).strip()
            desc = re.sub(r'\s+', ' ', desc)

            events.append({
                'title': name,
                'dtstart': dtstart,
                'dtend': dtend or dtstart,
                'location': DEFAULT_LOCATION,
                'description': desc[:500] if desc else '',
                'url': entry.get('link', ''),
            })

        self.logger.info(f"Got {len(events)} upcoming events (skipped {skipped_past} past)")
        return events


def main():
    parser = argparse.ArgumentParser(description="Scrape Asheville Area Chamber of Commerce events")
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = AshevilleChamberScraper()
    scraper.run(args.output)


if __name__ == '__main__':
    main()
