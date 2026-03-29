"""Sugar Calendar (WordPress plugin) scraper library.

WordPress sites using Sugar Calendar Lite render events in a list view with
`.sugar-calendar-event-list-block__listview__event` items. The list page has
titles, dates/times, and links; detail pages add location and description.

Usage:
    from lib.sugar_calendar import SugarCalendarScraper

    class MyEventsScraper(SugarCalendarScraper):
        name = "My Events"
        domain = "example.org"
        events_url = "https://example.org/events/"
        default_location = "Anytown, USA"

    if __name__ == '__main__':
        MyEventsScraper.main()
"""

import re
from datetime import datetime, timedelta
from typing import Any, Optional
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from .base import BaseScraper

BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


class SugarCalendarScraper(BaseScraper):
    """Base class for scrapers targeting Sugar Calendar WordPress sites.

    Subclasses should set:
        name: str - Source name
        domain: str - Domain for UIDs
        events_url: str - Events list page URL
        timezone: str - IANA timezone

    Optional:
        default_location: str - Fallback location string
        fetch_details: bool - Whether to fetch individual event pages for location/description (default True)
    """

    events_url: str = ''
    default_location: str = ''
    fetch_details: bool = True

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from the Sugar Calendar list page."""
        self.logger.info(f"Fetching {self.events_url}")
        response = requests.get(self.events_url, headers=BROWSER_HEADERS, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        tz = ZoneInfo(self.timezone)
        events = []

        for event_el in soup.select('.sugar-calendar-event-list-block__listview__event'):
            parsed = self._parse_list_item(event_el, tz)
            if parsed:
                events.append(parsed)

        if self.fetch_details:
            for event in events:
                if event.get('url'):
                    self._enrich_from_detail(event)

        self.logger.info(f"Found {len(events)} events")
        return events

    def _parse_list_item(self, el, tz: ZoneInfo) -> Optional[dict[str, Any]]:
        """Parse an event from the list view."""
        title_el = el.select_one('[class*=__title]')
        if not title_el:
            return None
        title = title_el.get_text(strip=True)

        link = el.select_one('a[href]')
        url = link.get('href', '') if link else ''

        # Date/time text like "March 29, 2026at7:00 pm-8:30 pm"
        date_el = el.select_one('[class*=__date]') or el.select_one('[class*=__time]')
        dtstart = None
        dtend = None
        if date_el:
            date_text = date_el.get_text(strip=True)
            dtstart, dtend = self._parse_datetime(date_text, tz)

        if not dtstart:
            return None

        if not dtend:
            dtend = dtstart + timedelta(hours=2)

        slug = re.sub(r'[^a-z0-9]+', '-', title.lower())[:40]
        uid = f"sc-{dtstart.strftime('%Y%m%d')}-{slug}@{self.domain}"

        return {
            'title': title,
            'dtstart': dtstart,
            'dtend': dtend,
            'url': url,
            'location': self.default_location,
            'description': '',
            'uid': uid,
        }

    def _parse_datetime(self, text: str, tz: ZoneInfo):
        """Parse 'March 29, 2026at7:00 pm-8:30 pm' or similar."""
        # Normalize: insert space before 'at' if missing
        text = re.sub(r'(\d{4})at', r'\1 at ', text)
        # Split date and time
        match = re.match(
            r'(\w+ \d{1,2}, \d{4})\s*at\s*(\d{1,2}:\d{2}\s*[ap]m)\s*[-–]?\s*(\d{1,2}:\d{2}\s*[ap]m)?',
            text, re.IGNORECASE
        )
        if not match:
            return None, None

        date_str = match.group(1)
        start_time = match.group(2).strip()
        end_time = match.group(3).strip() if match.group(3) else None

        try:
            dt_date = datetime.strptime(date_str, '%B %d, %Y')
        except ValueError:
            return None, None

        dtstart = self._combine_date_time(dt_date, start_time, tz)
        dtend = self._combine_date_time(dt_date, end_time, tz) if end_time else None

        if dtend and dtstart and dtend < dtstart:
            dtend += timedelta(days=1)

        return dtstart, dtend

    @staticmethod
    def _combine_date_time(dt_date: datetime, time_str: str, tz: ZoneInfo) -> Optional[datetime]:
        """Combine a date with a time string like '7:00 pm'."""
        time_str = time_str.strip().lower()
        match = re.match(r'(\d{1,2}):(\d{2})\s*(am|pm)', time_str)
        if not match:
            return None

        hour = int(match.group(1))
        minute = int(match.group(2))
        ampm = match.group(3)

        if ampm == 'pm' and hour != 12:
            hour += 12
        elif ampm == 'am' and hour == 12:
            hour = 0

        return datetime(dt_date.year, dt_date.month, dt_date.day, hour, minute, tzinfo=tz)

    def _enrich_from_detail(self, event: dict):
        """Fetch the detail page to get location and description."""
        try:
            resp = requests.get(event['url'], headers=BROWSER_HEADERS, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            self.logger.debug(f"Could not fetch detail page {event['url']}: {e}")
            return

        soup = BeautifulSoup(resp.text, 'html.parser')

        # Sugar Calendar detail pages use label/value pairs
        for label_el in soup.select('.sc-frontend-single-event__details__label'):
            label = label_el.get_text(strip=True).rstrip(':').lower()
            value_el = label_el.find_next_sibling()
            if not value_el:
                continue
            value = value_el.get_text(strip=True)

            if label == 'location' and value:
                event['location'] = value

        # Description from post content
        content = soup.select_one('.entry-content, .post-content')
        if content:
            desc = content.get_text(strip=True)
            if desc and len(desc) > 10:
                event['description'] = desc[:500]
