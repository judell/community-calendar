#!/usr/bin/env python3
"""Tests for the FAR Center scraper's event UID and date parsing."""

import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from bs4 import BeautifulSoup

# Add project root and scrapers/ to path so scraper imports resolve
_proj_root = Path(__file__).parent.parent
sys.path.insert(0, str(_proj_root))
sys.path.insert(0, str(_proj_root / "scrapers"))

from scrapers.far_center import FARCenterScraper  # noqa: E402

TZ = ZoneInfo("America/Indiana/Indianapolis")
NOW = datetime(2026, 10, 10, tzinfo=TZ)


def _card(
    title: str,
    href: str,
    date_line: str = "Sunday, October 11 | 2:00pm - 5:00pm",
    extra: str = "",
) -> str:
    extra_p = f'<p class="text-sm mb-1">{extra}</p>' if extra else ""
    return f"""
    <div class="mb-8">
      <h3><a href="{href}">{title}</a></h3>
      <p class="text-sm mb-1">A description.</p>
      <p class="text-sm mb-1">{date_line}</p>
      {extra_p}
    </div>
    """


def _parse_all(html: str) -> list[dict]:
    card = BeautifulSoup(html, "html.parser").select_one("div.mb-8")
    assert card is not None
    events = FARCenterScraper()._parse_card(card, TZ, NOW)
    assert events
    return events


def _parse(html: str) -> dict:
    return _parse_all(html)[0]


class _Resp:
    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self):
        pass


def _fetch(html: str) -> list[dict]:
    with patch("scrapers.far_center.requests.get", return_value=_Resp(html)):
        return FARCenterScraper().fetch_events()


def test_uid_is_stable_across_runs():
    href = "https://www.thefar.org/events/event/122918/"
    first = _parse(_card("Photo Forward", href))
    second = _parse(_card("Photo Forward", href))
    assert first["uid"] == second["uid"]


def test_distinct_events_do_not_collide():
    # Same day, titles sharing the first 40 characters: the old title slug
    # collapsed these to one UID.
    title = "Bloomington Photography Exhibition " + "X" * 20
    a = _parse(_card(title, "https://www.thefar.org/events/event/111111/"))
    b = _parse(_card(title, "https://www.thefar.org/events/event/222222/"))
    assert a["uid"] != b["uid"]


def test_uid_falls_back_when_url_has_no_id():
    event = _parse(_card("Photo Review", "https://www.thefar.org/events/list"))
    assert event["uid"].endswith("@thefar.org")


def test_next_year_date_rolls_forward():
    # Seen in October, a January date belongs to the next year.
    dtstart, _ = FARCenterScraper()._parse_datetime("January 20", TZ, NOW)
    assert dtstart is not None
    assert (dtstart.year, dtstart.month, dtstart.day) == (2027, 1, 20)


def test_same_year_date_is_unchanged():
    dtstart, _ = FARCenterScraper()._parse_datetime("November 5", TZ, NOW)
    assert dtstart is not None
    assert dtstart.year == 2026


def test_multi_day_range_crosses_new_year():
    # The end date belongs to the next year, not the start date's year.
    dtstart, dtend = FARCenterScraper()._parse_datetime(
        "December 30 8:00pm - January 2 10:00pm", TZ, NOW
    )
    assert dtstart is not None and dtend is not None
    assert dtstart == datetime(2026, 12, 30, 20, 0, tzinfo=TZ)
    assert dtend == datetime(2027, 1, 2, 22, 0, tzinfo=TZ)


def test_single_date_card_emits_one_event():
    assert len(_parse_all(_card("Photo Forward", "https://www.thefar.org/events/event/1/"))) == 1


def test_multi_date_card_emits_every_occurrence():
    # The monthly Photo Review lists its next dates under "Upcoming:".
    href = "https://www.thefar.org/events/event/17709/2026/10/21"
    events = _parse_all(
        _card(
            "FAR Photo Review",
            href,
            date_line="Wednesday, October 21 | 7:00pm - 9:00pm",
            extra="Upcoming: November 18, December 16, January 20, February 17, March 17",
        )
    )
    dates = [(e["dtstart"].year, e["dtstart"].month, e["dtstart"].day) for e in events]
    assert dates == [
        (2026, 10, 21),
        (2026, 11, 18),
        (2026, 12, 16),
        (2027, 1, 20),
        (2027, 2, 17),
        (2027, 3, 17),
    ]
    # Each occurrence keeps the primary date's time of day.
    for event in events:
        assert event["dtstart"].hour == 19
        assert event["dtend"] == event["dtstart"].replace(hour=21)


def test_multi_date_occurrences_have_distinct_stable_uids():
    href = "https://www.thefar.org/events/event/17709/2026/10/21"
    html = _card(
        "FAR Photo Review",
        href,
        date_line="Wednesday, October 21 | 7:00pm - 9:00pm",
        extra="Upcoming: November 18, December 16",
    )
    first = [e["uid"] for e in _parse_all(html)]
    second = [e["uid"] for e in _parse_all(html)]
    assert first == second
    assert len(set(first)) == len(first) == 3


def test_unparseable_upcoming_date_warns_and_keeps_primary(caplog):
    # An abbreviated month the parser can't read must not vanish silently.
    href = "https://www.thefar.org/events/event/17709/2026/10/21"
    with caplog.at_level("WARNING"):
        events = _parse_all(
            _card(
                "FAR Photo Review",
                href,
                date_line="Wednesday, October 21 | 7:00pm - 9:00pm",
                extra="Upcoming: Nov 18",
            )
        )
    assert len(events) == 1
    assert events[0]["dtstart"].day == 21
    assert any("Nov 18" in record.getMessage() for record in caplog.records)


def test_upcoming_token_that_does_not_look_like_a_date_warns(caplog):
    # "11/18" matches no month-name shape at all, so the old regex-based
    # extractor dropped it without a word. Every unparsed token must warn.
    href = "https://www.thefar.org/events/event/17709/2026/10/21"
    with caplog.at_level("WARNING"):
        events = _parse_all(
            _card(
                "FAR Photo Review",
                href,
                date_line="Wednesday, October 21 | 7:00pm - 9:00pm",
                extra="Upcoming: 11/18, December 16",
            )
        )
    assert [e["dtstart"].day for e in events] == [21, 16]
    assert any("11/18" in record.getMessage() for record in caplog.records)


def test_missing_container_raises():
    with pytest.raises(RuntimeError, match="entry-main"):
        _fetch('<html><body><div class="other">no events here</div></body></html>')


def test_container_with_no_cards_is_quiet():
    assert _fetch('<div class="entry-main"></div>') == []


def test_cards_without_parseable_dates_raise():
    html = (
        '<div class="entry-main">'
        + _card("Mystery", "https://www.thefar.org/events/event/1/", date_line="TBA")
        + "</div>"
    )
    with pytest.raises(RuntimeError, match="parseable date"):
        _fetch(html)
