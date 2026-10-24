"""Squarespace Event scraper library.

Squarespace sites expose event collection data at ?format=json on collection pages.
The JSON includes an 'upcoming' array (and optionally 'items'/'past') with event objects
containing title, startDate/endDate (epoch ms), location, body (HTML), and fullUrl.

Usage:
    from lib.squarespace import SquarespaceScraper

    class MyVenueScraper(SquarespaceScraper):
        name = "My Venue"
        domain = "myvenue.com"
        collection_url = "https://myvenue.com/events"
        default_location = "My Venue, 123 Main St, Anytown, CA"

    if __name__ == '__main__':
        MyVenueScraper.main()
"""

import json
import re
from datetime import UTC, datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .base import BaseScraper


class SquarespaceScraper(BaseScraper):
    """Base class for scrapers that use Squarespace ?format=json API.

    Subclasses should set:
        name: str - Source name
        domain: str - Domain for UIDs
        collection_url: str - Squarespace collection page URL (without ?format=json)
        default_location: str - Fallback location string

    Optional:
        site_url: str - Base URL for resolving relative fullUrl paths (defaults to collection_url's origin)
    """

    collection_url: str = ""
    default_location: str = ""
    site_url: str = ""

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from Squarespace JSON API."""
        url = f"{self.collection_url}?format=json"
        self.logger.info(f"Fetching {url}")

        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; CommunityCalendar/1.0)",
            "Accept": "application/json",
        }
        req = Request(url, headers=headers)
        try:
            with urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except (HTTPError, URLError, json.JSONDecodeError) as e:
            self.logger.error(f"Failed to fetch: {e}")
            return []
        self.mark_source_reached()

        items = data.get("upcoming", data.get("items", []))
        events = []

        base_url = self.site_url
        if not base_url:
            # Derive from collection_url: https://example.com/events -> https://example.com
            from urllib.parse import urlparse

            parsed = urlparse(self.collection_url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"

        for item in items:
            parsed_event = self._parse_item(item, base_url)
            if parsed_event:
                events.append(parsed_event)

        self.logger.info(f"Found {len(events)} upcoming events")
        return events

    def _parse_item(self, item: dict, base_url: str) -> dict[str, Any] | None:
        """Parse a single Squarespace event item."""
        title = item.get("title", "Untitled")
        start_ms = item.get("startDate")
        if not start_ms:
            return None

        dtstart = datetime.fromtimestamp(start_ms / 1000, tz=UTC)

        end_ms = item.get("endDate")
        dtend = datetime.fromtimestamp(end_ms / 1000, tz=UTC) if end_ms else None

        # Description: strip HTML tags
        body = item.get("body", "") or item.get("excerpt", "") or ""
        desc = re.sub(r"<[^>]+>", " ", body).strip()
        desc = re.sub(r"\s+", " ", desc)

        # Location
        location_data = item.get("location", {})
        if isinstance(location_data, dict):
            addr_parts = [
                location_data.get("addressTitle", ""),
                location_data.get("addressLine1", ""),
                location_data.get("addressLine2", ""),
            ]
            loc_str = ", ".join(p for p in addr_parts if p)
            if not loc_str:
                loc_str = self.default_location
        else:
            loc_str = self.default_location

        # URL
        full_url = item.get("fullUrl", "")
        if full_url and not full_url.startswith("http"):
            full_url = f"{base_url}{full_url}"

        return {
            "title": title,
            "dtstart": dtstart,
            "dtend": dtend,
            "description": desc,
            "location": loc_str,
            "url": full_url,
        }
