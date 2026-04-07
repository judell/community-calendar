#!/usr/bin/env python3
"""Download all live ICS feeds for a city.

Usage: python scripts/download_feeds.py <city>

Queries the feeds table in Supabase for active ics_url/curator feeds,
downloads each to an auto-named .ics file in cities/<city>/, and injects
X-SOURCE headers. Falls back to feeds.txt if SUPABASE_URL is not set.
"""

import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.error
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


def fetch_feeds_from_db(city: str):
    """Query the feeds table for active ics_url and curator feeds.
    Returns list of (url, name, fallback_url) tuples, or None if DB not available."""
    supabase_url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not supabase_url or not service_key:
        return None

    query_url = (
        f"{supabase_url}/rest/v1/feeds"
        f"?select=url,name"
        f"&city=eq.{city}"
        f"&status=eq.active"
        f"&feed_type=in.(ics_url,curator)"
        f"&order=name.asc"
    )
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
    }
    req = urllib.request.Request(query_url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            feeds = json.loads(resp.read().decode())
    except urllib.error.URLError as e:
        print(f"  ⚠️  Failed to query feeds table: {e}")
        return None

    return [(f["url"], f["name"], None) for f in feeds]


def download_feeds(city: str) -> None:
    output_dir = os.path.join("cities", city)
    os.makedirs(output_dir, exist_ok=True)

    # Try DB first, fall back to feeds.txt
    feed_list = fetch_feeds_from_db(city)
    if feed_list is not None:
        print(f"  Using feeds table ({len(feed_list)} feeds)")
    else:
        feeds_file = os.path.join("cities", city, "feeds.txt")
        if not os.path.exists(feeds_file):
            print(f"No feeds.txt found for {city}")
            return
        feed_list = list(parse_feeds_txt(feeds_file))
        print(f"  Using feeds.txt ({len(feed_list)} feeds)")

    count = 0
    for url, friendly_name, fallback_url in feed_list:
        filename = slugify(url) + ".ics"
        outfile = os.path.join(output_dir, filename)

        cmd = ["curl", "-sL",
               "-A", "Mozilla/5.0 (compatible; CommunityCalendar/1.0)",
               url, "-o", outfile]

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
