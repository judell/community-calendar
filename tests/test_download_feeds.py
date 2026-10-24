#!/usr/bin/env python3
"""Tests for download_feeds.py retry/throttle behavior.

Locks down the 429 retry path and the same-host throttle so rate-limited
sources (events.in.gov / Localist) stop flapping between "a good build" and
"serving html, not ICS" — the alternating pass/fail signature from the report.
"""

import email.message
import json
import socket
import subprocess
import sys
import threading
import time
from contextlib import contextmanager, suppress
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import urllib.error

import download_feeds as df
import pytest

from tests.helpers import make_ics, make_vevent


def _raise_urlerror(_url):
    """Force the urllib attempt to fail so the curl fallback is exercised."""
    raise urllib.error.URLError("connection refused")


@contextmanager
def _stalled_http_server():
    """Yield a URL whose server accepts the connection but never responds.

    Reproduces a source that is reachable enough to connect but stalls
    forever — the shape that hung the Download live feeds step.
    """
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]
    held: list[socket.socket] = []

    def serve():
        try:
            conn, _ = srv.accept()
        except OSError:
            return
        with suppress(OSError):
            conn.recv(65536)  # read the request, then never respond
        held.append(conn)

    threading.Thread(target=serve, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{port}/feed.ics"
    finally:
        for conn in held:
            conn.close()
        srv.close()


def _rate_limited(req) -> urllib.error.HTTPError:
    """Build the HTTPError urllib raises for an HTTP 429 response."""
    return urllib.error.HTTPError(
        req.full_url, 429, "Too Many Requests", email.message.Message(), None
    )


class _Resp:
    """Minimal urllib success-response stand-in."""

    def __init__(self, body=b""):
        self._body = body
        self._pos = 0

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self, size=-1):
        if size is None or size < 0:
            data = self._body[self._pos :]
            self._pos = len(self._body)
            return data
        data = self._body[self._pos : self._pos + size]
        self._pos += len(data)
        return data


class TestRateLimitRetry:
    def _no_backoff_sleep(self, monkeypatch):
        # tenacity's nap sleep calls the global time.sleep; make the
        # exponential backoff instant so retry tests don't wait ~24s.
        monkeypatch.setattr(df.time, "sleep", lambda _s: None)

    def test_retries_then_recovers_on_429(self, monkeypatch):
        self._no_backoff_sleep(monkeypatch)
        calls = {"n": 0}

        def fake_urlopen(req, timeout=None):
            calls["n"] += 1
            if calls["n"] < 3:
                raise _rate_limited(req)
            return _Resp(b"BEGIN:VEVENT\r\nEND:VEVENT\r\n")

        monkeypatch.setattr(df.urllib.request, "urlopen", fake_urlopen)

        body = df._download_body("https://fake.example/ics")
        assert body.count(b"BEGIN:VEVENT") == 1
        assert calls["n"] == 3

    def test_retries_then_recovers_on_503(self, monkeypatch):
        self._no_backoff_sleep(monkeypatch)
        calls = {"n": 0}

        def fake_urlopen(req, timeout=None):
            calls["n"] += 1
            if calls["n"] < 3:
                raise urllib.error.HTTPError(
                    req.full_url, 503, "Service Unavailable", email.message.Message(), None
                )
            return _Resp(b"BEGIN:VEVENT\r\nEND:VEVENT\r\n")

        monkeypatch.setattr(df.urllib.request, "urlopen", fake_urlopen)

        body = df._download_body("https://fake.example/ics")
        assert body.count(b"BEGIN:VEVENT") == 1
        assert calls["n"] == 3

    def test_exhausted_retries_raise(self, monkeypatch):
        self._no_backoff_sleep(monkeypatch)

        def always_429(req, timeout=None):
            raise _rate_limited(req)

        monkeypatch.setattr(df.urllib.request, "urlopen", always_429)

        with pytest.raises(df._RateLimited):
            df._download_body("https://fake.example/ics")


