"""CitySpark API scraper base class.

Used by Bohemian and Press Democrat event calendars.
"""

from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import requests

from .base import BaseScraper


class CitySparkScraper(BaseScraper):
    """
    Scraper for CitySpark-powered event calendars.

    Subclasses must set:
    - name: str - Source name
    - domain: str - Domain for UIDs
    - api_slug: str - API endpoint slug (e.g., "Bohemian")
    - ppid: int - Publisher/partner ID
    - lat: float - Latitude for geo search
    - lng: float - Longitude for geo search
    - distance: int - Search radius in miles (default: 30)
    - calendar_url: str - Fallback calendar URL when event has no link
    """

    api_slug: str = ""
    ppid: int = 0
    lat: float = 0.0
    lng: float = 0.0
    distance: int = 30
    calendar_url: str = ""
    months_ahead: int = 3  # How many months ahead to fetch

    API_BASE = "https://portal.cityspark.com/v1/events"

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from CitySpark API."""
        results = []
        seen_ids = set()
        page_size = 100  # API max

        # Fetch from today to N months ahead
        now = datetime.now()
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=self.months_ahead * 31)

        start_str = start_date.strftime("%Y-%m-%dT%H:%M:%S")
        end_str = end_date.strftime("%Y-%m-%dT%H:%M:%S")

        skip = 0
        while True:
            url = f"{self.API_BASE}/{self.api_slug}"
            payload = {
                "ppid": self.ppid,
                "start": start_str,
                "end": end_str,
                "distance": self.distance,
                "lat": self.lat,
                "lng": self.lng,
                "sort": "Date",
                "skip": skip,
                "tps": str(page_size)
            }

            self.logger.info(f"Fetching page at skip={skip}")
            response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
            response.raise_for_status()
            data = response.json()

            events = data.get('Value') or []
            if not events:
                break

            for event in events:
                event_id = event.get('Id') or event.get('PId', '')
                if event_id in seen_ids:
                    continue
                seen_ids.add(event_id)

                parsed = self._parse_event(event)
                if parsed:
                    results.append(parsed)

            if len(events) < page_size:
                break
            skip += page_size

        return results

    def _parse_event(self, event: dict) -> dict[str, Any] | None:
        """Parse a single event from API response."""
        pacific = ZoneInfo('America/Los_Angeles')

        # Parse UTC times and convert to Pacific
        start_utc = event.get('StartUTC')
        if not start_utc:
            return None

        event_start_utc = datetime.fromisoformat(start_utc.replace('Z', '+00:00'))
        event_start = event_start_utc.astimezone(pacific)

        # Parse end time
        end_utc = event.get('EndUTC')
        if end_utc:
            event_end_utc = datetime.fromisoformat(end_utc.replace('Z', '+00:00'))
            event_end = event_end_utc.astimezone(pacific)
        else:
            event_end = event_start

        # Get URL from links, fall back to CitySpark event page
        url = ''
        links = event.get('Links') or []
        if links and isinstance(links, list) and len(links) > 0:
            url = links[0].get('url') or ''

        # If no link URL, use publisher's calendar page as fallback
        if not url and self.calendar_url:
            url = self.calendar_url

        return {
            'title': event.get('Name', 'Untitled Event'),
            'dtstart': event_start,
            'dtend': event_end,
            'location': event.get('Venue', ''),
            'description': event.get('Description', ''),
            'url': url,
            'uid': event.get('Id') or event.get('PId', ''),
        }


class BohemianScraper(CitySparkScraper):
    """Scraper for North Bay Bohemian events."""

    name = "North Bay Bohemian"
    domain = "bohemian.com"
    api_slug = "Bohemian"
    ppid = 9093
    lat = 38.4282591
    lng = -122.5548637
    distance = 30
    calendar_url = "https://bohemian.com/events-calendar/"


class PressDemocratScraper(CitySparkScraper):
    """Scraper for Press Democrat events."""

    name = "Press Democrat"
    domain = "pressdemocrat.com"
    api_slug = "SRPressDemocrat"
    ppid = 8662
    lat = 38.5212368
    lng = -122.8540282
    distance = 40
    calendar_url = "https://www.pressdemocrat.com/events/"
