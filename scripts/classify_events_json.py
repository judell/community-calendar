#!/usr/bin/env python3
"""
Classify events in events.json files using the Anthropic API (Claude Haiku).

Reads events.json, classifies events missing a category, writes back with
categories added. Designed to run during the build pipeline before publishing.

Curator overrides from Supabase are used as few-shot examples when available.

Usage:
    python3 scripts/classify_events_json.py cities/toronto/events.json
    python3 scripts/classify_events_json.py cities/*/events.json
    python3 scripts/classify_events_json.py cities/toronto/events.json --dry-run
"""

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    print("Set SUPABASE_URL and SUPABASE_KEY environment variables")
    sys.exit(1)

CATEGORIES_FILE = os.path.join(os.path.dirname(__file__), '..', 'categories.json')
with open(CATEGORIES_FILE) as f:
    CATEGORIES = [c['name'] for c in json.load(f)]

VALID_CATEGORIES = set(CATEGORIES)
BATCH_SIZE = 50


def anthropic_call(api_key, model, prompt):
    """Call Anthropic Messages API."""
    body = json.dumps({
        "model": model,
        "max_tokens": 4096,
        "temperature": 0,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    req = urllib.request.Request(ANTHROPIC_API_URL, data=body, headers={
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        print(f"API error {e.code}: {error_body}", file=sys.stderr)
        raise
    return result["content"][0]["text"].strip()


def fetch_overrides():
    """Fetch curator overrides from Supabase as few-shot examples."""
    path = "category_overrides?select=category,events(title,location,description)"
    url = SUPABASE_URL + "/rest/v1/" + path
    req = urllib.request.Request(url, headers={
        "apikey": SUPABASE_KEY,
        "Authorization": "Bearer " + SUPABASE_KEY,
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
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


def classify_batch(events, few_shot, api_key, model):
    """Classify a batch of events. Returns dict mapping index to category."""
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

Respond with ONLY a JSON array. Each element must have "index" (1-based) and "category" (exact category name from the list, or null if none fit). Example: [{{"index": 1, "category": "Music / Concerts"}}, {{"index": 2, "category": null}}]"""

    raw = anthropic_call(api_key, model, prompt)

    start = raw.find("[")
    end = raw.rfind("]") + 1
    if start < 0 or end <= 0:
        print(f"  WARNING: no JSON array in response: {raw[:200]}", file=sys.stderr)
        return {}

    try:
        items = json.loads(raw[start:end])
    except json.JSONDecodeError as exc:
        print(f"  WARNING: JSON parse error: {exc}", file=sys.stderr)
        return {}

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

    return result_map


def process_file(filepath, api_key, model, few_shot, dry_run=False):
    """Classify events in a single events.json file."""
    path = Path(filepath)
    if not path.exists():
        print(f"  Skipping {filepath}: not found")
        return

    with open(path) as f:
        events = json.load(f)

    # Find events needing classification
    to_classify = [(i, e) for i, e in enumerate(events) if not e.get("category")]
    already = len(events) - len(to_classify)

    city = path.parent.name
    print(f"{city}: {len(events)} events, {already} already classified, {len(to_classify)} to classify")

    if not to_classify:
        return

    # Group by title to avoid re-classifying recurring event instances
    from collections import Counter, defaultdict
    title_groups = defaultdict(list)
    for idx, event in to_classify:
        title_key = (event.get("title") or "").strip().lower()
        title_groups[title_key].append((idx, event))

    # Pick one representative per title group
    representative_items = [(group[0][0], group[0][1]) for group in title_groups.values()]
    if len(representative_items) < len(to_classify):
        print(f"  {len(representative_items)} unique titles (deduplicated from {len(to_classify)} events)")

    # Classify in batches (using representatives only)
    classified = 0
    cats = Counter()
    rep_results = {}  # maps representative index to category

    for batch_start in range(0, len(representative_items), BATCH_SIZE):
        batch_items = representative_items[batch_start:batch_start + BATCH_SIZE]
        batch_events = [e for _, e in batch_items]
        batch_num = batch_start // BATCH_SIZE + 1
        total_batches = (len(representative_items) + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"  Batch {batch_num}/{total_batches} ({len(batch_events)} events)...", flush=True)

        result_map = classify_batch(batch_events, few_shot, api_key, model)

        for j, (orig_idx, event) in enumerate(batch_items):
            cat = result_map.get(j + 1)
            if cat:
                title_key = (event.get("title") or "").strip().lower()
                rep_results[title_key] = cat

    # Fan out classifications to all events sharing each title
    for title_key, group in title_groups.items():
        cat = rep_results.get(title_key)
        if cat:
            for orig_idx, event in group:
                events[orig_idx]["category"] = cat
                classified += 1
                cats[cat] += 1

    print(f"  Classified {classified}/{len(to_classify)} events ({len(representative_items)} unique titles)")
    for cat, count in cats.most_common():
        print(f"    {count:4d}  {cat}")

    if not dry_run:
        with open(path, 'w') as f:
            json.dump(events, f, ensure_ascii=False)
        print(f"  Wrote {filepath}")


def main():
    parser = argparse.ArgumentParser(description="Classify events in JSON files via Claude")
    parser.add_argument("files", nargs="+", help="events.json files to classify")
    parser.add_argument("--model", default="claude-haiku-4-5-20251001", help="Anthropic model")
    parser.add_argument("--dry-run", action="store_true", help="Print results without writing")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY env var not set", file=sys.stderr)
        sys.exit(1)

    overrides = fetch_overrides()
    few_shot = build_few_shot(overrides)
    if overrides:
        print(f"Using {len(overrides)} curator overrides as few-shot examples")

    for filepath in args.files:
        process_file(filepath, api_key, args.model, few_shot, args.dry_run)


if __name__ == "__main__":
    main()
