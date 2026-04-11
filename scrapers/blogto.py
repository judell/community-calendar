#!/usr/bin/env python3
"""
Scraper for blogTO event listings (Toronto).

blogTO renders its events page client-side from a public REST API:
    GET /api/v2/events/?date=YYYY-MM-DD&bundle_type=medium&limit=9999

Each per-day response includes the full payload we need (title,
description_stripped, venue_name, start_time, end_time, share_url,
image_url, all_day) — no per-event detail fetch required.

Strategy:
- Walk forward day-by-day from today.
- Dedupe events by id; keep the earliest occurrence as dtstart.
- Stop after STOP_AFTER_EMPTY_DAYS consecutive empty days, or when
  we hit the SCRAPE_MONTHS hard ceiling from BaseScraper.

Usage:
    python scrapers/blogto.py --output cities/toronto/blogto.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import json
import logging
from datetime import datetime, date, timedelta
from typing import Any, Optional
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from zoneinfo import ZoneInfo

from lib.base import BaseScraper

API_URL = "https://www.blogto.com/api/v2/events/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json',
}

STOP_AFTER_EMPTY_DAYS = 7


def _parse_clock(s: str) -> Optional[tuple[int, int]]:
    """Parse '9:00 AM' / '12:30 PM' / '8 PM' into (hour24, minute)."""
    if not s:
        return None
    s = s.strip().upper().replace('.', '')
    ampm = None
    if s.endswith('AM'):
        ampm = 'AM'
        s = s[:-2].strip()
    elif s.endswith('PM'):
        ampm = 'PM'
        s = s[:-2].strip()
    if ':' in s:
        h_str, m_str = s.split(':', 1)
    else:
        h_str, m_str = s, '0'
    try:
        h = int(h_str)
        m = int(m_str)
    except ValueError:
        return None
    if ampm == 'PM' and h < 12:
        h += 12
    elif ampm == 'AM' and h == 12:
        h = 0
    if not (0 <= h < 24 and 0 <= m < 60):
        return None
    return h, m


class BlogToScraper(BaseScraper):
    """Scraper for blogTO events via the public /api/v2/events/ listing endpoint."""

    name = "blogTO"
    domain = "blogto.com"
    timezone = "America/Toronto"

    def _fetch_day(self, day: date) -> list[dict[str, Any]]:
        params = {
            'date': day.isoformat(),
            'bundle_type': 'medium',
            'limit': 9999,
            'offset': 0,
        }
        url = f"{API_URL}?{urlencode(params)}"
        req = Request(url, headers=HEADERS)
        try:
            with urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read().decode('utf-8'))
        except (HTTPError, URLError) as e:
            self.logger.warning(f"Failed to fetch {day}: {e}")
            return []
        return payload.get('results', []) or []

    def fetch_events(self) -> list[dict[str, Any]]:
        tz = ZoneInfo(self.timezone)
        today = datetime.now(tz).date()
        horizon_days = self.months_ahead * 31  # hard ceiling

        seen: dict[int, dict[str, Any]] = {}
        empty_streak = 0
        days_walked = 0

        for offset in range(horizon_days):
            day = today + timedelta(days=offset)
            results = self._fetch_day(day)
            days_walked += 1

            if not results:
                empty_streak += 1
                if empty_streak >= STOP_AFTER_EMPTY_DAYS:
                    self.logger.info(
                        f"Stopping after {empty_streak} empty days at {day} "
                        f"(walked {days_walked} days)"
                    )
                    break
                continue
            empty_streak = 0

            for r in results:
                event_id = r.get('id')
                if event_id is None or event_id in seen:
                    continue

                title = r.get('title')
                if not title:
                    continue

                all_day = bool(r.get('all_day'))
                start_clock = _parse_clock(r.get('start_time') or '')
                end_clock = _parse_clock(r.get('end_time') or '')

                if all_day or not start_clock:
                    dtstart: Any = day
                    dtend: Any = day + timedelta(days=1)
                else:
                    sh, sm = start_clock
                    dtstart = datetime(day.year, day.month, day.day, sh, sm, tzinfo=tz)
                    if end_clock:
                        eh, em = end_clock
                        dtend = datetime(day.year, day.month, day.day, eh, em, tzinfo=tz)
                        # End-time before start-time means it crosses midnight
                        if dtend <= dtstart:
                            dtend = dtend + timedelta(days=1)
                    else:
                        dtend = dtstart + timedelta(hours=2)

                venue = r.get('venue_name') or ''
                description = r.get('description_stripped') or ''
                share_url = r.get('share_url') or ''
                image_url = r.get('image_url') or r.get('hub_page_image_url') or ''

                seen[event_id] = {
                    'title': title,
                    'dtstart': dtstart,
                    'dtend': dtend,
                    'location': venue,
                    'description': description,
                    'url': share_url,
                    'image_url': image_url,
                    'uid': f"blogto-{event_id}@blogto.com",
                }

        self.logger.info(
            f"Walked {days_walked} days, collected {len(seen)} unique events"
        )
        return list(seen.values())


def main():
    BlogToScraper.setup_logging()
    args = BlogToScraper.parse_args()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    BlogToScraper().run(args.output)


if __name__ == '__main__':
    main()
