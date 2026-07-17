#!/usr/bin/env python3
"""
Scraper for Haw Creek Community Association (hawcreekavl.com).

Platform: Wild Apricot.
RSS feed: https://hawcreekavl.com/events/RSS redirects to the canonical
Wild Apricot RSS URL, which includes upcoming events with their start times
encoded as pubDate (UTC).

Usage:
    python scrapers/haw_creek.py --output cities/asheville/haw_creek.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import logging
import re
from datetime import timedelta
from html import unescape
from typing import Any, Optional

from bs4 import BeautifulSoup

from lib.wild_apricot_rss import WildApricotRssScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class HawCreekScraper(WildApricotRssScraper):
    """
    Scraper for Haw Creek Community Association events via Wild Apricot RSS.

    Wild Apricot encodes the event start time in the RSS <pubDate> field
    (as UTC). The event listing page redirect to the canonical RSS URL:
    https://hawcreekavl.com/events/RSS → page-7741/EventModule/6456050/RSS
    """

    name = "Haw Creek Community Association"
    domain = "hawcreekavl.com"
    timezone = "America/New_York"
    default_location = "Haw Creek, Asheville, NC"

    # Primary URL redirects correctly; canonical URL as fallback
    rss_fallback_urls = [
        "https://hawcreekavl.com/events/RSS",
        "http://hawcreekavl.com/page-7741/EventModule/6456050/RSS",
    ]

    # Wild Apricot titles often include the date in parentheses; strip it
    # clean_title() in WildApricotRssScraper already handles "(MM/DD/YYYY)" patterns.

    # Haw Creek events are small community gatherings — 2 hours is a safe default
    def default_duration(self, title: str, text: str) -> timedelta:
        blob = f"{title} {text}".lower()
        if any(w in blob for w in ["meeting", "board", "agenda"]):
            return timedelta(hours=1, minutes=30)
        if any(w in blob for w in ["potluck", "dinner", "festival", "fair", "concert", "music"]):
            return timedelta(hours=3)
        return timedelta(hours=2)

    def parse_entry(self, entry: dict) -> Optional[dict[str, Any]]:
        """
        Parse a Wild Apricot RSS item into an event dict.

        Wild Apricot encodes the event start time as the RSS <pubDate>
        (UTC). parse_rss_date() converts UTC → America/New_York.
        """
        dt_start = self.parse_rss_date(entry)
        if not dt_start:
            self.logger.debug(f"No date for entry: {entry.get('title','?')}")
            return None

        title = self.clean_title(entry.get('title', ''))
        if not title:
            return None

        description_html = entry.get('description', '') or ''
        soup = BeautifulSoup(description_html, 'html.parser')
        text = unescape(soup.get_text(' ', strip=True))
        text = re.sub(r'\s+', ' ', text).strip()

        # Try to extract a specific location from description text
        location = self._extract_haw_creek_location(text)
        if not location:
            location = self.default_location

        description = text[:700] + ('...' if len(text) > 700 else '')

        dt_end = dt_start + self.default_duration(title, text)

        return {
            'title': title,
            'dtstart': dt_start,
            'dtend': dt_end,
            'url': entry.get('link', ''),
            'location': location,
            'description': description,
        }

    def _extract_haw_creek_location(self, text: str) -> Optional[str]:
        """
        Pull a meeting/venue location from description text when present.
        Wild Apricot descriptions often name the venue explicitly.
        """
        patterns = [
            r'\bat\s+((?:Groce\b|Haw Creek\b)[^.<]{3,80})',
            r'\bat\s+([A-Z][^.<]{5,80}(?:Church|Center|Hall|Park|School|Library|Pavilion))',
            r'(?:held|located|meet)\s+at\s+([^.<]{5,80})',
            r'Location:\s*([^.<\n]{5,100})',
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                loc = m.group(1).strip()
                # Trim trailing noise
                loc = re.split(r'\.\s|\bThis\b|\bWe\b|\bEvery\b', loc, maxsplit=1)[0].strip()
                if 5 < len(loc) < 150:
                    return loc
        return None


if __name__ == '__main__':
    HawCreekScraper.main()
