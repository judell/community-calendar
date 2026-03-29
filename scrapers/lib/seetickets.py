"""SeeTickets widget scraper library.

WordPress sites embedding SeeTickets render event cards with structured
CSS classes: `.seetickets-list-event-container` containing `p.title`,
`p.date`, `span.see-showtime`, `p.venue`, `span.price`, `p.genre`.

Usage:
    from lib.seetickets import SeeTicketsScraper

    class MyVenueScraper(SeeTicketsScraper):
        name = "My Venue"
        domain = "myvenue.com"
        events_url = "https://myvenue.com/"
        default_location = "My Venue, 123 Main St, Anytown"

    if __name__ == '__main__':
        MyVenueScraper.main()
"""

import re
from datetime import datetime, timedelta
from typing import Any, Optional
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from .base import BaseScraper

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


class SeeTicketsScraper(BaseScraper):
    """Base class for scrapers targeting SeeTickets widget embeds.

    Subclasses should set:
        name: str - Source name
        domain: str - Domain for UIDs
        events_url: str - Page URL containing SeeTickets widget
        timezone: str - IANA timezone

    Optional:
        default_location: str - Fallback location string
        verify_ssl: bool - Whether to verify SSL (default True)
    """

    events_url: str = ''
    default_location: str = ''
    verify_ssl: bool = True

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from the SeeTickets widget on the page."""
        self.logger.info(f"Fetching {self.events_url}")
        response = requests.get(self.events_url, headers=HEADERS,
                                timeout=30, verify=self.verify_ssl)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        tz = ZoneInfo(self.timezone)
        now = datetime.now(tz)
        events = []

        for card in soup.select('.seetickets-list-event-container'):
            parsed = self._parse_card(card, now, tz)
            if parsed:
                events.append(parsed)

        self.logger.info(f"Found {len(events)} events")
        return events

    def _parse_card(self, card, now: datetime, tz: ZoneInfo) -> Optional[dict[str, Any]]:
        """Parse a single SeeTickets event card."""
        title_el = card.select_one('p.title')
        if not title_el:
            return None
        title = title_el.get_text(strip=True)

        date_el = card.select_one('p.date')
        if not date_el:
            return None
        date_text = date_el.get_text(strip=True)

        time_el = card.select_one('span.see-showtime')
        time_text = time_el.get_text(strip=True) if time_el else ''

        dtstart = self._parse_datetime(date_text, time_text, now, tz)
        if not dtstart:
            return None

        dtend = dtstart + timedelta(hours=3)

        # Location
        venue_el = card.select_one('p.venue')
        location = venue_el.get_text(strip=True).lstrip('at ') if venue_el else self.default_location
        if not location:
            location = self.default_location

        # URL
        link = card.select_one('a.seetickets-buy-btn')
        url = link.get('href', '') if link else ''

        # Genre and price for description
        genre_el = card.select_one('p.genre')
        price_el = card.select_one('span.price')
        ages_el = card.select_one('span.ages')
        desc_parts = []
        if genre_el:
            desc_parts.append(genre_el.get_text(strip=True))
        if price_el:
            desc_parts.append(price_el.get_text(strip=True))
        if ages_el:
            desc_parts.append(ages_el.get_text(strip=True))
        description = ' | '.join(desc_parts)

        slug = re.sub(r'[^a-z0-9]+', '-', title.lower())[:40]
        uid = f"seetickets-{dtstart.strftime('%Y%m%d')}-{slug}@{self.domain}"

        return {
            'title': title,
            'dtstart': dtstart,
            'dtend': dtend,
            'url': url,
            'location': location,
            'description': description,
            'uid': uid,
        }

    @staticmethod
    def _parse_datetime(date_text: str, time_text: str, now: datetime, tz: ZoneInfo) -> Optional[datetime]:
        """Parse 'Wed Apr 1' + '10:00PM' into a datetime."""
        # Strip day-of-week
        date_text = re.sub(r'^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+', '', date_text)

        # Parse month and day
        match = re.match(r'(\w+)\s+(\d+)', date_text)
        if not match:
            return None

        month_str = match.group(1)
        day = int(match.group(2))

        months = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12,
        }
        month = months.get(month_str, 0)
        if not month:
            return None

        # Infer year
        year = now.year
        if month < now.month or (month == now.month and day < now.day):
            year += 1

        # Parse time
        hour, minute = 20, 0  # default 8pm
        if time_text:
            tm = re.match(r'(\d+):(\d+)\s*(AM|PM)', time_text, re.IGNORECASE)
            if tm:
                hour = int(tm.group(1))
                minute = int(tm.group(2))
                if tm.group(3).upper() == 'PM' and hour != 12:
                    hour += 12
                elif tm.group(3).upper() == 'AM' and hour == 12:
                    hour = 0

        return datetime(year, month, day, hour, minute, tzinfo=tz)
