"""Generic Bibliocommons events scraper base."""

from datetime import datetime, timedelta
from typing import Any, Optional
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from .base import BaseScraper


class BibliocommonsEventsScraper(BaseScraper):
    """
    Reusable scraper for Bibliocommons library event endpoints.

    Subclasses should set:
    - name
    - domain
    - timezone
    - library_slug (e.g. "tpl")
    - optional audience_ids/type_ids/program_ids/language_ids filters
    """

    gateway_url = "https://gateway.bibliocommons.com/v2"
    library_slug: str = ""
    page_limit: int = 100
    max_pages: int = 120
    request_timeout: int = 30

    # Optional allow-list filters applied client-side on event definition IDs
    audience_ids: list[str] = []
    type_ids: list[str] = []
    program_ids: list[str] = []
    language_ids: list[str] = []

    headers = {"User-Agent": "Mozilla/5.0 (compatible; community-calendar/1.0)"}

    def fetch_events(self) -> list[dict[str, Any]]:
        if not self.library_slug:
            self.logger.error("library_slug is required for BibliocommonsEventsScraper")
            return []

        tz = ZoneInfo(self.timezone)
        horizon = datetime.now(tz) + timedelta(days=self.months_ahead * 31)
        base_url = f"{self.gateway_url}/libraries/{self.library_slug}/events"

        events: list[dict[str, Any]] = []
        seen_ids: set[str] = set()

        for page in range(1, self.max_pages + 1):
            payload = self._fetch_page(base_url, page)
            if not payload:
                break

            page_items = payload.get("events", {}).get("items", [])
            if not page_items:
                break

            entities = payload.get("entities", {})
            location_entities = entities.get("locations", {}) or {}
            event_entities = entities.get("events", {}) or {}

            page_starts: list[datetime] = []

            for event_id in page_items:
                event_obj = event_entities.get(event_id)
                if not isinstance(event_obj, dict):
                    continue

                definition = event_obj.get("definition") or {}
                if not isinstance(definition, dict):
                    continue

                if not self._matches_filters(definition):
                    continue

                event = self._map_event(event_id, event_obj, definition, location_entities, tz)
                if not event:
                    continue

                dtstart = event.get("dtstart")
                if isinstance(dtstart, datetime):
                    page_starts.append(dtstart)

                if event_id in seen_ids:
                    continue
                seen_ids.add(event_id)
                events.append(event)

            # Heuristic early stop: listings are chronological; once an entire
            # page starts after our horizon, remaining pages are out-of-range.
            if page_starts and min(page_starts) > horizon:
                break

        self.logger.info(f"Collected {len(events)} Bibliocommons events ({self.library_slug})")
        return events

    def _fetch_page(self, base_url: str, page: int) -> Optional[dict[str, Any]]:
        try:
            resp = requests.get(
                base_url,
                params={"limit": self.page_limit, "page": page},
                headers=self.headers,
                timeout=self.request_timeout,
            )
            if resp.status_code != 200:
                self.logger.debug(f"HTTP {resp.status_code} for page {page}")
                return None
            return resp.json()
        except Exception as exc:
            self.logger.debug(f"Failed page {page}: {exc}")
            return None

    def _matches_filters(self, definition: dict[str, Any]) -> bool:
        if self.audience_ids:
            current = set(definition.get("audienceIds") or [])
            if not current.intersection(self.audience_ids):
                return False

        if self.type_ids:
            current = set(definition.get("typeIds") or [])
            if not current.intersection(self.type_ids):
                return False

        if self.program_ids:
            program = definition.get("programId")
            if not program or program not in self.program_ids:
                return False

        if self.language_ids:
            current = set(definition.get("languageIds") or [])
            if not current.intersection(self.language_ids):
                return False

        return True

    def _map_event(
        self,
        event_id: str,
        event_obj: dict[str, Any],
        definition: dict[str, Any],
        location_entities: dict[str, Any],
        tz: ZoneInfo,
    ) -> Optional[dict[str, Any]]:
        title = (definition.get("title") or "").strip()
        if not title:
            return None

        if definition.get("isCancelled") is True:
            return None

        dtstart = self._parse_dt(event_obj.get("indexStart") or definition.get("start"), tz)
        if not dtstart:
            return None
        dtend = self._parse_dt(event_obj.get("indexEnd") or definition.get("end"), tz)

        location = self._location_text(definition, location_entities)
        description = self._clean_html(definition.get("description") or "")

        return {
            "uid": f"{event_id}@{self.domain}",
            "title": title,
            "dtstart": dtstart,
            "dtend": dtend or dtstart,
            "location": location,
            "description": description,
            "url": f"https://{self.library_slug}.bibliocommons.com/v2/events/{event_id}",
        }

    def _parse_dt(self, value: Any, tz: ZoneInfo) -> Optional[datetime]:
        if not value or not isinstance(value, str):
            return None
        s = value.strip().replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=tz)
            return dt
        except ValueError:
            return None

    def _location_text(self, definition: dict[str, Any], location_entities: dict[str, Any]) -> str:
        parts: list[str] = []

        branch_id = definition.get("branchLocationId")
        if branch_id and branch_id in location_entities:
            name = (location_entities[branch_id].get("name") or "").strip()
            if name:
                parts.append(name)

        non_branch_id = definition.get("nonBranchLocationId")
        if non_branch_id and non_branch_id in location_entities:
            name = (location_entities[non_branch_id].get("name") or "").strip()
            if name and name not in parts:
                parts.append(name)

        detail = (definition.get("locationDetails") or "").strip()
        if detail:
            parts.append(detail)

        return ", ".join([p for p in parts if p])

    def _clean_html(self, raw: str) -> str:
        if not raw:
            return ""
        soup = BeautifulSoup(raw, "html.parser")
        return soup.get_text("\n", strip=True)

