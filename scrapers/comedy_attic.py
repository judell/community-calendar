#!/usr/bin/env python3
"""Scraper for The Comedy Attic events.

SeatEngine-hosted site. Listing page has date ranges but no times;
detail pages have JSON-LD Event schema with per-showtime startDate in UTC.
"""

import json
import re
import sys
import time
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(__file__).rsplit("/", 1)[0])
from lib.base import BaseScraper


class ComedyAtticScraper(BaseScraper):
    """Scraper for The Comedy Attic in Bloomington."""

    name = "The Comedy Attic"
    domain = "comedyattic.com"
    events_url = "https://comedyattic.com/events"
    timezone = "America/Indiana/Indianapolis"
    location = "The Comedy Attic, 123 S Walnut St, Bloomington, IN"

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events by scraping listing page, then parsing JSON-LD from each detail page."""
        self.logger.info(f"Fetching event listing from {self.events_url}")

        response = requests.get(
            self.events_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            },
            timeout=30,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        tz = ZoneInfo(self.timezone)

        # Extract event URLs from listing page
        event_entries = []
        for item in soup.select(".event-list-item"):
            header = item.select_one(".el-header a")
            if not header:
                continue
            title = header.get_text(strip=True)
            url = header.get("href", "")
            if url and not url.startswith("http"):
                url = f"https://comedyattic.com{url}"
            event_entries.append((title, url))

        self.logger.info(f"Found {len(event_entries)} events on listing page")

        # Fetch each detail page and extract JSON-LD showtimes
        events = []
        for idx, (_, url) in enumerate(event_entries):
            self.logger.debug(
                f"Fetching detail page {idx + 1}/{len(event_entries)}: {url}"
            )
            try:
                showtimes = self._fetch_detail_jsonld(url, tz)
                events.extend(showtimes)
            except Exception as e:
                self.logger.warning(f"Failed to fetch {url}: {e}")
                continue
            # Be polite between requests
            if idx < len(event_entries) - 1:
                time.sleep(0.3)

        self.logger.info(
            f"Found {len(events)} showtimes across {len(event_entries)} events"
        )
        return events

    def _fetch_detail_jsonld(self, url: str, tz: ZoneInfo) -> list[dict[str, Any]]:
        """Fetch an event detail page and extract JSON-LD Event schema."""
        response = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            },
            timeout=30,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        events = []

        for script in soup.select('script[type="application/ld+json"]'):
            try:
                data = json.loads(script.string)
            except (json.JSONDecodeError, TypeError):
                continue

            if not isinstance(data, dict) or data.get("@type") != "Event":
                continue

            name = data.get("name", "").strip()
            start_str = data.get("startDate", "")
            if not name or not start_str:
                continue

            # Parse ISO 8601 UTC date
            try:
                dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
            except ValueError:
                self.logger.warning(f"Could not parse startDate: {start_str}")
                continue

            # Convert to local timezone
            dt = dt.astimezone(tz)

            # Default show time is 8 PM if no specific time (midnight UTC)
            if dt.hour == 0 and dt.minute == 0:
                dt = dt.replace(hour=20)

            # 2-hour shows by default
            dtend = dt + timedelta(hours=2)

            # Location from JSON-LD or fallback
            loc = self.location
            ld_loc = data.get("location", {})
            if isinstance(ld_loc, dict):
                addr = ld_loc.get("address", {})
                venue_name = ld_loc.get("name", "")
                if isinstance(addr, dict):
                    parts = [venue_name] if venue_name else []
                    street = addr.get("streetAddress", "")
                    locality = addr.get("addressLocality", "")
                    region = addr.get("addressRegion", "")
                    city_state = f"{locality}, {region}".strip(", ")
                    if street:
                        parts.append(street)
                    if city_state:
                        parts.append(city_state)
                    loc = ", ".join(parts) or loc

            # Description: strip HTML tags from JSON-LD description
            desc = data.get("description", name)
            if desc and "<" in desc:
                desc = BeautifulSoup(desc, "html.parser").get_text(" ", strip=True)
            if not desc:
                desc = name

            # Use show URL from JSON-LD for per-showtime linking and UID
            show_url = data.get("url", url)
            slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40]
            uid = f"{dt.strftime('%Y%m%d')}-{slug}-{dt.strftime('%H%M')}"

            events.append(
                {
                    "title": name,
                    "dtstart": dt,
                    "dtend": dtend,
                    "url": show_url,
                    "location": loc,
                    "description": desc,
                    "uid": uid,
                }
            )

        return events


if __name__ == "__main__":
    ComedyAtticScraper.main()
