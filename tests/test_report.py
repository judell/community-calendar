#!/usr/bin/env python3
"""Tests for the feed-health report's missing-calendar handling.

A source listed in feeds.txt whose .ics is absent after a build produced no
calendar — a blocked scraper or a failed download. The report must keep it as
a failed build so the source stays visible, instead of deleting the entry and
letting the failure go dark.
"""

import json
import sys
from pathlib import Path

# Add project root to path so the scripts package imports resolve
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts import report


def _scraper_reference(*stems: str) -> dict:
    return {
        stem: {"kind": "scraper", "name": stem, "cmd": f"python scrapers/{stem}.py"}
        for stem in stems
    }


def test_expected_source_with_no_calendar_is_reported_not_deleted(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "cities" / "bloomington").mkdir(parents=True)
    monkeypatch.setattr(
        report, "parse_feeds_reference", lambda city: _scraper_reference("hardtruth")
    )

    report_path = tmp_path / "report.json"
    report.update_report(["bloomington"], report_path=str(report_path))

    saved = json.loads(report_path.read_text())
    feed = saved["cities"]["bloomington"]["feeds"]["hardtruth"]
    assert feed["content"] == "no_calendar"
    assert feed["history"][-1]["error"] == "no calendar produced"

    slice_ = report.build_city_slice(saved, "bloomington", set())
    problems = slice_["problems"]
    assert [i["kind"] for i in problems] == ["no_calendar"]
    assert problems[0]["severity"] == 1
    assert problems[0]["feed"] == "hardtruth"


def test_source_removed_from_feeds_txt_is_dropped(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "cities" / "bloomington").mkdir(parents=True)
    monkeypatch.setattr(report, "parse_feeds_reference", lambda city: {})

    report_path = tmp_path / "report.json"
    report_path.write_text(
        json.dumps(
            {
                "generated": None,
                "cities": {
                    "bloomington": {
                        "feeds": {"retired": {"history": [{"date": "2020-01-01", "count": 3}]}}
                    }
                },
                "anomalies": [],
            }
        )
    )
    report.update_report(["bloomington"], report_path=str(report_path))

    saved = json.loads(report_path.read_text())
    assert "retired" not in saved["cities"]["bloomington"]["feeds"]


