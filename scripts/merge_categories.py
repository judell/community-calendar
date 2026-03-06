#!/usr/bin/env python3
"""
Carry forward categories from a previous events.json into a freshly generated one.

Matches events by source_uid. Only copies the category field — all other fields
come from the fresh file (which has the latest event data from ICS).

Usage:
    python scripts/merge_categories.py cities/toronto/events.prev.json cities/toronto/events.json
"""

import json
import sys


def main():
    if len(sys.argv) != 3:
        print("Usage: merge_categories.py <prev.json> <current.json>", file=sys.stderr)
        sys.exit(1)

    prev_path, current_path = sys.argv[1], sys.argv[2]

    with open(prev_path) as f:
        prev_events = json.load(f)

    with open(current_path) as f:
        current_events = json.load(f)

    # Build lookup from previous categories
    prev_categories = {}
    for e in prev_events:
        uid = e.get("source_uid")
        cat = e.get("category")
        if uid and cat:
            prev_categories[uid] = cat

    # Apply to current events
    carried = 0
    for e in current_events:
        uid = e.get("source_uid")
        if uid and uid in prev_categories and not e.get("category"):
            e["category"] = prev_categories[uid]
            carried += 1

    with open(current_path, 'w') as f:
        json.dump(current_events, f, ensure_ascii=False)

    total = len(current_events)
    uncategorized = sum(1 for e in current_events if not e.get("category"))
    print(f"  Merged categories: {carried} carried forward, {uncategorized} new (of {total} total)")


if __name__ == "__main__":
    main()
