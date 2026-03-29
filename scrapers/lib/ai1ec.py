"""All-in-One Event Calendar (ai1ec) scraper library.

WordPress sites using the All-in-One Event Calendar plugin render events in an
agenda view with well-structured CSS classes (ai1ec-date, ai1ec-event, etc.).
The plugin's native ICS export is often blocked by WAFs, but the HTML agenda
view is accessible with a browser User-Agent.

Pagination uses URL segments: action~agenda/page_offset~N/

Usage:
    from lib.ai1ec import Ai1ecScraper

    class MyCommunityScraper(Ai1ecScraper):
        name = "My Community Calendar"
        domain = "example.org"
        calendar_url = "https://example.org/calendar/"
        default_location = "Anytown, USA"

    if __name__ == '__main__':
        MyCommunityScraper.main()
"""

import re
from datetime import datetime, timedelta
from typing import Any, Optional
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from .base import BaseScraper

MONTHS = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
    'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12,
}

BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}


class Ai1ecScraper(BaseScraper):
    """Base class for scrapers targeting All-in-One Event Calendar sites.

    Subclasses should set:
        name: str - Source name
        domain: str - Domain for UIDs
        calendar_url: str - Calendar page URL (e.g. https://example.org/calendar/)
        timezone: str - IANA timezone

    Optional:
        default_location: str - Fallback location string
        max_pages: int - Number of agenda pages to fetch (default 4)
    """

    calendar_url: str = ''
    default_location: str = ''
    max_pages: int = 4

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from the ai1ec agenda view, paginating through multiple pages."""
        all_events = []
        seen_ids = set()

        for page_offset in range(self.max_pages):
            url = self.calendar_url if page_offset == 0 else \
                f"{self.calendar_url}action~agenda/page_offset~{page_offset}/"
            self.logger.info(f"Fetching page {page_offset}: {url}")
            try:
                page_events = self._fetch_page(url)
                for event in page_events:
                    if event['uid'] not in seen_ids:
                        seen_ids.add(event['uid'])
                        all_events.append(event)
            except Exception as e:
                self.logger.warning(f"Error fetching page {page_offset}: {e}")
                break

        self.logger.info(f"Found {len(all_events)} events total")
        return all_events

    def _fetch_page(self, url: str) -> list[dict[str, Any]]:
        """Fetch and parse events from a single calendar page."""
        response = requests.get(url, headers=BROWSER_HEADERS, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        events = []
        tz = ZoneInfo(self.timezone)

        for date_group in soup.select('.ai1ec-date'):
            date_title = date_group.select_one('.ai1ec-date-title')
            if not date_title:
                continue

            month_el = date_title.select_one('.ai1ec-month')
            day_el = date_title.select_one('.ai1ec-day')
            year_el = date_title.select_one('.ai1ec-year')
            if not month_el or not day_el:
                continue

            month = MONTHS.get(month_el.text.strip(), 0)
            day = int(day_el.text.strip())
            year = int(year_el.text.strip()) if year_el else datetime.now().year

            events_div = date_group.select_one('.ai1ec-date-events')
            if not events_div:
                continue

            for event_el in events_div.select('.ai1ec-event'):
                parsed = self._parse_event(event_el, year, month, day, tz)
                if parsed:
                    events.append(parsed)

        return events

    def _parse_event(self, event_el, year: int, month: int, day: int, tz: ZoneInfo) -> Optional[dict[str, Any]]:
        """Parse a single ai1ec event element."""
        title_el = event_el.select_one('.ai1ec-event-title')
        if not title_el:
            return None

        raw_title = title_el.get_text(strip=True)
        # Title often includes location after @, e.g. "Event Name@ Venue, Address"
        title, _, title_location = raw_title.partition('@')
        title = title.strip()
        title_location = title_location.strip()

        # Location from dedicated element (also starts with @)
        location = ''
        loc_el = event_el.select_one('.ai1ec-event-location')
        if loc_el:
            location = loc_el.get_text(strip=True).lstrip('@').strip()
        elif title_location:
            location = title_location
        if not location:
            location = self.default_location

        # Time parsing: "Mar 28 @ 7:00 pm – 10:00 pm" or "Mar 28 @ 9:00 pm"
        time_el = event_el.select_one('.ai1ec-event-time')
        dtstart = None
        dtend = None
        if time_el:
            time_text = time_el.get_text(strip=True)
            dtstart, dtend = self._parse_time(time_text, year, month, day, tz)

        if not dtstart:
            dtstart = datetime(year, month, day, tzinfo=tz)

        if not dtend:
            dtend = dtstart + timedelta(hours=2)

        # Event URL
        link = event_el.select_one('a.ai1ec-load-event')
        url = link.get('href', '') if link else ''

        # Description
        desc_el = event_el.select_one('.ai1ec-event-description')
        description = desc_el.get_text(strip=True) if desc_el else ''

        # UID from event classes
        classes = ' '.join(event_el.get('class', []))
        event_id_match = re.search(r'ai1ec-event-id-(\d+)', classes)
        instance_id_match = re.search(r'ai1ec-event-instance-id-(\d+)', classes)
        event_id = event_id_match.group(1) if event_id_match else ''
        instance_id = instance_id_match.group(1) if instance_id_match else ''
        uid = f"ai1ec-{event_id}-{instance_id}@{self.domain}" if event_id else None

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
    def _parse_time(time_text: str, year: int, month: int, day: int, tz: ZoneInfo):
        """Parse time string like 'Mar 28 @ 7:00 pm – 10:00 pm'."""
        parts = time_text.split('@', 1)
        if len(parts) < 2:
            return None, None

        time_part = parts[1].strip()
        time_range = re.split(r'\s*[–\-]\s*', time_part, maxsplit=1)

        start_str = time_range[0].strip()
        end_str = time_range[1].strip() if len(time_range) > 1 else None

        dtstart = _parse_single_time(start_str, year, month, day, tz)
        dtend = _parse_single_time(end_str, year, month, day, tz) if end_str else None

        if dtend and dtstart and dtend < dtstart:
            dtend += timedelta(days=1)

        return dtstart, dtend


def _parse_single_time(time_str: str, year: int, month: int, day: int, tz: ZoneInfo):
    """Parse a single time like '7:00 pm' or '10:00 pm'."""
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

    return datetime(year, month, day, hour, minute, tzinfo=tz)
