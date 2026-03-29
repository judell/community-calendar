#!/usr/bin/env python3
"""Scraper for Habitat for Humanity of Monroe County events."""

import re
import sys
from datetime import datetime, timedelta
from typing import Any, Optional
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from lib.base import BaseScraper

MONTHS = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
    'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12,
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


class HabitatScraper(BaseScraper):
    """Scraper for Habitat for Humanity of Monroe County."""

    name = "Habitat for Humanity Monroe County"
    domain = "monroecountyhabitat.org"
    events_url = "https://monroecountyhabitat.org/who-we-are/"
    timezone = "America/Indiana/Indianapolis"

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from the who-we-are page #events section."""
        self.logger.info(f"Fetching {self.events_url}")
        response = requests.get(self.events_url, headers=HEADERS, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        events_section = soup.find(id='events')
        if not events_section:
            self.logger.warning("No #events section found")
            return []

        tz = ZoneInfo(self.timezone)
        now = datetime.now(tz)
        events = []
        seen = set()

        for h3 in events_section.select('h3'):
            title = h3.get_text(strip=True)
            if title in seen:
                continue
            seen.add(title)

            parent = h3.parent
            if not parent:
                continue

            h1 = parent.select_one('h1')
            h2 = parent.select_one('h2')
            if not h1 or not h2:
                continue

            month_str = h1.get_text(strip=True)
            day_str = h2.get_text(strip=True)

            month = MONTHS.get(month_str, 0)
            if not month:
                continue
            day = int(day_str)

            # Infer year: use current year, bump to next if month is past
            year = now.year
            if month < now.month or (month == now.month and day < now.day):
                year += 1

            dtstart = datetime(year, month, day, 12, 0, tzinfo=tz)
            dtend = dtstart + timedelta(hours=3)

            a = parent.select_one('a[href*=events]')
            url = a.get('href', '') if a else ''

            # Get description from first <p>
            desc_p = parent.select_one('p')
            description = desc_p.get_text(strip=True)[:300] if desc_p else ''

            slug = re.sub(r'[^a-z0-9]+', '-', title.lower())[:40]
            uid = f"habitat-{year}{month:02d}{day:02d}-{slug}@monroecountyhabitat.org"

            events.append({
                'title': title,
                'dtstart': dtstart,
                'dtend': dtend,
                'url': url,
                'location': 'Bloomington, IN',
                'description': description,
                'uid': uid,
            })

        self.logger.info(f"Found {len(events)} events")
        return events


if __name__ == '__main__':
    HabitatScraper.main()
