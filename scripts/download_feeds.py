#!/usr/bin/env python3
"""Download all live ICS feeds listed in a city's feeds.txt.

Usage: python scripts/download_feeds.py <city>

Reads cities/<city>/feeds.txt, downloads each https:// URL to an auto-named
.ics file in cities/<city>/. Skips comments and local file references.
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


def download_feeds(city: str) -> None:
    feeds_file = os.path.join("cities", city, "feeds.txt")
    output_dir = os.path.join("cities", city)

    if not os.path.exists(feeds_file):
        print(f"No feeds.txt found for {city}")
        return

    count = 0
    with open(feeds_file) as f:
        for line in f:
            # Strip comments and whitespace
            line = line.split("#")[0].strip()
            if not line or not line.startswith("https://"):
                continue

            filename = slugify(line) + ".ics"
            outfile = os.path.join(output_dir, filename)

            # Meetup requires User-Agent
            cmd = ["curl", "-sL"]
            if "meetup.com" in line:
                cmd += ["-A", "Mozilla/5.0"]
            cmd += [line, "-o", outfile]

            subprocess.run(cmd)

            # Report result
            if os.path.exists(outfile) and os.path.getsize(outfile) > 0:
                try:
                    with open(outfile) as ics:
                        events = ics.read().count("BEGIN:VEVENT")
                except Exception:
                    events = 0
                print(f"  ✅ {filename}: {events} events")
            else:
                print(f"  ❌ {filename}: empty or failed")

            count += 1

    print(f"Downloaded {count} feeds for {city}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/download_feeds.py <city>", file=sys.stderr)
        sys.exit(1)
    download_feeds(sys.argv[1])
