#!/usr/bin/env python3
"""WFIU Community Calendar (Indiana Public Media) via server-rendered HTML.

The listing at https://www.ipm.org/community-calendar is Brightspot HTML with
no JSON/GraphQL/REST API, no RSS/Atom, no iCal/ICS, and no JSON-LD (verified in
the surface research). The only way in is to scrape the server-rendered pages
over plain HTTP -- no browser, no Node, no Crawlee, no new runtime dependency.

The listing is occurrence-expanded: it renders one `ps-promo.PromoEvent` card
per occurrence of a series, so each card becomes exactly one event. The listing
supports a server-side date filter and fixed 10-card pages:

    GET https://www.ipm.org/community-calendar?f1=<startMs>-<endMs>&p=1..N

`f1` is the machine value behind the From/To date pickers (`?from=`/`?to=` are
ignored). This scraper fetches only the pages inside the calendar's Horizon,
reads the rendered `1 of N` to bound paging, and hard-caps the pages it will
walk (failing loud rather than truncating a crawl).

Each unique detail URL is fetched once for the stable `brightspot.contentId`
that keys the UID. WFIU is an aggregator: it loses cross-source dedupe to
direct venue/CVB sources and merges with other aggregators under the existing
binary-tier sort in `scripts/combine_ics.py`/`source_priority.json`.

Usage:
    python scrapers/wfiu_community_calendar.py --output cities/bloomington/wfiu_community_calendar.ics
"""

import sys
from pathlib import Path

sys.path.insert(0, __file__.rsplit("/", 1)[0])
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import hashlib
import html
import json
import logging
import os
import re
import time
from datetime import date, datetime, timedelta
from datetime import time as dtime
from typing import Any
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from lib.base import BaseScraper
from lib.city_filter import has_address_indicator
from lib.horizon import within

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent

BASE_URL = "https://www.ipm.org"
LISTING_URL = f"{BASE_URL}/community-calendar"
# The listing page itself is the source page attributed to every event.
SOURCE_URL = f"{LISTING_URL}/"

DOMAIN = "ipm.org"
DEFAULT_TIMEZONE = "America/Indiana/Indianapolis"
TIMEZONE = ZoneInfo(DEFAULT_TIMEZONE)

CITY = "bloomington"
CITY_DIR = ROOT_DIR / "cities" / CITY

# The listing reports `1 of N`; walk at most this many pages and raise if the
# source claims more, so a runaway crawl surfaces instead of quietly stopping.
PAGE_CAP = 80
# The registration flow (`scripts/add_scraper.py`) smoke-tests the exact
# registered command under a 120s timeout, which a full Horizon crawl can
# exceed. When this env var is set the walk stops cleanly after that many pages
# and the run is not recorded; the registered command never sets it, so
# production crawls still fail loud at PAGE_CAP. This is a test harness bound,
# never a coverage policy.
TEST_PAGE_CAP_ENV = "SCRAPER_TEST_PAGE_CAP"
# One detail fetch per unique event URL, for the stable content id. Raise on
# cap-hit rather than truncate the inventory.
DETAIL_CAP = 500
# A card whose month/day names no real calendar date (a format change, a typo),
# or whose date has already passed, is a data-drift signal. A few are tolerated
# (a lone bad card should not lose the run); more than this and the run fails
# loud rather than silently dropping events. A real date merely ahead of the
# Horizon is not drift: the listing's inclusive end filter leaks the day past
# the Horizon for a series that starts in-window, and that drop is normal.
DATE_ERROR_THRESHOLD = 3
# A detail fetch that fails degrades to a card-fallback event. A few failures
# are tolerated; more than this and the run fails loud rather than emitting a
# page of address-less cards. Retry logic is deliberately unchanged: one
# attempt per URL, no new retry or backoff layer.
DETAIL_ERROR_THRESHOLD = 3
# robots.txt allows all and sets no Crawl-delay; this is voluntary citizenship.
CRAWL_DELAY = 2.0
REQUEST_TIMEOUT = 90

