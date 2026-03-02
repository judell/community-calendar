#!/usr/bin/env python3
"""
Scraper for Turtle Back Zoo events (West Orange, NJ).

Turtle Back Zoo uses WordPress with Modern Events Calendar (MEC).
The MEC ICS feed doesn't work, but the WP REST API exposes mec-events
with dates embedded in post content HTML. We parse date patterns like:
  - "Sunday, March 1 @ 1-3 PM"
  - "Sunday, March 15, 2026 @10am"
  - "March 14" (standalone)

Usage:
    python scrapers/turtle_back_zoo.py --output cities/montclair/turtle_back_zoo.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import html as html_mod
import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

from lib.base import BaseScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

API_URL = "https://www.turtlebackzoo.com/wp-json/wp/v2/mec-events?per_page=50"
LOCATION = "Turtle Back Zoo, 560 Northfield Ave, West Orange, NJ 07052"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json',
}

# Match patterns like "Sunday, March 15, 2026 @10am" or "March 1 @ 1-3 PM"
DATE_TIME_RE = re.compile(
    r'(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)?,?\s*'
    r'((?:January|February|March|April|May|June|July|August|September|October|November|December)'
    r'\s+\d{1,2})'
    r'(?:,?\s*(\d{4}))?'  # optional year
    r'\s*@?\s*'
    r'(\d{1,2}(?::\d{2})?\s*(?:-\s*\d{1,2}(?::\d{2})?)?\s*(?:am|pm|AM|PM))?',  # optional time
    re.IGNORECASE
)

SKIP_TITLES = {'CLOSED', 'MODIFIED ZOO HOURS', 'Members Only', 'Holiday Lights', 'Seasonal Job Fair'}


def _parse_time(time_str: str) -> tuple[int, int]:
    """Parse time like '1-3 PM' or '10am' into (start_hour, end_hour)."""
    time_str = time_str.strip()
    # Extract start and optional end
    parts = re.split(r'\s*-\s*', time_str)
    ampm = 'am'
    if re.search(r'pm', time_str, re.IGNORECASE):
        ampm = 'pm'

    def parse_one(t: str) -> int:
        t = re.sub(r'[ap]m', '', t, flags=re.IGNORECASE).strip()
        if ':' in t:
            h, _ = t.split(':')
            h = int(h)
        else:
            h = int(t)
        if ampm == 'pm' and h < 12:
            h += 12
        if ampm == 'am' and h == 12:
            h = 0
        return h

    start_h = parse_one(parts[0])
    end_h = parse_one(parts[1]) if len(parts) > 1 else start_h + 2
    return start_h, end_h


class TurtleBackZooScraper(BaseScraper):
    """Scraper for Turtle Back Zoo via WP REST API + content date parsing."""

    name = "Turtle Back Zoo"
    domain = "turtlebackzoo.com"
    timezone = "America/New_York"

    def fetch_events(self) -> list[dict[str, Any]]:
        req = Request(API_URL, headers=HEADERS)
        try:
            with urlopen(req, timeout=30) as resp:
                posts = json.loads(resp.read().decode('utf-8'))
        except (HTTPError, URLError) as e:
            self.logger.warning(f"Failed to fetch WP API: {e}")
            return []

        now = datetime.now(timezone.utc)
        current_year = now.year
        all_events = []

        for post in posts:
            title = html_mod.unescape(post.get('title', {}).get('rendered', ''))

            # Skip non-event posts
            if any(skip in title for skip in SKIP_TITLES):
                continue

            content = html_mod.unescape(post.get('content', {}).get('rendered', ''))
            text = re.sub(r'<[^>]+>', ' ', content)
            link = post.get('link', '')

            for match in DATE_TIME_RE.finditer(text):
                date_str, year_str, time_str = match.groups()

                year = int(year_str) if year_str else current_year
                try:
                    dt = datetime.strptime(f"{date_str} {year}", '%B %d %Y')
                except ValueError:
                    continue

                # If no year given and date is in the past, try next year
                if not year_str and dt.replace(tzinfo=timezone.utc) < now:
                    dt = dt.replace(year=current_year + 1)

                dt = dt.replace(tzinfo=timezone.utc)
                if dt < now:
                    continue

                start_hour, end_hour = (10, 12)  # default
                if time_str:
                    start_hour, end_hour = _parse_time(time_str)

                dtstart = dt.replace(hour=start_hour)
                dtend = dt.replace(hour=end_hour)

                all_events.append({
                    'title': title,
                    'dtstart': dtstart,
                    'dtend': dtend,
                    'location': LOCATION,
                    'description': f'{title} at Turtle Back Zoo. {link}',
                    'url': link,
                })

        self.logger.info(f"Extracted {len(all_events)} future events from {len(posts)} posts")
        return all_events


def main():
    parser = argparse.ArgumentParser(description="Scrape Turtle Back Zoo events")
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    scraper = TurtleBackZooScraper()
    scraper.run(args.output)


if __name__ == '__main__':
    main()
