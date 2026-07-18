#!/usr/bin/env python3
"""
Parameterized scraper for GatherBoard community-calendar sites.

GatherBoard (gatherboard.com) powers local event listing sites.
The homepage server-renders event listings with date-pattern URLs
(/MM/DD/YYYY/slug/). Each event detail page has a per-event ICS link
at /{hex-id}/ical/ (PRODID: GatherBoard.com). We discover events from
the listing pages, fetch the ICS from each detail page, and merge.

Known sites:
  - https://www.sonomavalleyevents.com  (Sonoma Valley aggregator)

Usage:
    python scrapers/gatherboard.py \\
        --url "https://www.sonomavalleyevents.com" \\
        --name "Sonoma Valley Events" \\
        --output cities/santarosa/sonoma_valley_events.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urljoin
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

from icalendar import Calendar as ICalendar

from lib.base import BaseScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


class GatherBoardScraper(BaseScraper):
    """Parameterized scraper for GatherBoard community calendar sites."""

    def __init__(self, site_url: str, source_name: str, tz: str = "America/Los_Angeles"):
        self.site_url = site_url.rstrip('/')
        self.name = source_name
        self.domain = re.sub(r'^https?://(www\.)?', '', site_url).rstrip('/').split('/')[0]
        self.timezone = tz
        super().__init__()

    def _fetch(self, url: str) -> Optional[str]:
        req = Request(url, headers=HEADERS)
        try:
            with urlopen(req, timeout=30) as resp:
                return resp.read().decode('utf-8', errors='replace')
        except (HTTPError, URLError) as e:
            self.logger.warning(f"Failed to fetch {url}: {e}")
            return None

    def _discover_event_paths(self) -> list[str]:
        """Scrape listing pages to find all event detail URL paths."""
        seen = set()
        paths = []

        # Start from homepage; follow 'next page' pagination links
        next_url = self.site_url + '/'
        page_num = 0
        max_pages = 30
        visited_urls = set()

        while next_url and page_num < max_pages:
            # Normalize URL for loop detection
            norm_url = next_url.rstrip('/')
            if norm_url in visited_urls:
                self.logger.info(f"Pagination loop detected at {next_url}, stopping")
                break
            visited_urls.add(norm_url)

            self.logger.info(f"Fetching listing page: {next_url}")
            html = self._fetch(next_url)
            if not html:
                break

            # Find relative date-pattern event links: MM/DD/YYYY/slug/
            new_links = re.findall(
                r'href=["\'](\d{2}/\d{2}/\d{4}/[^"\'>\s]+)["\']',
                html
            )
            # Also absolute links to this domain
            abs_links = re.findall(
                rf'href=["\']({re.escape(self.site_url)}/\d{{2}}/\d{{2}}/\d{{4}}/[^"\'>\s]+)["\']',
                html
            )
            for link in new_links:
                # Preserve trailing slash — the server 404s without it
                path = '/' + link
                if not path.endswith('/'):
                    path += '/'
                if path not in seen:
                    seen.add(path)
                    paths.append(path)
            for link in abs_links:
                path = link[len(self.site_url):]
                if not path.endswith('/'):
                    path += '/'
                if path not in seen:
                    seen.add(path)
                    paths.append(path)

            # Find next-page pagination link
            # Links look like: .../view/next/page/N/DayChange/Forward/LastDate/MM-DD-YYYY/
            # Find all page links and pick the highest-numbered one we haven't visited
            all_page_links = re.findall(
                r'href=["\'](' + re.escape(self.site_url) + r'/view/next/page/(\d+)/[^"\']*)["\']',
                html
            )
            candidate = None
            best_page = 0
            for link_url, page_n_str in all_page_links:
                page_n = int(page_n_str)
                norm = link_url.rstrip('/')
                if norm not in visited_urls and page_n > best_page:
                    best_page = page_n
                    candidate = link_url
            if candidate:
                raw_url = candidate
                next_url = raw_url if raw_url.endswith('/') else raw_url + '/'
                page_num += 1
            else:
                break

        self.logger.info(f"Discovered {len(paths)} unique event paths")
        return paths

    def _fetch_event_from_detail(self, path: str) -> Optional[dict[str, Any]]:
        """Fetch an event detail page, extract the ICS link, parse the event."""
        detail_url = self.site_url + path
        html = self._fetch(detail_url)
        if not html:
            return None

        # Find the per-event ICS link: /{hex-id}/ical/
        ics_match = re.search(
            r'href=["\'](' + re.escape(self.site_url) + r'/[a-f0-9]+/ical/)["\']',
            html, re.IGNORECASE
        )
        if not ics_match:
            # Try without site prefix (relative)
            ics_match = re.search(
                r'href=["\'](/[a-f0-9]+/ical/)["\']',
                html, re.IGNORECASE
            )
            if ics_match:
                ics_url = self.site_url + ics_match.group(1)
            else:
                self.logger.debug(f"No ICS link found on {detail_url}")
                return None
        else:
            ics_url = ics_match.group(1)

        # Fetch the ICS
        ics_content = self._fetch(ics_url)
        if not ics_content:
            return None

        return self._parse_ics(ics_content, detail_url)

    def _parse_ics(self, ics_content: str, fallback_url: str) -> Optional[dict[str, Any]]:
        """Parse a per-event ICS file into an event dict.

        GatherBoard ICS quirks:
        - X-WR-CALNAME contains the event title
        - SUMMARY contains the event description (not the title)
        - LOCATION merges venue name + address without separator
        """
        try:
            cal = ICalendar.from_ical(ics_content)
        except Exception as e:
            self.logger.debug(f"Failed to parse ICS: {e}")
            return None

        now = datetime.now(timezone.utc)

        # Extract calendar-level title (X-WR-CALNAME) which holds the real event name
        cal_name = str(cal.get('x-wr-calname', '')).strip()

        for component in cal.walk():
            if component.name != 'VEVENT':
                continue

            dtstart_raw = component.get('dtstart')
            if dtstart_raw is None:
                continue

            dtstart = dtstart_raw.dt
            # Normalize to datetime for comparison
            if hasattr(dtstart, 'hour'):
                dt_for_compare = dtstart if dtstart.tzinfo else dtstart.replace(tzinfo=timezone.utc)
            else:
                dt_for_compare = datetime(dtstart.year, dtstart.month, dtstart.day, tzinfo=timezone.utc)

            if dt_for_compare < now:
                return None

            dtend_raw = component.get('dtend')
            dtend = dtend_raw.dt if dtend_raw else dtstart

            url_prop = component.get('url')
            url = str(url_prop) if url_prop else fallback_url

            # SUMMARY in GatherBoard ICS is the description text, not the event name
            summary_raw = str(component.get('summary', '')).strip()

            # Use X-WR-CALNAME as title; fall back to SUMMARY if it looks like a real title
            if cal_name and len(cal_name) < 150:
                title = cal_name
                description = summary_raw[:500]
            elif summary_raw and len(summary_raw) < 150:
                title = summary_raw
                description = ''
            elif summary_raw:
                # Long summary is really the description
                title = summary_raw[:100].rsplit(' ', 1)[0] + '...'
                description = summary_raw[:500]
            else:
                return None

            if not title:
                return None

            location = str(component.get('location', '')) or ''

            return {
                'title': title,
                'dtstart': dtstart,
                'dtend': dtend,
                'location': location,
                'description': description[:500],
                'url': url,
            }

        return None

    def fetch_events(self) -> list[dict[str, Any]]:
        """Discover and fetch all events from this GatherBoard site."""
        paths = self._discover_event_paths()
        if not paths:
            self.logger.warning("No event paths discovered")
            return []

        events = []
        self.logger.info(f"Fetching {len(paths)} event detail pages...")

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self._fetch_event_from_detail, p): p for p in paths}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    events.append(result)

        self.logger.info(f"Got {len(events)} future events")
        return events


def main():
    parser = argparse.ArgumentParser(description="Scrape a GatherBoard community calendar site")
    parser.add_argument('--url', required=True, help='Site base URL (e.g. https://www.sonomavalleyevents.com)')
    parser.add_argument('--name', required=True, help='Source display name')
    parser.add_argument('--timezone', default='America/Los_Angeles', help='IANA timezone')
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = GatherBoardScraper(args.url, args.name, args.timezone)
    scraper.run(args.output)


if __name__ == '__main__':
    main()
