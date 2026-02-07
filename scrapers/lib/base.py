"""Base scraper class with common functionality."""

import argparse
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Optional

from icalendar import Calendar, Event

from .utils import append_source, generate_uid


class BaseScraper(ABC):
    """
    Base class for event scrapers.

    Subclasses must implement:
    - name: str - Source name (e.g., "Redwood Cafe")
    - domain: str - Domain for UIDs (e.g., "redwoodcafecotati.com")
    - fetch_events() -> list[dict]

    Each event dict should have:
    - title: str (required)
    - dtstart: datetime (required)
    - dtend: datetime (optional, defaults to dtstart)
    - url: str (optional)
    - location: str (optional)
    - description: str (optional)
    """

    name: str = "Unknown Source"
    domain: str = "example.com"
    timezone: str = "America/Los_Angeles"

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.months_ahead = int(os.environ.get('SCRAPE_MONTHS', 6))

    @classmethod
    def setup_logging(cls, level: int = logging.INFO):
        """Configure logging for scrapers."""
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    @classmethod
    def parse_args(cls, description: Optional[str] = None) -> argparse.Namespace:
        """Parse standard command-line arguments."""
        parser = argparse.ArgumentParser(
            description=description or f'Scrape events from {cls.name}'
        )
        parser.add_argument('--output', '-o', type=str, help='Output filename')
        parser.add_argument('--debug', action='store_true', help='Enable debug logging')
        return parser.parse_args()

    @abstractmethod
    def fetch_events(self) -> list[dict[str, Any]]:
        """
        Fetch and parse all available events from the source.

        Returns list of event dicts with keys:
        - title, dtstart, dtend, url, location, description
        """
        pass

    def create_calendar(self, events: list[dict]) -> Calendar:
        """Create an iCalendar from parsed events."""
        cal = Calendar()
        cal.add('prodid', f'-//{self.name}//{self.domain}//')
        cal.add('version', '2.0')
        cal.add('x-wr-calname', self.name)
        cal.add('x-wr-timezone', self.timezone)

        for event_data in events:
            event = self.create_event(event_data)
            if event:
                cal.add_component(event)

        return cal
    
    def create_event(self, data: dict[str, Any]) -> Optional[Event]:
        """Create an iCalendar Event from event data."""
        title = data.get('title')
        dtstart = data.get('dtstart')
        
        if not title or not dtstart:
            self.logger.warning(f"Skipping event with missing title or dtstart: {data}")
            return None
        
        event = Event()
        event.add('summary', title)
        event.add('dtstart', dtstart)
        event.add('dtend', data.get('dtend') or dtstart)
        
        if data.get('url'):
            event.add('url', data['url'])
        
        if data.get('location'):
            event.add('location', data['location'])
        
        description = append_source(data.get('description', ''), self.name)
        event.add('description', description)
        
        uid = data.get('uid') or generate_uid(title, dtstart, self.domain)
        event.add('uid', uid)
        event.add('x-source', self.name)
        
        return event
    
    def default_output_filename(self) -> str:
        """Generate default output filename."""
        # Convert name to snake_case
        name_slug = self.name.lower().replace(' ', '_').replace("'", '')
        return f"{name_slug}.ics"

    def run(self, output: Optional[str] = None) -> str:
        """Main entry point: fetch events and write calendar."""
        self.logger.info(f"Scraping {self.name}")

        events = self.fetch_events()
        cutoff = datetime.now().astimezone() + timedelta(days=self.months_ahead * 31)
        before = len(events)
        # Handle both datetime and date objects
        def is_before_cutoff(e):
            dt = e.get('dtstart')
            if not dt:
                return False
            if hasattr(dt, 'tzinfo') and dt.tzinfo is None:
                dt = dt.replace(tzinfo=cutoff.tzinfo)
            elif not hasattr(dt, 'hour'):  # date object, not datetime
                dt = datetime.combine(dt, datetime.min.time()).replace(tzinfo=cutoff.tzinfo)
            return dt <= cutoff
        events = [e for e in events if is_before_cutoff(e)]
        if len(events) < before:
            self.logger.info(f"Filtered {before - len(events)} events beyond {self.months_ahead} months out")
        self.logger.info(f"Found {len(events)} events")

        calendar = self.create_calendar(events)

        filename = output or self.default_output_filename()
        with open(filename, 'wb') as f:
            f.write(calendar.to_ical())

        self.logger.info(f"Written to {filename}")
        return filename

    @classmethod
    def main(cls):
        """CLI entry point."""
        cls.setup_logging()
        args = cls.parse_args()

        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)

        scraper = cls()
        scraper.run(args.output)