class TestHostThrottle:
    def test_host_of_extracts_netloc(self):
        assert df._host_of("https://events.in.gov/search/events.ics") == "events.in.gov"
        assert df._host_of("https://calendar.google.com/ical/x") == "calendar.google.com"

    def test_interleaved_same_host_is_throttled(self, monkeypatch):
        sleeps: list[float] = []
        now = {"t": 10.0}

        def fake_now():
            now["t"] += 1.0
            return now["t"]

        def fake_sleep(seconds):
            sleeps.append(seconds)

        monkeypatch.setattr(df.time, "monotonic", fake_now)
        monkeypatch.setattr(df.time, "sleep", fake_sleep)

        last_request_at: dict[str, float] = {}
        df._wait_for_host("events.in.gov", last_request_at)  # t=11
        df._wait_for_host("calendar.google.com", last_request_at)  # t=12
        df._wait_for_host("events.in.gov", last_request_at)  # t=13, 2s later

        assert sleeps == []

    def test_same_host_within_window_sleeps(self, monkeypatch):
        sleeps: list[float] = []
        now = {"t": 10.0}

        def fake_now():
            now["t"] += 0.2
            return now["t"]

        def fake_sleep(seconds):
            sleeps.append(seconds)

        monkeypatch.setattr(df.time, "monotonic", fake_now)
        monkeypatch.setattr(df.time, "sleep", fake_sleep)

        last_request_at: dict[str, float] = {}
        df._wait_for_host("events.in.gov", last_request_at)  # t=10.2
        df._wait_for_host("events.in.gov", last_request_at)  # t=10.4, 0.2s later

        assert 0 < sleeps[0] <= 1.0


BROWNCOUNTY_URL = "https://browncounty.com/events/?mec-ical-feed=1"
BROWNCOUNTY_RAW_ICS = make_ics(
    make_vevent(
        "Live Music at Country Heritage",
        "DTSTART;TZID=America/Indiana/Indianapolis:20260912T180000",
        "DTEND;TZID=America/Indiana/Indianapolis:20260912T210000",
        "MEC-test@browncounty.com",
    )
)


class TestMecTimezonePassthrough:
    def test_browncounty_tzid_times_left_untouched(self, monkeypatch, tmp_path):
        """MEC v7.32 emits correct TZID wall-clock times — download must not shift them.

        Regression for: Live Music at Country Heritage showed 10pm in the
        calendar vs 6pm on https://browncounty.com/events/live-music-at-country-heritage/
        because the stale v7.25 workaround added +4h to every DTSTART/DTEND.
        Drives the production download_feeds path (fetch + DB mocked) so a
        reintroduced rewrite hook fails this test.
        """
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(
            df,
            "fetch_feeds_from_db",
            lambda city: [
                {
                    "id": 1,
                    "url": BROWNCOUNTY_URL,
                    "name": "Brown County Events",
                    "fallback_url": None,
                    "status": "active",
                    "feed_type": "ics_url",
                    "source_ids": [],
                }
            ],
        )

        def fake_fetch(url, outfile):
            outfile.write_text(BROWNCOUNTY_RAW_ICS, encoding="utf-8")
            return True

        monkeypatch.setattr(df, "fetch_with_curl_fallback", fake_fetch)

        df.download_feeds("bloomington")

        produced = list((tmp_path / "cities" / "bloomington").glob("*.ics"))
        assert len(produced) == 1
        content = produced[0].read_text(encoding="utf-8")
        assert "DTSTART;TZID=America/Indiana/Indianapolis:20260912T180000" in content
        assert "DTEND;TZID=America/Indiana/Indianapolis:20260912T210000" in content
        assert "20260912T220000" not in content


class TestCurlFallback:
    def test_non_rate_limited_error_falls_through_to_curl(self, monkeypatch, tmp_path):
        """URLError (DNS/TLS/connection) must not crash the run — curl takes over."""
        outfile = tmp_path / "x.ics"

        def fake_urlopen(req, timeout=None):
            raise urllib.error.URLError("connection refused")

        monkeypatch.setattr(df.urllib.request, "urlopen", fake_urlopen)

        def fake_run(cmd, *args, **kwargs):
            outfile.write_bytes(b"BEGIN:VEVENT\r\nEND:VEVENT\r\n")

        monkeypatch.setattr(df.subprocess, "run", fake_run)

        assert df.fetch_with_curl_fallback("https://fake.example/ics", outfile) is True
        assert outfile.read_bytes().count(b"BEGIN:VEVENT") == 1

    def test_exhausted_retries_fall_through_to_curl(self, monkeypatch, tmp_path):
        """After 429 retries are exhausted, curl still gets a shot."""
        outfile = tmp_path / "x.ics"

        def always_429(req, timeout=None):
            raise _rate_limited(req)

        monkeypatch.setattr(df.urllib.request, "urlopen", always_429)

        def fake_run(cmd, *args, **kwargs):
            outfile.write_bytes(b"BEGIN:VEVENT\r\nEND:VEVENT\r\n")

        monkeypatch.setattr(df.subprocess, "run", fake_run)

        assert df.fetch_with_curl_fallback("https://fake.example/ics", outfile) is True
        assert outfile.read_bytes().count(b"BEGIN:VEVENT") == 1

    def test_stale_outfile_removed_before_fetch(self, monkeypatch, tmp_path):
        """A failed fetch must not leave a prior run's file reported as success."""
        outfile = tmp_path / "x.ics"
        outfile.write_bytes(b"BEGIN:VEVENT\r\nEND:VEVENT\r\n")  # from a prior run

        def fake_urlopen(req, timeout=None):
            raise urllib.error.URLError("connection refused")

        monkeypatch.setattr(df.urllib.request, "urlopen", fake_urlopen)

        # curl also fails: no output written
        monkeypatch.setattr(df.subprocess, "run", lambda cmd, *a, **k: None)

        assert df.fetch_with_curl_fallback("https://fake.example/ics", outfile) is False
        assert not outfile.exists()


