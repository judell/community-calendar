#!/usr/bin/env python3
"""
Classify events using the Anthropic API (Claude Haiku).

Fetches unclassified events from Supabase, classifies via Claude in batches,
and updates the category in Supabase. Curator overrides from the
category_overrides table are used as few-shot examples and never overwritten.

No external dependencies — uses urllib only (same as ollama_classify.py).

Usage:
    python3 scripts/classify_events_anthropic.py --limit 500
    python3 scripts/classify_events_anthropic.py --limit 50 --city santarosa --dry-run
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timezone

SUPABASE_URL = "https://dzpdualvwspgqghrysyz.supabase.co"
SUPABASE_KEY = "sb_publishable_NnzobdoFNU39fjs84UNq8Q_X45oiMG5"
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

CATEGORIES_FILE = os.path.join(os.path.dirname(__file__), '..', 'categories.json')
with open(CATEGORIES_FILE) as f:
    CATEGORIES = [c['name'] for c in json.load(f)]

VALID_CATEGORIES = set(CATEGORIES)
BATCH_SIZE = 20


def supabase_get(path):
    """GET from Supabase REST API."""
    url = SUPABASE_URL + "/rest/v1/" + path
    req = urllib.request.Request(url, headers={
        "apikey": SUPABASE_KEY,
        "Authorization": "Bearer " + SUPABASE_KEY,
    })
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def batch_update_categories(updates):
    """Batch update categories via psql (service role).
    updates is a list of (event_id, category) tuples."""
    if not updates:
        return
    import subprocess
    conn = os.environ.get("SUPABASE_DB_URL")
    if not conn:
        print("ERROR: SUPABASE_DB_URL env var not set", file=sys.stderr)
        print("Set it or use --dry-run", file=sys.stderr)
        return
    cases = []
    ids = []
    for event_id, category in updates:
        escaped = category.replace("'", "''")
        cases.append(f"WHEN {event_id} THEN '{escaped}'")
        ids.append(str(event_id))
    sql = f"UPDATE events SET category = CASE id {' '.join(cases)} END WHERE id IN ({','.join(ids)});"
    result = subprocess.run(["psql", conn, "-c", sql], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  DB update error: {result.stderr}", file=sys.stderr)
    else:
        print(f"  Updated {len(updates)} events in DB")


def fetch_overrides(city=None):
    """Fetch curator overrides as few-shot examples."""
    path = "category_overrides?select=category,events(title,location,description)"
    if city:
        path += "&events.city=eq." + urllib.parse.quote(city)
    try:
        return supabase_get(path)
    except Exception:
        return []


def build_few_shot(overrides):
    """Build few-shot examples string from curator overrides."""
    if not overrides:
        return ""
    lines = ["\nHere are examples of how the curator has classified similar events:"]
    for o in overrides[:20]:
        ev = o.get("events", {})
        if not ev:
            continue
        title = ev.get("title", "")
        location = ev.get("location", "")
        cat = o.get("category", "")
        lines.append(f'  Title: "{title}" Location: "{location}" → {cat}')
    return "\n".join(lines) if len(lines) > 1 else ""


def anthropic_call(api_key, model, prompt):
    """Call Anthropic Messages API via urllib."""
    body = json.dumps({
        "model": model,
        "max_tokens": 1024,
        "temperature": 0,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    req = urllib.request.Request(ANTHROPIC_API_URL, data=body, headers={
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read())
    return result["content"][0]["text"].strip()


def classify_batch(events, few_shot, api_key, model):
    """Classify a batch of events via Anthropic API. Returns list of (event, category)."""
    event_lines = []
    for i, event in enumerate(events):
        title = event.get("title", "")
        location = event.get("location", "")
        description = (event.get("description") or "")[:300]
        ics_cats = event.get("ics_categories")
        ics_str = ""
        if ics_cats:
            if isinstance(ics_cats, list):
                ics_str = ", ".join(ics_cats)
            else:
                ics_str = str(ics_cats)
        event_lines.append(
            f'{i+1}. Title: "{title}" Location: "{location}"'
            + (f' ICS tags: "{ics_str}"' if ics_str else '')
            + (f' Description: "{description}"' if description else '')
        )

    prompt = f"""Classify each event into exactly one category. Categories:
{chr(10).join('- ' + c for c in CATEGORIES)}
{few_shot}

