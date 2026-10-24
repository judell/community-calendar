#!/usr/bin/env python3
"""Tests for the Sycamore Land Trust curl failure path (#243)."""

import subprocess
import sys
from pathlib import Path

import pytest

# Add project root to path so scraper imports resolve
sys.path.insert(0, str(Path(__file__).parent.parent))

import scrapers.sycamore_land_trust as slt
from scrapers.sycamore_land_trust import SycamoreLandTrustScraper


def test_curl_failure_raises_without_writing_a_calendar(tmp_path, monkeypatch):
    result = subprocess.CompletedProcess(
        args=["curl"], returncode=22, stdout="", stderr="404 Not Found"
    )
    monkeypatch.setattr(slt.subprocess, "run", lambda *args, **kwargs: result)
    out = tmp_path / "sycamore.ics"

    with pytest.raises(RuntimeError, match="curl fetch failed"):
        SycamoreLandTrustScraper().run(str(out))

    assert not out.exists()
