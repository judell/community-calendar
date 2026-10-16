#!/usr/bin/env python3
"""The fetch contract shared by both Tribe REST scrapers.

`scrapers/lib/tribe_events.py` (TribeEventsScraper) and `scrapers/tribe_rest.py`
(TribeRestScraper) own separate fetch loops but must behave the same at the
seam: a broken first page fails the run, a dormant 200+empty calendar does not,
and a later-page failure keeps the pages already fetched.

Written once here and parameterized over both scrapers, so the two copies
cannot drift.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

# Add project root and scrapers/ to path so scraper imports resolve
_proj_root = Path(__file__).parent.parent
sys.path.insert(0, str(_proj_root))
sys.path.insert(0, str(_proj_root / "scrapers"))

from scrapers.lib.tribe_events import TribeEventsScraper  # noqa: E402
from scrapers.tribe_rest import TribeRestScraper  # noqa: E402


class _LibScraper(TribeEventsScraper):
    name = "Test Source"
    domain = "test.example.com"
    api_url = "https://test.example.com/wp-json/tribe/events/v1/events/"
    max_pages = 3


def _ok_response(payload: dict) -> Mock:
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = payload
    return response


SCRAPERS = [
    pytest.param(
        "scrapers.lib.tribe_events.requests.get",
        lambda: _LibScraper(),
        id="lib",
    ),
    pytest.param(
        "scrapers.tribe_rest.requests.get",
        lambda: TribeRestScraper(api_base="https://example.org", source_name="Example Venue"),
        id="rest",
    ),
]


@pytest.mark.parametrize("get_path, make_scraper", SCRAPERS)
def test_dormant_200_with_no_events_returns_empty(get_path, make_scraper):
    with patch(get_path) as mock_get:
        mock_get.return_value = _ok_response({"events": [], "total_pages": 1})
        assert make_scraper().fetch_events() == []


@pytest.mark.parametrize("get_path, make_scraper", SCRAPERS)
def test_first_page_http_error_raises(get_path, make_scraper):
    with patch(get_path) as mock_get:
        response = Mock()
        response.raise_for_status.side_effect = requests.exceptions.HTTPError("403 Client Error")
        mock_get.return_value = response
        with pytest.raises(requests.exceptions.HTTPError):
            make_scraper().fetch_events()


@pytest.mark.parametrize("get_path, make_scraper", SCRAPERS)
def test_first_page_network_error_raises(get_path, make_scraper):
    with patch(get_path) as mock_get:
        mock_get.side_effect = requests.exceptions.ConnectionError("connection refused")
        with pytest.raises(requests.exceptions.ConnectionError):
            make_scraper().fetch_events()


@pytest.mark.parametrize("get_path, make_scraper", SCRAPERS)
def test_first_page_malformed_json_raises(get_path, make_scraper):
    with patch(get_path) as mock_get:
        response = _ok_response({})
        response.json.side_effect = ValueError("Expecting value: line 1 column 1")
        mock_get.return_value = response
        with pytest.raises(ValueError):
            make_scraper().fetch_events()


@pytest.mark.parametrize("get_path, make_scraper", SCRAPERS)
def test_later_page_failure_keeps_pages_already_fetched(get_path, make_scraper):
    page1 = _ok_response(
        {
            "events": [{"id": 1, "title": "Concert", "start_date": "2030-05-01 19:00:00"}],
            "total_pages": 2,
        }
    )
    page2 = Mock()
    page2.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
    with patch(get_path) as mock_get:
        mock_get.side_effect = [page1, page2]
        events = make_scraper().fetch_events()
    assert [e["title"] for e in events] == ["Concert"]
