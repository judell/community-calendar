#!/usr/bin/env python3
"""Run-level tests for the parameterized Tribe REST scraper (scrapers/tribe_rest.py).

The shared fetch contract (a broken first page fails, a dormant calendar stays
quiet, a later-page failure keeps the pages already fetched) lives in
tests/test_tribe_fetch.py. These tests pin what run() writes to disk.
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

from scrapers.tribe_rest import TribeRestScraper  # noqa: E402


def _scraper() -> TribeRestScraper:
    return TribeRestScraper(api_base="https://example.org", source_name="Example Venue")


def _response(payload: dict) -> Mock:
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = payload
    return response


def test_dormant_calendar_writes_a_valid_empty_ics(tmp_path):
    """A dormant 200+empty calendar still writes a valid, zero-event file."""
    output = tmp_path / "example.ics"
    with patch("scrapers.tribe_rest.requests.get") as mock_get:
        mock_get.return_value = _response({"events": [], "total_pages": 1})
        _scraper().run(str(output))
    content = output.read_text()
    assert "BEGIN:VCALENDAR" in content
    assert "BEGIN:VEVENT" not in content


def test_first_page_failure_writes_no_calendar(tmp_path):
    """A failed first page must not overwrite the source's output file."""
    output = tmp_path / "example.ics"
    with patch("scrapers.tribe_rest.requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.ConnectionError("connection refused")
        with pytest.raises(requests.exceptions.ConnectionError):
            _scraper().run(str(output))
    assert not output.exists()
