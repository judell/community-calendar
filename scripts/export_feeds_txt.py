#!/usr/bin/env python3
"""Export feeds table to feeds.txt files for each city.

Usage: SUPABASE_URL=... SUPABASE_SERVICE_KEY=... python scripts/export_feeds_txt.py [city]

Queries the feeds table for active and pending feeds and writes
cities/<city>/feeds.txt.
If no city is given, exports all cities.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

# A my-picks URL is authenticated by its query-string token alone, and this
# file is committed to a public repo. The DB CHECK forbids such a row; this is
# the last line of defence for a token that predates it (GHSA-3pg8-w4j4-6wv8).
CAPABILITY_PATH = "/functions/v1/my-picks"
# Every field this exporter writes; a token in any of them is published.
EXPORTED_FIELDS = ("url", "name", "scraper_cmd")


def has_capability_url(row: dict) -> bool:
    return any(CAPABILITY_PATH in (row.get(field) or "") for field in EXPORTED_FIELDS)


def export_feeds_txt(city, supabase_url, service_key):
    """Export feeds for a city to feeds.txt."""
    query_url = (
        f"{supabase_url}/rest/v1/feeds"
        f"?select=name,url,feed_type,scraper_cmd"
        f"&city=eq.{city}"
        f"&status=in.(active,pending)"
        f"&order=feed_type.asc,name.asc"
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
        print(f"  ⚠️  Failed to query feeds for {city}: {e}")
        return

    leaked = [f for f in feeds if has_capability_url(f)]
    if leaked:
        # Never echo the row: the token may be in the name or command.
        print(
            f"  ⚠️  {len(leaked)} feed(s) skipped: a my-picks URL is a credential "
            f"and is never written to feeds.txt"
        )
        feeds = [f for f in feeds if not has_capability_url(f)]

    feeds_file = Path("cities") / city / "feeds.txt"
    feeds_file.parent.mkdir(parents=True, exist_ok=True)

    ics_urls = [f for f in feeds if f["feed_type"] == "ics_url"]
    scrapers = [f for f in feeds if f["feed_type"] == "scraper"]
    curators = [f for f in feeds if f["feed_type"] == "curator"]

    with feeds_file.open("w") as out:
        out.write(f"# {city.title()} - source inventory\n")
        out.write("# Generated from feeds table (active + pending). Do not edit manually.\n")
        out.write("# To add feeds, use pending_feeds.txt in this directory.\n\n")

        if ics_urls:
            out.write("# --- Live feeds ---\n")
            for f in ics_urls:
                out.write(f"# {f['name']}\n")
                out.write(f"{f['url']}\n")
            out.write("\n")

        if scrapers:
            out.write("# --- Scrapers ---\n")
            for f in scrapers:
                out.write(f"# {f['name']}\n")
                if f.get("scraper_cmd"):
                    cmd = f["scraper_cmd"]
                    if not cmd.startswith("cmd:"):
                        cmd = f"cmd: {cmd}"
                    out.write(f"# {cmd}\n")
                out.write(f"{f['url']}\n")
            out.write("\n")

        if curators:
            out.write("# --- Curator feeds ---\n")
            for f in curators:
                out.write(f"# {f['name']}\n")
                out.write(f"{f['url']}\n")

    print(f"  {city}: {len(feeds)} feeds → {feeds_file}")


def main():
    supabase_url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_KEY")

    if not supabase_url or not service_key:
        print("Set SUPABASE_URL and SUPABASE_SERVICE_KEY")
        sys.exit(1)

    if len(sys.argv) > 1:
        cities = [sys.argv[1]]
    else:
        # Get all distinct cities from feeds table
        query_url = f"{supabase_url}/rest/v1/feeds?select=city&status=in.(active,pending)"
        headers = {
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
        }
        req = urllib.request.Request(query_url, headers=headers)
        try:
            with urllib.request.urlopen(req) as resp:
                rows = json.loads(resp.read().decode())
        except urllib.error.URLError as e:
            print(f"Failed to query cities: {e}")
            sys.exit(1)
        cities = sorted({r["city"] for r in rows})

    for city in cities:
        export_feeds_txt(city, supabase_url, service_key)


if __name__ == "__main__":
    main()