# Silent-degradation guard: each run appends its counts to a history file under
# the committed per-city report slice (`report/<city>/` is published by the
# workflow's existing `git add report/`), so the next run can warn when the
# fetched card count collapses against the trailing window.
RUN_HISTORY_PATH = ROOT_DIR / "report" / CITY / "wfiu_community_calendar.runs.json"
RUN_HISTORY_MAX = 30
RUN_HISTORY_WINDOW = 7
DEGRADATION_FRACTION = 0.5

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

_LEADING_TIME = re.compile(r"^(\d{1,2}:\d{2}\s*[AP]M)\s*-\s*(\d{1,2}:\d{2}\s*[AP]M)", re.I)
_SCHEDULE_ENTRY = re.compile(
    r"([A-Z][a-z]+):\s*(\d{1,2}:\d{2}\s*[AP]M)\s*-\s*(\d{1,2}:\d{2}\s*[AP]M)"
)
_START_ONLY = re.compile(r"^(\d{1,2}:\d{2}\s*[AP]M)\b", re.I)
_PAGE_COUNT = re.compile(r"(\d+)\s+of\s+(\d+)")
_MONTH_DAY = re.compile(r"([A-Z][a-z]{2})\s+(\d{1,2})")
_CLOCK = re.compile(r"(\d{1,2}):(\d{2})(AM|PM)")
_MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


def _now() -> datetime:
    """Current time in the source's timezone (a seam, patched in tests)."""
    return datetime.now(TIMEZONE)


def _test_page_cap() -> int | None:
    """The registration smoke test's page bound, or None outside it.

    Read at call time so a test can arm it through the environment. A missing
    or unparseable value means "not a smoke test", so a stray env var can never
    silently truncate a production crawl.
    """
    raw = os.environ.get(TEST_PAGE_CAP_ENV)
    if not raw:
        return None
    try:
        cap = int(raw)
    except ValueError:
        return None
    return cap if cap > 0 else None


def _fetch_html(url: str) -> str:
    """Fetch one page over plain HTTP (a seam, patched in tests)."""
    response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    if response.status_code != 200:
        raise RuntimeError(f"WFIU returned HTTP {response.status_code} for {url}")
    return response.text


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


def _text(element) -> str:
    """Collapsed visible text of a selected node, or "" when absent."""
    return " ".join(element.get_text(" ", strip=True).split()) if element else ""


def _plain_text(markup: str) -> str:
    """Strip card/detail HTML to readable plain text, with no length cap.

    Entities are decoded so the published text reads as written (a detail
    paragraph's `&amp;` must not survive as a literal entity into the ICS).
    """
    if not markup:
        return ""
    text = html.unescape(markup)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p\s*>", "\n", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()


def _parse_clock(value: str) -> dtime:
    """Parse an `HH:MM AM/PM` clock string as a local wall-clock time."""
    match = _CLOCK.fullmatch(value.strip().upper().replace(" ", ""))
    if not match:
        raise ValueError(f"unparseable clock: {value!r}")
    hour = int(match.group(1)) % 12
    if match.group(3) == "PM":
        hour += 12
    return dtime(hour, int(match.group(2)))


def _plus_hour(value: dtime) -> dtime:
    """One hour after a wall-clock time, wrapping past midnight."""
    return (datetime.combine(date.min, value) + timedelta(hours=1)).time()


def _resolve_end(start: dtime, end: dtime) -> dtime:
    """The wall-clock end, never equal to the start.

    A block that ends where it starts is a start-only marker, so it gets the
    one-hour default rather than emitting a zero-duration event. A genuinely
    earlier end (a past-midnight show) is left literal; `_parse_card` rolls the
    date forward, never coercing it to all-day.
    """
    return _plus_hour(start) if end == start else end


