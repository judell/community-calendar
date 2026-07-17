#!/usr/bin/env python3
"""
Scraper for the Bloomington Symphony Orchestra (Bloomington, INDIANA).

NOTE ON DOMAINS: the Indiana orchestra lives at bloomingtonsymphony.COM —
bloomingtonsymphony.ORG is the Bloomington MINNESOTA symphony. Discovery
notes pointing at bloomingtonsymphony.org/concert/ were the wrong state.

The .com site is WordPress running The Events Calendar (Tribe) plugin,
so the ~6 concerts/year are available structured from the REST API at
/wp-json/tribe/events/v1/events/ (which also carries per-event venues:
Buskirk-Chumley Theater, Switchyard Park, Tivoli Theatre in Spencer).
mod_security 406s some plain user agents on HTML pages, but the REST
API answers the shared lib's UA.

Judgment-heavy bit: some concerts are entered as ALL-DAY events with the
showtime buried in the title (e.g. "Celebrate the Season with the BSO,
5pm and 8pm at Buskirk-Chumley Theater"). For those we recover the first
listed showtime from the title/description instead of emitting a bogus
midnight start; if no time can be recovered the event is emitted as a
true all-day date. Past events are skipped.

Usage:
    python scrapers/bloomington_symphony.py --output cities/bloomington/bloomington_symphony.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import html as html_mod
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Optional
from zoneinfo import ZoneInfo

from lib.tribe_events import TribeEventsScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TIME_RE = re.compile(r'\b(\d{1,2})(?::(\d{2}))?\s*([ap])\.?m\.?\b', re.IGNORECASE)


def extract_times(text: str) -> list[tuple[int, int]]:
    """All explicit am/pm times in text, as (hour24, minute)."""
    times = []
    for m in TIME_RE.finditer(text):
        hour = int(m.group(1))
        minute = int(m.group(2) or 0)
        if not (1 <= hour <= 12) or minute > 59:
            continue
        if m.group(3).lower() == 'p' and hour != 12:
            hour += 12
        elif m.group(3).lower() == 'a' and hour == 12:
            hour = 0
        times.append((hour, minute))
    return times


class BloomingtonSymphonyScraper(TribeEventsScraper):
    """Bloomington Symphony Orchestra (Indiana) via Tribe Events REST API."""

    name = "Bloomington Symphony Orchestra"
    domain = "bloomingtonsymphony.com"
    api_url = "https://www.bloomingtonsymphony.com/wp-json/tribe/events/v1/events/"
    timezone = "America/Indiana/Indianapolis"
    default_location = "Buskirk-Chumley Theater, 114 E Kirkwood Ave, Bloomington, IN 47408"

    def _parse_event(self, item: dict, tz: ZoneInfo) -> Optional[dict[str, Any]]:
        parsed = super()._parse_event(item, tz)
        if not parsed:
            return None

        # The shared lib leaves HTML entities in titles (e.g. &#8211;).
        parsed['title'] = html_mod.unescape(parsed['title'])
        title = parsed['title']

        if item.get('all_day'):
            fixed = self._fix_all_day(parsed, item, tz)
            if fixed is None:
                return None
            parsed = fixed

        # Skip past events.
        now = datetime.now(tz)
        end = parsed.get('dtend') or parsed['dtstart']
        if hasattr(end, 'hour'):
            if end < now:
                self.logger.debug(f"Skipping past event: {title!r}")
                return None
        else:  # all-day date object
            if end <= now.date():
                self.logger.debug(f"Skipping past all-day event: {title!r}")
                return None

        return parsed

    def _fix_all_day(self, parsed: dict[str, Any], item: dict,
                     tz: ZoneInfo) -> Optional[dict[str, Any]]:
        """All-day Tribe entries here are really timed concerts with the
        showtime in the title (e.g. "..., 5pm and 8pm at Buskirk-Chumley
        Theater"). Recover the first showtime; otherwise emit a genuine
        all-day date rather than a fake midnight datetime."""
        title = parsed['title']
        desc = parsed.get('description') or ''
        times = extract_times(title) or extract_times(desc)
        day = parsed['dtstart'].date()

        if times:
            hour, minute = times[0]
            parsed['dtstart'] = datetime(day.year, day.month, day.day, hour, minute, tzinfo=tz)
            parsed['dtend'] = parsed['dtstart'] + timedelta(minutes=90)
            if len(times) > 1:
                extra = ', '.join(
                    f"{(h - 12) if h > 12 else (h or 12)}:{m:02d}{'pm' if h >= 12 else 'am'}"
                    for h, m in times)
                note = f"Showings at {extra}."
                if 'showing' not in desc.lower():
                    parsed['description'] = f"{desc} {note}".strip()[:500]
            self.logger.info(
                f"All-day entry {title!r}: recovered showtime {times[0][0]:02d}:{times[0][1]:02d}")
        else:
            # True all-day: date objects (DTEND exclusive).
            parsed['dtstart'] = day
            parsed['dtend'] = day + timedelta(days=1)
            self.logger.info(f"All-day entry {title!r}: no showtime found, emitting as all-day")
        return parsed


def main():
    parser = argparse.ArgumentParser(
        description="Scrape Bloomington Symphony Orchestra (Indiana) concerts")
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = BloomingtonSymphonyScraper()
    scraper.run(args.output)


if __name__ == '__main__':
    main()
