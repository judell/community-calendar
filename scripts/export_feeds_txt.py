#!/usr/bin/env python3
"""Export feeds table to feeds.txt files for each city.

Usage: SUPABASE_URL=... SUPABASE_SERVICE_KEY=... python scripts/export_feeds_txt.py [city]

Queries the feeds table for active feeds and writes cities/<city>/feeds.txt.
If no city is given, exports all cities.
"""

import json
import os
import sys
import urllib.request
import urllib.error


def export_feeds_txt(city, supabase_url, service_key):
    """Export feeds for a city to feeds.txt."""
    query_url = (
        f"{supabase_url}/rest/v1/feeds"
        f"?select=name,url,feed_type,scraper_cmd"
        f"&city=eq.{city}"
        f"&status=eq.active"
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

    feeds_file = os.path.join("cities", city, "feeds.txt")
    os.makedirs(os.path.dirname(feeds_file), exist_ok=True)

    scrapers = [f for f in feeds if f["feed_type"] == "scraper"]
    ics_urls = [f for f in feeds if f["feed_type"] == "ics_url"]
    curators = [f for f in feeds if f["feed_type"] == "curator"]

    with open(feeds_file, "w") as out:
        out.write(f"# {city.title()} - source inventory\n")
        out.write(f"# Generated from feeds table. Do not edit manually.\n\n")

        if scrapers:
            out.write("# --- Scrapers ---\n")
            for f in scrapers:
                out.write(f"# {f['name']}\n")
                if f.get("scraper_cmd"):
                    out.write(f"# {f['scraper_cmd']}\n")
                out.write(f"{f['url']}\n")
            out.write("\n")

        if ics_urls:
            out.write("# --- Live feeds ---\n")
            for f in ics_urls:
                out.write(f"# {f['name']}\n")
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
        query_url = (
            f"{supabase_url}/rest/v1/feeds"
            f"?select=city"
            f"&status=eq.active"
        )
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
        cities = sorted(set(r["city"] for r in rows))

    for city in cities:
        export_feeds_txt(city, supabase_url, service_key)


if __name__ == "__main__":
    main()