def _time_range(raw: str, weekday: str | None) -> tuple[dtime, dtime] | None:
    """The card's clock range, or None when the text carries no parseable time.

    One-off, daily, and monthly cards lead with `HH:MM AM - HH:MM PM`. Weekly
    cards instead list `Weekday: HH:MM AM - HH:MM PM` entries; the occurrence
    card's own weekday selects the matching entry. A weekday mismatch or a
    lone `HH:MM AM` without a matching entry means no usable clock for this
    occurrence: mismatch returns None so the caller emits a date-only
    all-day VEVENT with a warning, never another weekday's hours.
    A lone `HH:MM AM` is a start-only time and gets the one-hour default.
    """
    text = " ".join((raw or "").split())
    head = _LEADING_TIME.match(text)
    if head:
        start, end = _parse_clock(head.group(1)), _parse_clock(head.group(2))
        return start, _resolve_end(start, end)
    entries = _SCHEDULE_ENTRY.findall(text)
    if entries:
        for name, start_raw, end_raw in entries:
            if weekday and name.lower() == weekday.lower():
                start, end = _parse_clock(start_raw), _parse_clock(end_raw)
                return start, _resolve_end(start, end)
        return None
    start_only = _START_ONLY.match(text)
    if start_only:
        start = _parse_clock(start_only.group(1))
        return start, _plus_hour(start)
    return None


def _time_key(start: dtime | None, end: dtime | None) -> str:
    """The occurrence's time block as an identity component (`all-day` if none)."""
    if start is None or end is None:
        return "all-day"
    return f"{start:%H%M}-{end:%H%M}"


def _is_real_month_day(month: int, day: int) -> bool:
    """Does month/day name a real calendar date on some year?

    `date` is asked about a leap year so Feb 29 counts as real while Feb 30 and
    Apr 31 do not. This is the line between date drift and a well-formed date
    that merely fell outside the Horizon.
    """
    try:
        date(2000, month, day)
    except ValueError:
        return False
    return True


def _weekday_agrees(candidate: date, weekday: str | None) -> bool:
    """Does `candidate` fall on the card's stated weekday (when it states one)?"""
    return weekday is not None and candidate.strftime("%A").lower() == weekday.lower()


def _bind_year(
    display: str, weekday: str | None, today: date, horizon: date
) -> tuple[date | None, bool, bool]:
    """Bind the card's year-less month/day inside `[today, horizon]`.

    Returns `(occurrence, weekday_agreed, drift)`. The candidate year whose
    weekday agrees is preferred, which resolves the Dec->Jan rollover; when no
    in-window candidate agrees, the earliest is used with `agreed=False` so the
    caller can warn.

    `occurrence` is None when no year lands in-window, and `drift` then says
    which kind of miss it is. A month/day that names no real calendar date is
    drift. Otherwise the card is the occurrence just outside the window: the
    adjacent past one is stale drift (the listing is filtered from today, so a
    past card is anomalous) and the adjacent future one is the listing's leak
    (its inclusive end filter returns the next occurrence of a series that
    starts in-window). The card's weekday picks between those two, exactly as it
    picks between in-window years; only drift is logged and counted. For a bound
    date `drift` is always False.
    """
    match = _MONTH_DAY.match(display)
    if not match:
        return None, False, True
    month = _MONTHS.get(match.group(1).lower())
    if month is None:
        return None, False, True
    day = int(match.group(2))
    if not _is_real_month_day(month, day):
        return None, False, True

    # Four years either side bracket the window and a whole leap-year cycle, so
    # a Feb 29 card resolves to the leap year the weekday names.
    occurrences: list[date] = []
    for year in range(today.year - 4, horizon.year + 5):
        try:
            occurrences.append(date(year, month, day))
        except ValueError:
            continue
    in_window = [candidate for candidate in occurrences if today <= candidate <= horizon]
    if in_window:
        if weekday:
            for candidate in in_window:
                if _weekday_agrees(candidate, weekday):
                    return candidate, True, False
            return in_window[0], False, False
        return in_window[0], True, False

    previous = max((candidate for candidate in occurrences if candidate < today), default=None)
    upcoming = min((candidate for candidate in occurrences if candidate > today), default=None)
    previous_agrees = previous is not None and _weekday_agrees(previous, weekday)
    upcoming_agrees = upcoming is not None and _weekday_agrees(upcoming, weekday)
    if upcoming_agrees and not previous_agrees:
        return None, False, False
    if previous_agrees and not upcoming_agrees:
        return None, False, True
    # Weekday absent or wrong: whichever adjacent occurrence sits nearer the
    # window boundary decides.
    if upcoming is None or (previous is not None and (today - previous) < (upcoming - horizon)):
        return None, False, True
    return None, False, False