class TestBoundedTimeouts:
    """Every network call in the download path must be time-bounded.

    Regression: the curl fallback ran with curl's default of no overall
    timeout, so a source that accepted the connection and then stalled made
    the Download live feeds step spin until the job was cancelled.
    """

    def test_curl_command_bounds_each_attempt(self, tmp_path):
        cmd = df._curl_command("https://fake.example/ics", tmp_path / "x.ics")

        for flag, value in (
            ("--connect-timeout", df._CURL_CONNECT_TIMEOUT_SECONDS),
            ("--max-time", df._CURL_MAX_TIME_SECONDS),
            ("--retry-max-time", df._CURL_RETRY_MAX_TIME_SECONDS),
        ):
            assert flag in cmd, f"curl is missing {flag}"
            assert int(cmd[cmd.index(flag) + 1]) == value
            assert value > 0

    def test_hard_timeout_clears_curls_worst_case(self):
        """The backstop must not fire while curl is still within its own bounds.

        curl can overshoot --retry-max-time by one in-flight --max-time, so
        sizing the backstop below that sum would kill a legitimate retry.
        """
        assert df._CURL_HARD_TIMEOUT_SECONDS >= (
            df._CURL_RETRY_MAX_TIME_SECONDS + df._CURL_MAX_TIME_SECONDS
        )

    def test_curl_run_passes_a_hard_timeout(self, monkeypatch, tmp_path):
        outfile = tmp_path / "x.ics"
        seen: dict[str, object] = {}
        monkeypatch.setattr(df, "_download_body", _raise_urlerror)

        def fake_run(cmd, *args, **kwargs):
            seen["timeout"] = kwargs.get("timeout")
            seen["check"] = kwargs.get("check")
            outfile.write_bytes(b"BEGIN:VEVENT\r\nEND:VEVENT\r\n")

        monkeypatch.setattr(df.subprocess, "run", fake_run)

        assert df.fetch_with_curl_fallback("https://fake.example/ics", outfile) is True
        assert seen["timeout"] == df._CURL_HARD_TIMEOUT_SECONDS
        assert seen["check"] is True

    def test_curl_timeout_discards_partial_file(self, monkeypatch, tmp_path, capsys):
        """A curl killed by the backstop must not leave a truncated file as success."""
        outfile = tmp_path / "x.ics"
        monkeypatch.setattr(df, "_download_body", _raise_urlerror)

        def fake_run(cmd, *args, **kwargs):
            outfile.write_bytes(b"BEGIN:VEVENT\r\n")  # partial download
            raise subprocess.TimeoutExpired(cmd, kwargs.get("timeout", 0))

        monkeypatch.setattr(df.subprocess, "run", fake_run)

        assert df.fetch_with_curl_fallback("https://fake.example/ics", outfile) is False
        assert not outfile.exists()
        # The timeout reason is visible in the log, not just a generic failure.
        assert "timed out after" in capsys.readouterr().out

    def test_curl_nonzero_exit_discards_partial_file(self, monkeypatch, tmp_path):
        """curl's own --max-time exits 28 leaving a partial file behind.

        It does not raise TimeoutExpired (that is only the subprocess backstop),
        so the non-zero exit must itself discard the truncated output.
        """
        outfile = tmp_path / "x.ics"
        monkeypatch.setattr(df, "_download_body", _raise_urlerror)

        def fake_run(cmd, *args, **kwargs):
            outfile.write_bytes(b"BEGIN:VEVENT\r\n")  # partial download
            raise subprocess.CalledProcessError(28, cmd)

        monkeypatch.setattr(df.subprocess, "run", fake_run)

        assert df.fetch_with_curl_fallback("https://fake.example/ics", outfile) is False
        assert not outfile.exists()

    def test_stalled_server_returns_instead_of_hanging(self, monkeypatch, tmp_path):
        """A reachable-but-silent source must fail fast, not hang the build."""
        monkeypatch.setattr(df, "_CURL_CONNECT_TIMEOUT_SECONDS", 1)
        monkeypatch.setattr(df, "_CURL_MAX_TIME_SECONDS", 2)
        monkeypatch.setattr(df, "_CURL_RETRIES", 0)
        monkeypatch.setattr(df, "_CURL_RETRY_MAX_TIME_SECONDS", 2)
        monkeypatch.setattr(df, "_CURL_HARD_TIMEOUT_SECONDS", 3)
        monkeypatch.setattr(df, "_download_body", _raise_urlerror)

        result: dict[str, bool] = {}
        with _stalled_http_server() as url:
            outfile = tmp_path / "x.ics"
            worker = threading.Thread(
                target=lambda: result.update(ok=df.fetch_with_curl_fallback(url, outfile)),
                daemon=True,
            )
            worker.start()
            worker.join(10)

            assert not worker.is_alive(), "fetch hung on a stalled server"
        assert result["ok"] is False

    def test_urllib_attempt_uses_configured_timeout(self, monkeypatch):
        seen: dict[str, float | None] = {}

        def fake_urlopen(req, timeout=None):
            seen["timeout"] = timeout
            return _Resp(b"BEGIN:VEVENT\r\nEND:VEVENT\r\n")

        monkeypatch.setattr(df.urllib.request, "urlopen", fake_urlopen)

        df._download_body("https://fake.example/ics")

        assert seen["timeout"] == df._URLLIB_TIMEOUT_SECONDS

    def test_feeds_query_uses_configured_timeout(self, monkeypatch):
        seen: dict[str, float | None] = {}

        def fake_urlopen(req, timeout=None):
            seen["timeout"] = timeout
            return _Resp(b"[]")

        monkeypatch.setattr(df.urllib.request, "urlopen", fake_urlopen)
        monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_KEY", "service-key")

        assert df.fetch_feeds_from_db("bloomington") == []
        assert seen["timeout"] == df._DB_TIMEOUT_SECONDS

    def test_feeds_query_read_timeout_degrades_to_feeds_txt(self, monkeypatch):
        """A stalled DB read must return None (feeds.txt fallback), not crash.

        urlopen(timeout=...) can raise TimeoutError from resp.read(), which is
        not a URLError — it must still be caught.
        """

        class _HangingResp:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def read(self, size=-1):
                raise TimeoutError("read timed out")

        monkeypatch.setattr(df.urllib.request, "urlopen", lambda req, timeout=None: _HangingResp())
        monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_KEY", "service-key")

        assert df.fetch_feeds_from_db("bloomington") is None

    def test_slow_drip_feed_response_hits_overall_deadline(self, monkeypatch):
        """A trickling body must hit the wall-clock deadline, not the idle timeout.

        urlopen(timeout=...) only bounds idle socket operations, so a host that
        sends a byte at a time keeps read() alive without ever going idle.
        """
        monkeypatch.setattr(df, "_URLLIB_TOTAL_TIMEOUT_SECONDS", 0.05)

        class _Drip:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def read(self, size=-1):
                time.sleep(0.02)  # never reaches EOF
                return b"x"

        monkeypatch.setattr(df.urllib.request, "urlopen", lambda req, timeout=None: _Drip())

        with pytest.raises(TimeoutError):
            df._download_body("https://fake.example/ics")

    def test_slow_drip_db_response_degrades_to_feeds_txt(self, monkeypatch):
        monkeypatch.setattr(df, "_DB_TOTAL_TIMEOUT_SECONDS", 0.05)

        class _Drip:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def read(self, size=-1):
                time.sleep(0.02)  # never reaches EOF
                return b"x"

        monkeypatch.setattr(df.urllib.request, "urlopen", lambda req, timeout=None: _Drip())
        monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_KEY", "service-key")

        assert df.fetch_feeds_from_db("bloomington") is None


