#!/usr/bin/env python3
"""
Scraper for Brown County, IN government calendar.

The county runs CivicEngage (CivicPlus) at browncounty-in.gov.
The CivicPlus GET-based iCalendar feed at:
  /common/modules/iCalendar/iCalendar.aspx?catID=14&feed=calendar
returns a well-formed ICS file with government meeting events.
No form POST or ASP.NET hidden fields are needed — a plain GET works.

The feed's VEVENT URLs are relative; we rewrite them to absolute.
The feed timezone label says America/New_York but Brown County is in
the Eastern zone, so we re-emit with TZID=America/Indiana/Indianapolis
(same UTC offset, correct for the locale).

Usage:
    python scrapers/brown_county_gov.py --output cities/bloomington/brown_county_gov.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import logging
import re
from datetime import datetime, timezone
from typing import Any
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from zoneinfo import ZoneInfo

from icalendar import Calendar as ICalendar

from lib.base import BaseScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "https://browncounty-in.gov"
ICAL_URL = f"{BASE_URL}/common/modules/iCalendar/iCalendar.aspx?catID=14&feed=calendar"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/calendar,*/*',
}
TZ = ZoneInfo("America/Indiana/Indianapolis")

# Strip HTML tags from location fields (CivicPlus sometimes includes markup)
_HTML_TAG_RE = re.compile(r'<[^>]+>')
_NBSP_RE = re.compile(r'&nbsp;|\\s+')


def _clean_location(raw: str) -> str:
    """Remove HTML tags and normalize whitespace from a location string."""
    text = _HTML_TAG_RE.sub(' ', raw)
    text = text.replace('&nbsp;', ' ').replace('\\,', ',')
    return re.sub(r'\s+', ' ', text).strip()


class BrownCountyGovScraper(BaseScraper):
    """Scraper for Brown County IN government meetings via CivicPlus iCal feed."""

    name = "Brown County Government"
    domain = "browncounty-in.gov"
    timezone = "America/Indiana/Indianapolis"

    def _fetch_ical(self) -> bytes | None:
        req = Request(ICAL_URL, headers=HEADERS)
        try:
            with urlopen(req, timeout=30) as resp:
                return resp.read()
        except (HTTPError, URLError) as e:
            self.logger.error(f"Failed to fetch iCal feed: {e}")
            return None

    def fetch_events(self) -> list[dict[str, Any]]:
        data = self._fetch_ical()
        if not data:
            return []

        try:
            cal = ICalendar.from_ical(data)
        except Exception as e:
            self.logger.error(f"Failed to parse iCal: {e}")
            return []

        now = datetime.now(timezone.utc)
        events = []

        for comp in cal.walk('VEVENT'):
            dtstart_prop = comp.get('dtstart')
            if not dtstart_prop:
                continue

            dt = dtstart_prop.dt

            # Normalize to aware datetime for comparison
            if hasattr(dt, 'hour'):
                start_aware = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            else:
                import datetime as _dt
                start_aware = _dt.datetime.combine(dt, _dt.time.min).replace(tzinfo=timezone.utc)

            if start_aware < now:
                continue

            # Convert to local tz
            dtstart_local = start_aware.astimezone(TZ)

            dtend = None
            dtend_prop = comp.get('dtend')
            if dtend_prop:
                end_dt = dtend_prop.dt
                if hasattr(end_dt, 'hour'):
                    end_aware = end_dt if end_dt.tzinfo else end_dt.replace(tzinfo=timezone.utc)
                else:
                    import datetime as _dt
                    end_aware = _dt.datetime.combine(end_dt, _dt.time.min).replace(tzinfo=timezone.utc)
                dtend = end_aware.astimezone(TZ)

            title = str(comp.get('summary', 'Untitled'))

            # Location may contain HTML from CivicPlus
            raw_location = str(comp.get('location', ''))
            location = _clean_location(raw_location) if raw_location else ''

            # Description contains the event URL in this feed
            raw_desc = str(comp.get('description', ''))
            desc = raw_desc.strip()

            # URL: CivicPlus puts a relative URL in the URL field; make it absolute
            raw_url = str(comp.get('url', ''))
            if raw_url.startswith('/'):
                event_url = f"{BASE_URL}{raw_url}"
            elif raw_url.startswith('http'):
                event_url = raw_url
            else:
                # URL is sometimes in the description line
                desc_url_match = re.search(r'https?://\S+', desc)
                event_url = desc_url_match.group(0) if desc_url_match else BASE_URL + '/calendar.aspx'

            events.append({
                'title': title,
                'dtstart': dtstart_local,
                'dtend': dtend,
                'location': location,
                'description': desc[:500],
                'url': event_url,
            })

        self.logger.info(f"Found {len(events)} future events")
        return events


def main():
    parser = argparse.ArgumentParser(description="Scrape Brown County IN government meetings")
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    scraper = BrownCountyGovScraper()
    scraper.run(args.output)


if __name__ == '__main__':
    main()
