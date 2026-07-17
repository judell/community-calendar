#!/usr/bin/env python3
"""Tests for Comedy Attic scraper JSON-LD parsing."""

import json
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root and scrapers/ to path so scraper imports resolve
_proj_root = Path(__file__).parent.parent
sys.path.insert(0, str(_proj_root))
sys.path.insert(0, str(_proj_root / "scrapers"))

from zoneinfo import ZoneInfo  # noqa: E402

from scrapers.comedy_attic import ComedyAtticScraper  # noqa: E402

# Real JSON-LD captured from comedyattic.com/events/129480 (Gianmarco Soresi)
# 6 showtimes across 3 days, with full location + description
MULTI_SHOWTIME_JSONLD = [
    {
        "@context": "http://schema.org",
        "@type": "Event",
        "name": "Gianmarco Soresi: Drama King MORE SHOWS ADDED!",
        "location": {
            "@context": "http://schema.org",
            "@type": "Place",
            "name": "The Comedy Attic",
            "address": {
                "@type": "PostalAddress",
                "streetAddress": "123 S Walnut Street",
                "addressLocality": "Bloomington",
                "addressRegion": "IN",
            },
            "url": "http://www.comedyattic.com",
        },
        "startDate": "2026-06-19T23:00:00Z",
        "description": "<p>Gianmarco Soresi is a New York based stand-up comedian.</p>",
        "url": "https://www.comedyattic.com/shows/354181",
    },
    {
        "@context": "http://schema.org",
        "@type": "Event",
        "name": "Gianmarco Soresi: Drama King MORE SHOWS ADDED!",
        "location": {
            "@context": "http://schema.org",
            "@type": "Place",
            "name": "The Comedy Attic",
            "address": {
                "@type": "PostalAddress",
                "streetAddress": "123 S Walnut Street",
                "addressLocality": "Bloomington",
                "addressRegion": "IN",
            },
        },
        "startDate": "2026-06-20T01:30:00Z",
        "description": "<p>Gianmarco Soresi is a New York based stand-up comedian.</p>",
        "url": "https://www.comedyattic.com/shows/354183",
    },
    {
        "@context": "http://schema.org",
        "@type": "Event",
        "name": "Gianmarco Soresi: Drama King MORE SHOWS ADDED!",
        "startDate": "2026-06-20T23:00:00Z",
        "description": "<p>Gianmarco Soresi is a New York based stand-up comedian.</p>",
        "url": "https://www.comedyattic.com/shows/354182",
    },
    {
        "@context": "http://schema.org",
        "@type": "Event",
        "name": "Gianmarco Soresi: Drama King MORE SHOWS ADDED!",
        "startDate": "2026-06-21T01:30:00Z",
        "url": "https://www.comedyattic.com/shows/354184",
    },
    {
        "@context": "http://schema.org",
        "@type": "Event",
        "name": "Gianmarco Soresi: Drama King MORE SHOWS ADDED!",
        "startDate": "2026-06-21T19:30:00Z",
        "url": "https://www.comedyattic.com/shows/375192",
    },
    {
        "@context": "http://schema.org",
        "@type": "Event",
        "name": "Gianmarco Soresi: Drama King MORE SHOWS ADDED!",
        "startDate": "2026-06-21T22:00:00Z",
        "url": "https://www.comedyattic.com/shows/372909",
    },
]

# Real JSON-LD from comedyattic.com/events/137587 (Bloomington Comedy Festival)
# Date-only events with T00:00:00Z startDate — should default to 8 PM local
DATE_ONLY_JSONLD = [
    {
        "@context": "http://schema.org",
        "@type": "Event",
        "name": "The 18th Annual Bloomington Comedy Festival",
        "location": {
            "@type": "Place",
            "name": "The Comedy Attic",
            "address": {
                "@type": "PostalAddress",
                "streetAddress": "123 S Walnut Street",
                "addressLocality": "Bloomington",
                "addressRegion": "IN",
            },
        },
        "startDate": "2026-06-25T00:00:00Z",
        "description": "<p>Comedy festival all summer long.</p>",
        "url": "https://www.comedyattic.com/shows/373413",
    },
    {
        "@context": "http://schema.org",
        "@type": "Event",
        "name": "The 18th Annual Bloomington Comedy Festival",
        "startDate": "2026-07-02T00:00:00Z",
        "url": "https://www.comedyattic.com/shows/373414",
    },
]


def _make_html(jsonld_blocks: list[dict]) -> str:
    """Build a minimal HTML page with embedded JSON-LD script tags."""
    scripts = "".join(
        f'<script type="application/ld+json">{json.dumps(block)}</script>\n'
        for block in jsonld_blocks
    )
    return f"<html><head></head><body>{scripts}</body></html>"


