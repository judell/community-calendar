#!/usr/bin/env python3
"""
Scraper for Spreckels Performing Arts Center (Rohnert Park, CA).

The site dropped The Events Calendar (Tribe) in its 2026 redesign; the REST
API at /wp-json/tribe/events/v1/events now returns 404. Shows are
server-rendered Divi pages at /show/<season>-season/<slug>/ with the run
dates in adjacent text modules ("September 25" / "– October 11") and no
explicit year — the year is inferred from the season slug (months
August–December belong to the first season year, January–July to the
second). Ticketing is via Arts People links; no per-performance times are
exposed, so events are emitted as all-day date ranges.

Usage:
    python scrapers/spreckels.py --output cities/santarosa/spreckels.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import re
from datetime import datetime
from typing import Any, Optional

import requests
from bs4 import BeautifulSoup

from lib.base import BaseScraper
from lib.utils import DEFAULT_HEADERS


class SpreckelsScraper(BaseScraper):
    """Scraper for Spreckels Performing Arts Center show pages."""

    name = "Spreckels Performing Arts Center"
    domain = "spreckelsonline.com"

    BASE_URL = "https://spreckelsonline.com/"
    VENUE_ADDRESS = "Spreckels Performing Arts Center, 5409 Snyder Ln, Rohnert Park, CA 94928"

    SHOW_LINK_RE = re.compile(
        r'https://spreckelsonline\.com/show/(\d{4})-(\d{2})-season/[^"\'#?]+/')
    SEASON_LINK_RE = re.compile(
        r'https://spreckelsonline\.com/\d{4}-\d{2}-season/')

    MONTHS = {name: num for num, name in enumerate(
        ['january', 'february', 'march', 'april', 'may', 'june', 'july',
         'august', 'september', 'october', 'november', 'december'], start=1)}

    def fetch_events(self) -> list[dict[str, Any]]:
        """Discover show pages from the homepage and season indexes, then
        parse each show page for title, date range, and theatre."""
        show_urls: dict[str, tuple[int, int]] = {}

        index_pages = [self.BASE_URL]
        try:
            home_html = self._get(self.BASE_URL)
            index_pages += sorted(set(self.SEASON_LINK_RE.findall(home_html)))
            self._collect_show_urls(home_html, show_urls)
        except requests.RequestException as e:
            self.logger.warning(f"Failed to fetch {self.BASE_URL}: {e}")

        for page in index_pages[1:]:
            try:
                self._collect_show_urls(self._get(page), show_urls)
            except requests.RequestException as e:
                self.logger.warning(f"Failed to fetch {page}: {e}")

        if not show_urls:
            self.logger.warning("No show pages discovered")
            return []

        events = []
        for url, season_years in sorted(show_urls.items()):
            try:
                event = self._parse_show(url, season_years)
            except requests.RequestException as e:
                self.logger.warning(f"Failed to fetch {url}: {e}")
                continue
            if event:
                events.append(event)

        return events

    def _get(self, url: str) -> str:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=30)
        response.raise_for_status()
        return response.text

    def _collect_show_urls(self, html: str, show_urls: dict) -> None:
        for m in self.SHOW_LINK_RE.finditer(html):
            year1 = int(m.group(1))
            year2 = year1 - year1 % 100 + int(m.group(2))
            if year2 < year1:
                year2 += 100  # century wrap, e.g. 2099-00
            show_urls[m.group(0)] = (year1, year2)

    def _parse_show(self, url: str, season_years: tuple[int, int]) -> Optional[dict]:
        html = self._get(url)
        soup = BeautifulSoup(html, 'html.parser')

        title_el = soup.find('h1')
        title = title_el.get_text(strip=True) if title_el else ''
        if not title:
            self.logger.warning(f"Skipping {url}: no title found")
            return None

        # Divi text modules: consecutive short paragraphs carry
        # "September 25", "– October 11", then the theatre name.
        paragraphs = [p.get_text(strip=True).replace('–', '-').replace('—', '-')
                      for p in soup.select('div.et_pb_text_inner p')]
        paragraphs = [p for p in paragraphs if p and len(p) < 60]

        dtstart = dtend = None
        theatre = ''
        for i, text in enumerate(paragraphs):
            start = self._parse_month_day(text)
            if not start:
                continue
            end = None
            if i + 1 < len(paragraphs):
                m = re.match(r'-\s*(.+)$', paragraphs[i + 1])
                if m:
                    end = self._parse_month_day(m.group(1))
                    for later in paragraphs[i + 2:i + 4]:
                        if re.search(r'\btheat(re|er)\b', later, re.IGNORECASE):
                            theatre = later
                            break
            dtstart = self._apply_season_year(start, season_years)
            dtend = self._apply_season_year(end, season_years) if end else dtstart
            if dtend < dtstart:
                dtend = dtstart
            break

        if not dtstart:
            self.logger.warning(f"Skipping {title}: no run dates found at {url}")
            return None

        location = self.VENUE_ADDRESS
        if theatre:
            location = f"{theatre}, {self.VENUE_ADDRESS}"

        date_text = dtstart.strftime('%B %-d')
        if dtend != dtstart:
            date_text += dtend.strftime(' - %B %-d, %Y')
        else:
            date_text += dtstart.strftime(', %Y')

        self.logger.info(f"Found: {title} ({date_text})")
        return {
            'title': title,
            'dtstart': dtstart,
            'dtend': dtend,
            'url': url,
            'location': location,
            'description': f"Performance dates: {date_text}. Tickets at {url}",
        }

    @classmethod
    def _parse_month_day(cls, text: str) -> Optional[tuple[int, int]]:
        """Parse 'September 25' / 'Sept. 25' into (month, day)."""
        m = re.match(r'^([A-Za-z.]+)\s+(\d{1,2})$', text.strip())
        if not m:
            return None
        token = m.group(1).rstrip('.').lower()
        if len(token) < 3:
            return None
        for name, num in cls.MONTHS.items():
            if name.startswith(token):
                return num, int(m.group(2))
        return None

    @staticmethod
    def _apply_season_year(month_day: tuple[int, int], season_years: tuple[int, int]) -> datetime:
        """A season like 2026-27 runs Aug–Dec in the first year and
        Jan–Jul in the second."""
        month, day = month_day
        year = season_years[0] if month >= 8 else season_years[1]
        return datetime(year, month, day)


if __name__ == '__main__':
    SpreckelsScraper.main()
