#!/usr/bin/env python3
"""Scraper for FAR Center for Contemporary Arts events (Craft CMS)."""

import re
import sys
from datetime import datetime, timedelta
from typing import Any, ClassVar
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, __file__.rsplit("/", 2)[0])
from lib.base import BaseScraper
from lib.timeutil import parse_naive_ics
from lib.utils import generate_uid


class FARCenterScraper(BaseScraper):
    """Scraper for FAR Center for Contemporary Arts in Bloomington."""

    name = "FAR Center for Contemporary Arts"
    domain = "thefar.org"
    events_url = "https://www.thefar.org/events/list"
    timezone = "America/Indiana/Indianapolis"

    HEADERS: ClassVar[dict[str, str]] = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    # Day-of-week names to strip from date strings
    DAYS = r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s*"

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from the FAR Center events list."""
        self.logger.info(f"Fetching {self.events_url}")
        response = requests.get(self.events_url, headers=self.HEADERS, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        tz = ZoneInfo(self.timezone)
        events: list[dict[str, Any]] = []

        main = soup.select_one(".entry-main")
        if not main:
            # A missing container is a layout change, not a quiet week. Raise
            # so the run exits non-zero with a traceback, instead of writing a
            # valid-empty calendar that report.py reads as a quiet week.
            raise RuntimeError(
                "FAR Center listing page has no .entry-main container; the layout changed"
            )

        now = datetime.now(tz)
        cards = list(main.select("div.mb-8"))
        for card in cards:
            events.extend(self._parse_card(card, tz, now))

        # Container present with no cards is a genuine quiet week; cards that
        # yield no date at all mean the cards changed shape.
        if cards and not events:
            raise RuntimeError(
                f"FAR Center listing has {len(cards)} cards but none carried a "
                "parseable date; the card layout changed"
            )

        self.logger.info(f"Found {len(events)} events")
        return events

    def _parse_card(self, card, tz: ZoneInfo, now: datetime) -> list[dict[str, Any]]:
        """Parse a card into one event per date it lists."""
        title_el = card.select_one("h3 a")
        if not title_el:
            return []

        title = title_el.get_text(strip=True)
        url = title_el.get("href", "")
        if url and not url.startswith("http"):
            url = f"https://www.thefar.org{url}"

        paragraphs = card.select("p.text-sm.mb-1")
        description = ""
        dtstart = None
        dtend = None
        upcoming = ""

        for p in paragraphs:
            text = p.get_text(strip=True)
            if text.lower().startswith("upcoming:"):
                upcoming = text
            # Check if this paragraph contains a date pattern
            elif not dtstart and re.search(
                r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d",
                text,
            ):
                start, end = self._parse_datetime(text, tz, now)
                if start:
                    dtstart, dtend = start, end
            elif not dtstart:
                description = text

        if not dtstart:
            return []

        if not dtend:
            dtend = dtstart + timedelta(hours=2)

        # Key the UID by the detail-page id and the occurrence datetime, as
        # WFIU does. A truncated title slug can collide across events; the
        # datetime keeps each occurrence of a recurring card distinct.
        event_id = re.search(r"/events/event/(\d+)", url)
        identity = event_id.group(1) if event_id else (url or title)

        def occurrence(start: datetime, end: datetime) -> dict[str, Any]:
            return {
                "title": title,
                "dtstart": start,
                "dtend": end,
                "url": url,
                "location": "FAR Center for Contemporary Arts, 505 W 4th St, Bloomington, IN",
                "description": description,
                "uid": generate_uid(identity, start, self.domain),
            }

        events = [occurrence(dtstart, dtend)]
        for start, end in self._parse_upcoming(upcoming, dtstart, dtend, tz, now):
            events.append(occurrence(start, end))
        return events

    def _parse_upcoming(
        self, text: str, dtstart: datetime, dtend: datetime, tz: ZoneInfo, now: datetime
    ) -> list[tuple[datetime, datetime]]:
        """Extra dates a card lists after "Upcoming:".

        The monthly Photo Review lists e.g. "Upcoming: November 18, December
        16, January 20, February 17, March 17". Each shares the primary
        occurrence's time of day.
        """
        if not text:
            return []
        body = text.split(":", 1)[1]
        span = dtend - dtstart
        time_str = dtstart.strftime("%I:%M%p")
        occurrences = []
        for token in body.split(","):
            token = token.strip()
            if not token:
                continue
            # Each comma-separated entry is "Month D". Warn for any token that
            # is not one, so an unrecognised format (Nov. 18, 11/18) surfaces
            # instead of the date vanishing while the primary still parses.
            if re.fullmatch(r"[A-Za-z]+ \d{1,2}", token):
                start = self._make_dt(token, time_str, self._resolve_year(token, now), tz)
            else:
                start = None
            if start:
                occurrences.append((start, start + span))
            else:
                self.logger.warning(f"Unparseable upcoming date {token!r} in {text!r}")
        return occurrences

    def _parse_datetime(self, text: str, tz: ZoneInfo, now: datetime):
        """Parse date/time from strings like 'Friday, April 3 | 5:00pm - 8:00pm'.

        A yearless date binds to `now`'s year, or to the next year when it has
        already passed; the listing carries upcoming events only.
        """
        # Strip day-of-week
        text = re.sub(self.DAYS, "", text, flags=re.IGNORECASE)

        # Match: "April 3 | 5:00pm - 8:00pm" or "April 9 2:30pm - April 10 9:30pm"
        # Simple case: single date with time range
        m = re.match(
            r"(\w+ \d{1,2})\s*\|\s*(\d{1,2}:\d{2}\s*[ap]m)\s*[-–]\s*(\d{1,2}:\d{2}\s*[ap]m)",
            text,
            re.IGNORECASE,
        )
        if m:
            year = self._resolve_year(m.group(1), now)
            dtstart = self._make_dt(m.group(1), m.group(2), year, tz)
            dtend = self._make_dt(m.group(1), m.group(3), year, tz)
            if dtstart and dtend and dtend < dtstart:
                dtend += timedelta(days=1)
            return dtstart, dtend

        # Multi-day: "April 9 2:30pm - April 10 9:30pm"
        m = re.match(
            r"(\w+ \d{1,2})\s+(\d{1,2}:\d{2}\s*[ap]m)\s*[-–]\s*(\w+ \d{1,2})\s+(\d{1,2}:\d{2}\s*[ap]m)",
            text,
            re.IGNORECASE,
        )
        if m:
            dtstart = self._make_dt(m.group(1), m.group(2), self._resolve_year(m.group(1), now), tz)
            dtend = self._make_dt(m.group(3), m.group(4), self._resolve_year(m.group(3), now), tz)
            if dtstart and dtend and dtend < dtstart:
                dtend = dtend.replace(year=dtend.year + 1)
            return dtstart, dtend

        # Date only, no time: "April 3"
        m = re.match(r"(\w+ \d{1,2})", text)
        if m:
            year = self._resolve_year(m.group(1), now)
            dtstart = self._make_dt(m.group(1), "12:00 pm", year, tz)
            return dtstart, None

        return None, None

    @staticmethod
    def _resolve_year(date_str: str, now: datetime) -> int:
        """The year a yearless 'Month D' refers to relative to `now`.

        The listing shows upcoming events, so a date that has already passed
        this year belongs to the next one.
        """
        try:
            parsed = parse_naive_ics(f"{date_str} {now.year}", "%B %d %Y")
        except ValueError:
            return now.year
        if (parsed.month, parsed.day) < (now.month, now.day):
            return now.year + 1
        return now.year

    @staticmethod
    def _make_dt(date_str: str, time_str: str, year: int, tz: ZoneInfo) -> datetime | None:
        """Combine 'April 3' + '5:00pm' into a datetime."""
        try:
            dt = parse_naive_ics(f"{date_str} {year}", "%B %d %Y")
        except ValueError:
            return None

        time_str = time_str.strip().lower()
        m = re.match(r"(\d{1,2}):(\d{2})\s*(am|pm)", time_str)
        if not m:
            return None

        hour = int(m.group(1))
        minute = int(m.group(2))
        if m.group(3) == "pm" and hour != 12:
            hour += 12
        elif m.group(3) == "am" and hour == 12:
            hour = 0

        return datetime(dt.year, dt.month, dt.day, hour, minute, tzinfo=tz)


if __name__ == "__main__":
    FARCenterScraper.main()
