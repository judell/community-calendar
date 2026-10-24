#!/usr/bin/env python3
"""Tests for the MaxPreps layout-change guard (#243)."""

import sys
from pathlib import Path

import pytest

# Add project root to path so scraper imports resolve
sys.path.insert(0, str(Path(__file__).parent.parent))

import scrapers.maxpreps as mp
from scrapers.maxpreps import MaxPrepsScraper

SCHOOL = {
    "name": "Test School",
    "url": "https://www.maxpreps.com/in/test/test-school/events/",
    "timezone": "America/Indiana/Indianapolis",
}

NO_CONTESTS_HTML = (
    '<html><script id="__NEXT_DATA__" type="application/json">'
    '{"props":{"pageProps":{}}}'
    "</script></html>"
)


class _Response:
    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self):
        pass


def test_missing_contests_raises_without_writing_a_calendar(tmp_path, monkeypatch):
    monkeypatch.setattr(mp.requests, "get", lambda *args, **kwargs: _Response(NO_CONTESTS_HTML))
    out = tmp_path / "maxpreps.ics"

    with pytest.raises(RuntimeError, match="initSchoolContests"):
        MaxPrepsScraper(SCHOOL).run(str(out))

    assert not out.exists()
