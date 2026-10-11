#!/usr/bin/env python3
"""Tests for the Habitat for Humanity Monroe County scraper.

The site was redesigned: events now live on /events/ as Kadence cards whose
date is a "Month D, YYYY" (or month-only "Month YYYY") string, not the old
who-we-are #events section. `requests.get` is mocked so these tests drive the
real card parsing without touching the network.
"""

import sys
from pathlib import Path
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

# Add project root and scrapers/ to path so scraper imports resolve
_proj_root = Path(__file__).parent.parent
sys.path.insert(0, str(_proj_root))
sys.path.insert(0, str(_proj_root / "scrapers"))

from scrapers.habitat import HabitatScraper  # noqa: E402

TZ = ZoneInfo("America/Indiana/Indianapolis")


def _card(date_text: str, title: str, desc: str = "A description.") -> str:
    # Mirrors the live card: the title lives in a dynamic-html <div>, and the
    # blurb is its next-sibling <div>. The real markup has no <p> in the card.
    return f"""
    <div class="wp-block-kadence-column kadence-column-abc">
      <div class="kt-inside-inner-col">
        <div class="kt-adv-heading force-inline">{date_text}</div>
        <div class="wp-block-kadence-dynamichtml"><h3>{title}</h3></div>
        <div class="wp-block-kadence-dynamichtml">{desc}</div>
      </div>
    </div>
    """


def _parse_card(date_text: str, title: str, desc: str = "A description.") -> dict | None:
    soup = BeautifulSoup(_card(date_text, title, desc), "html.parser")
    col = soup.select_one("div.kt-inside-inner-col")
    assert col is not None
    h3 = col.find("h3")
    assert h3 is not None
    return HabitatScraper()._parse_card(col, h3, TZ)


class _Resp:
    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self) -> None:
        pass


def test_full_date_is_parsed():
    event = _parse_card("October 11, 2026", "Hoosier Strong Community Event")
    assert event is not None
    assert (event["dtstart"].year, event["dtstart"].month, event["dtstart"].day) == (2026, 10, 11)
    assert event["title"] == "Hoosier Strong Community Event"
    assert event["url"] == HabitatScraper.events_url
    assert event["description"] == "A description."


def test_description_is_read_from_the_sibling_div():
    # The live card has no <p>; the blurb is the title div's next sibling.
    event = _parse_card("October 11, 2026", "Hoosier Strong", "Enjoy the watch party.")
    assert event is not None
    assert event["description"] == "Enjoy the watch party."


def test_month_only_date_is_skipped():
    # "December 2026" has no real day: publishing one would invent a date, and
    # the past-event filter would then drop the event after that day passes.
    assert _parse_card("December 2026", "Homeownership Information Meeting") is None


def test_card_without_a_date_is_skipped():
    # "Stay in the know." and nav/footer copy have no date.
    assert _parse_card("Sign up for our newsletter", "Stay in the know.") is None


def test_impossible_day_is_skipped_not_crashed():
    # A malformed card date must not take down the whole scrape.
    assert _parse_card("February 31, 2027", "Bad card") is None


def test_impossible_year_is_skipped_not_crashed():
    assert _parse_card("October 11, 0000", "Bad card") is None


def test_uid_is_stable_across_runs():
    first = _parse_card("October 11, 2026", "Hoosier Strong Community Event")
    second = _parse_card("October 11, 2026", "Hoosier Strong Community Event")
    assert first is not None and second is not None
    assert first["uid"] == second["uid"]


def test_fetch_events_parses_the_events_archive(monkeypatch):
    html = (
        "<html><body>"
        + _card("October 11, 2026", "Hoosier Strong Community Event")
        + _card("November 7, 2026", "Stand Up for Habitat")
        + "</body></html>"
    )
    monkeypatch.setattr("scrapers.habitat.requests.get", lambda *a, **k: _Resp(html))

    events = HabitatScraper().fetch_events()

    assert [e["title"] for e in events] == [
        "Hoosier Strong Community Event",
        "Stand Up for Habitat",
    ]
