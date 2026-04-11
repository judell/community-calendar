"""Generic Bookmanager events scraper base.

Bookmanager hosts the storefronts of many Canadian indie bookstores as a React
SPA. The events page on each store's domain calls the platform API at
``api.bookmanager.com/customer/event/v2/list`` after a two-step bootstrap:

    POST customer/store/getSettings  → store_info.id, store_info.san
    POST customer/session/get        → session_id (cookie-less, per-call)
    POST customer/event/v2/list      → rows[]

Subclasses (or callers via ``__init__``) need only provide:

- ``name``: display name for source attribution
- ``domain``: store website host (used for Origin/Referer + UID namespace)
- ``san``: Standard Address Number (the ``var san="..."`` value embedded in the
  store's events page HTML — also called ``webstore_name`` in API params)
- ``timezone``: IANA timezone (defaults to America/Toronto)

This is the platform-level analogue of ``BibliocommonsEventsScraper``: one base
class that covers every store using Bookmanager hosting.
"""

from datetime import date, datetime
from typing import Any, Optional
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from .base import BaseScraper


class BookmanagerEventsScraper(BaseScraper):
    """Reusable scraper for Bookmanager-hosted bookstore events pages."""

    api_base = "https://api.bookmanager.com/customer/"
    request_timeout: int = 30

    # Subclasses set these (or pass via __init__)
    san: str = ""

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        ),
    }

    def __init__(
        self,
        san: Optional[str] = None,
        name: Optional[str] = None,
        domain: Optional[str] = None,
        timezone: Optional[str] = None,
    ):
        super().__init__()
        if san:
            self.san = san
        if name:
            self.name = name
        if domain:
            self.domain = domain
        if timezone:
            self.timezone = timezone
        self._store_id: Optional[str] = None
        self._session_id: Optional[str] = None

    def _post(self, endpoint: str, params: dict[str, str]) -> dict[str, Any]:
        """POST multipart form to Bookmanager API with the right Origin header."""
        url = f"{self.api_base}{endpoint}?_cb={self.san}"
        # requests.post with files= forces multipart/form-data encoding even for
        # plain string fields, which matches what the SPA sends.
        files = {k: (None, str(v)) for k, v in params.items()}
        headers = dict(self.headers)
        headers["Origin"] = f"https://{self.domain}"
        headers["Referer"] = f"https://{self.domain}/events"
        resp = requests.post(url, files=files, headers=headers, timeout=self.request_timeout)
        resp.raise_for_status()
        return resp.json()

    def _bootstrap(self) -> None:
        """Resolve store_id and session_id by calling the bootstrap endpoints."""
        if not self.san:
            raise ValueError("san is required for BookmanagerEventsScraper")

        settings = self._post("store/getSettings", {"webstore_name": self.san})
        if isinstance(settings, dict) and settings.get("error"):
            raise RuntimeError(f"store/getSettings failed: {settings}")
        store_info = settings.get("store_info") or {}
        store_id = store_info.get("id")
        if store_id is None:
            raise RuntimeError(f"store/getSettings missing store_info.id: {settings}")
        self._store_id = str(store_id)

        sess = self._post(
            "session/get",
            {"store_id": self._store_id, "webstore_name": self.san, "referrer": ""},
        )
        if isinstance(sess, dict) and sess.get("error"):
            raise RuntimeError(f"session/get failed: {sess}")
        session_id = sess.get("session_id")
        if not session_id:
            raise RuntimeError(f"session/get missing session_id: {sess}")
        self._session_id = session_id

    def fetch_events(self) -> list[dict[str, Any]]:
        try:
            self._bootstrap()
        except Exception as exc:
            self.logger.error(f"Bookmanager bootstrap failed for {self.name}: {exc}")
            return []

        try:
            resp = self._post(
                "event/v2/list",
                {
                    "store_id": self._store_id or "",
                    "session_id": self._session_id or "",
                    "webstore_name": self.san,
                    "log_url": "/events",
                },
            )
        except Exception as exc:
            self.logger.error(f"event/v2/list failed for {self.name}: {exc}")
            return []

        rows = resp.get("rows", []) if isinstance(resp, dict) else []
        tz = ZoneInfo(self.timezone)

        events: list[dict[str, Any]] = []
        for row in rows:
            mapped = self._map_event(row, tz)
            if mapped:
                events.append(mapped)

        self.logger.info(
            f"Collected {len(events)} Bookmanager events ({self.name}, san={self.san})"
        )
        return events

    def _map_event(self, row: dict[str, Any], tz: ZoneInfo) -> Optional[dict[str, Any]]:
        title = (row.get("title") or "").strip()
        if not title:
            return None

        date_str = row.get("date") or row.get("original_date")
        if not date_str or len(str(date_str)) != 8:
            return None
        end_date_str = str(row.get("end_date") or date_str)
        date_str = str(date_str)

        all_day = bool(row.get("all_day"))

        try:
            if all_day:
                dtstart: Any = date(int(date_str[:4]), int(date_str[4:6]), int(date_str[6:8]))
                dtend: Any = date(
                    int(end_date_str[:4]), int(end_date_str[4:6]), int(end_date_str[6:8])
                )
            else:
                start_time = row.get("start_time") or "00:00:00"
                end_time = row.get("end_time") or start_time
                dtstart = datetime.strptime(f"{date_str}{start_time}", "%Y%m%d%H:%M:%S").replace(
                    tzinfo=tz
                )
                dtend = datetime.strptime(f"{end_date_str}{end_time}", "%Y%m%d%H:%M:%S").replace(
                    tzinfo=tz
                )
        except (ValueError, TypeError) as exc:
            self.logger.debug(f"Failed to parse event dates ({title}): {exc}")
            return None

        description = self._clean_html(row.get("description") or row.get("summary") or "")
        category = row.get("category") or {}
        category_name = category.get("name") if isinstance(category, dict) else None
        if category_name:
            description = f"[{category_name}]\n{description}" if description else f"[{category_name}]"

        return {
            "uid": f"bm-{row.get('id')}@{self.domain}",
            "title": title,
            "dtstart": dtstart,
            "dtend": dtend,
            "location": (row.get("location_text") or "").strip(),
            "description": description,
            "url": f"https://{self.domain}/events",
            "image_url": row.get("image_url") or None,
        }

    def _clean_html(self, raw: str) -> str:
        if not raw:
            return ""
        soup = BeautifulSoup(raw, "html.parser")
        return soup.get_text("\n", strip=True)