class TestFetchDetailJsonld:
    """Tests for _fetch_detail_jsonld() — the JSON-LD parsing method."""

    def test_multi_showtime_event(self):
        """Parse a detail page with 6 showtimes across 3 days.

        Verifies: timezone conversion (UTC→EDT), location from JSON-LD,
        description HTML stripping, per-showtime URLs, and unique UIDs.
        """
        scraper = ComedyAtticScraper()
        tz = ZoneInfo("America/Indiana/Indianapolis")

        with patch("scrapers.comedy_attic.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.text = _make_html(MULTI_SHOWTIME_JSONLD)
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            events = scraper._fetch_detail_jsonld(
                "https://comedyattic.com/events/129480", tz
            )

        assert len(events) == 6, f"Expected 6 events, got {len(events)}"

        # First event: 2026-06-19T23:00:00Z → 7:00 PM EDT
        ev = events[0]
        assert ev["title"] == "Gianmarco Soresi: Drama King MORE SHOWS ADDED!"
        assert ev["dtstart"] == datetime(2026, 6, 19, 19, 0, tzinfo=tz)
        assert ev["dtend"] == datetime(2026, 6, 19, 21, 0, tzinfo=tz)
        assert ev["url"] == "https://www.comedyattic.com/shows/354181"
        assert (
            ev["location"] == "The Comedy Attic, 123 S Walnut Street, Bloomington, IN"
        )
        assert "Gianmarco Soresi" in ev["description"]
        assert "<p>" not in ev["description"]  # HTML stripped

        # Second event: 2026-06-20T01:30:00Z → 9:30 PM EDT on June 19
        ev = events[1]
        assert ev["dtstart"] == datetime(2026, 6, 19, 21, 30, tzinfo=tz)
        assert ev["url"] == "https://www.comedyattic.com/shows/354183"

        # Third event: 2026-06-20T23:00:00Z → 7:00 PM EDT on June 20
        ev = events[2]
        assert ev["dtstart"] == datetime(2026, 6, 20, 19, 0, tzinfo=tz)

        # Afternoon show: 2026-06-21T19:30:00Z → 3:30 PM EDT
        ev = events[4]
        assert ev["dtstart"] == datetime(2026, 6, 21, 15, 30, tzinfo=tz)

        # Evening show: 2026-06-21T22:00:00Z → 6:00 PM EDT
        ev = events[5]
        assert ev["dtstart"] == datetime(2026, 6, 21, 18, 0, tzinfo=tz)

        # All UIDs should be unique
        uids = [e["uid"] for e in events]
        assert len(uids) == len(set(uids)), f"Duplicate UIDs: {uids}"

    def test_date_only_defaults_to_8pm(self):
        """Date-only events (T00:00:00Z) should default to 8 PM local time."""
        scraper = ComedyAtticScraper()
        tz = ZoneInfo("America/Indiana/Indianapolis")

        with patch("scrapers.comedy_attic.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.text = _make_html(DATE_ONLY_JSONLD)
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            events = scraper._fetch_detail_jsonld(
                "https://comedyattic.com/events/137587", tz
            )

        assert len(events) == 2

        # June 25 midnight UTC → 8:00 PM EDT on June 24
        ev = events[0]
        assert ev["dtstart"] == datetime(2026, 6, 24, 20, 0, tzinfo=tz)
        assert ev["dtend"] == datetime(2026, 6, 24, 22, 0, tzinfo=tz)

        # July 2 midnight UTC → 8:00 PM EDT on July 1
        ev = events[1]
        assert ev["dtstart"] == datetime(2026, 7, 1, 20, 0, tzinfo=tz)

    def test_skips_non_event_jsonld(self):
        """Non-Event JSON-LD (like Organization) should be ignored."""
        blocks = [
            {
                "@context": "http://schema.org",
                "@type": "Organization",
                "name": "The Comedy Attic",
            },
            {
                "@context": "http://schema.org",
                "@type": "Event",
                "name": "A Real Show",
                "startDate": "2026-07-04T23:00:00Z",
                "url": "https://www.comedyattic.com/shows/999999",
            },
        ]

        scraper = ComedyAtticScraper()
        tz = ZoneInfo("America/Indiana/Indianapolis")

        with patch("scrapers.comedy_attic.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.text = _make_html(blocks)
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            events = scraper._fetch_detail_jsonld(
                "https://comedyattic.com/events/test", tz
            )

        assert len(events) == 1
        assert events[0]["title"] == "A Real Show"

    def test_missing_location_falls_back_to_default(self):
        """When JSON-LD has no location block, use the scraper's default location."""
        blocks = [
            {
                "@context": "http://schema.org",
                "@type": "Event",
                "name": "No Location Show",
                "startDate": "2026-08-01T23:00:00Z",
                "url": "https://www.comedyattic.com/shows/888888",
            }
        ]

        scraper = ComedyAtticScraper()
        tz = ZoneInfo("America/Indiana/Indianapolis")

        with patch("scrapers.comedy_attic.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.text = _make_html(blocks)
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            events = scraper._fetch_detail_jsonld(
                "https://comedyattic.com/events/test", tz
            )

        assert len(events) == 1
        assert (
            events[0]["location"]
            == "The Comedy Attic, 123 S Walnut St, Bloomington, IN"
        )

    def test_missing_description_falls_back_to_title(self):
        """When JSON-LD has no description, use the event title."""
        blocks = [
            {
                "@context": "http://schema.org",
                "@type": "Event",
                "name": "Mystery Show",
                "startDate": "2026-08-15T23:00:00Z",
                "url": "https://www.comedyattic.com/shows/777777",
            }
        ]

        scraper = ComedyAtticScraper()
        tz = ZoneInfo("America/Indiana/Indianapolis")

        with patch("scrapers.comedy_attic.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.text = _make_html(blocks)
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            events = scraper._fetch_detail_jsonld(
                "https://comedyattic.com/events/test", tz
            )

        assert len(events) == 1
        assert events[0]["description"] == "Mystery Show"
