#!/usr/bin/env python3
"""Tests for the pending-feeds insert path.

A duplicate insert is a normal outcome (the same URL can be re-submitted), but
the skip must name a `removed` tombstone: otherwise a curator re-adding a
retired feed watches it vanish with no explanation (#240).
"""

import email.message
import io
import json
import sys
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import scripts.process_pending_feeds as ppf

FEED = {
    "name": "Indiana State Events",
    "url": "https://events.in.gov/search/events.ics?event_types%5B%5D=1",
    "feed_type": "ics_url",
    "scraper_cmd": None,
}


class _Resp:
    def __init__(self, body=b"", status=201):
        self._body = body
        self.status = status

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _duplicate(req) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        req.full_url, 409, "Conflict", email.message.Message(), io.BytesIO(b"duplicate key")
    )


class TestDuplicateReporting:
    def _fake_urlopen(self, monkeypatch, post, rows=None):
        """Serve POST via post(req); serve the status lookup from rows."""
        calls: list[tuple[str, str]] = []

        def fake(req, timeout=None):
            calls.append((req.get_method(), req.full_url))
            if req.get_method() == "POST":
                result = post(req)
                if isinstance(result, urllib.error.HTTPError):
                    raise result
                return result
            return _Resp(json.dumps(rows or []).encode(), status=200)

        monkeypatch.setattr(ppf.urllib.request, "urlopen", fake)
        return calls

    def test_removed_tombstone_is_named(self, monkeypatch, capsys):
        calls = self._fake_urlopen(monkeypatch, _duplicate, [{"status": "removed"}])

        inserted, skipped, errors = ppf.insert_feeds(
            "bloomington", [FEED], "https://db.example", "key"
        )

        assert (inserted, skipped, errors) == (0, 1, 0)
        assert (
            f"= {FEED['name']} (already exists as removed; "
            "re-adding it has no effect — see #240)" in capsys.readouterr().out
        )
        assert any(method == "GET" and "url=eq." in url for method, url in calls)

    def test_ignored_duplicate_201_reports_the_tombstone(self, monkeypatch, capsys):
        """PostgREST answers an ignored duplicate with 201 and an empty array."""
        self._fake_urlopen(
            monkeypatch, lambda req: _Resp(b"[]", status=201), [{"status": "removed"}]
        )

        inserted, skipped, errors = ppf.insert_feeds(
            "bloomington", [FEED], "https://db.example", "key"
        )

        assert (inserted, skipped, errors) == (0, 1, 0)
        assert (
            f"= {FEED['name']} (already exists as removed; "
            "re-adding it has no effect — see #240)" in capsys.readouterr().out
        )

    def test_conflict_response_reports_the_skip(self, monkeypatch, capsys):
        """Some PostgREST versions surface the unique violation as 409."""
        self._fake_urlopen(monkeypatch, _duplicate, [{"status": "active"}])

        inserted, skipped, errors = ppf.insert_feeds(
            "bloomington", [FEED], "https://db.example", "key"
        )

        assert (inserted, skipped, errors) == (0, 1, 0)
        assert f"= {FEED['name']} (already exists)" in capsys.readouterr().out

    def test_empty_lookup_keeps_the_plain_message(self, monkeypatch, capsys):
        self._fake_urlopen(monkeypatch, lambda req: _Resp(b"[]", status=201), [])

        ppf.insert_feeds("bloomington", [FEED], "https://db.example", "key")

        assert f"= {FEED['name']} (already exists)" in capsys.readouterr().out

    def test_active_duplicate_stays_terse(self, monkeypatch, capsys):
        self._fake_urlopen(monkeypatch, _duplicate, [{"status": "active"}])

        ppf.insert_feeds("bloomington", [FEED], "https://db.example", "key")

        assert f"= {FEED['name']} (already exists)" in capsys.readouterr().out

    def test_lookup_failure_keeps_the_plain_message(self, monkeypatch, capsys):
        def fake(req, timeout=None):
            if req.get_method() == "POST":
                raise _duplicate(req)
            raise urllib.error.URLError("offline")

        monkeypatch.setattr(ppf.urllib.request, "urlopen", fake)

        inserted, skipped, errors = ppf.insert_feeds(
            "bloomington", [FEED], "https://db.example", "key"
        )

        assert (inserted, skipped, errors) == (0, 1, 0)
        assert f"= {FEED['name']} (already exists)" in capsys.readouterr().out

    def test_insert_needs_no_status_lookup(self, monkeypatch, capsys):
        calls = self._fake_urlopen(monkeypatch, lambda req: _Resp(b'[{"id": 1}]', status=201))

        inserted, skipped, errors = ppf.insert_feeds(
            "bloomington", [FEED], "https://db.example", "key"
        )

        assert (inserted, skipped, errors) == (1, 0, 0)
        assert [method for method, _ in calls] == ["POST"]
