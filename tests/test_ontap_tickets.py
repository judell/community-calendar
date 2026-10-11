#!/usr/bin/env python3
"""Tests for the On Tap Tickets (Evvnt discovery) scraper."""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

_proj_root = Path(__file__).parent.parent
sys.path.insert(0, str(_proj_root))
sys.path.insert(0, str(_proj_root / "scrapers"))

from lib.city_filter import load_allowed_cities, location_matches_allowed_cities  # noqa: E402

from scrapers.ontap_tickets import MAX_PAGES, OnTapTicketsScraper  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures/bloomington/ontap_tickets_page1.json"
NOW = datetime(2026, 10, 1, tzinfo=UTC)


def _items() -> list[dict]:
    return json.loads(FIXTURE.read_text())["rawEvents"]


def _parse(item: dict) -> dict:
    event = OnTapTicketsScraper()._parse_event(item, NOW)
    assert event is not None
    return event


def _parsed(title: str) -> dict:
    return _parse(next(i for i in _items() if i["title"] == title))


def _with_venue(venue: dict) -> dict:
    """The MET item with a different venue block."""
    return dict(_items()[0], venue=venue)


def test_parses_the_met_listing():
    event = _parsed("The Little Rascals - Benefit for MSD of Martinsville Education Foundation")

    assert event["dtstart"].isoformat() == "2026-11-06T19:00:00-05:00"
    assert event["dtend"].isoformat() == "2026-11-06T20:30:00-05:00"
    assert event["location"].endswith("Martinsville, 46151")
    assert event["geo"] == (39.428027, -86.4280804)
    # The source's own ticket page, not Evvnt's affiliate redirect
    assert event["url"].startswith("https://event.ontaptickets.com/")
    assert event["image_url"].startswith("https://cdn.prod.discovery.evvnt.com/")
    assert event["uid"].endswith("@ontaptickets.com")


def test_finished_events_are_skipped():
    item = next(i for i in _items() if i["title"] == "Long-finished Tour")
    assert OnTapTicketsScraper()._parse_event(item, NOW) is None


def test_unparseable_start_skips_only_that_event():
    # "2026-11-06T19:00" is still valid ISO; this is not.
    item = dict(_items()[0], title="Broken", start_time="11/06/2026 7:00 PM")

    assert OnTapTicketsScraper()._parse_event(item, NOW) is None


def test_zoneless_end_is_read_on_the_start_s_clock():
    # A zoneless end used to crash the finished-event compare (TypeError) and,
    # once compared, base.create_event read it as the runner's zone.
    item = dict(_items()[0], end_time="2026-11-06T20:30:00")

    event = _parse(item)

    assert event["dtstart"].isoformat() == "2026-11-06T19:00:00-05:00"
    assert event["dtend"].isoformat() == "2026-11-06T20:30:00-05:00"

    # The emitted ICS is the user-visible consequence: unshared, this end came
    # out as 15:30 on a UTC runner, an hour and a half before its own start.
    ics = OnTapTicketsScraper().create_calendar([event]).to_ical().decode()
    assert "DTEND;TZID=America/Indiana/Indianapolis:20261106T203000" in ics


def test_fully_zoneless_times_stay_wall_clock():
    # No offset anywhere: the house convention keeps the wall clock naive and
    # ics_to_json stamps the zone at the ICS boundary.
    item = dict(_items()[0], start_time="2026-11-06T19:00:00", end_time="2026-11-06T20:30:00")

    event = _parse(item)

    assert event["dtstart"].tzinfo is None
    assert event["dtend"].tzinfo is None


def test_location_drops_parts_the_venue_name_already_has():
    met = _parsed("The Little Rascals - Benefit for MSD of Martinsville Education Foundation")
    assert met["location"] == (
        "Martinsville Entertainment Theatre (The MET), 36 East Morgan Street, Martinsville, 46151"
    )

    # name == address_1, the most common shape in the live listing
    street_named = _with_venue(
        {
            "name": "1125 E Brookside Ave",
            "address_1": "1125 E Brookside Ave",
            "town": "Indianapolis",
            "post_code": "46202",
        }
    )
    assert _parse(street_named)["location"] == "1125 E Brookside Ave, Indianapolis, 46202"

    # name == address_1 == town; the longer city line wins
    town_named = _with_venue(
        {
            "name": "Indianapolis",
            "address_1": "Indianapolis",
            "town": "Indianapolis",
            "post_code": "46204",
        }
    )
    assert _parse(town_named)["location"] == "Indianapolis, 46204"

    # the address is a substring of the name
    contained = _with_venue(
        {
            "name": "Shelbyville Public Square",
            "address_1": "Public Square",
            "town": "Shelbyville",
            "post_code": "46176",
        }
    )
    assert _parse(contained)["location"] == ("Shelbyville Public Square, Shelbyville, 46176")


def test_duplicate_listings_keep_distinct_stable_uids():
    duplicates = [i for i in _items() if i["title"].startswith("Fall Workshop")]
    uids = [_parse(i)["uid"] for i in duplicates]

    assert len(set(uids)) == 2  # same title and start, two event ids
    assert uids == [_parse(i)["uid"] for i in duplicates]


def test_pagination_stops_at_the_first_empty_page(monkeypatch):
    calls: list[str] = []

    def fake_fetch(url: str, *args, **kwargs) -> str:
        calls.append(url)
        page = url.rsplit("page=", 1)[1]
        return json.dumps({"rawEvents": _items() if page == "1" else []})

    monkeypatch.setattr("scrapers.ontap_tickets.fetch_with_retry", fake_fetch)
    events = OnTapTicketsScraper().fetch_events()

    assert [c.rsplit("page=", 1)[1] for c in calls] == ["1", "2"]
    assert len(events) == len(_items()) - 1  # the finished event is dropped


def test_page_cap_exhaustion_is_reported(monkeypatch, caplog):
    # Every page full: the listing runs past the cap, so the run is partial and
    # must say so rather than look like a complete 10-page listing.
    page = [dict(_items()[0], title="Filler")]
    monkeypatch.setattr(
        "scrapers.ontap_tickets.fetch_with_retry",
        lambda url, *a, **k: json.dumps({"rawEvents": page}),
    )

    with caplog.at_level("WARNING"):
        events = OnTapTicketsScraper().fetch_events()

    assert len(events) == MAX_PAGES
    assert f"page cap ({MAX_PAGES}); more pages remain" in caplog.text


def test_only_the_in_area_location_survives_the_city_filter():
    allowed, excluded, zips = load_allowed_cities(_proj_root / "cities/bloomington")

    in_area = _parsed("The Little Rascals - Benefit for MSD of Martinsville Education Foundation")
    out_of_area = _parsed("Louisville Official Halloween Bar Crawl 2026")

    assert location_matches_allowed_cities(in_area["location"], allowed, excluded, zips)
    assert not location_matches_allowed_cities(out_of_area["location"], allowed, excluded, zips)
