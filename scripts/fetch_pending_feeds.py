#!/usr/bin/env python3
"""Sync pending_feeds table with feeds.txt.

Usage: python scripts/fetch_pending_feeds.py <city>

Two passes:
  1. Pending: queries status='pending', appends to feeds.txt, marks 'active'
  2. Removed: queries status='removed', removes from feeds.txt, deletes row

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

    # Remove feeds marked as 'removed'
    remove_url = (
        f"{supabase_url}/rest/v1/pending_feeds"
        f"?select=id,url,name"
        f"&city=eq.{city}"
        f"&status=eq.removed"
    )
    req = urllib.request.Request(remove_url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            removed_feeds = json.loads(resp.read().decode())
    except urllib.error.URLError as e:
        print(f"  ⚠️  Failed to query removed feeds: {e}")
        return

    if not removed_feeds:
        return

    # Read feeds.txt and remove matching entries by name
    # Entry formats:
    #   # Name\n https://...\n                    (live feed)
    #   # Name\n # cmd: ...\n cities/x/y.ics\n   (scraper)
    if os.path.exists(feeds_file):
        removed_names = {f["name"] for f in removed_feeds}
        lines = open(feeds_file).readlines()
        new_lines = []
        i = 0
        while i < len(lines):
            stripped = lines[i].strip()
            if (stripped.startswith('#')
                and not stripped.startswith('# ---')
                and not stripped.startswith('# cmd:')):
                name = stripped.lstrip('# ').split(' | ')[0].strip()
                if name in removed_names:
                    # Skip this line plus subsequent cmd/url/file lines
                    i += 1
                    while i < len(lines):
                        s = lines[i].strip()
                        if s.startswith('# cmd:') or s.startswith('https://') or s.startswith('cities/'):
                            i += 1
                        else:
                            break
                    continue
            new_lines.append(lines[i])
            i += 1
        with open(feeds_file, 'w') as f:
            f.writelines(new_lines)

    for feed in removed_feeds:
        feed_id = feed["id"]
        name = feed["name"]
        # Delete the row now that feeds.txt is cleaned up
        del_url = (
            f"{supabase_url}/rest/v1/pending_feeds"
            f"?id=eq.{feed_id}"
        )
        del_req = urllib.request.Request(
            del_url,
            headers={**headers, "Prefer": "return=minimal"},
            method="DELETE",
        )
        try:
            urllib.request.urlopen(del_req)
            print(f"  🗑️  Removed from feeds.txt and DB: {name}")
        except urllib.error.URLError as e:
            print(f"  ⚠️  Failed to delete removed feed: {name}: {e}")

    print(f"  Removed {len(removed_feeds)} feed(s) for {city}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/fetch_pending_feeds.py <city>", file=sys.stderr)
        sys.exit(1)
    fetch_pending_feeds(sys.argv[1])
