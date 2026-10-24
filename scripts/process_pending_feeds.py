#!/usr/bin/env python3
"""Process pending_feeds.txt for a city: insert into the feeds table, then reset to template.

Contributors add ICS feed URLs to cities/<city>/pending_feeds.txt in their PRs.
After merging, the build runs this script to move them into the database.

For scraper entries, this script registers source metadata only. It does not
run the scraper. Actual scraper execution still comes from the matching line in
.github/workflows/generate-calendar.yml.

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
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent


def parse_pending_feeds(path: Path):
    """Parse pending_feeds.txt into a list of feed dicts."""
    feeds = []
    with path.open() as f:
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
        if url.startswith(("https://", "http://")):
            feed_type = "ics_url"
        elif url.startswith("cities/") or url.endswith(".ics"):
            feed_type = "scraper"
        else:
            continue

        feeds.append(
            {
                "name": name or url,
                "url": url,
                "feed_type": feed_type,
                "scraper_cmd": scraper_cmd,
            }
        )
        name = None
        scraper_cmd = None

    return feeds


def existing_feed_status(city, url, supabase_url, service_key):
    """Status of the row that made an insert a duplicate, or None.

    A removed row is a tombstone (#240): the unique key keeps that URL from
    returning as a new feed, so the skip must say so rather than read as noise.
    """
    query = urllib.parse.urlencode({"city": f"eq.{city}", "url": f"eq.{url}", "select": "status"})
    req = urllib.request.Request(
        f"{supabase_url}/rest/v1/feeds?{query}",
        headers={"apikey": service_key, "Authorization": f"Bearer {service_key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            rows = json.loads(resp.read().decode())
    except OSError, ValueError:
        return None
    return rows[0].get("status") if isinstance(rows, list) and rows else None


def report_skipped(feed, city, supabase_url, service_key):
    status = existing_feed_status(city, feed["url"], supabase_url, service_key)
    if status == "removed":
        print(
            f"  = {feed['name']} (already exists as removed; re-adding it has no effect — see #240)"
        )
    else:
        print(f"  = {feed['name']} (already exists)")


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
                "Prefer": "resolution=ignore-duplicates,return=representation",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req) as resp:
                # An ignored duplicate returns an empty array, so the body, not
                # the status, says whether the row was inserted.
                created = json.loads(resp.read().decode() or "[]")
            if created:
                inserted += 1
                print(f"  + {feed['name']}")
            else:
                skipped += 1
                report_skipped(feed, city, supabase_url, service_key)
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            if "duplicate" in body.lower() or e.code == 409:
                skipped += 1
                report_skipped(feed, city, supabase_url, service_key)
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
# Think of this file as a temporary inbox for new sources, not as a
# long-term source inventory.
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
# Add the name, cmd, and output path. That is the whole job: the build
# inserts the row into the feeds table (validated at insert time) and
# the DB-first runner executes it in that same build. The workflow is
# never edited. Prefer scripts/add_scraper.py, which tests the exact
# command and writes this entry for you.
#
#   # Source Name
#   # cmd: python scrapers/example.py --name "Source Name" --output cities/{city}/example.ics
#   cities/{city}/example.ics
#
# Validate without registering (--test writes nothing); run without
# --test to validate and register:
#   python scripts/add_feed.py URL {city} "Source Name" --test
#   python scripts/add_scraper.py example {city} "Source Name" --test
#
# See CONTRIBUTING.md for details.
"""


def write_template(path: Path, city):
    """Reset pending_feeds.txt to the template."""
    with path.open("w") as f:
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
        print("  reset pending_feeds.txt to template")
    else:
        print("  pending_feeds.txt NOT cleared (errors occurred)")

    return True


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: SUPABASE_URL=... SUPABASE_SERVICE_KEY=... python scripts/process_pending_feeds.py <city>"
        )
        print(
            "       SUPABASE_URL=... SUPABASE_SERVICE_KEY=... python scripts/process_pending_feeds.py --all"
        )
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
