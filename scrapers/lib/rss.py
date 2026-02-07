"""RSS feed scraper base class."""

import logging
from abc import abstractmethod
from datetime import datetime
from typing import Any, Optional
from zoneinfo import ZoneInfo

import feedparser

from .base import BaseScraper


class RssScraper(BaseScraper):
    """
    Base class for RSS feed scrapers.

    Subclasses must set:
    - name: str - Source name
    - domain: str - Domain for UIDs
    - rss_url: str - URL of the RSS feed

    And implement:
    - parse_entry(entry) -> dict | None
    """

    rss_url: str = ""
    timezone: str = "America/Los_Angeles"

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch and parse events from RSS feed."""
        self.logger.info(f"Fetching RSS feed: {self.rss_url}")
        feed = feedparser.parse(self.rss_url)
        self.logger.info(f"Found {len(feed.entries)} entries in RSS feed")

        events = []
        for entry in feed.entries:
            event = self.parse_entry(entry)
            if event:
                events.append(event)
                self.logger.info(f"Found event: {event['title']} on {event['dtstart']}")

        return events

    @abstractmethod
    def parse_entry(self, entry: dict) -> Optional[dict[str, Any]]:
        """
        Parse a single RSS entry into event data.

        Returns None if parsing fails.

        Returns dict with: title, dtstart, dtend, url, location, description
        """
        pass
    
    def parse_rss_date(self, entry: dict) -> Optional[datetime]:
        """
        Parse date from RSS entry's published_parsed or published field.
        Returns datetime in local timezone.
        """
        tz = ZoneInfo(self.timezone)
        
        # Try parsed tuple first
        if entry.get('published_parsed'):
            dt_tuple = entry.published_parsed
            dt_utc = datetime(*dt_tuple[:6], tzinfo=ZoneInfo('UTC'))
            return dt_utc.astimezone(tz)
        
        # Try raw string
        pub_date = entry.get('published')
        if pub_date:
            try:
                # Common RSS format: "Sat, 07 Feb 2026 16:30:00 GMT"
                dt_utc = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
                dt_utc = dt_utc.replace(tzinfo=ZoneInfo('UTC'))
                return dt_utc.astimezone(tz)
            except ValueError:
                pass
        
        return None
