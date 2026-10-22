#!/usr/bin/env python3
"""Tests for Monroe County History Center scraper (SiteGround handling)."""

import logging
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add project root and scrapers/ to path so scraper imports resolve
_proj_root = Path(__file__).parent.parent
sys.path.insert(0, str(_proj_root))
sys.path.insert(0, str(_proj_root / "scrapers"))

from scrapers.monroe_county_history_center import HistoryCenterScraper  # noqa: E402

# The SiteGround sgcaptcha challenge: a 202 meta-refresh page, not a calendar.
CAPTCHA_HTML = (
    '<html><head><link rel="icon" href="data:;"><meta http-equiv="refresh" '
    'content="0;/.well-known/sgcaptcha/?r=%2Fwp-json%2Fwp%2Fv2%2Fajde_events'
    '&y=ipc:64.38.182.56:1791648429.348"></meta></head></html>'
)


def _mock_response(status_code: int, text: str) -> Mock:
    mock = Mock()
    mock.status_code = status_code
    mock.text = text
    mock.json.return_value = []
    return mock


# One listing item whose date the scraper can parse from the content field.
EVENT_ITEM = {
    "slug": "test-event",
    "title": {"rendered": "Test Event"},
    "link": "https://monroehistory.org/event/test-event/",
    "date": "2026-10-01T12:00:00",
    "content": {"rendered": '<div class="eelisttime">Thursday, July 16: 5:30pm – 6:30pm</div>'},
}


class TestUserAgent:
    """monroehistory.org hard-403s the project UA; a plain one is required."""

    def test_plain_mozilla_user_agent_sent(self):
        scraper = HistoryCenterScraper()
        captured_headers: dict[str, str] = {}

        def intercept_get(url, **kwargs):
            captured_headers.update(kwargs.get("headers", {}))
            return _mock_response(200, "[]")

        with patch("scrapers.monroe_county_history_center.requests.get", intercept_get):
            scraper.fetch_events()

        assert captured_headers["User-Agent"] == "Mozilla/5.0", (
            "Project User-Agent is hard-403'd by SiteGround; "
            f"got {captured_headers.get('User-Agent')!r}"
        )


class TestListingFailure:
    """A failed listing page is a block or a truncation, not an empty calendar."""

    def test_first_page_challenge_fails_the_run(self, caplog):
        """A blocked first page is a broken ingest, not a dormant calendar."""
        scraper = HistoryCenterScraper()

        with (
            patch(
                "scrapers.monroe_county_history_center.requests.get",
                return_value=_mock_response(202, CAPTCHA_HTML),
            ),
            caplog.at_level(logging.WARNING, logger="HistoryCenterScraper"),
            pytest.raises(RuntimeError, match="HTTP 202"),
        ):
            scraper.fetch_events()

        assert any("captcha challenge" in r.message for r in caplog.records)

    def test_failed_first_page_writes_no_calendar(self, tmp_path):
        """The run exits non-zero without leaving a quiet-looking calendar."""
        scraper = HistoryCenterScraper()
        output = tmp_path / "monroe.ics"

        with (
            patch(
                "scrapers.monroe_county_history_center.requests.get",
                return_value=_mock_response(202, CAPTCHA_HTML),
            ),
            pytest.raises(RuntimeError, match="HTTP 202"),
        ):
            scraper.run(str(output))

        assert not output.exists()

    def test_end_of_list_400_is_not_a_challenge(self, caplog):
        """WordPress 400 past the last page is normal, not a block."""
        scraper = HistoryCenterScraper()
        page_one = _mock_response(200, "")
        page_one.json.return_value = [EVENT_ITEM]

        with (
            patch(
                "scrapers.monroe_county_history_center.requests.get",
                side_effect=[
                    page_one,
                    _mock_response(400, '{"code":"rest_post_invalid_page_number"}'),
                ],
            ),
            caplog.at_level(logging.WARNING, logger="HistoryCenterScraper"),
        ):
            events = scraper.fetch_events()

        assert len(events) == 1
        assert not any("captcha" in r.message for r in caplog.records)
        assert not any(r.levelno >= logging.WARNING for r in caplog.records), (
            "a 400 past the last page is the normal end-of-list signal, not a warning"
        )

    def test_later_page_error_is_logged(self, caplog):
        """A truncated later page names its status in the build log."""
        scraper = HistoryCenterScraper()
        page_one = _mock_response(200, "")
        page_one.json.return_value = [EVENT_ITEM]

        with (
            patch(
                "scrapers.monroe_county_history_center.requests.get",
                side_effect=[page_one, _mock_response(500, "Internal Error")],
            ),
            caplog.at_level(logging.WARNING, logger="HistoryCenterScraper"),
        ):
            events = scraper.fetch_events()

        assert len(events) == 1
        assert any("page 2 returned HTTP 500" in r.message for r in caplog.records)

    def test_partial_pages_kept_when_challenge_hits_later_page(self, caplog):
        """A mid-pagination block keeps earlier pages, not an empty calendar.

        A partial set is still real output: the source stays present in the
        payload, so only the unfetched pages' uids are swept, subject to the
        50% partial-load guard (ADR 0017). An empty calendar would instead
        hand feed-health a quiet-looking zero.
        """
        scraper = HistoryCenterScraper()
        page_one = _mock_response(200, "")
        page_one.json.return_value = [EVENT_ITEM]

        with (
            patch(
                "scrapers.monroe_county_history_center.requests.get",
                side_effect=[page_one, _mock_response(202, CAPTCHA_HTML)],
            ),
            caplog.at_level(logging.WARNING, logger="HistoryCenterScraper"),
        ):
            events = scraper.fetch_events()

        assert len(events) == 1
        assert events[0]["title"] == "Test Event"
        assert any("captcha challenge" in r.message for r in caplog.records)