def _uid(identity: str, occurrence_date: date, time_key: str) -> str:
    """Stable per-occurrence UID: content id + occurrence date + time block.

    The time block is part of the key so a matinee and an evening showing of the
    same work on the same date never collapse into one VEVENT.
    """
    digest = hashlib.md5(
        f"{identity}-{occurrence_date.isoformat()}-{time_key}".encode()
    ).hexdigest()
    return f"{digest}@{DOMAIN}"


def _parse_detail(markup: str) -> dict[str, Any]:
    """Canonical fields from one detail page, empty strings when absent.

    Card fallback is the caller's job: this reports only what the detail
    actually carries, so the caller can tell "detail missing" from "detail
    present but fieldless".
    """
    soup = BeautifulSoup(markup, "html.parser")
    meta = soup.select_one("meta[name='brightspot.contentId']")
    image = soup.select_one(".EventPage-image img[src]")
    ticket = soup.select_one(".EventPage-ticketing a[href]")
    description = soup.select_one(".EventPage-description")
    content = meta.get("content") if meta else None
    return {
        "content_id": content.strip() if isinstance(content, str) and content.strip() else None,
        "title": _text(soup.select_one(".EventPage-name")),
        "venue": _text(soup.select_one(".EventPage-information-venueName"))
        or _text(soup.select_one(".VenueInformation-name")),
        "description": _plain_text(description.decode_contents()) if description else "",
        "presenting_org": _text(soup.select_one(".PresentingOrganizationInformation-name")),
        "street": _text(soup.select_one(".VenueInformation-address-streetAddress")),
        "city": _text(soup.select_one(".VenueInformation-address-city")),
        "state": _text(soup.select_one(".VenueInformation-address-state")),
        "zip": _text(soup.select_one(".VenueInformation-address-zip")),
        "ticket_url": (ticket.get("href") if ticket else None) or "",
        "image_url": (image.get("src") if image else None) or "",
    }


def _build_location(detail: dict[str, Any], card_venue: str) -> str:
    """Venue + street + city + state + ZIP as one location string.

    Mirrors Visit Bloomington's `_build_location`. The postal address is
    load-bearing: the shared combine-time city filter only geo-filters a
    location carrying an address indicator (state, ZIP, city+state, or a
    street), and fails open on a bare venue name.
    """
    venue = detail["venue"] or card_venue
    street = ", ".join(part for part in (venue, detail["street"]) if part)
    state_zip = " ".join(part for part in (detail["state"], detail["zip"]) if part)
    city = ", ".join(part for part in (detail["city"], state_zip) if part)
    return ", ".join(part for part in (street, city) if part)


def _assemble_description(detail: dict[str, Any], card_description: str) -> str:
    """Plain-text body with the presenting-org line prepended and tickets appended.

    The body is stripped first so the two synthetic lines are never eaten by
    the stripper; ticket and org are detail-only (the card carries neither).
    """
    body = detail["description"] or _plain_text(card_description)
    parts: list[str] = []
    if detail["presenting_org"]:
        parts.append(f"Presented by {detail['presenting_org']}")
    if body:
        parts.append(body)
    if detail["ticket_url"]:
        parts.append(f"Tickets: {detail['ticket_url']}")
    return "\n".join(parts)


