#!/usr/bin/env python3
"""Tests for export_feeds_txt.py's capability-URL guard.

The export copies feeds.url into cities/<city>/feeds.txt, which is committed to
a public repo. A my-picks token is the only credential for that curator's saved
events, so a tokenized row must never be written there, even if the DB still
holds one from before the CHECK constraint (GHSA-3pg8-w4j4-6wv8).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import export_feeds_txt as ex


class _Resp:
    def __init__(self, body: bytes):
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._body


def _export(tmp_path, monkeypatch, rows):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        ex.urllib.request,
        "urlopen",
        lambda req: _Resp(json.dumps(rows).encode()),
    )
    ex.export_feeds_txt("bloomington", "https://fake.supabase.co", "service-key")
    return (tmp_path / "cities" / "bloomington" / "feeds.txt").read_text()


def test_tokenized_row_is_not_written(tmp_path, monkeypatch, capsys):
    text = _export(
        tmp_path,
        monkeypatch,
        [
            {
                "name": "Plain",
                "url": "https://example.invalid/events.ics",
                "feed_type": "ics_url",
                "scraper_cmd": None,
            },
            {
                "name": "Curator",
                "url": "curator://u-1",
                "feed_type": "curator",
                "scraper_cmd": None,
            },
            {
                "name": "Leaked",
                "url": "https://ref.supabase.co/functions/v1/my-picks?token=abc",
                "feed_type": "ics_url",
                "scraper_cmd": None,
            },
        ],
    )

    assert "https://example.invalid/events.ics" in text
    assert "curator://u-1" in text
    assert "token=abc" not in text
    assert "Leaked" not in text
    assert "skipped" in capsys.readouterr().out


def test_token_in_name_or_cmd_is_not_written(tmp_path, monkeypatch, capsys):
    """The exporter writes name and scraper_cmd too; the guard must cover them,
    and its warning must not echo the metadata it rejected."""
    text = _export(
        tmp_path,
        monkeypatch,
        [
            {
                "name": "Leak https://ref.supabase.co/functions/v1/my-picks?token=abc",
                "url": "https://example.invalid/events.ics",
                "feed_type": "ics_url",
                "scraper_cmd": None,
            },
            {
                "name": "Cmd leak",
                "url": "cities/bloomington/x.ics",
                "feed_type": "scraper",
                "scraper_cmd": (
                    "python scrapers/x.py https://ref.supabase.co/functions/v1/my-picks?token=def"
                ),
            },
        ],
    )

    assert "example.invalid" not in text
    assert "token=" not in text
    out = capsys.readouterr().out
    assert "skipped" in out
    assert "token=" not in out
