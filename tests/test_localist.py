#!/usr/bin/env python3
"""Tests for the Localist scraper: URL normalization and pagination."""

import sys
from pathlib import Path

_proj_root = Path(__file__).parent.parent
sys.path.insert(0, str(_proj_root))
sys.path.insert(0, str(_proj_root / "scrapers"))

from scrapers.localist import MAX_PAGES, LocalistScraper  # noqa: E402


def _page(events, *, current, total, next_page):
    return {
        "events": events,
        "page": {
            "current": current,
            "size": 100,
            "total": total,
            "total_items": len(events),
            "next_page": next_page,
        },
    }


def _event(title, url=None, localist_url=None):
    evt = {
        "title": title,
        "event_instances": [
            {
                "event_instance": {
                    "start": "2026-11-01T10:00:00-05:00",
                    "end": "2026-11-01T11:00:00-05:00",
                }
            }
        ],
    }
    if url is not None:
        evt["url"] = url
    if localist_url is not None:
        evt["localist_url"] = localist_url
    return {"event": evt}


def _scraper(monkeypatch, pages):
    scraper = LocalistScraper(base_url="https://events.in.gov", name="Test")
    monkeypatch.setattr(scraper, "_fetch_api", lambda page=1: pages[page - 1])
    return scraper


def test_follows_next_page_cursor(monkeypatch):
    # The API's `total` counts pages, not items; a size-based offset stopped
    # after page 1 and silently dropped later pages.
    pages = [
        _page([_event("Page one")], current=1, total=2, next_page=2),
        _page([_event("Page two")], current=2, total=2, next_page=None),
    ]
    titles = [e["title"] for e in _scraper(monkeypatch, pages).fetch_events()]
    assert titles == ["Page one", "Page two"]


def test_pagination_stops_at_page_cap(monkeypatch):
    calls: list[int] = []

    def always_more(page=1):
        calls.append(page)
        return _page([_event(f"E{page}")], current=page, total=999, next_page=page + 1)

    scraper = LocalistScraper(base_url="https://events.in.gov", name="Test")
    monkeypatch.setattr(scraper, "_fetch_api", always_more)

    events = scraper.fetch_events()
    assert len(calls) == MAX_PAGES
    assert len(events) == MAX_PAGES


def test_scheme_less_url_falls_back_to_localist_url(monkeypatch):
    page = _page(
        [
            _event(
                "T", url="on.IN.gov/mccormickscreek", localist_url="https://events.in.gov/event/t"
            )
        ],
        current=1,
        total=1,
        next_page=None,
    )
    [event] = _scraper(monkeypatch, [page]).fetch_events()
    assert event["url"] == "https://events.in.gov/event/t"


def test_absolute_url_is_preserved(monkeypatch):
    page = _page(
        [
            _event(
                "T",
                url="https://on.in.gov/BrownCountySP",
                localist_url="https://events.in.gov/event/t",
            )
        ],
        current=1,
        total=1,
        next_page=None,
    )
    [event] = _scraper(monkeypatch, [page]).fetch_events()
    assert event["url"] == "https://on.in.gov/BrownCountySP"


def test_scheme_less_url_without_localist_url_gets_https(monkeypatch):
    page = _page([_event("T", url="on.in.gov/foo")], current=1, total=1, next_page=None)
    [event] = _scraper(monkeypatch, [page]).fetch_events()
    assert event["url"] == "https://on.in.gov/foo"


def test_days_default_follows_scrape_months(monkeypatch):
    monkeypatch.setenv("SCRAPE_MONTHS", "3")
    scraper = LocalistScraper(base_url="https://events.in.gov", name="Test")
    assert scraper.days == 3 * 31