def _parse_cards(soup: BeautifulSoup) -> list[dict[str, Any]]:
    """One dict per `ps-promo.PromoEvent` occurrence card on a listing page."""
    cards: list[dict[str, Any]] = []
    for node in soup.select("ps-promo.PromoEvent"):
        link = node.select_one("a.PromoEvent-link-link") or node.select_one("h3.PromoEvent-title a")
        href = link.get("href") if link else None
        cards.append(
            {
                # Resolve against BASE_URL so a relative href never becomes a
                # relative URL: line or a relative content-id fallback UID.
                "url": urljoin(BASE_URL, href) if isinstance(href, str) and href else None,
                "title": _text(node.select_one(".PromoEvent-title")),
                "venue": _text(node.select_one(".PromoEvent-venue")),
                "date_display": _text(node.select_one(".PromoEvent-date-date")),
                "weekday": _text(node.select_one(".PromoEvent-date-day")) or None,
                "time_raw": _text(node.select_one(".PromoEvent-time")),
                "description": _text(node.select_one(".PromoEvent-description")),
            }
        )
    return cards


def _parse_listing_page(html: str) -> tuple[list[dict[str, Any]], int, int]:
    """The page's cards plus its rendered `current of total` page counts."""
    soup = BeautifulSoup(html, "html.parser")
    counts = _PAGE_COUNT.search(_text(soup.select_one(".EventSearchResultsModule-pageCounts")))
    if not counts:
        raise RuntimeError("WFIU listing page did not report a page count")
    return _parse_cards(soup), int(counts.group(1)), int(counts.group(2))


