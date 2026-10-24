"""Base scraper class with common functionality."""

import argparse
import logging
import os
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo

from icalendar import Calendar, Event

from .horizon import horizon_end, within
from .utils import generate_uid

if TYPE_CHECKING:
    from datetime import datetime


class SourceNotReachedError(RuntimeError):
    """A scraper returned no events without declaring it reached its source.

    An empty result from a source that was never reached is a False quiet: it
    looks like a dormant calendar and would be swept like one. Failing keeps
    the source's rows and makes the outage visible.
    """


class BaseScraper(ABC):
    """
    Base class for event scrapers.

    Subclasses must implement:
    - name: str - Source name (e.g., "Redwood Cafe")
    - domain: str - Domain for UIDs (e.g., "redwoodcafecotati.com")
    - fetch_events() -> list[dict]

    Subclasses must also call `mark_source_reached()` from `fetch_events()`
    once their primary fetch has returned and parsed. Without that declaration
    an empty result fails the run, because the base class cannot tell an
    unreachable source from a quiet one.

    Each event dict should have:
    - title: str (required)
    - dtstart: datetime (required)
    - dtend: datetime (optional, defaults to dtstart)
    - url: str (optional)
    - location: str (optional)
    - description: str (optional)
    - geo: tuple[float, float] (optional, (lat, lng) emitted as ICS GEO)
    - uid: str (optional, defaults to a generated UID)
    - image_url: str (optional, emitted as an ICS ATTACH)
    """

    name: str = "Unknown Source"
    domain: str = "example.com"
    timezone: str = "America/Los_Angeles"
    default_url: str | None = None
    source_url: str | None = None

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.months_ahead = int(os.environ.get("SCRAPE_MONTHS", 6))

    def horizon_cutoff(self, now: datetime | None = None) -> datetime:
        """This scraper's Horizon boundary; see `lib/horizon.py`.

        Pass `now` to key the boundary to the source's own clock.
        """
        return horizon_end(now, self.months_ahead)

    def mark_source_reached(self) -> None:
        """Declare that the primary fetch reached the source.

        Call this from `fetch_events()` once the primary listing or API payload
        has come back and parsed. It lets a quiet source (valid payload, no
        upcoming events) exit 0 while an outage fails the run. Never call it
        from an exception handler.
        """
        self._source_reached = True

    @classmethod
    def setup_logging(cls, level: int = logging.INFO):
        """Configure logging for scrapers."""
        logging.basicConfig(
            level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    @classmethod
    def parse_args(cls, description: str | None = None) -> argparse.Namespace:
        """Parse standard command-line arguments."""
        parser = argparse.ArgumentParser(
            description=description or f"Scrape events from {cls.name}"
        )
        parser.add_argument("--output", "-o", type=str, help="Output filename")
        parser.add_argument(
            "--default-url", type=str, help="Fallback URL when events have no per-event URL"
        )
        parser.add_argument("--debug", action="store_true", help="Enable debug logging")
        return parser.parse_args()

    @abstractmethod
    def fetch_events(self) -> list[dict[str, Any]]:
        """
        Fetch and parse all available events from the source.

        Returns list of event dicts with keys:
        - title, dtstart, dtend, url, location, description
        """

    def create_calendar(self, events: list[dict[str, Any]]) -> Calendar:
        """Create an iCalendar from parsed events."""
        cal = Calendar()
        cal.add("prodid", f"-//{self.name}//{self.domain}//")
        cal.add("version", "2.0")
        cal.add("x-wr-calname", self.name)
        cal.add("x-wr-timezone", self.timezone)

        for event_data in events:
            event = self.create_event(event_data)
            if event:
                cal.add_component(event)

        return cal

    def create_event(self, data: dict[str, Any]) -> Event | None:
        """Create an iCalendar Event from event data."""
        title = data.get("title")
        dtstart = data.get("dtstart")

        if not title or not dtstart:
            self.logger.warning(f"Skipping event with missing title or dtstart: {data}")
            return None

        event = Event()
        event.add("summary", title)
        # Convert to target timezone then strip tzinfo, setting TZID explicitly
        # as a string to avoid icalendar serializing ZoneInfo objects
        if hasattr(dtstart, "tzinfo") and dtstart.tzinfo is not None:
            target_tz = ZoneInfo(self.timezone)
            dtstart = dtstart.astimezone(target_tz)
            dtend = data.get("dtend") or dtstart
            dtend = dtend.astimezone(target_tz)
            tz_params = {"TZID": self.timezone}
            event.add("dtstart", dtstart.replace(tzinfo=None), parameters=tz_params)
            event.add("dtend", dtend.replace(tzinfo=None), parameters=tz_params)
        else:
            event.add("dtstart", dtstart)
            event.add("dtend", data.get("dtend") or dtstart)

        url = data.get("url") or self.default_url
        if url:
            event.add("url", url)

        if data.get("location"):
            event.add("location", data["location"])

        if data.get("geo"):
            lat, lng = data["geo"]
            event.add("geo", (lat, lng))

        event.add("description", data.get("description", ""))

        uid = data.get("uid") or generate_uid(title, dtstart, self.domain)
        event.add("uid", uid)
        event.add("x-source", self.name)
        if self.source_url:
            event.add("x-source-url", self.source_url)

        if data.get("image_url"):
            event.add("attach", data["image_url"], parameters={"fmttype": "image/jpeg"})

        return event

    def default_output_filename(self) -> str:
        """Generate default output filename."""
        # Convert name to snake_case
        name_slug = self.name.lower().replace(" ", "_").replace("'", "")
        return f"{name_slug}.ics"

    def fetch_text_with_curl(
        self,
        url: str,
        *,
        accept: str | None = None,
        referer: str | None = None,
        timeout: int = 30,
    ) -> str:
        """Fetch text content via curl for sites that block urllib in CI."""
        # shortcut: no -f, so HTTP error bodies are returned to the caller.
        # Adding it changes error semantics for the non-Bloomington scrapers
        # that share this helper (#243 left that migration out of scope).
        cmd = ["curl", "-sL", "-A", "Mozilla/5.0", "--max-time", str(timeout)]
        if accept:
            cmd.extend(["-H", f"Accept: {accept}"])
        if referer:
            cmd.extend(["-e", referer])
        cmd.append(url)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)
        if result.returncode != 0 or not result.stdout:
            stderr = (result.stderr or "").strip()
            raise RuntimeError(f"curl fetch failed for {url}: {stderr or result.returncode}")
        return result.stdout

    def run(self, output: str | None = None) -> str:
        """Main entry point: fetch events and write calendar."""
        self.logger.info(f"Scraping {self.name}")

        self._source_reached = False
        events = self.fetch_events()
        if not events and not self._source_reached:
            raise SourceNotReachedError(
                f"{self.name} returned no events without declaring reaching its "
                "source: the primary fetch failed (see the logged fetch error) or "
                "mark_source_reached() was never called after a successful parse"
            )
        cutoff = self.horizon_cutoff()
        before = len(events)

        events = [e for e in events if within(e.get("dtstart"), cutoff)]
        if len(events) < before:
            self.logger.info(
                f"Filtered {before - len(events)} events beyond {self.months_ahead} months out"
            )
        self.logger.info(f"Found {len(events)} events")

        calendar = self.create_calendar(events)

        filename = output or self.default_output_filename()
        with Path(filename).open("wb") as f:
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
        if getattr(args, "default_url", None):
            scraper.default_url = args.default_url
        scraper.run(args.output)
