#!/usr/bin/env python3
"""Fetch pending feeds from Supabase and append them to feeds.txt.

Usage: python scripts/fetch_pending_feeds.py <city>

Queries the pending_feeds table for feeds with status='pending' for the given city.
For each one:
  1. Appends the entry to cities/<city>/feeds.txt (if not already present)
  2. Updates status to 'active' in the DB

Requires SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables.
"""

import os
import sys
import json
import urllib.request
import urllib.error


def fetch_pending_feeds(city: str) -> None:
    supabase_url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_KEY")

    if not supabase_url or not service_key:
        print("  ⚠️  SUPABASE_URL or SUPABASE_SERVICE_KEY not set, skipping pending feeds")
        return

    # Query pending feeds for this city
    query_url = (
        f"{supabase_url}/rest/v1/pending_feeds"
        f"?select=id,url,name,fallback_url"
        f"&city=eq.{city}"
        f"&status=eq.pending"
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
        print(f"  ⚠️  Failed to query pending_feeds: {e}")
        return

    if not feeds:
        print(f"  No pending feeds for {city}")
        return

    feeds_file = os.path.join("cities", city, "feeds.txt")

    # Read existing URLs to avoid duplicates
    existing_urls = set()
    if os.path.exists(feeds_file):
        with open(feeds_file) as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("https://"):
                    existing_urls.add(stripped)

    appended = 0
    for feed in feeds:
        feed_id = feed["id"]
        url = "".join(feed["url"].split())
        name = feed["name"]
        fallback_url = feed.get("fallback_url")

        # Append to feeds.txt if not already present
        if url not in existing_urls:
            with open(feeds_file, "a") as f:
                comment = f"\n# {name}"
                if fallback_url:
                    comment += f" | {fallback_url}"
                f.write(comment + "\n")
                f.write(url + "\n")
            appended += 1
            print(f"  ✅ Appended to feeds.txt: {name} ({url})")
        else:
            print(f"  ⏭️  Already in feeds.txt: {name}")

        # Mark as active
        patch_url = (
            f"{supabase_url}/rest/v1/pending_feeds"
            f"?id=eq.{feed_id}"
        )
        patch_data = json.dumps({"status": "active"}).encode()
        patch_req = urllib.request.Request(
            patch_url,
            data=patch_data,
            headers={
                **headers,
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            method="PATCH",
        )
        try:
            urllib.request.urlopen(patch_req)
            print(f"  ✅ Marked as active: {name}")
        except urllib.error.URLError as e:
            print(f"  ⚠️  Failed to mark active: {name}: {e}")

    print(f"  Processed {len(feeds)} pending feed(s) for {city} ({appended} new)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/fetch_pending_feeds.py <city>", file=sys.stderr)
        sys.exit(1)
    fetch_pending_feeds(sys.argv[1])
