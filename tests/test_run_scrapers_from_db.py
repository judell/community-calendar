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


class TestRecordRanIfSuccess:
    """Only a clean exit with a real calendar marks a source as ran (#233)."""

    def _calendar(self, tmp_path, body="BEGIN:VCALENDAR\r\nEND:VCALENDAR\r\n"):
        out = tmp_path / "cities" / "bloomington" / "iu_events.ics"
        out.parent.mkdir(parents=True)
        out.write_text(body)
        return out

    def test_clean_exit_with_calendar_is_recorded(self, tmp_path, monkeypatch):
        monkeypatch.setattr(rs, "ROOT", tmp_path)
        out = self._calendar(tmp_path)

        rs.record_ran_if_success(_row(), 0)

        assert (out.parent / "ran_sources.txt").read_text() == "iu_events\n"

    def test_nonzero_exit_is_not_recorded(self, tmp_path, monkeypatch):
        monkeypatch.setattr(rs, "ROOT", tmp_path)
        out = self._calendar(tmp_path)

        rs.record_ran_if_success(_row(), 1)

        assert not (out.parent / "ran_sources.txt").exists()

    def test_missing_output_is_not_recorded(self, tmp_path, monkeypatch):
        monkeypatch.setattr(rs, "ROOT", tmp_path)
        out = self._calendar(tmp_path)
        out.unlink()

        rs.record_ran_if_success(_row(), 0)

        assert not (out.parent / "ran_sources.txt").exists()

    def test_block_page_is_not_recorded(self, tmp_path, monkeypatch):
        """A 200 HTML body is a failed source, not a quiet one."""
        monkeypatch.setattr(rs, "ROOT", tmp_path)
        out = self._calendar(tmp_path, body="<html>Access denied</html>")

        rs.record_ran_if_success(_row(), 0)

        assert not (out.parent / "ran_sources.txt").exists()

    def test_truncated_calendar_is_not_recorded(self, tmp_path, monkeypatch):
        """A calendar that opens but never closes is a failed source."""
        monkeypatch.setattr(rs, "ROOT", tmp_path)
        out = self._calendar(tmp_path, body="BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\n")

        rs.record_ran_if_success(_row(), 0)

        assert not (out.parent / "ran_sources.txt").exists()
