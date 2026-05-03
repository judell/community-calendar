#!/usr/bin/env python3
"""Process pending_feeds.txt for a city: insert into the feeds table, then reset to template.

Contributors add ICS feed URLs to cities/<city>/pending_feeds.txt in their PRs.
After merging, the build runs this script to move them into the database.

Format of pending_feeds.txt:

    # Display Name
    https://example.com/events/?ical=1

Usage:
    SUPABASE_URL=... SUPABASE_SERVICE_KEY=... python scripts/process_pending_feeds.py <city>
    SUPABASE_URL=... SUPABASE_SERVICE_KEY=... python scripts/process_pending_feeds.py --all
"""

import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).parent.parent


def parse_pending_feeds(path):
    """Parse pending_feeds.txt into a list of feed dicts."""
    feeds = []
    with open(path) as f:
        lines = f.readlines()

    name = None
    scraper_cmd = None

    for line in lines:
        line = line.rstrip("\n")
        stripped = line.strip()

        if not stripped:
            continue

        # Comment line
        if stripped.startswith("#"):
            comment = stripped[1:].strip()
            if comment.startswith("cmd:"):
                scraper_cmd = comment[4:].strip()
            elif comment and not comment.startswith("Format:") and not comment.startswith("---"):
                name = comment
            continue

        # URL or path line
        url = stripped
        if url.startswith("https://") or url.startswith("http://"):
            feed_type = "ics_url"
        elif url.startswith("cities/") or url.endswith(".ics"):
            feed_type = "scraper"
        else:
            continue

        feeds.append({
            "name": name or url,
            "url": url,
            "feed_type": feed_type,
            "scraper_cmd": scraper_cmd,
        })
        name = None
        scraper_cmd = None

    return feeds


def insert_feeds(city, feeds, supabase_url, service_key):
    """Insert feeds into the feeds table. Returns (inserted, skipped, errors)."""
    inserted = 0
    skipped = 0
    errors = 0

    for feed in feeds:
        status = "active" if feed["feed_type"] == "scraper" else "pending"
        row = {
            "city": city,
            "url": feed["url"],
            "name": feed["name"],
            "feed_type": feed["feed_type"],
            "status": status,
        }
        if feed["scraper_cmd"]:
            row["scraper_cmd"] = feed["scraper_cmd"]

        data = json.dumps(row).encode()
        req = urllib.request.Request(
            f"{supabase_url}/rest/v1/feeds",
            data=data,
            headers={
                "apikey": service_key,
                "Authorization": f"Bearer {service_key}",
                "Content-Type": "application/json",
                "Prefer": "resolution=ignore-duplicates,return=minimal",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req) as resp:
                if resp.status == 201:
                    inserted += 1
                    print(f"  + {feed['name']}")
                else:
                    skipped += 1
                    print(f"  = {feed['name']} (already exists)")
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            if "duplicate" in body.lower() or e.code == 409:
                skipped += 1
                print(f"  = {feed['name']} (already exists)")
            else:
                errors += 1
                print(f"  ! {feed['name']}: {e.code} {body}")

    return inserted, skipped, errors


TEMPLATE = """\
# Add feed URLs or scraper outputs here.
#
# Pipeline: On each build, process_pending_feeds.py reads this file,
# inserts rows into the Supabase `feeds` table, then resets this file
# to the template below. export_feeds_txt.py then regenerates feeds.txt
# from the DB. Do not edit feeds.txt manually.
#
# The "# Source Name" comment becomes the display name in the calendar
# (user-visible source attribution under each event card). Use the bare
# canonical venue/source name only — no parenthetical context, no event
# counts, no strategy notes. Put verification/discovery notes in
# SOURCES_CHECKLIST.md, not here.
#
# --- ICS feed URLs ---
# Just add the name and URL. The build handles everything else.
#
#   # Source Name
#   https://example.com/events/?ical=1
#
# --- Scrapers ---
# Add the name, cmd, and output path here. But scrapers ALSO need a
# line added to .github/workflows/generate-calendar.yml (in the city's
# scrape step). This file only handles the DB insert; the workflow
# entry is what actually runs the scraper.
#
#   # Source Name
#   # cmd: python scrapers/example.py --name "Source Name"
#   cities/{city}/example.ics
#
# Test before adding:
#   python scripts/add_feed.py URL {city} "Source Name" --test
#   python scripts/add_scraper.py example {city} "Source Name" --test
#
# See CONTRIBUTING.md for details.
"""


def write_template(path, city):
    """Reset pending_feeds.txt to the template."""
    with open(path, "w") as f:
        f.write(TEMPLATE.replace("{city}", city))


def process_city(city, supabase_url, service_key):
    """Process pending_feeds.txt for one city. Returns True if any were processed."""
    pending_path = ROOT / "cities" / city / "pending_feeds.txt"
    if not pending_path.exists():
        return False

    feeds = parse_pending_feeds(pending_path)
    if not feeds:
        print(f"{city}: pending_feeds.txt has no feeds")
        return False

    print(f"{city}: {len(feeds)} pending feed(s)")
    inserted, skipped, errors = insert_feeds(city, feeds, supabase_url, service_key)
    print(f"  {inserted} inserted, {skipped} skipped, {errors} errors")

    if errors == 0:
        write_template(pending_path, city)
        print(f"  reset pending_feeds.txt to template")
    else:
        print(f"  pending_feeds.txt NOT cleared (errors occurred)")

    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: SUPABASE_URL=... SUPABASE_SERVICE_KEY=... python scripts/process_pending_feeds.py <city>")
        print("       SUPABASE_URL=... SUPABASE_SERVICE_KEY=... python scripts/process_pending_feeds.py --all")
        sys.exit(1)

    supabase_url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not supabase_url or not service_key:
        print("Set SUPABASE_URL and SUPABASE_SERVICE_KEY")
        sys.exit(1)

    if sys.argv[1] == "--all":
        cities_dir = ROOT / "cities"
        any_processed = False
        for city_dir in sorted(cities_dir.iterdir()):
            if city_dir.is_dir() and (city_dir / "pending_feeds.txt").exists():
                any_processed = True
                process_city(city_dir.name, supabase_url, service_key)
        if not any_processed:
            print("No pending_feeds.txt files found")
    else:
        city = sys.argv[1]
        if not process_city(city, supabase_url, service_key):
            print(f"No pending_feeds.txt for {city}")


if __name__ == "__main__":
    main()
