#!/usr/bin/env python3
"""One-time seed: parse all feeds.txt files and insert into feeds table.

Usage: SUPABASE_URL=... SUPABASE_SERVICE_KEY=... python scripts/seed_feeds_table.py

Parses each cities/*/feeds.txt and inserts rows into the feeds table.
"""

import os
import sys
import re
import json
import urllib.request
import urllib.error
from pathlib import Path


def parse_feeds_txt(feeds_file):
    """Parse feeds.txt into a list of feed dicts."""
    feeds = []
    lines = Path(feeds_file).read_text().splitlines()
    pending_name = None
    pending_cmd = None
    city = Path(feeds_file).parent.name

    for line in lines:
        stripped = line.strip()

        if stripped.startswith('# cmd:'):
            pending_cmd = stripped[2:].strip()  # "cmd: python scrapers/foo.py ..."
            # Extract --name if present
            m = re.search(r'--name\s+"([^"]+)"', stripped)
            if m and not pending_name:
                pending_name = m.group(1)
            continue

        if (stripped.startswith('#')
            and not stripped.startswith('# ---')
            and not stripped.startswith('# cmd:')
            and stripped not in ('# Scraper', '# Squarespace', '# Songkick',
                                 '# Chamber of Commerce')):
            name = stripped.lstrip('# ').split(' | ')[0].strip()
            if name:
                pending_name = name
            continue

        if stripped.startswith('cities/') and stripped.endswith('.ics'):
            # Scraper or static feed
            name = pending_name or Path(stripped).stem.replace('_', ' ').title()
            feeds.append({
                'city': city,
                'url': stripped,
                'name': name,
                'feed_type': 'scraper',
                'scraper_cmd': pending_cmd,
            })
            pending_name = None
            pending_cmd = None
            continue

        if stripped.startswith('https://'):
            name = pending_name or stripped
            # Detect curator feeds
            feed_type = 'curator' if 'my-picks' in stripped else 'ics_url'
            feeds.append({
                'city': city,
                'url': stripped,
                'name': name,
                'feed_type': feed_type,
                'scraper_cmd': None,
            })
            pending_name = None
            pending_cmd = None
            continue

        # Blank line or other — reset
        if not stripped:
            pending_name = None
            pending_cmd = None

    return feeds


def main():
    supabase_url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_KEY")

    if not supabase_url or not service_key:
        print("Set SUPABASE_URL and SUPABASE_SERVICE_KEY")
        sys.exit(1)

    all_feeds = []
    for feeds_file in sorted(Path('cities').glob('*/feeds.txt')):
        feeds = parse_feeds_txt(feeds_file)
        print(f"{feeds_file.parent.name}: {len(feeds)} feeds")
        all_feeds.extend(feeds)

    print(f"\nTotal: {len(all_feeds)} feeds")

    # Insert in batches
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }

    batch_size = 50
    inserted = 0
    for i in range(0, len(all_feeds), batch_size):
        batch = all_feeds[i:i+batch_size]
        body = json.dumps(batch).encode()
        req = urllib.request.Request(
            f"{supabase_url}/rest/v1/feeds",
            data=body,
            headers=headers,
            method="POST",
        )
        try:
            urllib.request.urlopen(req)
            inserted += len(batch)
            print(f"  Inserted {inserted}/{len(all_feeds)}")
        except urllib.error.URLError as e:
            error_body = e.read().decode() if hasattr(e, 'read') else str(e)
            print(f"  Error at batch {i}: {error_body}")
            sys.exit(1)

    print(f"\nDone: {inserted} feeds inserted")


if __name__ == '__main__':
    main()
