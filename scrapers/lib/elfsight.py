"""Elfsight Event Calendar widget scraper library.

Elfsight is a popular embeddable widget platform. Many sites use their
Event Calendar widget, which stores all event data in a JSON API.

This library provides:
- ElfsightCalendarScraper: Base class for Elfsight calendar scrapers
- fetch_elfsight_data(): Low-level API fetcher
- expand_recurring_events(): Recurrence expansion logic

Usage:
    from lib.elfsight import ElfsightCalendarScraper
    
    class MySiteScraper(ElfsightCalendarScraper):
        name = "My Site Events"
        domain = "mysite.com"
        widget_id = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        source_page = "https://mysite.com/events"
    
    if __name__ == '__main__':
        MySiteScraper.main()
"""

import hashlib
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Optional
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

from .base import BaseScraper

logger = logging.getLogger(__name__)

ELFSIGHT_API_BASE = "https://core.service.elfsight.com/p/boot/"


def fetch_elfsight_data(widget_id: str, source_page: str) -> Optional[dict]:
    """
    Fetch event data from Elfsight API.
    
    Args:
        widget_id: The Elfsight widget ID (UUID format)
        source_page: The page URL where the widget is embedded
    
    Returns:
        The widget settings dict containing events, locations, eventTypes, etc.
        Returns None on error.
    """
    url = f"{ELFSIGHT_API_BASE}?page={source_page}&w={widget_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    req = Request(url, headers=headers)
    
    try:
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data['data']['widgets'][widget_id]['data']['settings']
    except (HTTPError, URLError) as e:
        logger.error(f"HTTP error fetching Elfsight data: {e}")
        return None
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Error parsing Elfsight response: {e}")
        return None


def expand_recurring_events(
    event: dict,
    months_ahead: int = 3,
    max_occurrences: int = 500
) -> list[datetime]:
    """
    Expand a recurring event into individual occurrence datetimes.
    
    Args:
        event: Elfsight event dict with start, end, repeatPeriod, etc.
        months_ahead: How many months into the future to expand
        max_occurrences: Safety limit on number of occurrences
    
    Returns:
        List of datetime objects for each occurrence
    """
    occurrences = []
    
    start_date = event.get('start', {}).get('date')
    start_time = event.get('start', {}).get('time', '00:00')
    
    if not start_date:
        return occurrences
    
    try:
        base_dt = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        logger.warning(f"Could not parse start date/time: {start_date} {start_time}")
        return occurrences
    
    now = datetime.now()
    cutoff = now + timedelta(days=months_ahead * 30)
    
    repeat_period = event.get('repeatPeriod', 'noRepeat')
    
    # Non-recurring event
    if repeat_period == 'noRepeat':
        if base_dt >= now - timedelta(days=1):
            occurrences.append(base_dt)
        return occurrences
    
    # Recurring event parameters
    repeat_freq = event.get('repeatFrequency', 'weekly')
    repeat_interval = event.get('repeatInterval', 1)
    repeat_ends = event.get('repeatEnds', 'never')
    repeat_ends_date = event.get('repeatEndsDate', {}).get('date') if event.get('repeatEndsDate') else None
    repeat_weekly_days = event.get('repeatWeeklyOnDays', [])
    
    # Determine end cutoff
    end_cutoff = cutoff
    if repeat_ends == 'onDate' and repeat_ends_date:
        try:
            end_cutoff = min(cutoff, datetime.strptime(repeat_ends_date, "%Y-%m-%d"))
        except ValueError:
            pass
    
    # Parse exceptions (skipped dates)
    exceptions = set()
    for exc in event.get('exceptions', []):
        if exc.get('type') == 'skip':
            orig = exc.get('originalDate')
            if orig:
                # originalDate is typically a timestamp in milliseconds
                try:
                    exc_dt = datetime.fromtimestamp(orig / 1000)
                    exceptions.add(exc_dt.date())
                except (ValueError, TypeError):
                    pass
    
    # Day name to weekday number mapping
    day_map = {'su': 6, 'mo': 0, 'tu': 1, 'we': 2, 'th': 3, 'fr': 4, 'sa': 5}
    target_weekdays = [day_map[d] for d in repeat_weekly_days if d in day_map]
    
    current = base_dt
    iterations = 0
    
    while current <= end_cutoff and iterations < max_occurrences:
        iterations += 1
        
        should_include = False
        
        if repeat_period == 'weeklyOn' or (repeat_period == 'custom' and repeat_freq == 'weekly'):
            # Weekly on specific days
            if not target_weekdays or current.weekday() in target_weekdays:
                should_include = True
        elif repeat_period == 'custom' and repeat_freq == 'monthly':
            # Monthly on same week/day pattern (e.g., 4th Saturday)
            if target_weekdays and current.weekday() in target_weekdays:
                base_week = (base_dt.day - 1) // 7
                current_week = (current.day - 1) // 7
                if base_week == current_week:
                    should_include = True
        elif repeat_period == 'custom' and repeat_freq == 'daily':
            should_include = True
        
        if should_include and current >= now - timedelta(days=1):
            if current.date() not in exceptions:
                occurrences.append(current)
        
        # Advance based on frequency
        if repeat_freq == 'daily':
            current += timedelta(days=repeat_interval)
        elif repeat_freq == 'weekly':
            current += timedelta(days=1)  # Check each day for target weekdays
        elif repeat_freq == 'monthly':
            current += timedelta(days=7)  # Check weekly for monthly pattern matching
        else:
            current += timedelta(days=1)
    
    return occurrences


