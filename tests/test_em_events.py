#!/usr/bin/env python3
"""Tests for the Events Manager (EM) scraper library."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from unittest.mock import patch

from scrapers.lib.em_events import EmEventsScraper

TZ = ZoneInfo("America/Indiana/Indianapolis")


class TestParseDate:
    """_parse_date() parses EM date strings into (year, month, day) tuples."""

    def test_parse_date_full_month(self):
        """Parse 'June 18, 2026' — full month name."""
        scraper = EmEventsScraper()
        result = scraper._parse_date("June 18, 2026")
        assert result is not None
        assert result == (2026, 6, 18)

    def test_parse_date_abbreviated(self):
        """Parse 'Jan 5, 2026' — abbreviated month name."""
        scraper = EmEventsScraper()
        result = scraper._parse_date("Jan 5, 2026")
        assert result is not None
        assert result == (2026, 1, 5)


class TestParseTimeRange:
    """_parse_time_range() parses EM time strings into (dtstart, dtend) pairs."""

    def test_parse_standard_range(self):
        """Parse '10:00 am - 10:00 pm' on June 18, 2026."""
        scraper = EmEventsScraper()
        dtstart, dtend = scraper._parse_time_range(
            "10:00 am - 10:00 pm", 2026, 6, 18, TZ
        )
        assert dtstart == datetime(2026, 6, 18, 10, 0, tzinfo=TZ)
        assert dtend == datetime(2026, 6, 18, 22, 0, tzinfo=TZ)

    def test_parse_pm_to_pm_range(self):
        """Parse '7:00 pm - 10:00 pm' — both PM, no date wrap."""
        scraper = EmEventsScraper()
        dtstart, dtend = scraper._parse_time_range(
            "7:00 pm - 10:00 pm", 2026, 6, 18, TZ
        )
        assert dtstart == datetime(2026, 6, 18, 19, 0, tzinfo=TZ)
        assert dtend == datetime(2026, 6, 18, 22, 0, tzinfo=TZ)

    def test_parse_single_time(self):
        """Parse '9:00 pm' — single time, no range."""
        scraper = EmEventsScraper()
        dtstart, dtend = scraper._parse_time_range("9:00 pm", 2026, 6, 18, TZ)
        assert dtstart == datetime(2026, 6, 18, 21, 0, tzinfo=TZ)
        assert dtend is None

    def test_parse_all_day(self):
        """Parse 'All Day' — end = start + 1 day."""
        scraper = EmEventsScraper()
        dtstart, dtend = scraper._parse_time_range("All Day", 2026, 6, 18, TZ)
        assert dtstart == datetime(2026, 6, 18, 0, 0, tzinfo=TZ)
        assert dtend == datetime(2026, 6, 19, 0, 0, tzinfo=TZ)


class TestParseLocation:
    """_parse_location() extracts venue name + address from EM HTML."""

    def _wrap(self, inner_html: str) -> BeautifulSoup:
        """Wrap inner HTML in a container that _parse_location can find."""
        html = f'<div class="em-event">{inner_html}</div>'
        soup = BeautifulSoup(html, "html.parser")
        return soup.select_one(".em-event")

    def test_parse_location_with_name_and_address(self):
        """Extract venue name and address from a location div."""
        el = self._wrap("""<div class="em-item-meta-line em-event-location">
          <span class="em-icon-location em-icon"></span>
          <div class="em-event-location-info">
            <a href="https://example.org/locations/test-venue/">Test Venue</a>
            <div class="em-event-location-address">123 Main St, Anytown, ST</div>
          </div>
        </div>""")
        scraper = EmEventsScraper()
        result = scraper._parse_location(el)
        assert result == "Test Venue, 123 Main St, Anytown, ST"

    def test_parse_location_name_only(self):
        """Extract venue name when no address is present."""
        el = self._wrap("""<div class="em-item-meta-line em-event-location">
          <div class="em-event-location-info">
            <a href="https://example.org/locations/venue/">Venue Only</a>
          </div>
        </div>""")
        scraper = EmEventsScraper()
        result = scraper._parse_location(el)
        assert result == "Venue Only"


class TestParseEvent:
    """_parse_event() parses a full .em-event HTML fragment into an event dict."""

    def test_parse_complete_event(self):
        """Parse a real EM event HTML fragment with all fields present."""
        html = """<div class="em-event em-item" data-href="https://example.org/events/test-concert/">
          <div class="em-item-info">
            <h3 class="em-item-title">
              <a href="https://example.org/events/test-concert/">Test Concert</a>
            </h3>
            <div class="em-event-meta em-item-meta">
              <div class="em-event-date em-event-meta-datetime">June 18, 2026</div>
              <div class="em-event-time em-event-meta-datetime">7:00 pm - 10:00 pm</div>
              <div class="em-event-location">
                <div class="em-event-location-info">
                  <a href="https://example.org/locations/test-venue/">Test Venue</a>
                  <div class="em-event-location-address">123 Main St, Anytown, ST</div>
                </div>
              </div>
            </div>
          </div>
        </div>"""
        soup = BeautifulSoup(html, "html.parser")
        el = soup.select_one(".em-event")

        scraper = EmEventsScraper()
        scraper.domain = "example.org"
        result = scraper._parse_event(el, TZ)

        assert result is not None
        assert result["title"] == "Test Concert"
        assert result["url"] == "https://example.org/events/test-concert/"
        assert result["dtstart"] == datetime(2026, 6, 18, 19, 0, tzinfo=TZ)
        assert result["dtend"] == datetime(2026, 6, 18, 22, 0, tzinfo=TZ)
        assert result["location"] == "Test Venue, 123 Main St, Anytown, ST"
        assert result["uid"].endswith("@example.org")
        assert result["uid"].startswith("em-")


class TestFetchPage:
    """_fetch_page() parses real WFHB AJAX HTML into event dicts."""

    FIXTURE_PATH = Path(__file__).parent / "fixtures" / "wfhb_ajax_page1.html"

    def test_fetch_page_returns_events(self):
        """_fetch_page with saved WFHB fixture should return 50 events."""
        scraper = EmEventsScraper()
        scraper.name = "Test WFHB"
        scraper.domain = "wfhb.org"
        scraper.ajax_url = "https://wfhb.org/wp-admin/admin-ajax.php"
        scraper.timezone = "America/Indiana/Indianapolis"
        scraper.default_location = "Bloomington, IN"

        with open(self.FIXTURE_PATH, encoding="utf-8") as f:
            fixture_html = f.read()

        with patch("scrapers.lib.em_events.requests.post") as mock_post:
            mock_post.return_value.text = fixture_html
            mock_post.return_value.status_code = 200
            mock_post.return_value.ok = True

            events = scraper._fetch_page(1)

        # Should parse 50 events from the fixture
        assert len(events) > 40, f"Expected >40 events, got {len(events)}"
        # Verify first event has required fields
        first = events[0]
        assert "title" in first
        assert "url" in first
        assert "dtstart" in first
        assert "dtend" in first
        assert "location" in first
        assert "uid" in first
        assert first["title"], "Title should not be empty"
        assert isinstance(first["dtstart"], datetime)
