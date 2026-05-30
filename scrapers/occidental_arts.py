#!/usr/bin/env python3
"""Scraper for Occidental Center for the Arts events."""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import time
from datetime import date, datetime
from typing import Any
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from icalendar import Calendar

from lib.base import BaseScraper


class OccidentalArtsScraper(BaseScraper):
    """Scraper for Occidental Center for the Arts events."""

    name = "Occidental Center for the Arts"
    domain = "occidentalcenterforthearts.org"

    BASE_URL = "https://www.occidentalcenterforthearts.org"
    EVENTS_URL = f"{BASE_URL}/upcoming-events"
    DEFAULT_LOCATION = "Occidental Center for the Arts, 3850 Doris Murphy Court, Occidental, CA 95465"

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch and parse events from the upcoming-events listing."""
        self.logger.info(f"Fetching {self.EVENTS_URL}")
        main_page = self.fetch_text_with_curl(self.EVENTS_URL)

        soup = BeautifulSoup(main_page, "html.parser")
        events = []

        for event_elem in soup.find_all("article", class_="eventlist-event"):
            try:
                event = self._parse_event(event_elem)
                if event:
                    if self._is_past_event(event):
                        continue
                    events.append(event)
                    self.logger.info(f"Found event: {event['title']} on {event['dtstart']}")

                time.sleep(0.25)
            except Exception as e:
                self.logger.warning(f"Error parsing event: {e}")

        return events

    def _parse_event(self, event_elem) -> dict[str, Any] | None:
        """Parse a single event from the listing and its ICS export."""
        title_link = event_elem.find("a", class_="eventlist-title-link")
        if not title_link:
            return None

        title = title_link.text.strip()
        url = urljoin(self.BASE_URL, title_link["href"])
        description = self._extract_description(event_elem)
        ical_url = f"{url}?format=ical"

        ical_content = self.fetch_text_with_curl(
            ical_url,
            accept="text/calendar,*/*;q=0.9",
            referer=self.EVENTS_URL,
        )
        cal = Calendar.from_ical(ical_content)

        for component in cal.walk():
            if component.name != "VEVENT":
                continue

            dtstart = component.get("dtstart")
            if not dtstart:
                return None

            summary = str(component.get("summary", "")).strip() or title
            location = str(component.get("location", "")).strip() or self.DEFAULT_LOCATION
            ics_description = str(component.get("description", "")).strip()
            uid = str(component.get("uid", "")).strip()
            dtend = component.get("dtend")

            return {
                "title": summary,
                "dtstart": dtstart.dt,
                "dtend": dtend.dt if dtend else None,
                "url": url,
                "location": location,
                "description": ics_description or description,
                "uid": uid,
            }

        self.logger.warning(f"No VEVENT found in ICS for {title}")
        return None

    def _extract_description(self, event_elem) -> str:
        """Extract human-readable description from the listing card."""
        desc_elem = event_elem.find("div", class_="eventlist-description")
        if not desc_elem:
            return ""

        lines = []
        last_line = None
        for raw_line in desc_elem.get_text("\n", strip=True).splitlines():
            line = " ".join(raw_line.split())
            if not line or line == last_line:
                continue
            lines.append(line)
            last_line = line
        return "\n".join(lines)

    def _is_past_event(self, event: dict[str, Any]) -> bool:
        """Skip events that have already ended."""
        dt = event.get("dtend") or event.get("dtstart")
        if dt is None:
            return False

        now = datetime.now(ZoneInfo(self.timezone))
        if isinstance(dt, datetime):
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=ZoneInfo(self.timezone))
            else:
                dt = dt.astimezone(ZoneInfo(self.timezone))
            return dt < now

        if isinstance(dt, date):
            return dt < now.date()

        return False


if __name__ == '__main__':
    OccidentalArtsScraper.main()
