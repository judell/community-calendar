#!/usr/bin/env python3
"""Visit Bloomington (Monroe County CVB) events via the Simpleview REST API.

The CVB's Simpleview CMS exposes a same-origin JSON API that pages the whole
event inventory over plain HTTP (no browser, no cookie):

    TOKEN:  GET {BASE}/plugins/core/get_simple_token/
    EVENTS: GET {BASE}/includes/rest_v2/plugins_events_events_by_date/find/
              ?json=<{filter,options}>&token=<token>

Akamai rules, all avoided here: a realistic desktop-Chrome User-Agent is
required (the default python-requests UA is 403ed); `limit` must stay below 64
(403 at >=64); the `date_range` filter is a deterministic 403.  Requests are
spaced to honour the site's `robots.txt` `Crawl-delay: 2`.

The endpoint excludes past occurrences and pre-expands recurrence into one
document per occurrence.  A recurring-series document carries a `recurrence`
description and is emitted as its own occurrence; a document without one is
the event itself, and a span wider than a single local day is emitted as one
multi-day event.  The pull is always full, and each occurrence is filtered
client-side against the Horizon (never a server-side date bound).

Usage:
    python scrapers/visit_bloomington.py --output cities/bloomington/visit_bloomington.ics
"""

import sys
from pathlib import Path

sys.path.insert(0, __file__.rsplit("/", 1)[0])
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import hashlib
import html as html_mod
import json
import logging
import re
import time
from datetime import date, datetime, timedelta
from datetime import time as dtime
from typing import Any
from zoneinfo import ZoneInfo

import requests
from lib.base import BaseScraper
from lib.city_filter import load_allowed_cities, location_matches_allowed_cities
from lib.horizon import within

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent

BASE_URL = "https://www.visitbloomington.com"
TOKEN_URL = f"{BASE_URL}/plugins/core/get_simple_token/"
EVENTS_URL = f"{BASE_URL}/includes/rest_v2/plugins_events_events_by_date/find/"
SOURCE_URL = f"{BASE_URL}/events/"

DOMAIN = "visitbloomington.com"
DEFAULT_TIMEZONE = "America/Indiana/Indianapolis"
TIMEZONE = ZoneInfo(DEFAULT_TIMEZONE)

# The city whose allowlist scopes the scrape-time prefilter. It is the same
# cities/<city>/city.conf combine_ics reads, so the prefilter is an optimization
# over the authoritative combine-time geo filter, not a second definition.
CITY = "bloomington"
CITY_DIR = ROOT_DIR / "cities" / CITY

# Akamai 403s limit >= 64; 50 leaves margin. `count` is in occurrences, not
# distinct events. Bound the loop so a runaway source cannot hammer the site.
PAGE_LIMIT = 50
CRAWL_DELAY = 2.0
REQUEST_TIMEOUT = 90
MAX_PAGES = 60

# Silent-degradation guard: each run appends its occurrence count to a history
# file under the committed per-city report slice (`report/<city>/` is published
# by the workflow's existing `git add report/`), so the next run can compare
# against the trailing window and warn when a fetch collapses. The existing
# nightly failure signal stays the only alarm -- this is a log line, not a system.
RUN_HISTORY_PATH = ROOT_DIR / "report" / CITY / "visit_bloomington.runs.json"
RUN_HISTORY_MAX = 30
RUN_HISTORY_WINDOW = 7
DEGRADATION_FRACTION = 0.5

# A recurring-series document carries a human-readable `recurrence` and the
# source pre-expands it into one document per occurrence, keyed on `date`.
# Documents without a recurrence are the event itself: a start/end span on one
# local day is a single-day event, a wider span is a genuinely multi-day event
# (the source emits one document per day of the span; these collapse to one).

# The source sometimes gives startTime without endTime; a one-hour duration
# keeps the event usable without inventing more than the data supports.
DEFAULT_DURATION = timedelta(hours=1)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
}


def _now() -> datetime:
    """Current time in the source's timezone (a seam, patched in tests)."""
    return datetime.now(TIMEZONE)


def _trailing_median(counts: list[int]) -> float | None:
    """Median of the last RUN_HISTORY_WINDOW counts, or None when there are none."""
    window = counts[-RUN_HISTORY_WINDOW:]
    if not window:
        return None
    ordered = sorted(window)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[mid])
    return (ordered[mid - 1] + ordered[mid]) / 2


