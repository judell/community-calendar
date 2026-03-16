#!/usr/bin/env python3
"""Download all live ICS feeds listed in a city's feeds.txt.

Usage: python scripts/download_feeds.py <city>

Reads cities/<city>/feeds.txt, downloads each https:// URL to an auto-named
.ics file in cities/<city>/. Parses structured comments above each URL to
get the friendly source name and optional fallback URL, then injects
X-SOURCE (and X-SOURCE-URL) headers into each downloaded VEVENT.

feeds.txt format:
    # Friendly Name | https://fallback-url/
    https://actual-feed-url/ical/

    # Friendly Name
    https://another-feed-url/ical/
"""

import os
import re
import subprocess
import sys
from urllib.parse import urlparse


def slugify(url: str) -> str:
    """Generate a readable filename slug from a URL.

    Mirrors the logic in add_feed.py so that add_feed + download_feeds
    produce consistent filenames.
    """
    parsed = urlparse(url)

    # Meetup: extract group slug
    if 'meetup.com' in parsed.netloc:
        match = re.search(r'meetup\.com/([^/]+)', url)
        if match:
            group = match.group(1)
            group = re.sub(r'[^a-zA-Z0-9]+', '_', group).lower().strip('_')
            return f"meetup_{group}"

    # Tockify: extract calendar name
    if 'tockify.com' in parsed.netloc:
        match = re.search(r'/ics/([^/]+)', url)
        if match:
            return f"tockify_{match.group(1)}"

    # Google Calendar: extract calendar ID prefix
    if 'calendar.google.com' in parsed.netloc:
        match = re.search(r'ical/([^%/]+)', url)
        if match:
            cal_id = match.group(1)
            cal_id = re.sub(r'[^a-zA-Z0-9]+', '_', cal_id).lower().strip('_')
            return f"gcal_{cal_id}"

    # LibCal: extract institution and calendar ID
    if 'libcal.com' in parsed.netloc:
        match = re.match(r'([^.]+)\.libcal\.com', parsed.netloc)
        inst = match.group(1) if match else 'libcal'
        cid_match = re.search(r'cid=(\d+)', url)
        cid = f"_{cid_match.group(1)}" if cid_match else ''
        return f"libcal_{inst}{cid}"

    # CampusLabs / beINvolved
    if 'campuslabs.com' in parsed.netloc:
        match = re.match(r'([^.]+)\.campuslabs\.com', parsed.netloc)
        inst = match.group(1) if match else 'campuslabs'
        return f"campuslabs_{inst}"

    # LiveWhale (e.g., events.iu.edu/live/ical/events/group_id/56)
    if '/live/ical/' in parsed.path:
        domain = parsed.netloc.replace('www.', '').split('.')[0]
        gid_match = re.search(r'group_id/(\d+)', url)
        gid = f"_{gid_match.group(1)}" if gid_match else ''
        return f"{domain}_livewhale{gid}"

    # General case: domain + meaningful path parts
    domain = parsed.netloc.replace('www.', '').split('.')[0]
    path_parts = [p for p in parsed.path.split('/')
                  if p and p not in ('events', 'ical', 'feed', 'calendar',
                                     'list', 'public', 'basic.ics')]

    if path_parts:
        slug = f"{domain}_{'_'.join(path_parts[:2])}"
    else:
        slug = domain

    slug = re.sub(r'[^a-zA-Z0-9]+', '_', slug).lower().strip('_')
    return slug[:50]


def parse_feeds_txt(feeds_file: str):
    """Parse feeds.txt, yielding (url, friendly_name, fallback_url) tuples.

    Structured comment format:
        # Friendly Name | https://fallback-url/
        https://feed-url/

    A comment line immediately before a URL line is the metadata for that URL.
    Category headers (comments before blank lines or other comments) are ignored.
    """
    pending_name = None
    pending_fallback = None

    with open(feeds_file) as f:
        for line in f:
            stripped = line.strip()

            if stripped.startswith('#'):
                body = stripped[1:].strip()
                if '|' in body:
                    parts = body.split('|', 1)
                    pending_name = parts[0].strip()
                    pending_fallback = parts[1].strip() or None
                else:
                    pending_name = body
                    pending_fallback = None
                continue

            if not stripped or not stripped.startswith('https://'):
                # Blank line or local file ref resets pending comment
                pending_name = None
                pending_fallback = None
                continue

            yield stripped, pending_name, pending_fallback
            pending_name = None
            pending_fallback = None


def inject_source_headers(filepath: str, friendly_name: str, fallback_url: str | None) -> None:
    """Inject X-SOURCE (and optionally X-SOURCE-URL) into each VEVENT in an ICS file."""
    try:
        with open(filepath, 'rb') as f:
            raw = f.read()
    except Exception:
        return

    if b'BEGIN:VCALENDAR' not in raw:
        return  # Not valid ICS

    # Detect line ending style from raw bytes
    crlf = b'\r\n' if b'\r\n' in raw else b'\n'

    name_bytes = friendly_name.encode('utf-8')
    headers = b'X-SOURCE:' + name_bytes + crlf
    if fallback_url:
        headers += b'X-SOURCE-URL:' + fallback_url.encode('utf-8') + crlf

    marker = b'BEGIN:VEVENT' + crlf
    parts = raw.split(marker)

    result = [parts[0]]
    for part in parts[1:]:
        vevent_head = part.split(b'END:VEVENT')[0]
        if b'X-SOURCE:' not in vevent_head:
            result.append(headers + part)
        else:
            result.append(part)

    with open(filepath, 'wb') as f:
        f.write(marker.join(result))


def download_feeds(city: str) -> None:
    feeds_file = os.path.join("cities", city, "feeds.txt")
    output_dir = os.path.join("cities", city)

    if not os.path.exists(feeds_file):
        print(f"No feeds.txt found for {city}")
        return

    count = 0
    for url, friendly_name, fallback_url in parse_feeds_txt(feeds_file):
        filename = slugify(url) + ".ics"
        outfile = os.path.join(output_dir, filename)

        # Meetup requires User-Agent
        cmd = ["curl", "-sL"]
        if "meetup.com" in url:
            cmd += ["-A", "Mozilla/5.0"]
        cmd += [url, "-o", outfile]

        subprocess.run(cmd)

        # Report result
        if os.path.exists(outfile) and os.path.getsize(outfile) > 0:
            try:
                with open(outfile) as ics:
                    events = ics.read().count("BEGIN:VEVENT")
            except Exception:
                events = 0

            # Inject source headers from feeds.txt metadata
            if friendly_name:
                inject_source_headers(outfile, friendly_name, fallback_url)

            print(f"  ✅ {filename}: {events} events"
                  f"{' (source: ' + friendly_name + ')' if friendly_name else ''}")
        else:
            print(f"  ❌ {filename}: empty or failed")

        count += 1

    print(f"Downloaded {count} feeds for {city}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/download_feeds.py <city>", file=sys.stderr)
        sys.exit(1)
    download_feeds(sys.argv[1])
