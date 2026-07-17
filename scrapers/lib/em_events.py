"""Events Manager (EM) scraper library.

WordPress sites using the Events Manager plugin render events in a listing
with well-structured CSS classes (em-event, em-event-title, etc.). The plugin
exposes an AJAX endpoint at /wp-admin/admin-ajax.php that returns HTML with
configurable page size — allowing us to fetch all events in a small number
of requests.

Pagination: uses POST to admin-ajax.php with params action=search_events,
pno=N, and limit=N (max 50).

Usage:
    from lib.em_events import EmEventsScraper

    class MyCommunityScraper(EmEventsScraper):
        name = "My Community Calendar"
        domain = "example.org"
        ajax_url = "https://example.org/wp-admin/admin-ajax.php"
        timezone = "America/New_York"

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

MONTH_NAMES = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}
# Also accept abbreviated month names
MONTH_ABBRS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def _parse_month(text: str) -> Optional[int]:
    """Parse a month name (full or abbreviated) to month number."""
    clean = text.strip().rstrip(",").lower()
    return MONTH_NAMES.get(clean) or MONTH_ABBRS.get(clean)


def _parse_hour_minute(time_str: str) -> Optional[tuple[int, int]]:
    """Parse a time string like '7:00 pm' or '10:00 am'."""
    time_str = time_str.strip().lower()
    match = re.match(r"(\d{1,2}):(\d{2})\s*(am|pm)", time_str)
    if not match:
        # Try 12-hour without minutes, e.g. "9 pm"
        match = re.match(r"(\d{1,2})\s*(am|pm)", time_str)
        if not match:
            return None
        hour = int(match.group(1))
        minute = 0
    else:
        hour = int(match.group(1))
        minute = int(match.group(2))

    ampm = match.group(3)
    if ampm == "pm" and hour != 12:
        hour += 12
    elif ampm == "am" and hour == 12:
        hour = 0

    return (hour, minute)


class EmEventsScraper(BaseScraper):
    """Base class for scrapers targeting WordPress Events Manager plugin sites.

    Subclasses should set:
        name: str - Source name
        domain: str - Domain for UIDs
        ajax_url: str - URL to the admin-ajax.php endpoint
        timezone: str - IANA timezone

    Optional:
        ajax_action: str - AJAX action name (default 'search_events')
        default_location: str - Fallback location string
        batch_size: int - Events per AJAX request (max 50, default 50)
        max_pages: int - Max pages to fetch (default 20, set higher as needed)
    """

    ajax_url: str = ""
    ajax_action: str = "search_events"
    default_location: str = ""
    batch_size: int = 50
    max_pages: int = 20

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events via the EM AJAX endpoint, paginating through pages."""
        all_events = []
        seen_ids = set()

        for page_offset in range(self.max_pages):
            pno = page_offset + 1
            self.logger.info(f"Fetching page {pno} via AJAX (limit={self.batch_size})")
            try:
                page_events = self._fetch_page(pno)
                if not page_events:
                    self.logger.info(f"No events on page {pno}, stopping pagination")
                    break

                for event in page_events:
                    if event["uid"] not in seen_ids:
                        seen_ids.add(event["uid"])
                        all_events.append(event)

                # If we got fewer events than batch_size, we're on the last page
                if len(page_events) < self.batch_size:
                    self.logger.info(
                        f"Page {pno} had {len(page_events)} events (< {self.batch_size}), done"
                    )
                    break

            except Exception as e:
                self.logger.warning(f"Error fetching page {pno}: {e}")
                break

        self.logger.info(f"Found {len(all_events)} events total")
        return all_events

    def _fetch_page(self, pno: int) -> list[dict[str, Any]]:
        """Fetch and parse a single page of events from the EM AJAX endpoint."""
        response = requests.post(
            self.ajax_url,
            headers=BROWSER_HEADERS,
            data={
                "action": self.ajax_action,
                "pno": str(pno),
                "limit": str(self.batch_size),
            },
            timeout=30,
        )
        response.raise_for_status()

        text = response.text

        soup = BeautifulSoup(text, "html.parser")
        events = []
        tz = ZoneInfo(self.timezone)

        for event_el in soup.select(".em-event"):
            parsed = self._parse_event(event_el, tz)
            if parsed:
                events.append(parsed)

        return events

    def _parse_event(self, event_el, tz: ZoneInfo) -> Optional[dict[str, Any]]:
        """Parse a single .em-event element into an event dict."""
        # Title and URL
        title_el = event_el.select_one(".em-item-title a")
        if not title_el:
            return None

        title = title_el.get_text(strip=True)
        url = title_el.get("href", "") or event_el.get("data-href", "")

        # Date parsing: "June 18, 2026"
        date_el = event_el.select_one(".em-event-date")
        if not date_el:
            return None

        date_text = date_el.get_text(strip=True)
        event_date = self._parse_date(date_text)

        if not event_date:
            self.logger.debug(f"Could not parse date: {date_text}")
            return None

        year, month, day = event_date

        # Time parsing: "10:00 am - 10:00 pm"
        time_el = event_el.select_one(".em-event-time")
        dtstart = None
        dtend = None
        if time_el:
            time_text = time_el.get_text(strip=True)
            dtstart, dtend = self._parse_time_range(time_text, year, month, day, tz)

        if not dtstart:
            dtstart = datetime(year, month, day, tzinfo=tz)

        # Location parsing
        location = self._parse_location(event_el)
        if not location:
            location = self.default_location

        # UID
        event_id = event_el.get("data-event-id", "")
        if not event_id:
            # Fall back to URL-based UID
            uid_match = re.search(r"/(?:events/)?([^/]+)/?$", url)
            event_id = uid_match.group(1) if uid_match else str(id(event_el))
        uid = f"em-{event_id}@{self.domain}"

        # Description (from listing page — may be truncated or absent)
        desc_el = event_el.select_one(".em-event-description, .em-item-content")
        description = desc_el.get_text(strip=True) if desc_el else ""

        return {
            "title": title,
            "dtstart": dtstart,
            "dtend": dtend,
            "url": url,
            "location": location,
            "description": description,
            "uid": uid,
        }

    def _parse_date(self, date_text: str) -> Optional[tuple[int, int, int]]:
        """Parse a date string like 'June 18, 2026' or 'Jun 18, 2026'."""
        match = re.match(r"(\w+)\s+(\d{1,2}),?\s*(\d{4})", date_text)
        if not match:
            return None

        month_name = match.group(1)
        day = int(match.group(2))
        year = int(match.group(3))

        month = _parse_month(month_name)
        if not month:
            return None

        return (year, month, day)

    @staticmethod
    def _parse_time_range(
        time_text: str, year: int, month: int, day: int, tz: ZoneInfo
    ) -> tuple[Optional[datetime], Optional[datetime]]:
        """Parse time range like '10:00 am - 10:00 pm' or '7:00 pm - 10:00 pm'."""
        is_all_day = "all day" in time_text.lower()

        # Split on dash or en-dash
        parts = re.split(r"\s*[–\-]\s*", time_text, maxsplit=1)
        if len(parts) < 1 or not parts[0].strip():
            return None, None

        start_hm = _parse_hour_minute(parts[0].strip())
        if not start_hm:
            if is_all_day:
                dtstart = datetime(year, month, day, 0, 0, tzinfo=tz)
                return dtstart, dtstart + timedelta(days=1)
            return None, None

        dtstart = datetime(year, month, day, start_hm[0], start_hm[1], tzinfo=tz)

        dtend = None
        if len(parts) > 1:
            end_hm = _parse_hour_minute(parts[1].strip())
            if end_hm:
                dtend = datetime(year, month, day, end_hm[0], end_hm[1], tzinfo=tz)
                if dtend < dtstart:
                    dtend += timedelta(days=1)
            elif parts[1].strip().lower() == "all day":
                dtend = dtstart + timedelta(days=1)
        elif is_all_day:
            dtend = dtstart + timedelta(days=1)

        return dtstart, dtend

    @staticmethod
    def _parse_location(event_el) -> str:
        """Parse location from an .em-event element."""
        loc_el = event_el.select_one(".em-event-location")
        if not loc_el:
            return ""

        parts = []

        # Venue name from the .em-event-location-info a
        venue_link = loc_el.select_one(".em-event-location-info a")
        if venue_link:
            parts.append(venue_link.get_text(strip=True))

        # Address
        address_el = loc_el.select_one(".em-event-location-address")
        if address_el:
            address_text = address_el.get_text(strip=True)
            if address_text:
                parts.append(address_text)

        return ", ".join(parts) if parts else loc_el.get_text(strip=True)
