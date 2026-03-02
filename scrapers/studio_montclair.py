#!/usr/bin/env python3
"""
Scraper for Studio Montclair exhibitions and events.

Studio Montclair's mod_security blocks ICS requests, but the WordPress
REST API works fine. Exhibition posts contain dates in consistent patterns:
  - "Exhibition Dates: January 30 to February 27, 2026"
  - "Opening Reception: Friday, January 30, 6:00-8:00pm"
  - "The program is Thursday, February 5, 2026 ... program begins at 7pm"

We parse these from post content and generate calendar events for:
  1. Opening receptions
  2. Panel discussions / special programs
  3. The exhibition run (as a single long event)

Usage:
    python scrapers/studio_montclair.py --output cities/montclair/studio_montclair.ics
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
logger = logging.getLogger(__name__)

API_URL = "https://studiomontclair.org/wp-json/wp/v2/posts?per_page=10&orderby=date&order=desc"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json',
}

# Galleries
GALLERIES = {
    'leach': 'Leach Gallery, 641 Bloomfield Ave, Montclair, NJ 07042',
    'academy': 'Academy Square Gallery, 33 Plymouth St, Montclair, NJ 07042',
}


def _strip_html(s: str) -> str:
    """Remove HTML tags and normalize whitespace."""
    s = re.sub(r'\[/?vc_[^\]]*\]', ' ', s)  # WPBakery shortcodes
    s = re.sub(r'<[^>]+>', ' ', s)
    s = html_mod.unescape(s)
    return re.sub(r'\s+', ' ', s).strip()


def _parse_month_day_year(text: str, default_year: int = 2026) -> Optional[datetime]:
    """Parse 'January 30, 2026' or 'January 30' into datetime."""
    m = re.match(
        r'(January|February|March|April|May|June|July|August|September|October|November|December)'
        r'\s+(\d{1,2})(?:\s*,?\s*(\d{4}))?',
        text.strip()
    )
    if not m:
        return None
    month_str, day_str, year_str = m.groups()
    month = datetime.strptime(month_str, '%B').month
    day = int(day_str)
    year = int(year_str) if year_str else default_year
    return datetime(year, month, day, tzinfo=timezone.utc)


class StudioMontclairScraper(BaseScraper):
    """Scraper for Studio Montclair via WordPress REST API."""

    name = "Studio Montclair"
    domain = "studiomontclair.org"
    timezone = "America/New_York"

    def _detect_gallery(self, text: str) -> str:
        """Detect which gallery from post content."""
        text_lower = text.lower()
        if 'academy square' in text_lower or '33 plymouth' in text_lower:
            return GALLERIES['academy']
        return GALLERIES['leach']  # default

    def _extract_events_from_post(self, post: dict) -> list[dict[str, Any]]:
        """Extract exhibition and event dates from a single WP post."""
        title = html_mod.unescape(post['title']['rendered'])
        content = post['content']['rendered']
        text = _strip_html(content)
        link = post['link']
        events = []

        now = datetime.now(timezone.utc)
        location = self._detect_gallery(text)

        # 1. Exhibition dates: "January 30 to February 27, 2026"
        # Handle optional spaces around commas and line breaks in original
        exh_match = re.search(
            r'(?:Exhibition Dates?:?\s*)?'
            r'((?:January|February|March|April|May|June|July|August|September|October|November|December)'
            r'\s+\d{1,2})\s*'
            r'to\s*'
            r'((?:January|February|March|April|May|June|July|August|September|October|November|December)'
            r'\s+\d{1,2}\s*,?\s*\d{4})',
            text
        )
        if exh_match:
            end_dt = _parse_month_day_year(exh_match.group(2))
            if end_dt:
                start_dt = _parse_month_day_year(exh_match.group(1), default_year=end_dt.year)
                if start_dt and end_dt >= now:
                    events.append({
                        'title': f'{title} (Exhibition)',
                        'dtstart': start_dt,
                        'dtend': end_dt,
                        'location': location,
                        'description': f'Exhibition at Studio Montclair. {link}',
                        'url': link,
                    })

        # 2. Opening reception: "Opening Reception: Friday, January 30, 6:00-8:00pm"
        recep_match = re.search(
            r'Opening Reception:?\s*'
            r'(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)?,?\s*'
            r'((?:January|February|March|April|May|June|July|August|September|October|November|December)'
            r'\s+\d{1,2})\s*,?\s*'
            r'(\d{1,2}:\d{2})\s*-?\s*(\d{1,2}:\d{2})\s*(pm|am)?',
            text, re.IGNORECASE
        )
        if recep_match:
            year_guess = end_dt.year if exh_match and end_dt else 2026
            dt = _parse_month_day_year(recep_match.group(1), default_year=year_guess)
            if dt and dt >= now:
                start_time = recep_match.group(2)
                end_time = recep_match.group(3)
                sh, sm = map(int, start_time.split(':'))
                eh, em = map(int, end_time.split(':'))
                # Assume PM for evening receptions
                if sh < 12:
                    sh += 12
                if eh < 12:
                    eh += 12
                dtstart = dt.replace(hour=sh, minute=sm)
                dtend = dt.replace(hour=eh, minute=em)
                events.append({
                    'title': f'{title} — Opening Reception',
                    'dtstart': dtstart,
                    'dtend': dtend,
                    'location': location,
                    'description': f'Opening reception for "{title}" at Studio Montclair. {link}',
                    'url': link,
                })

        # 3. Special programs: "The program is Thursday, February 5, 2026 ... program begins at 7pm"
        prog_matches = re.finditer(
            r'(?:program is|program on)\s*'
            r'(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)?,?\s*'
            r'((?:January|February|March|April|May|June|July|August|September|October|November|December)'
            r'\s+\d{1,2})\s*,?\s*(\d{4})?',
            text, re.IGNORECASE
        )
        for pm in prog_matches:
            year = int(pm.group(2)) if pm.group(2) else (end_dt.year if exh_match and end_dt else 2026)
            dt = _parse_month_day_year(pm.group(1), default_year=year)
            if not dt or dt < now:
                continue

            # Look for time near this match
            after_text = text[pm.end():pm.end() + 200]
            time_match = re.search(r'(?:begins? at|at)\s*(\d{1,2})(?::(\d{2}))?\s*(pm|am)', after_text, re.IGNORECASE)
            hour = 19  # default 7pm
            if time_match:
                hour = int(time_match.group(1))
                if time_match.group(3).lower() == 'pm' and hour < 12:
                    hour += 12

            # Try to extract program topic from nearby text
            before_text = text[max(0, pm.start() - 200):pm.start()]
            topic_match = re.search(r'((?:Panel|Discussion|Talk|Lecture|Workshop)[^.]*)', before_text, re.IGNORECASE)
            topic = topic_match.group(1).strip() if topic_match else 'Special Program'

            dtstart = dt.replace(hour=hour)
            events.append({
                'title': f'{title} — {topic}',
                'dtstart': dtstart,
                'dtend': dtstart.replace(hour=hour + 2),
                'location': location,
                'description': f'Program at Studio Montclair. {link}',
                'url': link,
            })

        return events

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch posts from WP REST API and extract events."""
        req = Request(API_URL, headers=HEADERS)
        try:
            with urlopen(req, timeout=30) as resp:
                posts = json.loads(resp.read().decode('utf-8'))
        except (HTTPError, URLError) as e:
            self.logger.warning(f"Failed to fetch WP API: {e}")
            return []

        all_events = []
        for post in posts:
            events = self._extract_events_from_post(post)
            all_events.extend(events)

        self.logger.info(f"Extracted {len(all_events)} events from {len(posts)} posts")
        return all_events


def main():
    parser = argparse.ArgumentParser(description="Scrape Studio Montclair exhibitions and events")
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = StudioMontclairScraper()
    scraper.run(args.output)


if __name__ == '__main__':
    main()
