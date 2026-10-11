#!/usr/bin/env python3
"""Events from On Tap Tickets' ticketing calendar (Tier 10, The MET).

ontaptickets.com's event-calendar page embeds Evvnt's discovery widget
(publisher_id 11409), and that widget's listing comes from a public JSON API.
Each page of the API carries the full event — times, venue, ticket URL — so
no detail pages are fetched.

The listing is On Tap's clients across Indiana, not just Monroe County; the
pipeline's combine-time geo filter (lib/city_filter.py) drops the out-of-area
ones, so nothing is filtered here.
"""

import contextlib
import json
import sys
from datetime import datetime, timedelta
from typing import Any

sys.path.insert(0, __file__.rsplit("/", 1)[0])

from lib.base import BaseScraper
from lib.timeutil import assume_utc, utc_now
from lib.utils import fetch_with_retry, generate_uid

# From the widget config on https://www.ontaptickets.com/event-calendar.html
API_URL = "https://discovery.evvnt.com/api/publisher/11409/home_page_events"
MAX_PAGES = 10  # bounds fetches; the live listing is ~2 pages of 30


class OnTapTicketsScraper(BaseScraper):
    name = "On Tap Tickets"
    domain = "ontaptickets.com"
    timezone = "America/Indiana/Indianapolis"
    source_url = "https://www.ontaptickets.com/event-calendar.html"

    def fetch_events(self) -> list[dict[str, Any]]:
        now = utc_now()
        events: list[dict[str, Any]] = []
        for page in range(1, MAX_PAGES + 1):
            items = self._fetch_page(page)
            if not items:
                break
            if page == MAX_PAGES:
                # A full last page means the listing runs past the cap and this
                # run is incomplete. Same warning localist.py gives.
                self.logger.warning(f"Stopping at page cap ({MAX_PAGES}); more pages remain")
            self.logger.info(f"Page {page}: {len(items)} raw events")
            for item in items:
                parsed = self._parse_event(item, now)
                if parsed:
                    events.append(parsed)
        return events

    def _fetch_page(self, page: int) -> list[dict[str, Any]]:
        payload = json.loads(fetch_with_retry(f"{API_URL}?page={page}"))
        return payload.get("rawEvents") or []

    def _parse_event(self, item: dict[str, Any], now: datetime) -> dict[str, Any] | None:
        start = item.get("start_time")
        if not start:
            return None

        try:
            dtstart = datetime.fromisoformat(start)
        except ValueError:
            self.logger.warning(f"Skipping {item.get('title')!r}: unparseable start {start!r}")
            return None

        dtend = dtstart + timedelta(hours=2)
        end = item.get("end_time")
        if end:
            with contextlib.suppress(ValueError):
                dtend = datetime.fromisoformat(end)
        if dtstart.tzinfo and dtend.tzinfo is None:
            # An end with no offset belongs to the event's own clock. Left naive,
            # base.create_event reads it as the runner's zone and can emit an end
            # that precedes the start.
            dtend = dtend.replace(tzinfo=dtstart.tzinfo)

        # assume_utc, not a bare compare: a zoneless timestamp would otherwise
        # raise TypeError here and abandon every remaining event in the build.
        if assume_utc(dtend) < now:
            return None  # the listing still carries events that have already ended

        venue: dict[str, Any] = item.get("venue") or {}
        # original_links is the source's own ticket page; links is Evvnt's
        # affiliate redirect, used only when there is nothing better.
        links: dict[str, Any] = item.get("original_links") or item.get("links") or {}
        title = item.get("title", "")

        event: dict[str, Any] = {
            "title": title,
            "dtstart": dtstart,
            "dtend": dtend,
            "url": links.get("Tickets") or item.get("source_broadcast_url"),
            "location": venue_location(venue),
            "description": item.get("description") or item.get("summary") or "",
            # source_id keys the UID: one listing can repeat the same title and
            # start (a double-booked workshop), and title+time would collapse them.
            "uid": generate_uid(str(item.get("source_id") or title), dtstart, self.domain),
        }

        lat, lng = venue.get("latitude"), venue.get("longitude")
        if lat is not None and lng is not None:
            event["geo"] = (lat, lng)
        images: list[dict[str, Any]] = item.get("images") or []
        if images:
            event["image_url"] = (images[0].get("original") or {}).get("url")

        return event


def venue_location(venue: dict[str, Any]) -> str:
    """Venue, street, town and ZIP — the geo filter matches on the town or ZIP.

    A part the previous one already spells out is dropped, keeping whichever is
    longer: `name` is often the street address, or just the town.
    """
    town, post_code = venue.get("town"), venue.get("post_code")
    city_line = " ".join(p for p in (f"{town}," if town else "", post_code) if p)

    parts: list[str] = []
    for part in (venue.get("name"), venue.get("address_1"), city_line):
        if not part:
            continue
        if parts and (part.lower() in parts[-1].lower() or parts[-1].lower() in part.lower()):
            if len(part) > len(parts[-1]):
                parts[-1] = part
            continue
        parts.append(part)
    return ", ".join(parts)


if __name__ == "__main__":
    OnTapTicketsScraper.main()
