#!/usr/bin/env python3
"""
Scraper for the Asheville Theater Alliance performance calendar.

ATA (ashevilletheateralliance.org) is THE regional theater aggregator for
the Asheville area — NC Stage, SART, HART, Attic Salt, improv companies,
etc. WordPress + Elementor + JetEngine. The REST API exposes the `events`
post type (159 posts) but JetEngine meta is not registered, so REST has
NO usable dates. Individual event pages server-render the full
performance schedule as repeated rows like:

    Thu - Jul 30, 2026 7:30 pm
    Fri - Jul 31, 2026 7:30 pm
    Sat - Aug 1, 2026 2:30 pm

plus "Venue: <name>" and "Standard Ticket Price: $ 20".

Strategy:
1. Discover event URLs from the public calendar page (server-rendered
   month grid, ~16 upcoming links) — much cheaper than paginating 159
   mostly-stale REST posts.
2. Supplement with REST posts modified in the last 90 days (catches
   events beyond the current month grid).
3. Fetch each event page in parallel; parse every date/time row into one
   VEVENT per performance. Skip past performances.

This is an AGGREGATOR source (events originate with member theaters).

Usage:
    python scrapers/asheville_theater_alliance.py \
        --output cities/asheville/asheville_theater_alliance.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import html as html_mod
import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Any, Optional
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from zoneinfo import ZoneInfo

from lib.base import BaseScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CALENDAR_URL = "https://ashevilletheateralliance.org/asheville-performance-calendar/"
REST_URL = ("https://ashevilletheateralliance.org/wp-json/wp/v2/events"
            "?per_page=100&_fields=link,modified")
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

TZ = ZoneInfo("America/New_York")

# Performance rows: "Thu - Jul 30, 2026 7:30 pm" (month may be abbreviated or full)
PERF_ROW_RE = re.compile(
    r'\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*\s*[-–—]\s*'
    r'([A-Za-z]{3,9})\s+(\d{1,2}),\s*(\d{4})\s+(\d{1,2}):(\d{2})\s*(am|pm)\b',
    re.IGNORECASE
)

MONTHS = {m[:3].lower(): i for i, m in enumerate(
    ['January', 'February', 'March', 'April', 'May', 'June', 'July',
     'August', 'September', 'October', 'November', 'December'], start=1)}


class AshevilleTheaterAllianceScraper(BaseScraper):
    """Scraper for ATA regional performance calendar (aggregator)."""

    name = "Asheville Theater Alliance"
    domain = "ashevilletheateralliance.org"
    timezone = "America/New_York"

    def _fetch_page(self, url: str) -> Optional[str]:
        req = Request(url, headers=HEADERS)
        try:
            with urlopen(req, timeout=30) as resp:
                return resp.read().decode('utf-8', errors='replace')
        except (HTTPError, URLError) as e:
            self.logger.warning(f"Failed to fetch {url}: {e}")
            return None

    def _discover_event_urls(self) -> list[str]:
        """Calendar page links (primary), supplemented by recently-modified REST posts."""
        urls: set[str] = set()

        html = self._fetch_page(CALENDAR_URL)
        if html:
            found = set(re.findall(
                r'href="(https://ashevilletheateralliance\.org/events/[^"?#]+/)"', html))
            self.logger.info(f"Calendar page yielded {len(found)} event links")
            urls |= found
        else:
            self.logger.warning("Calendar page unavailable; relying on REST discovery")

        # Supplement: REST posts modified recently (dates aren't in REST, but a
        # recent modification means the schedule was touched → likely upcoming).
        rest = self._fetch_page(REST_URL)
        if rest:
            try:
                posts = json.loads(rest)
                cutoff = datetime.now() - timedelta(days=90)
                recent = {p['link'] for p in posts
                          if p.get('link')
                          and datetime.fromisoformat(p.get('modified', '1970-01-01')) >= cutoff}
                new = recent - urls
                self.logger.info(f"REST supplement added {len(new)} recently-modified event links")
                urls |= recent
            except (json.JSONDecodeError, ValueError, KeyError, TypeError) as e:
                self.logger.warning(f"Could not parse REST supplement: {e}")

        return sorted(urls)

    def _parse_event_page(self, url: str) -> list[dict[str, Any]]:
        """Parse one ATA event page into one event dict per future performance."""
        html = self._fetch_page(url)
        if not html:
            return []

        # Title from <h1>
        m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
        if not m:
            self.logger.warning(f"No <h1> title at {url}; skipping")
            return []
        title = re.sub(r'<[^>]+>', '', html_mod.unescape(m.group(1))).strip()
        if not title:
            self.logger.warning(f"Empty title at {url}; skipping")
            return []

        # Strip tags to pipe-separated text for row/venue/price extraction
        text = html_mod.unescape(re.sub(r'<[^>]+>', '|', html))

        venue = ''
        vm = re.search(r'Venue:\s*\|*\s*([^|]+)', text)
        if vm:
            venue = vm.group(1).strip()

        producer = ''
        prm = re.search(r'Produced By:\s*\|*\s*([^|]+)', text)
        if prm:
            producer = prm.group(1).strip()
        if not venue and producer:
            # Some pages omit Venue; the producing company (often its own
            # theater, e.g. Hendersonville Theatre) is the best fallback.
            venue = producer

        price = ''
        pm = re.search(r'Standard Ticket Price:\s*\|*\s*\$\s*([\d.,]+)', text)
        if pm and pm.group(1).strip('.,') not in ('0', '00'):
            price = f"${pm.group(1).strip('.,')}"

        now = datetime.now(TZ)
        events = []
        seen: set[datetime] = set()
        for row in PERF_ROW_RE.finditer(text):
            mon_str, day_s, year_s, hh_s, mm_s, ampm = row.groups()
            month = MONTHS.get(mon_str[:3].lower())
            if not month:
                self.logger.debug(f"Unknown month {mon_str!r} at {url}")
                continue
            hour = int(hh_s) % 12
            if ampm.lower() == 'pm':
                hour += 12
            try:
                dtstart = datetime(int(year_s), month, int(day_s), hour, int(mm_s), tzinfo=TZ)
            except ValueError:
                self.logger.debug(f"Bad date row {row.group(0)!r} at {url}")
                continue
            if dtstart in seen:  # pages sometimes repeat a row
                continue
            seen.add(dtstart)
            if dtstart < now:
                continue

            desc_parts = [title]
            if venue:
                desc_parts.append(f"at {venue}")
            desc = ' '.join(desc_parts) + '.'
            if producer and producer != venue:
                desc += f" Produced by {producer}."
            if price:
                desc += f" Standard ticket price: {price}."

            events.append({
                'title': title,
                'dtstart': dtstart,
                'dtend': dtstart + timedelta(hours=2),
                'location': venue,
                'description': desc,
                'url': url,
            })

        if not events:
            self.logger.info(f"No future performances parsed at {url} ({title})")
        return events

    def fetch_events(self) -> list[dict[str, Any]]:
        event_urls = self._discover_event_urls()
        if not event_urls:
            return []

        self.logger.info(f"Fetching {len(event_urls)} event pages (parallel)...")
        all_events = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self._parse_event_page, u): u for u in event_urls}
            for future in as_completed(futures):
                all_events.extend(future.result())

        self.logger.info(f"Got {len(all_events)} future performances")
        return all_events


def main():
    parser = argparse.ArgumentParser(description="Scrape the Asheville Theater Alliance calendar")
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = AshevilleTheaterAllianceScraper()
    scraper.run(args.output)


if __name__ == '__main__':
    main()
