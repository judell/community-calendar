#!/usr/bin/env python3
"""Tests for the Bloomington Brewing sitemap parse (#243)."""

import sys
from pathlib import Path
from urllib.error import URLError

import pytest

# Add project root to path so scraper imports resolve
sys.path.insert(0, str(Path(__file__).parent.parent))

import scrapers.bloomington_brewing as bb
from scrapers.bloomington_brewing import BloomingtonBrewingScraper

PAST_ICS = b"""\
BEGIN:VCALENDAR\r
VERSION:2.0\r
BEGIN:VEVENT\r
UID:past@example.com\r
DTSTART:20250101T190000Z\r
SUMMARY:Past Event\r
END:VEVENT\r
END:VCALENDAR\r
"""


class _FakeResponse:
    def __init__(self, body: bytes):
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _serve(monkeypatch, body: bytes) -> None:
    monkeypatch.setattr(bb, "urlopen", lambda req, timeout: _FakeResponse(body))


def _serve_sitemap_and_ics(monkeypatch, sitemap: bytes, ics: bytes) -> None:
    def fake_urlopen(req, timeout):
        return _FakeResponse(ics if "format=ical" in req.full_url else sitemap)

    monkeypatch.setattr(bb, "urlopen", fake_urlopen)


def test_non_sitemap_body_fails_without_writing_a_calendar(tmp_path, monkeypatch):
    _serve(monkeypatch, b"<html><body>blocked</body></html>")
    out = tmp_path / "brew.ics"

    with pytest.raises(RuntimeError, match="no <loc> entries"):
        BloomingtonBrewingScraper().run(str(out))

    assert not out.exists()


def test_sitemap_without_event_paths_fails(tmp_path, monkeypatch):
    _serve(
        monkeypatch,
        b"<urlset><url><loc>https://bloomingtonbrew.com/about</loc></url></urlset>",
    )
    out = tmp_path / "brew.ics"

    with pytest.raises(RuntimeError, match="no event URLs"):
        BloomingtonBrewingScraper().run(str(out))

    assert not out.exists()


def test_sitemap_with_only_past_events_stays_quiet(tmp_path, monkeypatch):
    _serve_sitemap_and_ics(
        monkeypatch,
        b"<urlset><url><loc>https://bloomingtonbrew.com/events/2025/5/3/past</loc></url></urlset>",
        PAST_ICS,
    )
    out = tmp_path / "brew.ics"

    BloomingtonBrewingScraper().run(str(out))

    ics = out.read_text()
    assert "BEGIN:VCALENDAR" in ics
    assert "VEVENT" not in ics


def test_unreachable_sitemap_names_the_failure(tmp_path, monkeypatch):
    def _raise(req, timeout):
        raise URLError("boom")

    monkeypatch.setattr(bb, "urlopen", _raise)
    out = tmp_path / "brew.ics"

    with pytest.raises(RuntimeError, match="Could not fetch sitemap"):
        BloomingtonBrewingScraper().run(str(out))

    assert not out.exists()
