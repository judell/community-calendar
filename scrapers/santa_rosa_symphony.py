#!/usr/bin/env python3
"""
Scraper for Santa Rosa Symphony (srsymphony.org) events.

The Tribe ICS feed is broken (200/empty) and Tribe REST returns 0.
Events moved to an rg-event plugin, but the WordPress AJAX backdoor still works:
POST to /wp-admin/admin-ajax.php with action=cvf_event_pagination_load_tribe_events
returns rendered HTML cards for events. We paginate until empty.

Default location is Green Music Center unless the card specifies another venue.

Usage:
    python scrapers/santa_rosa_symphony.py --output cities/santarosa/santa_rosa_symphony.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from zoneinfo import ZoneInfo

from lib.base import BaseScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

AJAX_URL = 'https://www.srsymphony.org/wp-admin/admin-ajax.php'
BASE_URL = 'https://www.srsymphony.org'
DEFAULT_LOCATION = "Green Music Center, 1801 E Cotati Ave, Rohnert Park, CA"

# Months pattern
MONTHS = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12,
}


class SantaRosaSymphonyScraper(BaseScraper):
    """Scraper for Santa Rosa Symphony events via WordPress AJAX."""

    name = "Santa Rosa Symphony"
    domain = "srsymphony.org"
    timezone = "America/Los_Angeles"

    def _post_ajax(self, page: int) -> Optional[str]:
        payload = urlencode({
            'action': 'cvf_event_pagination_load_tribe_events',
            'page': str(page),
        }).encode('utf-8')
        headers = {
            **HEADERS,
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        req = Request(AJAX_URL, data=payload, headers=headers, method='POST')
        try:
            with urlopen(req, timeout=30) as resp:
                return resp.read().decode('utf-8')
        except (HTTPError, URLError) as e:
            self.logger.warning(f"AJAX request failed (page {page}): {e}")
            return None

    def _parse_events_from_html(self, html: str) -> list[dict[str, Any]]:
        """Parse event cards from AJAX-returned HTML fragment."""
        events = []
        now = datetime.now(ZoneInfo(self.timezone))

        # Each event card has: h3 (title), h4 (date text), h4 (venue), a.link href (detail URL)
        # Pattern: <h3>Title</h3> ... <h4>Date text</h4> <h4>Venue</h4>
        # Extract event blocks
        event_blocks = re.findall(
            r'<div class="event_item">(.*?)</div>\s*</div>\s*</div>',
            html, re.DOTALL
        )

        for block in event_blocks:
            try:
                event = self._parse_event_block(block, now)
                if event:
                    events.append(event)
            except Exception as e:
                self.logger.debug(f"Error parsing event block: {e}")

        return events

    def _parse_event_block(self, block: str, now: datetime) -> Optional[dict[str, Any]]:
        """Parse a single event card HTML block."""
        # Title from h3
        title_match = re.search(r'<h3>(.*?)</h3>', block, re.DOTALL)
        if not title_match:
            return None
        title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
        # Unescape HTML entities
        title = title.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&#8217;', "'").replace('&#8211;', '-').replace('&nbsp;', ' ')
        if not title:
            return None

        # Date text from h4 (first one)
        h4_blocks = re.findall(r'<h4>(.*?)</h4>', block, re.DOTALL)
        if not h4_blocks:
            return None

        date_text = re.sub(r'<[^>]+>', '', h4_blocks[0]).strip()
        # Venue from second h4 (if exists)
        venue = DEFAULT_LOCATION
        if len(h4_blocks) >= 2:
            venue_raw = re.sub(r'<[^>]+>', '', h4_blocks[1]).strip()
            if venue_raw:
                venue = venue_raw

        # Detail URL from a.link
        url_match = re.search(r'<a\s+href="([^"]+)"\s+class="link"', block)
        detail_url = url_match.group(1) if url_match else BASE_URL + '/events/'

        # Parse date text
        # Formats: "July 26, 2026", "October 10, 11 & 12, 2026", "April 25, 2027"
        dates = self._parse_date_text(date_text)
        if not dates:
            self.logger.debug(f"Could not parse date from: {date_text!r}")
            return None

        events_out = []
        for dt in dates:
            if dt < now:
                continue
            events_out.append({
                'title': title,
                'dtstart': dt,
                'dtend': dt,
                'location': venue,
                'description': f"Santa Rosa Symphony. See {detail_url} for details.",
                'url': detail_url,
            })

        return events_out[0] if events_out else None

    def _parse_date_text(self, text: str) -> list[datetime]:
        """
        Parse date text into datetime objects.

        Handles:
        - "July 26, 2026"
        - "October 10, 11 & 12, 2026"
        - "April 25, 2027"
        """
        text = text.strip()
        tz = ZoneInfo(self.timezone)

        # Try: "Month Day1, Day2 & Day3, Year"
        # General pattern: month + days + year
        # First extract year
        year_match = re.search(r'\b(20\d{2})\b', text)
        if not year_match:
            return []
        year = int(year_match.group(1))

        # Extract month
        month = None
        for month_name, month_num in MONTHS.items():
            if month_name in text.lower():
                month = month_num
                break
        if not month:
            return []

        # Extract all day numbers before the year
        days_part = text[:year_match.start()]
        day_nums = re.findall(r'\b(\d{1,2})\b', days_part)
        if not day_nums:
            return []

        dates = []
        for day_str in day_nums:
            day = int(day_str)
            try:
                dt = datetime(year, month, day, tzinfo=tz)
                dates.append(dt)
            except ValueError:
                continue

        return dates

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch all events by paginating the AJAX endpoint."""
        all_events = []
        page = 1
        max_pages = 20

        while page <= max_pages:
            self.logger.info(f"Fetching page {page}...")
            html = self._post_ajax(page)
            if not html:
                break

            # Check if any event content is present
            if not re.search(r'<div class="event_item">', html):
                self.logger.info(f"No more events at page {page}")
                break

            page_events = self._parse_events_from_html(html)
            self.logger.info(f"Page {page}: {len(page_events)} events")

            if not page_events:
                break

            all_events.extend(page_events)
            page += 1

        # Deduplicate by (title, date)
        seen = set()
        unique = []
        for ev in all_events:
            key = (ev['title'], ev['dtstart'].date() if hasattr(ev['dtstart'], 'date') else ev['dtstart'])
            if key not in seen:
                seen.add(key)
                unique.append(ev)

        self.logger.info(f"Total unique future events: {len(unique)}")
        return unique


def main():
    parser = argparse.ArgumentParser(description="Scrape Santa Rosa Symphony events")
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = SantaRosaSymphonyScraper()
    scraper.run(args.output)


if __name__ == '__main__':
    main()