class WFIUCommunityCalendarScraper(BaseScraper):
    """WFIU Community Calendar (Indiana Public Media) via server-rendered HTML."""

    name = "WFIU Community Calendar"
    domain = DOMAIN
    timezone = DEFAULT_TIMEZONE
    source_url = SOURCE_URL

    def _walk_listing(self, start_ms: int, end_ms: int) -> tuple[list[dict[str, Any]], int]:
        """Fetch every listing page inside the Horizon, capped and loud.

        Under the registration smoke test (`TEST_PAGE_CAP_ENV`) the walk stops
        cleanly after the test cap instead of raising, so the harness proves the
        pipeline end to end without a full crawl. Production carries no cap env
        and keeps the loud PAGE_CAP ceiling.
        """
        test_cap = _test_page_cap()
        cards: list[dict[str, Any]] = []
        total: int | None = None
        page = 1
        while True:
            if test_cap is not None and page > test_cap:
                self.logger.info(
                    f"WFIU Community Calendar: test page cap {test_cap} reached; "
                    f"stopping the registration smoke crawl"
                )
                return cards, page - 1
            if page > PAGE_CAP:
                raise RuntimeError(f"WFIU listing exceeded the hard page cap of {PAGE_CAP}")
            html = _fetch_html(f"{LISTING_URL}?f1={start_ms}-{end_ms}&p={page}")
            page_cards, current, reported_total = _parse_listing_page(html)
            if current != page:
                raise RuntimeError(
                    f"WFIU listing requested page {page} but the page reports "
                    f"{current} of {reported_total}; refusing to count a repeated page"
                )
            self.mark_source_reached()
            if total is None:
                total = reported_total
                if test_cap is None and total > PAGE_CAP:
                    raise RuntimeError(
                        f"WFIU listing reports {total} pages, above the hard page cap "
                        f"of {PAGE_CAP}; refusing to truncate the crawl"
                    )
            cards.extend(page_cards)
            if page >= total:
                return cards, page
            page += 1
            time.sleep(CRAWL_DELAY)

    @staticmethod
    def _unique_urls(cards: list[dict[str, Any]]) -> list[str]:
        """Detail URLs in first-seen order, one per unique event."""
        return list(dict.fromkeys(c["url"] for c in cards if c.get("url")))

    def _fetch_details(self, urls: list[str]) -> dict[str, str]:
        """One fetch per unique detail URL; failures are left absent.

        The cap raises rather than truncating the inventory. A per-URL failure
        is not retried (retry logic deliberately unchanged): the caller emits a
        card-fallback event. The loop raises as soon as failures cross the small
        threshold, so a source outage never drives hundreds of remaining
        requests before the run fails loud.
        """
        if len(urls) > DETAIL_CAP:
            raise RuntimeError(
                f"WFIU listing yields {len(urls)} unique detail URLs, above the "
                f"detail-fetch cap of {DETAIL_CAP}; refusing to truncate"
            )
        details: dict[str, str] = {}
        errors = 0
        for url in urls:
            # Delay before every fetch, including the first, so the transition
            # from the last listing page to the first detail request stays spaced.
            time.sleep(CRAWL_DELAY)
            try:
                details[url] = _fetch_html(url)
            except Exception as exc:  # any detail failure degrades to a card fallback
                errors += 1
                self.logger.warning(
                    f"WFIU Community Calendar: detail fetch failed for {url} "
                    f"({exc}); emitting card fallback"
                )
                if errors > DETAIL_ERROR_THRESHOLD:
                    raise RuntimeError(
                        f"WFIU Community Calendar: {errors} detail fetches failed, "
                        f"above the threshold of {DETAIL_ERROR_THRESHOLD}; failing loud"
                    ) from exc
        return details

    def _parse_card(
        self,
        card: dict[str, Any],
        occurrence: date,
        weekday_agreed: bool,
        detail: dict[str, Any] | None,
    ) -> tuple[dict[str, Any], bool]:
        """One event from one occurrence card already bound to `occurrence`.

        `occurrence` and `weekday_agreed` come from `_bind_year`; the caller
        owns the Horizon and drift policy. Returns the event plus whether the
        emitted location carries an address indicator the shared city filter
        can geo-check, so the run record can keep pass-through visible. The
        indicator set is the city filter's own `has_address_indicator`, not ZIP
        alone: a location the filter can geo-check is not postal-less. Canonical
        fields come from the detail with the card as fallback.
        """
        if not weekday_agreed:
            self.logger.warning(
                f"WFIU Community Calendar: the weekday {card['weekday']!r} does not "
                f"match {occurrence.isoformat()} for {card['title']!r}; binding anyway"
            )

        clock = _time_range(card["time_raw"], card["weekday"])
        if clock is None:
            self.logger.warning(
                f"WFIU Community Calendar: no parseable time in {card['time_raw']!r} "
                f"for {card['title']!r}; emitting all-day"
            )
            dtstart: Any = occurrence
            dtend: Any = occurrence + timedelta(days=1)
            time_key = _time_key(None, None)
        else:
            start, end = clock
            dtstart = datetime.combine(occurrence, start, tzinfo=TIMEZONE)
            dtend = datetime.combine(occurrence, end, tzinfo=TIMEZONE)
            if dtend <= dtstart:
                dtend += timedelta(days=1)
            time_key = _time_key(start, end)

        detail = detail or _parse_detail("")
        identity = detail["content_id"] or card["url"]
        location = _build_location(detail, card["venue"])
        event: dict[str, Any] = {
            "title": detail["title"] or card["title"],
            "dtstart": dtstart,
            "dtend": dtend,
            "url": card["url"],
            "location": location,
            "description": _assemble_description(detail, card["description"]),
            "uid": _uid(identity, occurrence, time_key),
        }
        if detail["image_url"]:
            event["image_url"] = detail["image_url"]
        return event, has_address_indicator(location)

    def _load_runs(self) -> list[dict[str, Any]]:
        """Prior runs' records, or [] on a missing/corrupt history file."""
        try:
            data = json.loads(RUN_HISTORY_PATH.read_text())
        except OSError, ValueError:
            return []
        runs = data.get("runs") if isinstance(data, dict) else None
        if not isinstance(runs, list):
            return []
        return [r for r in runs if isinstance(r, dict)]

    def _record_run(self, run: dict[str, Any], runs: list[dict[str, Any]]) -> None:
        runs.append(run)
        try:
            RUN_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
            RUN_HISTORY_PATH.write_text(
                json.dumps({"runs": runs[-RUN_HISTORY_MAX:]}, indent=2) + "\n"
            )
        except OSError as exc:
            self.logger.warning(f"WFIU Community Calendar: could not write run history: {exc}")

    def _warn_if_degraded(self, cards: int, runs: list[dict[str, Any]]) -> None:
        counts = [r["cards_fetched"] for r in runs if isinstance(r.get("cards_fetched"), int)]
        median = _trailing_median(counts)
        if median and cards < median * DEGRADATION_FRACTION:
            self.logger.warning(
                f"WFIU Community Calendar: fetched {cards} cards, below 50% of the "
                f"trailing {min(len(counts), RUN_HISTORY_WINDOW)}-run median ({median:g}) "
                "-- possible coverage degradation"
            )

    def fetch_events(self) -> list[dict[str, Any]]:
        now = _now()
        today = now.date()
        horizon = self.horizon_cutoff(now)
        start_ms = int(datetime.combine(today, dtime.min, tzinfo=TIMEZONE).timestamp() * 1000)
        end_ms = int(horizon.timestamp() * 1000)

        cards, pages = self._walk_listing(start_ms, end_ms)
        urls = self._unique_urls(cards)
        details = self._fetch_details(urls)
        # Parse each unique detail once, not once per occurrence card.
        parsed_details = {url: _parse_detail(html) for url, html in details.items()}

        events: list[dict[str, Any]] = []
        seen_uids: set[str] = set()
        date_errors = 0
        postal_less = 0
        for card in cards:
            occurrence, weekday_agreed, drift = _bind_year(
                card["date_display"], card["weekday"], today, horizon.date()
            )
            if occurrence is None:
                if drift:
                    self.logger.error(
                        f"WFIU Community Calendar: could not bind a date from "
                        f"{card['date_display']!r} for {card['title']!r}"
                    )
                    date_errors += 1
                    if date_errors > DATE_ERROR_THRESHOLD:
                        raise RuntimeError(
                            f"WFIU Community Calendar: {date_errors} date-drift cards, above "
                            f"the threshold of {DATE_ERROR_THRESHOLD}; failing loud"
                        )
                # A real date ahead of the Horizon (the listing's leak) drops
                # silently; the Horizon guard would discard it anyway.
                continue
            detail = parsed_details.get(str(card.get("url") or ""))
            event, has_postal = self._parse_card(card, occurrence, weekday_agreed, detail)
            if not within(event["dtstart"], horizon):
                continue
            if event["uid"] in seen_uids:
                continue
            seen_uids.add(event["uid"])
            if not has_postal:
                postal_less += 1
            events.append(event)

        self.logger.info(
            f"WFIU Community Calendar: {pages} pages, {len(cards)} cards, "
            f"{len(urls)} unique detail URLs, {len(details)} details, "
            f"{len(events)} events emitted, {postal_less} postal-less"
        )
        if _test_page_cap() is not None:
            # A smoke test is not a coverage run: recording it would drag down
            # the trailing median the degradation guard depends on.
            self.logger.info(
                "WFIU Community Calendar: registration smoke test; not recording run history"
            )
            return events
        runs = self._load_runs()
        self._warn_if_degraded(len(cards), runs)
        self._record_run(
            {
                "date": now.date().isoformat(),
                "pages": pages,
                "cards_fetched": len(cards),
                "unique_detail_urls": len(urls),
                "details_fetched": len(details),
                "postal_less": postal_less,
                "emitted": len(events),
            },
            runs,
        )
        return events


if __name__ == "__main__":
    WFIUCommunityCalendarScraper.main()