def test_present_source_is_not_marked_no_calendar(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    city_dir = tmp_path / "cities" / "bloomington"
    city_dir.mkdir(parents=True)
    (city_dir / "hardtruth.ics").write_text("BEGIN:VCALENDAR\r\nVERSION:2.0\r\nEND:VCALENDAR\r\n")
    monkeypatch.setattr(
        report, "parse_feeds_reference", lambda city: _scraper_reference("hardtruth")
    )

    report_path = tmp_path / "report.json"
    report.update_report(["bloomington"], report_path=str(report_path))

    saved = json.loads(report_path.read_text())
    feed = saved["cities"]["bloomington"]["feeds"]["hardtruth"]
    assert feed["content"] == "quiet"
    assert report.build_city_slice(saved, "bloomington", set())["problems"] == []


def test_missing_build_keeps_the_anomaly_baseline():
    """A missing-calendar entry must not become the drop-alert baseline."""
    history = [
        {"date": "2026-10-01", "count": 100},
        {"date": "2026-10-02", "count": 0, "error": "no calendar produced"},
    ]
    assert [a["type"] for a in report.detect_anomalies("hardtruth", 10, history)] == [
        "significant_drop"
    ]


def test_skipped_scrapers_leave_prior_status_untouched(tmp_path, monkeypatch):
    """regenerate_only: scrapers did not run, so an absent .ics is not a failure."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "cities" / "bloomington").mkdir(parents=True)
    monkeypatch.setattr(
        report, "parse_feeds_reference", lambda city: _scraper_reference("hardtruth")
    )

    report_path = tmp_path / "report.json"
    report_path.write_text(
        json.dumps(
            {
                "generated": None,
                "cities": {
                    "bloomington": {
                        "feeds": {"hardtruth": {"history": [{"date": "2026-10-01", "count": 7}]}}
                    }
                },
                "anomalies": [],
            }
        )
    )
    report.update_report(["bloomington"], report_path=str(report_path), scrapers_skipped=True)

    saved = json.loads(report_path.read_text())
    feed = saved["cities"]["bloomington"]["feeds"]["hardtruth"]
    assert feed["history"] == [{"date": "2026-10-01", "count": 7}]
    assert "content" not in feed
    assert report.build_city_slice(saved, "bloomington", set())["problems"] == []


def test_skipped_scrapers_still_check_live_feeds(tmp_path, monkeypatch):
    """regenerate_only skips scrapers but still downloads live feeds."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "cities" / "bloomington").mkdir(parents=True)
    monkeypatch.setattr(
        report,
        "parse_feeds_reference",
        lambda city: {
            "uplandbeer": {"kind": "scraper", "name": "Upland Brewing", "cmd": "python x.py"},
            "bgcbloomington": {"kind": "feed", "name": "Boys & Girls Club", "url": "https://e/x"},
        },
    )

    report_path = tmp_path / "report.json"
    report_path.write_text(
        json.dumps(
            {
                "generated": None,
                "cities": {
                    "bloomington": {
                        "feeds": {
                            "uplandbeer": {"history": [{"date": "2026-10-01", "count": 4}]},
                            "retiredsrc": {"history": [{"date": "2026-10-01", "count": 2}]},
                        }
                    }
                },
                "anomalies": [],
            }
        )
    )
    report.update_report(["bloomington"], report_path=str(report_path), scrapers_skipped=True)

    feeds = json.loads(report_path.read_text())["cities"]["bloomington"]["feeds"]
    # A skipped scraper keeps its prior status.
    assert feeds["uplandbeer"]["history"] == [{"date": "2026-10-01", "count": 4}]
    assert "content" not in feeds["uplandbeer"]
    # A live feed that produced no .ics is still a failure.
    assert feeds["bgcbloomington"]["content"] == "no_calendar"
    # A source feeds.txt no longer lists is still retired.
    assert "retiredsrc" not in feeds


CURATOR_URL = "curator://0d6f3c1a-1111-2222-3333-444444444444"
CURATOR_STEM = "0d6f3c1a_1111_2222_3333_444444444444"
CURATOR_REFERENCE = {"kind": "curator", "name": "Curator Picks", "url": CURATOR_URL}


def test_parse_feeds_reference_registers_a_curator_feed(tmp_path, monkeypatch):
    """feeds.txt names a curator as curator://<user_id>. Without the stem the
    report reads the feed as retired and deletes its history."""
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    feeds = tmp_path / "cities" / "bloomington" / "feeds.txt"
    feeds.parent.mkdir(parents=True)
    feeds.write_text(f"# Curator Picks\n{CURATOR_URL}\n")
    monkeypatch.syspath_prepend(str(Path(__file__).parent.parent / "scripts"))
    monkeypatch.setattr(report, "__file__", str(scripts / "report.py"))

    assert report.parse_feeds_reference("bloomington") == {CURATOR_STEM: CURATOR_REFERENCE}


def test_curator_feed_with_no_calendar_keeps_its_history(tmp_path, monkeypatch):
    """A skipped curator download is a failed build like any other — and its
    repro must not carry a token (GHSA-3pg8-w4j4-6wv8)."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "cities" / "bloomington").mkdir(parents=True)
    monkeypatch.setattr(
        report, "parse_feeds_reference", lambda city: {CURATOR_STEM: CURATOR_REFERENCE}
    )

    report_path = tmp_path / "report.json"
    report.update_report(["bloomington"], report_path=str(report_path))

    saved = json.loads(report_path.read_text())
    feed = saved["cities"]["bloomington"]["feeds"][CURATOR_STEM]
    assert feed["content"] == "no_calendar"

    problem = report.build_city_slice(saved, "bloomington", set())["problems"][0]
    assert problem["kind"] == "no_calendar"
    assert problem["repro"] == {
        "display": "Curator Picks",
        "source": CURATOR_URL,
        "command": None,
    }
