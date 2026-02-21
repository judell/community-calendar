#!/usr/bin/env python3
"""
Scraper for Cinnabar Theater (Petaluma, CA).

Usage:
    python scrapers/cinnabar.py --output cities/santarosa/cinnabar.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import re
from datetime import datetime
from typing import Any

import requests
from bs4 import BeautifulSoup

from lib.base import BaseScraper
from lib.utils import DEFAULT_HEADERS


class CinnabarScraper(BaseScraper):
    """Scraper for Cinnabar Theater shows."""

    name = "Cinnabar Theater"
    domain = "cinnabartheater.org"

    URL = "https://cinnabartheater.org/shows/"
    VENUE_ADDRESS = "Cinnabar Theater, 3333 Petaluma Blvd N, Petaluma, CA 94952"

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch shows from Cinnabar Theater."""
        self.logger.info(f"Fetching {self.URL}")
        response = requests.get(self.URL, headers=DEFAULT_HEADERS, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        events = []

        for show in soup.select('div.pp-content-post.type-show'):
            title_el = show.select_one('h3.pp-content-grid-title')
            dates_el = show.select_one('div.pp-content-grid-content p')
            url_el = show.select_one('a.pp-post-link')

            if not title_el or not dates_el:
                continue

            title = title_el.get_text(strip=True)
            date_text = dates_el.get_text(strip=True)
            url = url_el['href'] if url_el and url_el.get('href') else self.URL

            dtstart, dtend = self._parse_date_range(date_text)
            if not dtstart:
                self.logger.warning(f"Skipping {title}: couldn't parse '{date_text}'")
                continue

            events.append({
                'title': title,
                'dtstart': dtstart,
                'dtend': dtend or dtstart,
                'url': url,
                'location': self.VENUE_ADDRESS,
                'description': f"Performance dates: {date_text}",
            })

            self.logger.info(f"Found: {title} ({date_text})")

        return events

    @staticmethod
    def _parse_date_range(text: str) -> tuple:
        """Parse date ranges like:
        - 'September 12–28, 2025' (same month)
        - 'January 23–February 8, 2026' (cross month)
        - 'June 12-June 28, 2026' (cross month, repeated month name)
        - 'December 19-21, 2025' (same month, hyphen)
        """
        # Normalize dashes
        text = text.replace('–', '-').replace('—', '-').strip()

        # Pattern: "Month DD-Month DD, YYYY" (cross-month with repeated month name)
        m = re.match(r'(\w+)\s+(\d+)\s*-\s*(\w+)\s+(\d+),\s*(\d{4})', text)
        if m:
            try:
                dtstart = datetime.strptime(f"{m.group(1)} {m.group(2)}, {m.group(5)}", '%B %d, %Y')
                dtend = datetime.strptime(f"{m.group(3)} {m.group(4)}, {m.group(5)}", '%B %d, %Y')
                return dtstart, dtend
            except ValueError:
                pass

        # Pattern: "Month DD-DD, YYYY" (same month)
        m = re.match(r'(\w+)\s+(\d+)\s*-\s*(\d+),\s*(\d{4})', text)
        if m:
            try:
                dtstart = datetime.strptime(f"{m.group(1)} {m.group(2)}, {m.group(4)}", '%B %d, %Y')
                dtend = datetime.strptime(f"{m.group(1)} {m.group(3)}, {m.group(4)}", '%B %d, %Y')
                return dtstart, dtend
            except ValueError:
                pass

        # Pattern: single date "Month DD, YYYY"
        m = re.match(r'(\w+\s+\d+,\s*\d{4})', text)
        if m:
            try:
                dtstart = datetime.strptime(m.group(1), '%B %d, %Y')
                return dtstart, None
            except ValueError:
                pass

        return None, None


if __name__ == '__main__':
    CinnabarScraper.main()
