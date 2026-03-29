#!/usr/bin/env python3
"""Scraper for Monroe County History Center events (EventON via WP REST API)."""

import re
import sys
from datetime import datetime, timedelta
from typing import Any, Optional
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from lib.base import BaseScraper

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; CommunityCalendar/1.0)',
    'Accept': 'application/json',
}

MONTHS = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
}


class HistoryCenterScraper(BaseScraper):
    """Scraper for Monroe County History Center."""

    name = "Monroe County History Center"
    domain = "monroehistory.org"
    api_url = "https://monroehistory.org/wp-json/wp/v2/ajde_events"
    timezone = "America/Indiana/Indianapolis"

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events via WP REST API, then scrape detail pages for dates."""
        self.logger.info(f"Fetching event list from {self.api_url}")
        tz = ZoneInfo(self.timezone)
        events = []
        seen_slugs = set()

        page = 1
        while True:
            response = requests.get(f"{self.api_url}?per_page=50&page={page}",
                                    headers=HEADERS, timeout=30)
            if response.status_code != 200:
                break

            items = response.json()
            if not items:
                break

            for item in items:
                slug = item.get('slug', '')
                if slug in seen_slugs:
                    continue
                seen_slugs.add(slug)

                url = item.get('link', '')
                title = item.get('title', {}).get('rendered', '')
                if not title or not url:
                    continue

                parsed = self._fetch_detail(url, title, tz)
                if parsed:
                    events.append(parsed)

            page += 1
            if page > 5:
                break

        self.logger.info(f"Found {len(events)} events")
        return events

    def _fetch_detail(self, url: str, title: str, tz: ZoneInfo) -> Optional[dict[str, Any]]:
        """Fetch an event detail page and parse the EventON inline date."""
        try:
            r = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }, timeout=15)
            r.raise_for_status()
        except Exception as e:
            self.logger.debug(f"Could not fetch {url}: {e}")
            return None

        soup = BeautifulSoup(r.text, 'html.parser')

        # Find the date string: "28mar1:00 pm2:30 pmTitle..."
        for p in soup.select('p'):
            text = p.get_text(strip=True)
            m = re.match(
                r'(\d{1,2})(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)'
                r'(\d{1,2}:\d{2}\s*[ap]m)'
                r'(\d{1,2}:\d{2}\s*[ap]m)',
                text, re.IGNORECASE
            )
            if m:
                day = int(m.group(1))
                month = MONTHS[m.group(2).lower()]
                start_time = m.group(3).strip()
                end_time = m.group(4).strip()

                now = datetime.now(tz)
                year = now.year
                if month < now.month or (month == now.month and day < now.day):
                    year += 1

                dtstart = self._make_dt(year, month, day, start_time, tz)
                dtend = self._make_dt(year, month, day, end_time, tz)

                if not dtstart:
                    continue

                # Get description from content
                desc = ''
                for dp in soup.select('p'):
                    dt = dp.get_text(strip=True)
                    if len(dt) > 30 and not re.match(r'\d{1,2}(jan|feb|mar|apr)', dt, re.I):
                        desc = dt[:300]
                        break

                slug = re.sub(r'[^a-z0-9]+', '-', title.lower())[:40]
                uid = f"mchc-{year}{month:02d}{day:02d}-{slug}@monroehistory.org"

                return {
                    'title': title,
                    'dtstart': dtstart,
                    'dtend': dtend or dtstart + timedelta(hours=2),
                    'url': url,
                    'location': 'Monroe County History Center, 202 E 6th St, Bloomington, IN',
                    'description': desc,
                    'uid': uid,
                }
        return None

    @staticmethod
    def _make_dt(year, month, day, time_str, tz):
        time_str = time_str.strip().lower()
        m = re.match(r'(\d{1,2}):(\d{2})\s*(am|pm)', time_str)
        if not m:
            return None
        hour = int(m.group(1))
        minute = int(m.group(2))
        if m.group(3) == 'pm' and hour != 12:
            hour += 12
        elif m.group(3) == 'am' and hour == 12:
            hour = 0
        return datetime(year, month, day, hour, minute, tzinfo=tz)


if __name__ == '__main__':
    HistoryCenterScraper.main()