class TestDownloadProgressLog:
    def test_logs_in_flight_feed_before_fetch(self, monkeypatch, capsys, tmp_path):
        """A hang must name the feed it is stuck on in the log."""
        monkeypatch.chdir(tmp_path)
        url = "https://calendar.google.com/calendar/ical/example.ics"
        monkeypatch.setattr(
            df,
            "fetch_feeds_from_db",
            lambda city: [
                {
                    "id": 1,
                    "url": url,
                    "name": "Example",
                    "fallback_url": None,
                    "status": "active",
                    "feed_type": "ics_url",
                    "source_ids": [],
                }
            ],
        )
        log_before_fetch: dict[str, str] = {}

        def fake_fetch(feed_url, outfile):
            log_before_fetch["log"] = capsys.readouterr().out
            outfile.write_text(
                "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nEND:VCALENDAR\r\n", encoding="utf-8"
            )
            return True

        monkeypatch.setattr(df, "fetch_with_curl_fallback", fake_fetch)

        df.download_feeds("bloomington")

        assert "calendar.google.com" in log_before_fetch["log"]
        assert ".ics" in log_before_fetch["log"]


class TestRecordFeedSources:
    """remove_feed reads feeds.source_ids, so a wrong payload here silently
    disables survivor deletion (#232)."""

    def test_posts_the_stem_and_activates_only_pending_rows(self, monkeypatch):
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

        monkeypatch.setattr(df.urllib.request, "urlopen", fake_urlopen)

        df.record_feed_sources(
            [
                {
                    "id": 7,
                    "url": "https://example.com/events/feed.ics",
                    "name": "Example",
                    "feed_type": "ics_url",
                    "status": "active",
                },
                {
                    "id": 8,
                    "url": "https://tockify.com/api/feeds/ics/examplefarmers",
                    "name": "Tockify",
                    "feed_type": "curator",
                    "status": "pending",
                },
            ]
        )

        assert sent == [
            (
                "POST",
                "https://fake.supabase.co/rest/v1/rpc/record_feed_source",
                {"p_feed_id": 7, "p_source_id": "example_feed_ics"},
            ),
            (
                "POST",
                "https://fake.supabase.co/rest/v1/rpc/record_feed_source",
                {"p_feed_id": 8, "p_source_id": "tockify_examplefarmers"},
            ),
            (
                "PATCH",
                "https://fake.supabase.co/rest/v1/feeds?id=eq.8",
                {"status": "active"},
            ),
        ]

    def test_a_failed_patch_is_reported_not_raised(self, monkeypatch, capsys):
        monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_KEY", "service-key")

        def boom(req, timeout=None):
            raise OSError("network down")

        monkeypatch.setattr(df.urllib.request, "urlopen", boom)

        df.record_feed_sources(
            [
                {
                    "id": 7,
                    "url": "https://example.com/events/feed.ics",
                    "name": "Example",
                    "feed_type": "ics_url",
                    "status": "active",
                }
            ]
        )

        assert "Failed to record source_id: Example" in capsys.readouterr().out


