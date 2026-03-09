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


def url_to_filename(url: str) -> str:
    """Convert a URL to a safe filename."""
    name = re.sub(r"https?://", "", url)
    name = re.sub(r"[^a-zA-Z0-9]", "_", name)
    return name[:80] + ".ics"


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

            outfile = os.path.join(output_dir, url_to_filename(line))

            # Meetup requires User-Agent
            cmd = ["curl", "-sL"]
            if "meetup.com" in line:
                cmd += ["-A", "Mozilla/5.0"]
            cmd += [line, "-o", outfile]

            subprocess.run(cmd)

            # Report result
            basename = os.path.basename(outfile)
            if os.path.exists(outfile) and os.path.getsize(outfile) > 0:
                try:
                    with open(outfile) as ics:
                        events = ics.read().count("BEGIN:VEVENT")
                except Exception:
                    events = 0
                print(f"  ✅ {basename}: {events} events")
            else:
                print(f"  ❌ {basename}: empty or failed")

            count += 1

    print(f"Downloaded {count} feeds for {city}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/download_feeds.py <city>", file=sys.stderr)
        sys.exit(1)
    download_feeds(sys.argv[1])
