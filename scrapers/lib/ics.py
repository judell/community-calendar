"""ICS feed scraper base class."""

import logging
from typing import Any, Optional

import requests
from icalendar import Calendar

from .base import BaseScraper


class IcsScraper(BaseScraper):
    """
    Base class for ICS feed scrapers.

    Subclasses must set:
    - name: str - Source name
    - domain: str - Domain for UIDs
    - ics_url: str - URL of the ICS feed (or override get_ics_urls())

    Optional overrides:
    - get_ics_urls() -> list[str] - Return multiple ICS URLs to merge
    - filter_event(event_data) -> bool - Return False to skip events
    - transform_event(event_data) -> dict - Modify event data after parsing
    - default_location: str - Default location if none in event
    - default_url: str - Default URL if none in event
    """

    ics_url: str = ""
    default_location: Optional[str] = None
    default_url: Optional[str] = None
    request_timeout: int = 60
    request_headers: Optional[dict] = None  # Custom headers for requests

    def get_ics_urls(self) -> list[str]:
        """Return list of ICS URLs to fetch. Override for multiple feeds."""
        if self.ics_url:
            return [self.ics_url]
        return []

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch and parse events from ICS feed(s)."""
        all_events = []
        urls = self.get_ics_urls()

        if not urls:
            self.logger.error("No ICS URLs configured")
            return []

        headers = self.request_headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        for url in urls:
            self.logger.info(f"Fetching ICS: {url}")
            try:
                response = requests.get(url, headers=headers, timeout=self.request_timeout)
                response.raise_for_status()
                events = self._parse_ics(response.text)
                all_events.extend(events)
                self.logger.info(f"Parsed {len(events)} events from {url}")
            except Exception as e:
                self.logger.error(f"Error fetching {url}: {e}")

        # Deduplicate by UID
        seen_uids = set()
        unique_events = []
        for event in all_events:
            uid = event.get('uid', '')
            if not uid or uid not in seen_uids:
                if uid:
                    seen_uids.add(uid)
                unique_events.append(event)

        self.logger.info(f"Total events after dedup: {len(unique_events)}")
        return unique_events

    def _parse_ics(self, ics_content: str) -> list[dict[str, Any]]:
        """Parse events from ICS content."""
        events = []
        try:
            cal = Calendar.from_ical(ics_content)
        except Exception as e:
            self.logger.warning(f"Error parsing ICS: {e}")
            return events

        for component in cal.walk():
            if component.name == "VEVENT":
                event = self._parse_vevent(component)
                if event:
                    # Apply filter
                    if self.filter_event(event):
                        # Apply transform
                        event = self.transform_event(event)
                        events.append(event)

        return events

    def _parse_vevent(self, component) -> Optional[dict[str, Any]]:
        """Parse a single VEVENT component."""
        try:
            title = str(component.get('summary', '')).strip()
            if not title:
                return None

            dtstart = component.get('dtstart')
            if not dtstart:
                return None
            dt_start = dtstart.dt

            dtend = component.get('dtend')
            dt_end = dtend.dt if dtend else None

            location = str(component.get('location', '')).strip() or self.default_location
            description = str(component.get('description', '')).strip() or None
            url = str(component.get('url', '')).strip() or self.default_url
            uid = str(component.get('uid', '')).strip()

            # Get categories if available
            categories = component.get('categories')
            cat_list = []
            if categories:
                if hasattr(categories, 'cats'):
                    cat_list = [str(c) for c in categories.cats]
                elif hasattr(categories, 'to_ical'):
                    cat_list = [str(categories)]

            return {
                'title': title,
                'dtstart': dt_start,
                'dtend': dt_end,
                'location': location,
                'description': description,
                'url': url,
                'uid': uid,
                'categories': cat_list,
            }

        except Exception as e:
            self.logger.warning(f"Error parsing VEVENT: {e}")
            return None

    def filter_event(self, event: dict[str, Any]) -> bool:
        """
        Return True to keep event, False to skip.
        Override to filter by title, location, date, etc.
        """
        return True

    def transform_event(self, event: dict[str, Any]) -> dict[str, Any]:
        """
        Transform event data after parsing.
        Override to modify title, add location, etc.
        """
        return event


class GoogleCalendarScraper(IcsScraper):
    """
    Scraper for Google Calendar public ICS feeds.

    Set calendar_ids to a list of Google Calendar IDs:
    - "user@gmail.com"
    - "abc123@group.calendar.google.com"
    """

    calendar_ids: list[str] = []

    def get_ics_urls(self) -> list[str]:
        """Convert calendar IDs to ICS URLs."""
        urls = []
        for cal_id in self.calendar_ids:
            # URL-encode the @ symbol
            encoded_id = cal_id.replace('@', '%40')
            url = f"https://calendar.google.com/calendar/ical/{encoded_id}/public/basic.ics"
            urls.append(url)
        return urls