class TestRanSourcesManifest:
    """Only a real calendar counts as ran; a block page keeps its rows (#233)."""

    def _run(self, monkeypatch, tmp_path, body):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(
            df,
            "fetch_feeds_from_db",
            lambda city: [
                {
                    "id": 1,
                    "url": BROWNCOUNTY_URL,
                    "name": "Brown County Events",
                    "fallback_url": None,
                    "status": "active",
                    "feed_type": "ics_url",
                    "source_ids": [],
                }
            ],
        )
        monkeypatch.setattr(df, "record_feed_sources", lambda rows: None)

        def fake_fetch(url, outfile):
            outfile.write_text(body, encoding="utf-8")
            return True

        monkeypatch.setattr(df, "fetch_with_curl_fallback", fake_fetch)

        df.download_feeds("bloomington")

        return tmp_path / "cities" / "bloomington" / "ran_sources.txt"

    def test_valid_calendar_is_recorded(self, monkeypatch, tmp_path):
        manifest = self._run(monkeypatch, tmp_path, BROWNCOUNTY_RAW_ICS)
        assert manifest.read_text().strip() == df.slugify(BROWNCOUNTY_URL)

    def test_quiet_calendar_is_recorded(self, monkeypatch, tmp_path):
        """Zero upcoming events is still a ran source, not a failure."""
        manifest = self._run(monkeypatch, tmp_path, make_ics(""))
        assert manifest.read_text().strip() == df.slugify(BROWNCOUNTY_URL)

    def test_block_page_is_not_recorded(self, monkeypatch, tmp_path):
        manifest = self._run(monkeypatch, tmp_path, "<html>Access denied</html>")
        assert not manifest.exists()

    def test_truncated_calendar_is_not_recorded(self, monkeypatch, tmp_path):
        """A body that opens a calendar but never closes it is a failed fetch."""
        manifest = self._run(monkeypatch, tmp_path, "BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\n")
        assert not manifest.exists()