Events to classify:

{chr(10).join(event_lines)}

Respond with ONLY a JSON array. Each element must have "index" (1-based) and "category" (exact category name from the list, or null if none fit). Example: [{{"index": 1, "category": "Music & Concerts"}}, {{"index": 2, "category": null}}]"""

    raw = anthropic_call(api_key, model, prompt)

    # Extract JSON array from response
    start = raw.find("[")
    end = raw.rfind("]") + 1
    if start < 0 or end <= 0:
        print(f"  WARNING: no JSON array in response: {raw[:200]}", file=sys.stderr)
        return [(e, None) for e in events]

    try:
        items = json.loads(raw[start:end])
    except json.JSONDecodeError as exc:
        print(f"  WARNING: JSON parse error: {exc}", file=sys.stderr)
        return [(e, None) for e in events]

    # Map results back to events
    result_map = {}
    for item in items:
        idx = item.get("index")
        cat = item.get("category")
        if cat and cat in VALID_CATEGORIES:
            result_map[idx] = cat
        elif cat:
            for valid_cat in CATEGORIES:
                if valid_cat.lower() in str(cat).lower():
                    result_map[idx] = valid_cat
                    break

    results = []
    for i, event in enumerate(events):
        results.append((event, result_map.get(i + 1)))
    return results


def main():
    parser = argparse.ArgumentParser(description="Classify events via Anthropic API")
    parser.add_argument("--limit", type=int, default=500, help="Max events to classify")
    parser.add_argument("--city", default=None, help="City to classify (default: all cities)")
    parser.add_argument("--model", default="claude-haiku-4-5-20251001", help="Anthropic model")
    parser.add_argument("--dry-run", action="store_true", help="Print results without updating DB")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY env var not set", file=sys.stderr)
        sys.exit(1)

    # Fetch overrides for few-shot examples
    overrides = fetch_overrides(args.city)
    few_shot = build_few_shot(overrides)
    if overrides:
        print(f"Using {len(overrides)} curator overrides as few-shot examples")

    # Fetch unclassified events
    today = datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00Z")
    path = (
        "events?select=id,title,location,description,ics_categories,category,source"
        "&category=is.null"
        "&start_time=gte." + today +
        "&order=start_time.asc"
        "&limit=" + str(args.limit)
    )
    if args.city:
        path += "&city=eq." + urllib.parse.quote(args.city)
    events = supabase_get(path)
    city_label = args.city or "all cities"
    print(f"Fetched {len(events)} unclassified events from {city_label}")

    if not events:
        print("Nothing to classify.")
        return

    # Classify in batches
    all_results = []
    all_updates = []
    for batch_start in range(0, len(events), BATCH_SIZE):
        batch = events[batch_start:batch_start + BATCH_SIZE]
        batch_num = batch_start // BATCH_SIZE + 1
        total_batches = (len(events) + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"  Batch {batch_num}/{total_batches} ({len(batch)} events)...", flush=True)

        results = classify_batch(batch, few_shot, api_key, args.model)
        for event, category in results:
            title = event.get("title", "")[:60]
            print(f"    {title} → {category or '(none)'}")
            all_results.append((event, category))
            if category:
                all_updates.append((event["id"], category))

    # Batch update DB unless dry-run
    if not args.dry_run and all_updates:
        batch_update_categories(all_updates)
    elif args.dry_run:
        print(f"\n  DRY RUN: would update {len(all_updates)} events")

    # Summary
    print("\n--- Summary ---")
    from collections import Counter
    cats = Counter(cat for _, cat in all_results)
    for cat, count in cats.most_common():
        print(f"  {count:4d}  {cat or '(none)'}")


if __name__ == "__main__":
    main()