def _local_date(value: str | None):
    """Parse an API UTC timestamp to the source's local calendar date."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).astimezone(TIMEZONE).date()
    except ValueError:
        return None


def _parse_clock(value: str | None) -> dtime | None:
    """Parse an API `HH:MM:SS` clock time, or None when absent/unparseable."""
    if not value:
        return None
    try:
        return dtime.fromisoformat(value)
    except ValueError:
        return None


def _timed_span(
    start_date: date,
    start_time: dtime,
    end_date: date,
    end_time: dtime | None,
    default_duration: timedelta | None = None,
) -> tuple[datetime, datetime]:
    """A tz-aware datetime span from local dates and clock times.

    The single definition of the combine-and-rollover rule: the end rolls forward
    one day when it does not advance past the start (an overnight event, or one
    ending exactly at midnight). `default_duration` supplies the end when the
    source has no end time at all (single-day events); without it the start time
    stands in on `end_date`, which is what the final day of a multi-day span
    means when its clock end is absent.
    """
    dtstart = datetime.combine(start_date, start_time).replace(tzinfo=TIMEZONE)
    if end_time is None and default_duration is not None:
        return dtstart, dtstart + default_duration
    dtend = datetime.combine(end_date, end_time or start_time).replace(tzinfo=TIMEZONE)
    if dtend <= dtstart:
        dtend += timedelta(days=1)
    return dtstart, dtend


def _span(
    start_date: date,
    end_date: date,
    start_time: dtime | None,
    end_time: dtime | None,
    default_duration: timedelta | None = None,
) -> tuple[date | datetime, date | datetime]:
    """A start/end span: all-day dates when there is no clock time.

    With no `start_time` the span is all-day and `end_date` is exclusive (the
    day after the last), whether the event is single- or multi-day. With a
    `start_time`, the clock-time rule in `_timed_span` applies.
    """
    if start_time is None:
        return start_date, end_date + timedelta(days=1)
    return _timed_span(start_date, start_time, end_date, end_time, default_duration)


def _plain_text(markup: str) -> str:
    """Strip the API's HTML to readable plain text, with no length cap."""
    if not markup:
        return ""
    text = html_mod.unescape(markup)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p\s*>", "\n", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_mod.unescape(text)
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()


def _build_location(doc: dict[str, Any]) -> str:
    """Venue + postal address as a single location string."""
    street = ", ".join(
        part for part in (doc.get("location"), doc.get("address1"), doc.get("address2")) if part
    )
    state_zip = " ".join(part for part in (doc.get("state"), doc.get("zip")) if part)
    city = ", ".join(part for part in (doc.get("city"), state_zip) if part)
    return ", ".join(part for part in (street, city) if part)


def _geo(doc: dict[str, Any]) -> tuple[float, float] | None:
    """(lat, lng) from the GeoJSON `loc.coordinates` ([lng, lat]), or None."""
    loc = doc.get("loc")
    if not isinstance(loc, dict):
        return None
    coords = loc.get("coordinates")
    if not isinstance(coords, (list, tuple)) or len(coords) != 2:
        return None
    lng, lat = coords
    if lat is None or lng is None:
        return None
    return (float(lat), float(lng))


def _uid(recid: str, occurrence_date) -> str:
    """Stable per-occurrence UID: hash of the source recid plus the occurrence date."""
    digest = hashlib.md5(f"{recid}-{occurrence_date.isoformat()}".encode()).hexdigest()
    return f"{digest}@{DOMAIN}"


def _slugify(text: str) -> str:
    text = re.sub(r"[^a-z0-9\s-]", "", text.lower())
    return re.sub(r"[\s_-]+", "-", text).strip("-") or "event"


def _event_url(recid: str, title: str) -> str:
    """The CVB event page. Any slug resolves; the canonical one is title-derived."""
    return f"{BASE_URL}/event/{_slugify(title)}/{recid}/"


def _recid(doc: dict[str, Any]) -> str:
    """The source's stable event id, tolerant of both `recid` and `recId`."""
    return str(doc.get("recid") or doc.get("recId") or "").strip()


def _title(doc: dict[str, Any]) -> str:
    return (doc.get("title") or "").strip()


def _raise_for_status(response: requests.Response, url: str) -> None:
    """The one non-200 error path: name the endpoint and status, then raise."""
    if response.status_code != 200:
        raise RuntimeError(f"Visit Bloomington API returned HTTP {response.status_code} for {url}")


