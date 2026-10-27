#!/usr/bin/env python3
"""Download all live ICS feeds for a city.

Usage: python scripts/download_feeds.py <city>

Queries the feeds table in Supabase for active ics_url/curator feeds,
downloads each to an auto-named .ics file in cities/<city>/, and injects
X-SOURCE headers. Falls back to feeds.txt if SUPABASE_URL is not set.
"""

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from feed_slug import slugify, source_id_for
from ran_sources import is_calendar_body, record_ran
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


def parse_feeds_txt(feeds_file: Path):
    """Parse feeds.txt, yielding (url, friendly_name, fallback_url) tuples.

    Structured comment format:
        # Friendly Name | https://fallback-url/
        https://feed-url/
        curator://<user_id>

    A comment line immediately before a URL line is the metadata for that URL.
    Category headers (comments before blank lines or other comments) are ignored.
    A curator entry is listed as its non-secret reference; the real URL is
    minted from feed_tokens at download time.
    """
    pending_name = None
    pending_fallback = None

    with feeds_file.open() as f:
        for line in f:
            stripped = line.strip()

            if stripped.startswith("#"):
                body = stripped[1:].strip()
                if "|" in body:
                    parts = body.split("|", 1)
                    pending_name = parts[0].strip()
                    pending_fallback = parts[1].strip() or None
                else:
                    pending_name = body
                    pending_fallback = None
                continue

            if not stripped or not stripped.startswith(("https://", CURATOR_PREFIX)):
                # Blank line or local file ref resets pending comment
                pending_name = None
                pending_fallback = None
                continue

            yield stripped, pending_name, pending_fallback
            pending_name = None
            pending_fallback = None


def inject_source_headers(filepath: Path, friendly_name: str, fallback_url: str | None) -> None:
    """Inject X-SOURCE (and optionally X-SOURCE-URL) into each VEVENT in an ICS file."""
    try:
        with filepath.open("rb") as f:
            raw = f.read()
    except Exception:
        return

    if b"BEGIN:VCALENDAR" not in raw:
        return  # Not valid ICS

    # Detect line ending style from raw bytes
    crlf = b"\r\n" if b"\r\n" in raw else b"\n"

    name_bytes = friendly_name.encode("utf-8")
    headers = b"X-SOURCE:" + name_bytes + crlf
    if fallback_url:
        headers += b"X-SOURCE-URL:" + fallback_url.encode("utf-8") + crlf

    marker = b"BEGIN:VEVENT" + crlf
    parts = raw.split(marker)

    result = [parts[0]]
    for part in parts[1:]:
        vevent_head = part.split(b"END:VEVENT")[0]
        if b"X-SOURCE:" not in vevent_head:
            result.append(headers + part)
        else:
            result.append(part)

    with filepath.open("wb") as out:
        out.write(marker.join(result))


def fetch_feeds_from_db(city: str):
    """Query the feeds table for active feeds: downloads and scraper outputs.

    Scraper rows come back only so download_feeds can reserve their output
    stems; the download loop skips them.
    Returns a list of row dicts, or None if the DB is not available."""
    supabase_url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not supabase_url or not service_key:
        return None

    query_url = (
        f"{supabase_url}/rest/v1/feeds"
        f"?select=id,url,name,status,fallback_url,feed_type,curator_user_id"
        f"&city=eq.{city}"
        f"&status=in.(active,pending)"
        f"&feed_type=in.(ics_url,curator,scraper)"
        f"&order=name.asc"
    )
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
    }
    req = urllib.request.Request(query_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=_DB_TIMEOUT_SECONDS) as resp:
            feeds = json.loads(_read_within(resp, _DB_TOTAL_TIMEOUT_SECONDS).decode())
    except OSError as e:
        # URLError, TimeoutError and socket errors are all OSError: a slow or
        # stalled query must degrade to feeds.txt, not crash the whole city.
        print(f"  ⚠️  Failed to query feeds table: {e}")
        return None

    return feeds  # list of dicts with id, url, name, status


