#!/usr/bin/env python3
"""Scraper for Habitat for Humanity of Monroe County events."""

import re
import sys
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup, Tag

sys.path.insert(0, __file__.rsplit("/", 2)[0])
from lib.base import BaseScraper

# The /events/ archive renders each card's date as a full month name.
MONTHS = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class HabitatScraper(BaseScraper):
    """Scraper for Habitat for Humanity of Monroe County."""

    name = "Habitat for Humanity Monroe County"
    domain = "monroecountyhabitat.org"
    events_url = "https://monroecountyhabitat.org/events/"
    timezone = "America/Indiana/Indianapolis"

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from the /events/ archive page."""
        self.logger.info(f"Fetching {self.events_url}")
        response = requests.get(self.events_url, headers=HEADERS, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        tz = ZoneInfo(self.timezone)
        events = []
        seen = set()

        for h3 in soup.select("h3"):
            card = h3.find_parent("div", class_="kt-inside-inner-col")
            if card is None:
                continue
            event = self._parse_card(card, h3, tz)
            if event is None or event["uid"] in seen:
                continue
            seen.add(event["uid"])
            events.append(event)

        self.logger.info(f"Found {len(events)} events")
        return events

    def _parse_card(self, card: Tag, title_el: Tag, tz: ZoneInfo) -> dict[str, Any] | None:
        """Parse one event card, or None if it has no title/date."""
        title = title_el.get_text(strip=True)
        if not title:
            return None

        dtstart = self._parse_date(card.get_text(" ", strip=True), tz)
        if dtstart is None:
            return None
        dtend = dtstart + timedelta(hours=3)

        title_div = title_el.find_parent("div")
        desc_el = title_div.find_next_sibling("div") if title_div else None
        description = desc_el.get_text(" ", strip=True)[:300] if desc_el else ""

        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:40]
        uid = f"habitat-{dtstart:%Y%m%d}-{slug}@monroecountyhabitat.org"

        return {
            "title": title,
            "dtstart": dtstart,
            "dtend": dtend,
            "url": self.events_url,
            "location": "Bloomington, IN",
            "description": description,
            "uid": uid,
        }

    @staticmethod
    def _parse_date(text: str, tz: ZoneInfo) -> datetime | None:
        """Parse a full "Month D, YYYY" date from card text.

        A month-only label ("December 2026") is not a date: its real day is
        unknown, so publishing any concrete day would invent one, and the
        past-event filter would then drop the event once that day passes.
        Skip it until the source supplies a real day.
        """
        match = re.search(r"([A-Z][a-z]+)\s+(\d{1,2}),\s*(\d{4})", text)
        if match and match.group(1) in MONTHS:
            day = int(match.group(2))
            if not 1 <= day <= 31:
                return None
            try:
                return datetime(int(match.group(3)), MONTHS[match.group(1)], day, 12, 0, tzinfo=tz)
            except ValueError:  # e.g. "February 31" — a malformed card, not ours to guess
                return None
        return None


if __name__ == "__main__":
    HabitatScraper.main()
