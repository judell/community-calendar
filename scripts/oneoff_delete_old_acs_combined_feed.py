#!/usr/bin/env python3
"""One-off cleanup for PR #72 (Asheville: split ACS into per-school feeds).

PR #71 added a single combined "Asheville City Schools" feed whose URL packs
16 calendar_ids into one request, so every school event was stamped with the
same source name. PR #72 replaces it with 12 per-school feeds (added via
cities/asheville/pending_feeds.txt, inserted into the `feeds` table by
scripts/process_pending_feeds.py on the next build).

That split does NOT remove the old combined feed — the URLs differ, so there
is no unique-constraint collision. Until the old feed is deleted, the old and
new feeds coexist: the same school events dedup-merge and the source line shows
both names (e.g. "Asheville City Schools, Claxton Elementary School").

This script performs the deletion the Manage Feeds dialog would do by hand
(xmlui/components/AddFeedDialog.xmlui): delete the feed's events, then remove
the feeds row via the remove_feed() RPC. It is idempotent — if the combined
feed is already gone it exits cleanly.

Identifying the old feed: the new district feed shares the name
"Asheville City Schools", so name alone is ambiguous. The old combined feed is
the only Asheville feed whose URL contains more than 6 calendar_ids (the
combined feed has 16; every per-school feed has <= 3), so we select on that.

Run AFTER the split feeds are live (i.e. after a build has processed
pending_feeds.txt), so the per-school events are already present when the old
combined events are removed. Any events also served by the new district feed
(source name "Asheville City Schools") are re-created on the next build.

Usage:
    SUPABASE_URL=... SUPABASE_SERVICE_KEY=... \
        python scripts/oneoff_delete_old_acs_combined_feed.py [--dry-run]
"""

import json
import os
import sys
import urllib.parse
import urllib.request
import urllib.error

CITY = "asheville"
FEED_NAME = "Asheville City Schools"
MIN_COMBINED_IDS = 7  # combined feed has 16; per-school feeds have <= 3


def request(url, service_key, method="GET", body=None, prefer=None):
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        raw = resp.read().decode()
        return resp.status, (json.loads(raw) if raw.strip() else None)


def main():
    dry_run = "--dry-run" in sys.argv
    supabase_url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not supabase_url or not service_key:
        print("ERROR: set SUPABASE_URL and SUPABASE_SERVICE_KEY", file=sys.stderr)
        return 1
    supabase_url = supabase_url.rstrip("/")

    # Find the Asheville "Asheville City Schools" feeds and pick the combined one.
    q = urllib.parse.urlencode({
        "city": f"eq.{CITY}",
        "name": f"eq.{FEED_NAME}",
        "select": "id,name,url,status",
    })
    _, feeds = request(f"{supabase_url}/rest/v1/feeds?{q}", service_key)
    feeds = feeds or []

    combined = [f for f in feeds if f["url"].count("calendar_ids") >= MIN_COMBINED_IDS]
    if not combined:
        print(f"No combined '{FEED_NAME}' feed found for {CITY} — already cleaned up.")
        return 0
    if len(combined) > 1:
        print("ERROR: more than one combined feed matched; aborting for safety:",
              file=sys.stderr)
        for f in combined:
            print(f"  id={f['id']} url={f['url']}", file=sys.stderr)
        return 1

    feed = combined[0]
    n_ids = feed["url"].count("calendar_ids")
    print(f"Combined feed: id={feed['id']} status={feed['status']} "
          f"({n_ids} calendar_ids)")

    if dry_run:
        print("--dry-run: would delete its events (source="
              f"'{FEED_NAME}', city='{CITY}') and remove feed id={feed['id']}")
        return 0

    # 1. Delete its events by source + city (same as the Manage Feeds dialog).
    eq = urllib.parse.urlencode({
        "source": f"eq.{FEED_NAME}",
        "city": f"eq.{CITY}",
    })
    status, _ = request(f"{supabase_url}/rest/v1/events?{eq}", service_key,
                        method="DELETE", prefer="return=minimal")
    print(f"Deleted events (source='{FEED_NAME}', city='{CITY}') — HTTP {status}")

    # 2. Remove the feeds row via the SECURITY DEFINER RPC.
    status, _ = request(f"{supabase_url}/rest/v1/rpc/remove_feed", service_key,
                        method="POST", body={"feed_id": feed["id"]},
                        prefer="return=minimal")
    print(f"remove_feed(feed_id={feed['id']}) — HTTP {status}")
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