def record_feed_sources(feeds_to_record):
    """Record each feed's source_id and activate pending rows.

    source_ids is the feed's history of produced .ics stems; remove_feed needs
    it to delete the merge survivors the feed owns (#232). The stem follows from
    the feed's url, so every row records it, whether or not this run wrote a
    file: a feed that has failed every build since deploy must still map.
    A failed PATCH leaves the mapping stale until the next build, and
    remove_feed falls back to matching by name.
    """
    supabase_url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not supabase_url or not service_key:
        return
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }
    for feed in feeds_to_record:
        source_id = source_id_for(feed["feed_type"], feed["url"])
        data = json.dumps({"p_feed_id": feed["id"], "p_source_id": source_id}).encode()
        req = urllib.request.Request(
            f"{supabase_url}/rest/v1/rpc/record_feed_source",
            data=data,
            headers=headers,
            method="POST",
        )
        try:
            urllib.request.urlopen(req, timeout=_DB_TIMEOUT_SECONDS)
        except OSError as e:
            print(f"  ⚠️  Failed to record source_id: {feed['name']}: {e}")
            continue
        if feed.get("status") != "pending":
            continue
        data = json.dumps({"status": "active"}).encode()
        req = urllib.request.Request(
            f"{supabase_url}/rest/v1/feeds?id=eq.{feed['id']}",
            data=data,
            headers=headers,
            method="PATCH",
        )
        try:
            urllib.request.urlopen(req, timeout=_DB_TIMEOUT_SECONDS)
            print(f"  ✅ Marked active: {feed['name']}")
        except OSError as e:
            print(f"  ⚠️  Failed to mark active: {feed['name']}: {e}")


# NOTE: browncounty.com's MEC v7.25.0 used to export UTC values mislabeled with
# TZID=America/Indiana/Indianapolis (a +4h workaround lived here). The feed now
# reports MEC v7.32.0 with correct TZID wall-clock times (verified 2026-09-12:
# 18:00 TZID == 6pm on the event page), so no rewrite is applied. If MEC
# regresses, fix it per-feed with a version-gated check — not a blanket shift.


USER_AGENT = "Mozilla/5.0 (compatible; CommunityCalendar/1.0)"

# Every network call in the download path is time-bounded so one bad source
# cannot hang the build. curl defaults to no overall timeout: a feed whose
# host accepts the connection and then stalls would spin the "Download live
# feeds" step until the job was cancelled (see _curl_command below).
#
# urlopen(timeout=...) only bounds each idle socket operation, so a host that
# trickles bytes can keep read() alive forever; body reads also get an overall
# deadline via _read_within.
_URLLIB_TIMEOUT_SECONDS = 60  # per idle socket operation
_URLLIB_TOTAL_TIMEOUT_SECONDS = 120  # overall response body deadline
_CURL_CONNECT_TIMEOUT_SECONDS = 15
_CURL_MAX_TIME_SECONDS = 90  # per curl attempt
_CURL_RETRIES = 3
_CURL_RETRY_MAX_TIME_SECONDS = 180  # caps curl's total retry window
# curl can overshoot --retry-max-time by one in-flight --max-time, so the
# subprocess backstop must clear 180 + 90 before it is allowed to fire.
_CURL_HARD_TIMEOUT_SECONDS = _CURL_RETRY_MAX_TIME_SECONDS + _CURL_MAX_TIME_SECONDS + 30
_DB_TIMEOUT_SECONDS = 30  # per idle socket operation
_DB_TOTAL_TIMEOUT_SECONDS = 60  # overall response body deadline
_READ_CHUNK_BYTES = 1 << 16  # chunk size for deadline-bounded body reads

# Seconds to wait between consecutive requests to the same host. Localist
# (events.in.gov) throttles when two requests land within the same second,
# causing the alternating pass/fail signature seen in the build report.
_HOST_DELAY_SECONDS = 1.0


class _RateLimited(Exception):
    """HTTP 429/503 — retryable."""


def _host_of(url: str) -> str:
    return urlparse(url).netloc


