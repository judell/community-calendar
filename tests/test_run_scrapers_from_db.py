#!/usr/bin/env python3
"""Tests for run_scrapers_from_db.py source_id recording (#232)."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import run_scrapers_from_db as rs


def _row(**overrides):
    row = {
        "id": 4,
        "city": "bloomington",
        "url": "cities/bloomington/iu_events.ics",
        "name": "IU Events",
        "feed_type": "scraper",
        "scraper_cmd": "python scrapers/example.py --output cities/bloomington/iu_events.ics",
    }
    row.update(overrides)
    return row


class TestRecordSourceId:
    def test_posts_the_output_stem(self, monkeypatch):
        monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_KEY", "service-key")
        sent: list[tuple[str, str, dict]] = []

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        def fake_urlopen(req, timeout=None):
            sent.append((req.get_method(), req.full_url, json.loads(req.data)))
            return FakeResponse()

        monkeypatch.setattr(rs.urllib.request, "urlopen", fake_urlopen)

        rs.record_source_id(_row())

        assert sent == [
            (
                "POST",
                "https://fake.supabase.co/rest/v1/rpc/record_feed_source",
                {"p_feed_id": 4, "p_source_id": "iu_events"},
            )
        ]

    def test_rows_without_an_id_are_skipped(self, monkeypatch):
        """feeds.txt fallback rows have no DB id, so there is nothing to record."""
        monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_KEY", "service-key")

        def boom(req, timeout=None):
            raise AssertionError("must not PATCH an id-less row")

        monkeypatch.setattr(rs.urllib.request, "urlopen", boom)

        rs.record_source_id(_row(id=None))


class TestRunRowsRecordsOnFailure:
    """The stem follows from the row, so a failed run must still record it;
    otherwise a scraper broken since deploy never maps and its survivors
    outlive retirement (#232)."""

    def test_failed_scraper_still_records_its_stem(self, monkeypatch):
        recorded: list[dict] = []
        monkeypatch.setattr(rs, "record_source_id", recorded.append)

        class FailedRun:
            returncode = 1
            stdout = ""
            stderr = "boom"

        monkeypatch.setattr(rs.subprocess, "run", lambda *a, **k: FailedRun())

        row = _row()
        failures = rs.run_rows("bloomington", [row], "3")

        assert failures == 1
        assert recorded == [row]
