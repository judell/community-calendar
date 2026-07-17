#!/usr/bin/env python3
"""Tests for Buskirk-Chumley Theater scraper."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root and scrapers/ to path so scraper imports resolve
_proj_root = Path(__file__).parent.parent
sys.path.insert(0, str(_proj_root))
sys.path.insert(0, str(_proj_root / "scrapers"))

from scrapers.buskirk_chumley import BuskirkChumleyScraper  # noqa: E402

# Minimal HTML with one event tile that the scraper can parse.
# Structure matches what the site serves: div[data-id] > .tile > .thumb + .details
TILE_HTML = """\
<html><body>
<div data-id="abc123">
  <div class="tile">
    <div class="thumb">
      <ul>
        <li>15</li>
        <li>July<br /><small>Tuesday</small></li>
      </ul>
    </div>
    <div class="details">
      <a href="https://buskirkchumley.org/event/test-show/">Test Show</a>
      <span>Test Presenter</span>
      <p>Doors: 6:30 PM / Show: 8:00 PM<br />@ Buskirk-Chumley Theater</p>
    </div>
  </div>
</div>
</body></html>"""


class TestAcceptEncoding:
    """Regression tests for #35: Accept-Encoding header triggers stripped page."""

    def test_accept_encoding_not_in_request_headers(self):
        """Accept-Encoding header must not be sent with requests.

        The SiteGround CDN serves a stripped page (no div[data-id] .tile
        elements) when Accept-Encoding: gzip, deflate is present.  urllib3
        handles transparent decompression regardless, so removing the
        header is safe.  Regression test for issue #35.
        """
        scraper = BuskirkChumleyScraper()
        captured_headers = {}

        def intercept_get(_self, url, **kwargs):
            """Replace Session.get — capture headers, return fixture HTML."""
            captured_headers.update(dict(_self.headers))
            mock = Mock()
            mock.text = TILE_HTML
            mock.content = TILE_HTML.encode()
            mock.raise_for_status = Mock()
            return mock

        with patch.object(
            __import__("requests").Session, "get", intercept_get
        ):
            events = scraper.fetch_events()

        assert "Accept-Encoding" not in captured_headers, (
            "Accept-Encoding header was present in request — "
            "SiteGround CDN will serve stripped page (issue #35)"
        )

        # Also verify we got an event back (the tile was parsed)
        assert len(events) == 1, f"Expected 1 event, got {len(events)}"
        assert events[0]["title"] == "Test Show"