def _wait_for_host(host: str, last_request_at: dict[str, float]) -> None:
    """Sleep so requests to the same host are spaced _HOST_DELAY_SECONDS apart.

    Tracks per-host timestamps rather than consecutive requests so feeds to
    the same host are throttled even when interleaved with other hosts.
    """
    if not host:
        return
    now = time.monotonic()
    prev = last_request_at.get(host)
    if prev is not None:
        delay = _HOST_DELAY_SECONDS - (now - prev)
        if delay > 0:
            time.sleep(delay)
    last_request_at[host] = time.monotonic()


def _read_within(resp, total_seconds: float) -> bytes:
    """Read a response body under an overall deadline.

    urlopen(timeout=...) only bounds each idle socket operation, so a host
    that trickles bytes can keep read() alive indefinitely. Reading in chunks
    lets us enforce a wall-clock total instead.
    """
    deadline = time.monotonic() + total_seconds
    chunks: list[bytes] = []
    while True:
        if time.monotonic() >= deadline:
            raise TimeoutError(f"response exceeded {total_seconds:g}s deadline")
        chunk = resp.read(_READ_CHUNK_BYTES)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


CURATOR_PREFIX = "curator://"

# A my-picks feed is authenticated by its query-string token alone: never
# echo it, and never download it from feeds.txt (GHSA-3pg8-w4j4-6wv8).
CAPABILITY_PATH = "/functions/v1/my-picks"


def _loggable(url: str) -> str:
    """The URL without its query string when that string is the credential."""
    return url.split("?")[0] if CAPABILITY_PATH in url else url