class VisitBloomingtonScraper(BaseScraper):
    """Visit Bloomington (Monroe County CVB) via the Simpleview events API."""

    name = "Visit Bloomington"
    domain = DOMAIN
    timezone = DEFAULT_TIMEZONE
    source_url = SOURCE_URL

    def __init__(self):
        super().__init__()
        # Per-instance run state; reset per run in fetch_events() to bound token
        # re-fetching to one per run.
        self._token_refreshed = False

    def _fetch_token(self) -> str:
        response = requests.get(TOKEN_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        _raise_for_status(response, TOKEN_URL)
        token = response.text.strip()
        if not token:
            raise RuntimeError("Visit Bloomington token endpoint returned an empty token")
        return token

    @staticmethod
    def _events_params(token: str, options: dict[str, Any]) -> dict[str, str]:
        return {"json": json.dumps({"filter": {}, "options": options}), "token": token}

    def _fetch_page(self, token: str, options: dict[str, Any]) -> tuple[dict, str]:
        """Fetch one events page, refreshing the token and retrying once on a 403.

        Returns the decoded `docs` payload and the token later pages should use.
        A single token re-fetch per run is the documented anti-bot answer; a
        second 403 after that means the retry failed and must surface.
        """
        response = requests.get(
            EVENTS_URL,
            headers=HEADERS,
            params=self._events_params(token, options),
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code == 403 and not self._token_refreshed:
            logger.warning(
                "Visit Bloomington: events request returned HTTP 403; "
                "re-fetching token and retrying once"
            )
            self._token_refreshed = True
            time.sleep(CRAWL_DELAY)
            token = self._fetch_token()
            time.sleep(CRAWL_DELAY)
            response = requests.get(
                EVENTS_URL,
                headers=HEADERS,
                params=self._events_params(token, options),
                timeout=REQUEST_TIMEOUT,
            )
        _raise_for_status(response, EVENTS_URL)
        docs: dict[str, Any] = response.json().get("docs", {}) or {}
        self.mark_source_reached()
        return docs, token

    def _fetch_docs(self, token: str) -> list[dict[str, Any]]:
        """Page the events endpoint until the reported `count` is exhausted.

        A pull that ends before the source reports no occurrences left is a
        failure, not a short-but-successful run. The degradation guard compares
        this run's fetched count to a trailing median, so a silently truncated
        inventory (an empty page mid-stream, or the MAX_PAGES ceiling) could
        not be told apart from healthy growth; both must surface here instead.
        """
        docs: list[dict[str, Any]] = []
        skip = 0
        count = 0
        for _ in range(MAX_PAGES):
            options = {
                "limit": PAGE_LIMIT,
                "skip": skip,
                "count": True,
                "castDocs": False,
                "sort": {"date": 1, "rank": 1, "title_sort": 1},
            }
            payload, token = self._fetch_page(token, options)
            page_docs: list[dict[str, Any]] = payload.get("docs") or []
            docs.extend(page_docs)
            count = payload.get("count") or 0
            if page_docs and not count:
                raise RuntimeError(
                    f"Visit Bloomington API returned {len(page_docs)} docs at "
                    f"skip={skip} without a reported count; cannot confirm the "
                    f"inventory is exhausted"
                )
            if not page_docs:
                if count or docs:
                    raise RuntimeError(
                        f"Visit Bloomington API returned an empty page at skip={skip} "
                        f"with {count} occurrences still reported"
                    )
                return docs
            if len(docs) >= count:
                return docs
            skip += PAGE_LIMIT
            time.sleep(CRAWL_DELAY)
        raise RuntimeError(
            f"Visit Bloomington API pagination did not exhaust the reported "
            f"{count} occurrences within MAX_PAGES={MAX_PAGES} "
            f"({MAX_PAGES * PAGE_LIMIT} max); inventory may be truncated"
        )

    def _load_runs(self) -> list[dict[str, Any]]:
        """Prior runs' counts, or [] on a missing/corrupt history file."""
        try:
            data = json.loads(RUN_HISTORY_PATH.read_text())
        except OSError, ValueError:
            return []
        runs = data.get("runs") if isinstance(data, dict) else None
        if not isinstance(runs, list):
            return []
        return [r for r in runs if isinstance(r, dict)]

    def _record_run(self, fetched: int, emitted: int, runs: list[dict[str, Any]]) -> None:
        runs.append({"date": _now().date().isoformat(), "fetched": fetched, "emitted": emitted})
        try:
            RUN_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
            RUN_HISTORY_PATH.write_text(
                json.dumps({"runs": runs[-RUN_HISTORY_MAX:]}, indent=2) + "\n"
            )
        except OSError as exc:
            logger.warning(f"Visit Bloomington: could not write run history: {exc}")

    def _warn_if_degraded(self, fetched: int, runs: list[dict[str, Any]]) -> None:
        counts = [r["fetched"] for r in runs if isinstance(r.get("fetched"), int)]
        median = _trailing_median(counts)
        if median and fetched < median * DEGRADATION_FRACTION:
            logger.warning(
                f"Visit Bloomington: fetched {fetched} occurrences, below 50% of the "
                f"trailing {min(len(counts), RUN_HISTORY_WINDOW)}-run median ({median:g}) "
                "-- possible coverage degradation"
            )

    def _parse_doc(self, doc: dict[str, Any], today, horizon) -> dict[str, Any] | None:
        if not _title(doc) or not _recid(doc):
            return None

        if (doc.get("recurrence") or "").strip():
            occurrence_date = _local_date(doc.get("date"))
            if (
                occurrence_date is None
                or occurrence_date < today
                or not within(occurrence_date, horizon)
            ):
                return None
            return self._single_day_event(doc, occurrence_date)

        start_date = _local_date(doc.get("startDate"))
        if start_date is None:
            return None
        end_date = _local_date(doc.get("endDate")) or start_date
        if end_date < today or not within(start_date, horizon):
            return None
        if start_date == end_date:
            return self._single_day_event(doc, start_date)
        return self._multi_day_event(doc, start_date, end_date)

    def _single_day_event(self, doc: dict[str, Any], occurrence_date) -> dict[str, Any]:
        dtstart, dtend = _span(
            occurrence_date,
            occurrence_date,
            _parse_clock(doc.get("startTime")),
            _parse_clock(doc.get("endTime")),
            default_duration=DEFAULT_DURATION,
        )
        return self._event(doc, dtstart, dtend, _uid(_recid(doc), occurrence_date))

    def _multi_day_event(self, doc: dict[str, Any], start_date, end_date) -> dict[str, Any]:
        dtstart, dtend = _span(
            start_date,
            end_date,
            _parse_clock(doc.get("startTime")),
            _parse_clock(doc.get("endTime")),
        )

        # UID keys on the span's first day; every per-day document of the span
        # shares it, so they collapse to one event across the dedupe in fetch_events.
        return self._event(doc, dtstart, dtend, _uid(_recid(doc), start_date))

    def _event(self, doc: dict[str, Any], dtstart: Any, dtend: Any, uid: str) -> dict[str, Any]:
        recid = _recid(doc)
        title = _title(doc)
        return {
            "title": title,
            "dtstart": dtstart,
            "dtend": dtend,
            "location": _build_location(doc),
            "description": _plain_text(doc.get("description") or ""),
            "url": _event_url(recid, title),
            "geo": _geo(doc),
            "uid": uid,
        }

    def fetch_events(self) -> list[dict[str, Any]]:
        self._token_refreshed = False
        token = self._fetch_token()
        time.sleep(CRAWL_DELAY)
        docs = self._fetch_docs(token)

        now = _now()
        today = now.date()
        horizon = self.horizon_cutoff(now)
        allowed_cities, excluded_cities, allowed_zips = load_allowed_cities(str(CITY_DIR))

        events = []
        seen_uids: set[str] = set()
        out_of_area = 0
        for doc in docs:
            parsed = self._parse_doc(doc, today, horizon)
            if not parsed or parsed["uid"] in seen_uids:
                continue
            if not location_matches_allowed_cities(
                parsed["location"], allowed_cities, excluded_cities, allowed_zips
            ):
                out_of_area += 1
                continue
            seen_uids.add(parsed["uid"])
            events.append(parsed)

        self.logger.info(
            f"Visit Bloomington: {len(docs)} occurrence docs fetched, {len(events)} events emitted"
            + (f", {out_of_area} dropped outside the allowed area" if out_of_area else "")
        )
        runs = self._load_runs()
        self._warn_if_degraded(len(docs), runs)
        self._record_run(len(docs), len(events), runs)
        return events


if __name__ == "__main__":
    VisitBloomingtonScraper.main()