class ElfsightCalendarScraper(BaseScraper):
    """
    Base scraper for sites using Elfsight Event Calendar widget.
    
    Subclasses must define:
        - widget_id: str - The Elfsight widget UUID
        - source_page: str - URL of the page containing the widget
    
    Optional overrides:
        - location_filter: list[str] - Filter events to these locations (partial match)
        - event_type_filter: list[str] - Filter to these event types (partial match)
    """
    
    widget_id: str = ""
    source_page: str = ""
    location_filter: list[str] = []
    event_type_filter: list[str] = []
    
    def __init__(self):
        super().__init__()
        self._settings = None
        self._locations_map = {}
        self._event_types_map = {}
    
    def fetch_settings(self) -> Optional[dict]:
        """Fetch and cache the Elfsight widget settings."""
        if self._settings is None:
            self.logger.info(f"Fetching Elfsight data for widget {self.widget_id}")
            self._settings = fetch_elfsight_data(self.widget_id, self.source_page)
            
            if self._settings:
                # Build lookup maps
                self._locations_map = {
                    loc['id']: loc['name'] 
                    for loc in self._settings.get('locations', [])
                }
                self._event_types_map = {
                    et['id']: et['name'] 
                    for et in self._settings.get('eventTypes', [])
                }
                self.logger.info(
                    f"Loaded {len(self._settings.get('events', []))} events, "
                    f"{len(self._locations_map)} locations, "
                    f"{len(self._event_types_map)} event types"
                )
        return self._settings
    
    def get_locations(self) -> dict[str, str]:
        """Get location ID to name mapping."""
        self.fetch_settings()
        return self._locations_map
    
    def get_event_types(self) -> dict[str, str]:
        """Get event type ID to name mapping."""
        self.fetch_settings()
        return self._event_types_map
    
    def _matches_filter(self, values: list[str], filters: list[str]) -> bool:
        """Check if any value matches any filter (case-insensitive partial match)."""
        if not filters:
            return True
        values_lower = [v.lower() for v in values]
        filters_lower = [f.lower() for f in filters]
        return any(
            filt in val 
            for val in values_lower 
            for filt in filters_lower
        )
    
    def _event_passes_filters(self, event: dict) -> bool:
        """Check if an event passes location and event type filters."""
        # Check location filter
        if self.location_filter:
            loc_ids = event.get('location', [])
            loc_names = [self._locations_map.get(lid, '') for lid in loc_ids]
            if not self._matches_filter(loc_names, self.location_filter):
                return False
        
        # Check event type filter
        if self.event_type_filter:
            type_ids = event.get('eventType', [])
            type_names = [self._event_types_map.get(tid, '') for tid in type_ids]
            if not self._matches_filter(type_names, self.event_type_filter):
                return False
        
        return True
    
    def fetch_events(self) -> list[dict]:
        """Fetch and expand all events from the Elfsight calendar."""
        settings = self.fetch_settings()
        if not settings:
            return []
        
        raw_events = settings.get('events', [])
        parsed_events = []
        
        for event in raw_events:
            if not self._event_passes_filters(event):
                continue
            
            # Expand recurring events
            occurrences = expand_recurring_events(event, self.months_ahead)
            
            if not occurrences:
                continue
            
            # Get event metadata
            name = event.get('name', 'Untitled')
            desc = event.get('description', '')
            # Strip HTML tags
            desc = re.sub(r'<[^>]+>', ' ', desc)
            desc = re.sub(r'\s+', ' ', desc).strip()
            
            start_time = event.get('start', {}).get('time', '00:00')
            end_time = event.get('end', {}).get('time', start_time)
            
            # Location names
            loc_ids = event.get('location', [])
            locations = [self._locations_map.get(lid, lid) for lid in loc_ids]
            location_str = ', '.join(locations)
            
            # Event type names (for categories)
            type_ids = event.get('eventType', [])
            event_types = [self._event_types_map.get(tid, tid) for tid in type_ids]
            
            # URL (button link or source page)
            button_link = event.get('buttonLink', {}).get('value', '')
            url = button_link if button_link else self.source_page
            
            # Create an event dict for each occurrence
            for occ_dt in occurrences:
                # Calculate end time
                try:
                    end_h, end_m = map(int, end_time.split(':'))
                    end_dt = occ_dt.replace(hour=end_h, minute=end_m)
                    if end_dt < occ_dt:
                        end_dt += timedelta(days=1)
                except (ValueError, AttributeError):
                    end_dt = occ_dt + timedelta(hours=1)
                
                # Generate unique ID
                uid_source = f"{event.get('id', name)}-{occ_dt.strftime('%Y%m%d')}"
                uid = hashlib.md5(uid_source.encode()).hexdigest()[:16]
                uid = f"{uid}@{self.domain}"
                
                parsed_events.append({
                    'title': name,
                    'dtstart': occ_dt,
                    'dtend': end_dt,
                    'location': location_str,
                    'description': desc,
                    'url': url,
                    'uid': uid,
                    'categories': event_types,
                })
            
            if occurrences:
                self.logger.debug(
                    f"  {name}: {len(occurrences)} occurrences @ {location_str}"
                )
        
        self.logger.info(f"Expanded to {len(parsed_events)} event occurrences")
        return parsed_events
    
    @classmethod
    def parse_args(cls, description: Optional[str] = None):
        """Parse command-line arguments with Elfsight-specific options."""
        import argparse
        parser = argparse.ArgumentParser(
            description=description or f'Scrape events from {cls.name}'
        )
        parser.add_argument('--output', '-o', type=str, help='Output filename')
        parser.add_argument('--debug', action='store_true', help='Enable debug logging')
        parser.add_argument(
            '--location', '-l', nargs='+', default=[],
            help='Filter to specific location(s)'
        )
        parser.add_argument(
            '--type', '-t', nargs='+', default=[],
            help='Filter to specific event type(s)'
        )
        parser.add_argument(
            '--list-locations', action='store_true',
            help='List available locations and exit'
        )
        parser.add_argument(
            '--list-types', action='store_true',
            help='List available event types and exit'
        )
        parser.add_argument(
            '--months', '-m', type=int, default=None,
            help='Months ahead to fetch (overrides SCRAPE_MONTHS env var)'
        )
        return parser.parse_args()
    
    @classmethod
    def main(cls):
        """CLI entry point with Elfsight-specific options."""
        cls.setup_logging()
        args = cls.parse_args()
        
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
        
        scraper = cls()
        
        # Apply CLI filters
        if args.location:
            scraper.location_filter = args.location
        if args.type:
            scraper.event_type_filter = args.type
        if args.months:
            scraper.months_ahead = args.months
        
        # Handle list commands
        if args.list_locations:
            scraper.fetch_settings()
            print("Available locations:")
            for name in sorted(scraper._locations_map.values()):
                print(f"  {name}")
            return
        
        if args.list_types:
            scraper.fetch_settings()
            print("Available event types:")
            for name in sorted(scraper._event_types_map.values()):
                print(f"  {name}")
            return
        
        scraper.run(args.output)
