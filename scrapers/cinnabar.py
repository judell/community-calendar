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

    MONTHS = {name: num for num, name in enumerate(
        ['january', 'february', 'march', 'april', 'may', 'june', 'july',
         'august', 'september', 'october', 'november', 'december'], start=1)}

    @classmethod
    def _month_num(cls, token: str):
        """Resolve a month token — full ('September'), abbreviated ('Sep',
        'Sept.'), with or without a trailing period — to its number."""
        t = token.strip().rstrip('.').lower()
        if len(t) < 3:
            return None
        for name, num in cls.MONTHS.items():
            if name.startswith(t):
                return num
        return None

    @classmethod
    def _parse_date_range(cls, text: str) -> tuple:
        """Parse date ranges like:
        - 'September 12–28, 2025' (same month)
        - 'January 23–February 8, 2026' (cross month)
        - 'June 12-June 28, 2026' (cross month, repeated month name)
        - 'December 19-21, 2025' (same month, hyphen)
        - 'Sept. 18 – Oct. 4 2026' (abbreviated months, no comma)
        - 'Jan. 22 – Feb. 7, 2027' (abbreviated months with periods)
        - 'April 9 – 25 2027' (same month, no comma before year)
        """
        # Normalize dashes
        text = text.replace('–', '-').replace('—', '-').strip()

        # Pattern: "Month DD - Month DD[,] YYYY" (cross month; abbreviations ok)
        m = re.match(r'([A-Za-z.]+)\s+(\d{1,2})\s*-\s*([A-Za-z.]+)\s+(\d{1,2}),?\s+(\d{4})', text)
        if m:
            start_month = cls._month_num(m.group(1))
            end_month = cls._month_num(m.group(3))
            year = int(m.group(5))
            if start_month and end_month:
                try:
                    dtstart = datetime(year, start_month, int(m.group(2)))
                    # A range like 'Dec. 19 - Jan. 4 2027' wraps into the next year
                    end_year = year + 1 if end_month < start_month else year
                    dtend = datetime(end_year, end_month, int(m.group(4)))
                    return dtstart, dtend
                except ValueError:
                    pass

        # Pattern: "Month DD-DD[,] YYYY" (same month; abbreviations ok)
        m = re.match(r'([A-Za-z.]+)\s+(\d{1,2})\s*-\s*(\d{1,2}),?\s+(\d{4})', text)
        if m:
            month = cls._month_num(m.group(1))
            if month:
                try:
                    year = int(m.group(4))
                    dtstart = datetime(year, month, int(m.group(2)))
                    dtend = datetime(year, month, int(m.group(3)))
                    return dtstart, dtend
                except ValueError:
                    pass

        # Pattern: single date "Month DD[,] YYYY" (abbreviations ok)
        m = re.match(r'([A-Za-z.]+)\s+(\d{1,2}),?\s+(\d{4})', text)
        if m:
            month = cls._month_num(m.group(1))
            if month:
                try:
                    dtstart = datetime(int(m.group(3)), month, int(m.group(2)))
                    return dtstart, None
                except ValueError:
                    pass

        return None, None


if __name__ == '__main__':
    CinnabarScraper.main()