def resolve_curator_urls(rows: list[dict]) -> dict[str, str]:
    """Map each curator row's curator://<user_id> to its my-picks URL.

    The token lives in feed_tokens (RLS: owner-only), never in feeds.url, so a
    curator feed's real URL exists only for the duration of the build. An
    empty result means no token to mint; the caller skips those rows.
    """
    user_ids = [r["curator_user_id"] for r in rows if r.get("curator_user_id")]
    supabase_url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not user_ids or not supabase_url or not service_key:
        return {}

    query_url = (
        f"{supabase_url}/rest/v1/feed_tokens?select=user_id,token&user_id=in.({','.join(user_ids)})"
    )
    req = urllib.request.Request(
        query_url,
        headers={"apikey": service_key, "Authorization": f"Bearer {service_key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=_DB_TIMEOUT_SECONDS) as resp:
            tokens = json.loads(_read_within(resp, _DB_TOTAL_TIMEOUT_SECONDS).decode())
    except (OSError, ValueError) as e:
        print(f"  ⚠️  Failed to query feed tokens: {e}")
        return {}

    return {
        f"{CURATOR_PREFIX}{t['user_id']}": (
            f"{supabase_url}/functions/v1/my-picks?token={t['token']}"
        )
        for t in tokens
    }


@retry(
    retry=retry_if_exception_type(_RateLimited),
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def _download_body(url: str) -> bytes:
    """Download a feed body, retrying with exponential backoff on 429/503."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=_URLLIB_TIMEOUT_SECONDS) as resp:
            return _read_within(resp, _URLLIB_TOTAL_TIMEOUT_SECONDS)
    except urllib.error.HTTPError as e:
        if e.code in (429, 503):
            raise _RateLimited() from e
        raise


def _curl_command(url: str, outfile: Path) -> list[str]:
    """Build the curl fallback command with per-attempt and total time bounds.

    curl has no default overall timeout, so a source that connects and then
    stalls would block the build indefinitely. --max-time bounds each attempt
    and --retry-max-time bounds the whole invocation.
    """
    return [
        "curl",
        "-sL",
        "-A",
        USER_AGENT,
        "--connect-timeout",
        str(_CURL_CONNECT_TIMEOUT_SECONDS),
        "--max-time",
        str(_CURL_MAX_TIME_SECONDS),
        "--retry",
        str(_CURL_RETRIES),
        "--retry-max-time",
        str(_CURL_RETRY_MAX_TIME_SECONDS),
        url,
        "-o",
        str(outfile),
    ]


def fetch_with_curl_fallback(url: str, outfile: Path) -> bool:
    """Download url to outfile, retrying transient 429/503s and falling back to curl.

    Returns True if a non-empty file was written. urllib exposes the HTTP
    status code (so we can detect 429/503 and retry); curl is the fallback
    for CDNs that reject urllib's TLS fingerprint.
    """
    # A failed fetch must not leave a stale file from a prior run behind:
    # the caller treats a non-empty outfile as success.
    outfile.unlink(missing_ok=True)

    try:
        outfile.write_bytes(_download_body(url))
    except Exception:
        # Any urllib failure (rate limit, network error, timeout, HTTP error)
        # falls through to curl. curl's own flags are the primary bound; the
        # subprocess backstop catches a curl that ignores them.
        try:
            subprocess.run(
                _curl_command(url, outfile),
                timeout=_CURL_HARD_TIMEOUT_SECONDS,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            # curl's own --max-time exits 28 having written a partial file;
            # without this the truncated feed counts as a success below.
            print(f"  ⚠️  curl failed (exit {e.returncode}): {_loggable(url)}")
            outfile.unlink(missing_ok=True)
        except subprocess.TimeoutExpired:
            print(f"  ⏱ curl timed out after {_CURL_HARD_TIMEOUT_SECONDS}s: {_loggable(url)}")
            outfile.unlink(missing_ok=True)

    return outfile.exists() and outfile.stat().st_size > 0


def scraper_stems_from_feeds_txt(feeds_file: Path) -> dict[str, str]:
    """Stems of the scraper outputs feeds.txt lists, for the collision preflight."""
    return {
        Path(entry).stem: f"scraper output {entry}"
        for entry in (line.strip() for line in feeds_file.read_text().splitlines())
        if entry.startswith("cities/") and entry.endswith(".ics")
    }


def assert_unique_stems(feed_list, reserved_stems: dict[str, str]) -> None:
    """Refuse to download a feed onto a file another source already writes.

    Each download is slugify(url).ics, so two URLs that differ only in the
    query string overwrite each other on a provider without a slug case, and a
    feed can overwrite a scraper's output (scrapers run first). The loser's
    rows then look stale to the sweep (ADR 0017), so fail the run instead of
    losing a source. The PR-time check in tests/test_feed_slug.py cannot see a
    feed added through Manage Feeds (#240).
    """
    stems: dict[str, str] = dict(reserved_stems)
    for url, name, _fallback_url in feed_list:
        stem = slugify(url)
        if stem in stems:
            raise SystemExit(
                f"slug collision: {name!r} and {stems[stem]!r} both write "
                f"{stem}.ics; give one URL a distinct path or slug case (#240)"
            )
        stems[stem] = name


def download_feeds(city: str, use_feeds_txt: bool = False) -> None:
    """Download every active feed for a city.

    use_feeds_txt forces the feeds.txt inventory even when DB credentials are
    present, which is how a local build keeps its guarded snapshot in charge.
    Curator tokens are still resolved from feed_tokens (read-only) and no
    feed-status write happens on this path.
    """
    output_dir = Path("cities") / city
    output_dir.mkdir(parents=True, exist_ok=True)

    # Try DB first, fall back to feeds.txt
    db_feeds = None if use_feeds_txt else fetch_feeds_from_db(city)
    if db_feeds is not None:
        download_rows = [f for f in db_feeds if f["feed_type"] != "scraper"]
        print(f"  Using feeds table ({len(download_rows)} feeds)")
        feed_list = [(f["url"], f["name"], f.get("fallback_url")) for f in download_rows]
        db_feeds_by_url = {f["url"]: f for f in download_rows}
        curator_urls = resolve_curator_urls(download_rows)
        reserved_stems = {
            Path(f["url"]).stem: f"scraper output {f['url']}"
            for f in db_feeds
            if f["feed_type"] == "scraper"
        }
    else:
        feeds_file = Path("cities") / city / "feeds.txt"
        if not feeds_file.exists():
            print(f"No feeds.txt found for {city}")
            return
        # A tokenized URL copied into feeds.txt is a leaked credential: never
        # fetch it. Curator entries are curator://<user_id>; the token is minted
        # from feed_tokens, so a local build with credentials still resolves
        # them — that lookup only reads.
        entries = list(parse_feeds_txt(feeds_file))
        leaked = [entry for entry in entries if CAPABILITY_PATH in entry[0]]
        feed_list = [entry for entry in entries if CAPABILITY_PATH not in entry[0]]
        db_feeds_by_url = {}
        curator_urls = resolve_curator_urls(
            [
                {"curator_user_id": url[len(CURATOR_PREFIX) :]}
                for url, _name, _fallback in feed_list
                if url.startswith(CURATOR_PREFIX)
            ]
        )
        unresolvable = sum(
            1
            for url, _name, _fallback in feed_list
            if url.startswith(CURATOR_PREFIX) and url not in curator_urls
        )
        reserved_stems = scraper_stems_from_feeds_txt(feeds_file)
        print(f"  Using feeds.txt ({len(feed_list)} feeds)")
        if leaked:
            print(
                f"  ⚠️  {len(leaked)} capability URL(s) in feeds.txt ignored: a "
                f"my-picks token is never fetched from the repo"
            )
        if unresolvable:
            print(
                f"  ⚠️  {unresolvable} curator feed(s) skipped: no feed token available "
                f"(their URL is minted from feed_tokens)"
            )

    assert_unique_stems(feed_list, reserved_stems)

    count = 0
    last_request_at: dict[str, float] = {}
    for url, friendly_name, fallback_url in feed_list:
        filename = slugify(url) + ".ics"
        outfile = output_dir / filename

        # A curator row's URL is minted from feed_tokens; without a token
        # (owner never signed in) there is nothing to fetch.
        fetch_url = curator_urls.get(url, url)
        if url.startswith(CURATOR_PREFIX) and url not in curator_urls:
            print(f"  ⏭️  {friendly_name or filename}: no feed token for this deployment — skipped")
            continue

        # Throttle per-host so rate-limited sources (events.in.gov) aren't
        # hammered, even when their feeds are interleaved with other hosts.
        host = _host_of(fetch_url)
        _wait_for_host(host, last_request_at)

        # Log the in-flight feed before fetching so a hang names its suspect
        # (the workflow sets PYTHONUNBUFFERED so this line reaches the log).
        print(f"  ⬇️  {filename} ({host})")

        ok = fetch_with_curl_fallback(fetch_url, outfile)
        body = outfile.read_text(encoding="utf-8", errors="ignore") if ok else ""
        # A 200 carrying an HTML block page is a failed source, not a quiet
        # one: only a real calendar counts as ran (#233).
        ok = ok and is_calendar_body(body)

        # Report result
        if ok:
            events = body.count("BEGIN:VEVENT")

            # Inject source headers from feeds.txt metadata
            if friendly_name:
                inject_source_headers(outfile, friendly_name, fallback_url)

            record_ran(outfile)

            print(
                f"  ✅ {filename}: {events} events"
                f"{' (source: ' + friendly_name + ')' if friendly_name else ''}"
            )
        else:
            print(f"  ❌ {filename}: empty or failed")

        count += 1

    print(f"Downloaded {count} feeds for {city}")

    # Record every row's source_id: the stem follows from the url, so a feed
    # that failed this run must still map for a later retirement (#232).
    if db_feeds_by_url:
        record_feed_sources(db_feeds_by_url.values())


if __name__ == "__main__":
    argv = sys.argv[1:]
    use_feeds_txt = "--feeds-txt" in argv
    cities = [arg for arg in argv if arg != "--feeds-txt"]
    if len(cities) != 1:
        print(
            "Usage: python scripts/download_feeds.py <city> [--feeds-txt]",
            file=sys.stderr,
        )
        sys.exit(1)
    download_feeds(cities[0], use_feeds_txt=use_feeds_txt)
