#!/usr/bin/env python3
"""Scraper for BloomingtonArts.Today — curated arts calendar."""

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
    'Accept': 'text/html',
}

# Relative day names the site uses
RELATIVE_DAYS = {
    'today': 0,
    'tomorrow': 1,
}

DAYS_OF_WEEK = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

MONTHS = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
    'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
}


class BloomingtonArtsTodayScraper(BaseScraper):
    """Scraper for BloomingtonArts.Today."""

    name = "BloomingtonArts.Today"
    domain = "bloomingtonarts.today"
    events_url = "https://www.bloomingtonarts.today/"
    timezone = "America/Indiana/Indianapolis"

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from the curated arts calendar."""
        self.logger.info(f"Fetching {self.events_url}")
        response = requests.get(self.events_url, headers=HEADERS, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        tz = ZoneInfo(self.timezone)
        now = datetime.now(tz)
        events = []

        cards = soup.select('div.flex.items-start.justify-between.gap-6')
        self.logger.info(f"Found {len(cards)} event cards")

        for card in cards:
            parsed = self._parse_card(card, now, tz)
            if parsed:
                events.append(parsed)

        self.logger.info(f"Parsed {len(events)} events")
        return events

    def _parse_card(self, card, now: datetime, tz: ZoneInfo) -> Optional[dict[str, Any]]:
        """Parse a single event card."""
        parent = card.parent

        # Date/time
        date_el = card.select_one('p.text-xs.font-bold')
        if not date_el:
            return None
        date_text = date_el.get_text(strip=True)

        # Title
        title_el = card.select_one('h3')
        if not title_el:
            return None
        title = title_el.get_text(strip=True)

        # Parse date
        dtstart = self._parse_datetime(date_text, now, tz)
        if not dtstart:
            return None

        dtend = dtstart + timedelta(hours=2)

        # Venue — first p.text-gray-500 in parent
        venue = ''
        if parent:
            venue_el = parent.select_one('p.text-sm.text-gray-500')
            if venue_el:
                venue = venue_el.get_text(strip=True)

        # URL — first external link in parent
        url = ''
        if parent:
            for a in parent.select('a[href]'):
                href = a.get('href', '')
                if href.startswith('http') and 'google.com/maps' not in href:
                    url = href
                    break

        # Price
        price_el = card.select_one('span.text-sm.font-semibold')
        price = price_el.get_text(strip=True) if price_el else ''

        # Description from parent
        desc = ''
        if parent:
            desc_el = parent.select_one('p.text-sm.text-gray-600')
            if desc_el:
                desc = desc_el.get_text(strip=True)
        if price and price != 'Free':
            desc = f"{price}. {desc}" if desc else price

        slug = re.sub(r'[^a-z0-9]+', '-', title.lower())[:40]
        uid = f"bat-{dtstart.strftime('%Y%m%d%H%M')}-{slug}@bloomingtonarts.today"

        return {
            'title': title,
            'dtstart': dtstart,
            'dtend': dtend,
            'url': url,
            'location': venue,
            'description': desc,
            'uid': uid,
        }

    def _parse_datetime(self, text: str, now: datetime, tz: ZoneInfo) -> Optional[datetime]:
        """Parse date/time like 'Today•4:00 PM' or 'Tuesday, March 31•7:00 PM'."""
        # Split on bullet
        parts = re.split(r'[•\u2022]', text, maxsplit=1)
        date_part = parts[0].strip().lower()
        time_part = parts[1].strip() if len(parts) > 1 else ''

        # Parse time
        hour, minute = 19, 0  # default 7pm
        if time_part:
            tm = re.match(r'(\d+):(\d+)\s*(AM|PM)', time_part, re.IGNORECASE)
            if tm:
                hour = int(tm.group(1))
                minute = int(tm.group(2))
                if tm.group(3).upper() == 'PM' and hour != 12:
                    hour += 12
                elif tm.group(3).upper() == 'AM' and hour == 12:
                    hour = 0

        # Parse date
        if date_part in RELATIVE_DAYS:
            dt = now + timedelta(days=RELATIVE_DAYS[date_part])
            return datetime(dt.year, dt.month, dt.day, hour, minute, tzinfo=tz)

        # "tuesday, march 31" pattern
        m = re.match(r'(?:\w+,\s*)?(\w+)\s+(\d+)', date_part)
        if m:
            month_name = m.group(1)
            day = int(m.group(2))
            month = MONTHS.get(month_name, 0)
            if not month:
                return None
            year = now.year
            if month < now.month or (month == now.month and day < now.day):
                year += 1
            return datetime(year, month, day, hour, minute, tzinfo=tz)

        return None


if __name__ == '__main__':
    BloomingtonArtsTodayScraper.main()
