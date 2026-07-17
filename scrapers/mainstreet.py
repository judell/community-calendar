#!/usr/bin/env python3
"""
Parameterized scraper for MainStreet Online tourism sites.

MainStreet Online is a proprietary tourism-site SaaS (based in Asheville)
whose sites are WordPress-hosted and expose a REST API:

    <base>/wp-json/ms-events/v1/agenda?start=YYYY-MM-DD&end=YYYY-MM-DD&offset=N

Response shape (observed 2026-07-16 on hendersonville.com):

    {
      "events": [
        {
          "event_id": 265314, "instance_id": 197227,
          "title": "...", "excerpt": "", "description": "...",
          "permalink": "...", "occurrence_permalink": "...",
          "is_recurring": false, "recurrence_summary": "",
          "start_utc": "2026-05-25 04:00:00", "end_utc": "2026-08-05 03:59:50",
          "all_day": true, "timezone": "America/New_York",
          "venue_name": "...", "venue_address": "...",
          "cost_label": "Free",
          "is_multi_day": true, "spans_days": 72, "display_date": "2026-07-16",
          ...
        }, ...
      ],
      "has_more": true, "offset": 0, "limit": 50, "total": 130
    }

Notes:
- `start_utc` / `end_utc` are naive UTC timestamps; convert to the site's
  local timezone (each event also carries its own `timezone`).
- The agenda repeats multi-day events once per display day, so results
  must be deduplicated by `instance_id`.
- The endpoint sits behind Varnish/Cloudflare and needs full browser
  headers (UA alone gets a 503); occasional 503s are transient, so we retry.

These are AGGREGATOR sources (whole-region coverage); high volume is normal.

Usage:
    python scrapers/mainstreet.py \
        --url "https://www.hendersonville.com" \
        --name "Hendersonville.com" \
        --output cities/asheville/hendersonville_com.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import html as html_mod
import json
import logging
import re
import time
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from lib.base import BaseScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

WINDOW_DAYS = 92          # rolling window: today -> ~3 months out
PAGE_LIMIT = 50           # server-side page size observed
MAX_PAGES = 100           # safety cap
RETRIES = 3               # Varnish 503s are transient


class MainStreetScraper(BaseScraper):
    """Scraper for MainStreet Online sites via the ms-events REST API."""

    def __init__(self, base_url: str, source_name: str, tz: str = "America/New_York"):
        self.base_url = base_url.rstrip('/')
        self.name = source_name
        self.domain = urlparse(self.base_url).netloc.removeprefix('www.')
        self.timezone = tz
        super().__init__()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': f'{self.base_url}/events/',
        }

    def _fetch_json(self, url: str) -> Optional[dict[str, Any]]:
        """Fetch a URL and parse JSON, retrying on transient 5xx."""
        for attempt in range(1, RETRIES + 1):
            req = Request(url, headers=self.headers)
            try:
                with urlopen(req, timeout=40) as resp:
                    return json.loads(resp.read().decode('utf-8'))
            except HTTPError as e:
                if e.code >= 500 and attempt < RETRIES:
                    self.logger.warning(f"HTTP {e.code} on {url}, retry {attempt}/{RETRIES}")
                    time.sleep(2 * attempt)
                    continue
                self.logger.error(f"Failed to fetch {url}: HTTP {e.code}")
                return None
            except (URLError, json.JSONDecodeError, TimeoutError) as e:
                if attempt < RETRIES:
                    self.logger.warning(f"{e} on {url}, retry {attempt}/{RETRIES}")
                    time.sleep(2 * attempt)
                    continue
                self.logger.error(f"Failed to fetch {url}: {e}")
                return None
        return None

    def _fetch_agenda_pages(self, start: date, end: date) -> list[dict[str, Any]]:
        """Page through the agenda endpoint for the given date window."""
        raw = []
        offset = 0
        for page in range(MAX_PAGES):
            params = urlencode({
                'start': start.isoformat(),
                'end': end.isoformat(),
                'offset': offset,
            })
            url = f'{self.base_url}/wp-json/ms-events/v1/agenda?{params}'
            data = self._fetch_json(url)
            if data is None:
                break
            events = data.get('events') or []
            raw.extend(events)
            self.logger.debug(
                f"Page {page}: offset={data.get('offset')} n={len(events)} "
                f"total={data.get('total')} has_more={data.get('has_more')}")
            if not data.get('has_more') or not events:
                break
            offset += data.get('limit') or len(events) or PAGE_LIMIT
        self.logger.info(f"Fetched {len(raw)} agenda rows from {self.base_url}")
        return raw

    @staticmethod
    def _parse_utc(value: str) -> Optional[datetime]:
        """Parse a naive 'YYYY-MM-DD HH:MM:SS' UTC timestamp into an aware datetime."""
        if not value:
            return None
        try:
            return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
        except ValueError:
            return None

    def _parse_event(self, item: dict[str, Any]) -> Optional[dict[str, Any]]:
        title = html_mod.unescape((item.get('title') or '').strip())
        start_utc = self._parse_utc(item.get('start_utc') or '')
        if not title or not start_utc:
            return None

        end_utc = self._parse_utc(item.get('end_utc') or '')
        now = datetime.now(timezone.utc)
        # Skip events that are over (end in the past; if no end, start in the past).
        if (end_utc or start_utc) < now:
            return None

        tz = ZoneInfo(item.get('timezone') or self.timezone)
        local_start = start_utc.astimezone(tz)
        local_end = end_utc.astimezone(tz) if end_utc else None

        if item.get('all_day'):
            # Date-valued DTSTART/DTEND; ICS DTEND is exclusive.
            dtstart: Any = local_start.date()
            dtend: Any = (local_end.date() + timedelta(days=1)) if local_end else None
        else:
            dtstart = local_start
            dtend = local_end

        # Description: cost + recurrence context + prose, tags/entities stripped.
        desc = item.get('description') or item.get('excerpt') or ''
        desc = html_mod.unescape(desc)
        desc = re.sub(r'<[^>]+>', ' ', desc)
        desc = re.sub(r'\s+', ' ', desc).strip()
        extras = []
        cost = (item.get('cost_label') or '').strip()
        if cost:
            extras.append(f"Cost: {cost}")
        recur = (item.get('recurrence_summary') or '').strip()
        if recur:
            extras.append(recur)
        if extras:
            desc = f"{' | '.join(extras)}. {desc}".strip()

        venue = html_mod.unescape((item.get('venue_name') or '').strip())
        address = html_mod.unescape((item.get('venue_address') or '').strip())
        location = ', '.join(p for p in (venue, address) if p)

        url = item.get('occurrence_permalink') or item.get('permalink') or ''

        return {
            'title': title,
            'dtstart': dtstart,
            'dtend': dtend,
            'location': location,
            'description': desc[:500],
            'url': url,
        }

    def fetch_events(self) -> list[dict[str, Any]]:
        today = datetime.now(ZoneInfo(self.timezone)).date()
        raw = self._fetch_agenda_pages(today, today + timedelta(days=WINDOW_DAYS))

        # The agenda repeats multi-day events once per display day; dedupe by
        # instance. Then dedupe by (title, dtstart): these sites sometimes
        # double-post the same event as separate posts (distinct permalinks,
        # identical content), which would collide on the generated UID.
        seen: set[Any] = set()
        seen_content: set[Any] = set()
        events = []
        dupes = 0
        for item in raw:
            key = item.get('instance_id') or (item.get('event_id'), item.get('start_utc'))
            if key in seen:
                dupes += 1
                continue
            seen.add(key)
            event = self._parse_event(item)
            if not event:
                continue
            content_key = (event['title'].lower(), str(event['dtstart']))
            if content_key in seen_content:
                dupes += 1
                continue
            seen_content.add(content_key)
            events.append(event)

        self.logger.info(f"Parsed {len(events)} unique future events "
                         f"({dupes} duplicates skipped)")
        return events


def main():
    parser = argparse.ArgumentParser(description="Scrape a MainStreet Online tourism site")
    parser.add_argument('--url', required=True,
                        help='Site base URL (e.g. https://www.hendersonville.com)')
    parser.add_argument('--name', required=True, help='Source name')
    parser.add_argument('--timezone', default='America/New_York',
                        help='IANA timezone (default: America/New_York)')
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = MainStreetScraper(args.url, args.name, args.timezone)
    scraper.run(args.output)


if __name__ == '__main__':
    main()
