#!/usr/bin/env python3
"""
Classify events using Ollama LLM.

Fetches unclassified events from Supabase, classifies via local Ollama,
and updates the category in Supabase. Curator overrides from the
category_overrides table are used as few-shot examples and never overwritten.

Usage:
    python3 scripts/ollama_classify.py --limit 100 --city santarosa
    python3 scripts/ollama_classify.py --limit 50 --city santarosa --model llama3.2:3b
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.parse

SUPABASE_URL = "https://dzpdualvwspgqghrysyz.supabase.co"
SUPABASE_KEY = "sb_publishable_NnzobdoFNU39fjs84UNq8Q_X45oiMG5"
OLLAMA_URL = "http://localhost:11434"

CATEGORIES_FILE = os.path.join(os.path.dirname(__file__), '..', 'categories.json')
with open(CATEGORIES_FILE) as f:
    CATEGORIES = [c['name'] for c in json.load(f)]

VALID_CATEGORIES = set(CATEGORIES)


def supabase_get(path):
    """GET from Supabase REST API."""
    url = SUPABASE_URL + "/rest/v1/" + path
    req = urllib.request.Request(url, headers={
        "apikey": SUPABASE_KEY,
        "Authorization": "Bearer " + SUPABASE_KEY,
    })
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def supabase_patch(path, data):
    """PATCH to Supabase REST API."""
    url = SUPABASE_URL + "/rest/v1/" + path
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, method="PATCH", headers={
        "apikey": SUPABASE_KEY,
        "Authorization": "Bearer " + SUPABASE_KEY,
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    })
    with urllib.request.urlopen(req) as resp:
        return resp.status


def batch_update_categories(updates):
    """Batch update categories via psql (service role).
    updates is a list of (event_id, category) tuples."""
    if not updates:
        return
    import subprocess
    import os
    conn = os.environ.get("SUPABASE_DB_URL")
    if not conn:
        print("ERROR: SUPABASE_DB_URL env var not set", file=sys.stderr)
        print("Set it or use --dry-run", file=sys.stderr)
        return
    # Build a single SQL statement with CASE
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
        # Table may not exist yet
        return []


def build_few_shot(overrides):
    """Build few-shot examples string from curator overrides."""
    if not overrides:
        return ""
    lines = ["\nHere are examples of how the curator has classified similar events:"]
    for o in overrides[:20]:  # limit to 20 examples
        ev = o.get("events", {})
        if not ev:
            continue
        title = ev.get("title", "")
        location = ev.get("location", "")
        cat = o.get("category", "")
        lines.append(f'  Title: "{title}" Location: "{location}" → {cat}')
    return "\n".join(lines) if len(lines) > 1 else ""


def classify_one(event, few_shot, model):
    """Classify a single event via Ollama."""
    title = event.get("title", "")
    location = event.get("location", "")
    description = (event.get("description") or "")[:500]
    ics_cats = event.get("ics_categories")

    ics_line = ""
    if ics_cats:
        if isinstance(ics_cats, list):
            ics_line = f"\nThe event's ICS feed tagged it as: {', '.join(ics_cats)}\nWeigh the ICS tags heavily but use your judgment — they can be wrong."
        elif isinstance(ics_cats, str):
            ics_line = f"\nThe event's ICS feed tagged it as: {ics_cats}\nWeigh the ICS tags heavily but use your judgment — they can be wrong."

    prompt = f"""Classify this event into exactly one category. Categories:
{chr(10).join('- ' + c for c in CATEGORIES)}
{few_shot}
{ics_line}

Title: {title}
Location: {location}
Description: {description}

Respond with ONLY the category name, nothing else. If none fit, respond with "null"."""

    body = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1},
    }).encode()

    req = urllib.request.Request(
        OLLAMA_URL + "/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read())

    raw = result.get("response", "").strip()
    # Clean up: model may add quotes, periods, etc.
    cleaned = raw.strip('"\'.\n ')
    if cleaned in VALID_CATEGORIES:
        return cleaned
    # Try partial match
    for cat in CATEGORIES:
        if cat.lower() in cleaned.lower():
            return cat
    if cleaned.lower() == "null" or cleaned.lower() == "none":
        return None
    print(f"  WARNING: unexpected response '{raw}', skipping", file=sys.stderr)
    return None


def main():
    parser = argparse.ArgumentParser(description="Classify events via Ollama")
    parser.add_argument("--limit", type=int, default=100, help="Number of events to classify")
    parser.add_argument("--city", default="santarosa", help="City to classify")
    parser.add_argument("--model", default="llama3.2:3b", help="Ollama model to use")
    parser.add_argument("--dry-run", action="store_true", help="Print results without updating DB")
    args = parser.parse_args()

    # Check Ollama is running
    try:
        req = urllib.request.Request(OLLAMA_URL + "/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            pass
    except Exception as e:
        print(f"ERROR: Cannot connect to Ollama at {OLLAMA_URL}: {e}", file=sys.stderr)
        print("Start it with: ollama serve", file=sys.stderr)
        sys.exit(1)

    # Fetch overrides for few-shot examples
    overrides = fetch_overrides(args.city)
    few_shot = build_few_shot(overrides)
    if overrides:
        print(f"Using {len(overrides)} curator overrides as few-shot examples")

    # Fetch unclassified events
    path = (
        "events?select=id,title,location,description,ics_categories,category,source"
        "&category=is.null"
        "&city=eq." + urllib.parse.quote(args.city) +
        "&order=start_time.asc"
        "&limit=" + str(args.limit)
    )
    events = supabase_get(path)
    print(f"Fetched {len(events)} unclassified events from {args.city}")

    if not events:
        print("Nothing to classify.")
        return

    # Classify each event
    results = []
    updates = []
    for i, event in enumerate(events):
        title = event.get("title", "")[:60]
        print(f"  [{i+1}/{len(events)}] {title}...", end=" ", flush=True)
        category = classify_one(event, few_shot, args.model)
        print(f"→ {category or '(none)'}")
        results.append((event, category))
        if category:
            updates.append((event["id"], category))

    # Batch update DB unless dry-run
    if not args.dry_run and updates:
        batch_update_categories(updates)

    # Summary
    print("\n--- Summary ---")
    from collections import Counter
    cats = Counter(cat for _, cat in results)
    for cat, count in cats.most_common():
        print(f"  {count:4d}  {cat or '(none)'}")

    # Show ICS comparison where available
    ics_events = [(e, c) for e, c in results if e.get("ics_categories")]
    if ics_events:
        print(f"\n--- ICS tag comparison ({len(ics_events)} events) ---")
        for event, category in ics_events:
            ics = event["ics_categories"]
            if isinstance(ics, list):
                ics = ", ".join(ics)
            title = event.get("title", "")[:50]
            print(f"  {title}")
            print(f"    ICS: {ics}")
            print(f"    LLM: {category or '(none)'}")


if __name__ == "__main__":
    main()
