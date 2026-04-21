#!/usr/bin/env python3
"""
Classify concierge facets for a deduplicated event slice and upsert them to
public.event_facets.

Theory of operation:
1. Fetch deduplicated rows from public.deduplicated_chat_events.
2. Build a stable test slice, or classify all rows in a given time window.
3. Ask Claude for controlled JSON facets per deduplicated row.
4. Normalize those facets to fixed vocabularies.
5. Expand the facets across every raw event id in merged_ids.
6. Upsert to public.event_facets.

This script is intentionally conservative:
- It classifies deduplicated rows, not every raw row, to reduce cost.
- It writes the same normalized facet set to each merged raw event id.
- It supports dry-run iteration before touching the database.
"""

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Dict, List

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Set SUPABASE_URL and SUPABASE_KEY environment variables", file=sys.stderr)
    sys.exit(1)

if not ANTHROPIC_API_KEY:
    print("Set ANTHROPIC_API_KEY environment variable", file=sys.stderr)
    sys.exit(1)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_EXAMPLES_PATH = os.path.join(
    os.path.dirname(__file__), "..", "docs", "bloomington-concierge-facet-examples.json"
)

CATEGORY_LIMITS = {
    "Music / Concerts": 30,
    "Community / Social": 25,
    "Education / Workshops": 25,
    "Nature / Outdoors / Recreation": 20,
    "Family / Kids": 10,
    "Sports / Fitness": 10,
    "Arts / Culture": 10,
    "Books / Literature / Poetry": 10,
}

PARTICIPATION_MODES = {
    "attend",
    "participate",
    "learn",
    "volunteer",
    "socialize",
    "compete",
}

FORMAT_TAGS = {
    "class",
    "concert",
    "competition",
    "ensemble",
    "event",
    "exhibition",
    "festival",
    "hike",
    "jam",
    "lecture",
    "market",
    "meetup",
    "open_mic",
    "reading",
    "rehearsal",
    "screening",
    "session",
    "social",
    "talk",
    "tour",
    "volunteer_shift",
    "workshop",
}

AUDIENCE_TAGS = {
    "adults",
    "all_ages",
    "beginners",
    "families",
    "kids",
    "parents",
    "seniors",
    "students",
    "teens",
}

COST_TAGS = {
    "free",
    "paid",
    "donation",
    "unknown",
}

PARTICIPATION_SYNONYMS = {
    "watch": "attend",
    "watching": "attend",
    "listen": "attend",
    "listening": "attend",
    "observe": "attend",
    "joining": "participate",
    "join": "participate",
    "play": "participate",
    "playing": "participate",
    "make": "participate",
    "making": "participate",
    "perform": "participate",
    "performing": "participate",
    "study": "learn",
    "studying": "learn",
    "teach": "learn",
    "teaching": "learn",
    "service": "volunteer",
    "network": "socialize",
    "networking": "socialize",
    "meet": "socialize",
    "meeting": "socialize",
    "race": "compete",
    "racing": "compete",
}

FORMAT_SYNONYMS = {
    "performance": "concert",
    "show": "concert",
    "recital": "concert",
    "gig": "concert",
    "lecture": "talk",
    "panel": "talk",
    "discussion": "talk",
    "story_time": "reading",
    "storytime": "reading",
    "readings": "reading",
    "book_reading": "reading",
    "openmic": "open_mic",
    "open_mic_night": "open_mic",
    "mixer": "social",
    "social_hour": "social",
    "networking": "social",
    "club_meeting": "meetup",
    "meeting": "meetup",
    "gala": "event",
    "challenge": "competition",
    "contest": "competition",
    "race": "competition",
    "tournament": "competition",
    "match": "competition",
    "meet": "competition",
    "fair": "event",
    "job_fair": "event",
    "expo": "exhibition",
    "gallery_show": "exhibition",
    "installation": "exhibition",
    "walk": "tour",
}

AUDIENCE_SYNONYMS = {
    "allages": "all_ages",
    "all_age": "all_ages",
    "family": "families",
    "family_friendly": "families",
    "children": "kids",
    "child": "kids",
    "youth": "teens",
    "teenagers": "teens",
    "beginner": "beginners",
    "student": "students",
    "adult": "adults",
    "senior": "seniors",
}

COST_SYNONYMS = {
    "no_cost": "free",
    "free_entry": "free",
    "complimentary": "free",
    "ticketed": "paid",
    "fee": "paid",
    "fees": "paid",
    "donations": "donation",
}

ACTIVITY_SYNONYMS = {
    "outdoor": "outdoors",
    "outdoors": "outdoors",
    "music": "music",
    "jazz": "jazz",
    "hike": "hiking",
    "hiking": "hiking",
    "nature": "nature",
    "poem": "poetry",
    "poetry": "poetry",
    "literature": "books",
    "reading": "books",
    "lecture": "talks",
    "talk": "talks",
    "talks": "talks",
    "fitness": "fitness",
    "art": "art",
    "arts": "art",
    "volunteer": "volunteering",
    "volunteering": "volunteering",
    "food": "food",
    "drink": "drink",
    "history": "history",
    "games": "games",
    "writing": "writing",
}


def supabase_get(path: str):
    req = urllib.request.Request(
        SUPABASE_URL + "/rest/v1/" + path,
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": "Bearer " + SUPABASE_KEY,
        },
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def supabase_upsert(path: str, payload: List[Dict]):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        SUPABASE_URL + "/rest/v1/" + path,
        data=data,
        method="POST",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": "Bearer " + SUPABASE_KEY,
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=minimal",
        },
    )
    with urllib.request.urlopen(req) as resp:
        return resp.read()


def supabase_rpc(function_name: str, payload: Dict | None = None):
    data = json.dumps(payload or {}).encode()
    req = urllib.request.Request(
        SUPABASE_URL + "/rest/v1/rpc/" + function_name,
        data=data,
        method="POST",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": "Bearer " + SUPABASE_KEY,
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req) as resp:
        return resp.read()


def anthropic_call(model: str, system: str, user_prompt: str):
    body = json.dumps({
        "model": model,
        "max_tokens": 2048,
        "temperature": 0,
        "system": system,
        "messages": [{"role": "user", "content": user_prompt}],
    }).encode()

    req = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=body,
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read())
    return result["content"][0]["text"].strip()


def parse_json_payload(raw: str):
    text = raw.strip()
    if text.startswith("```"):
        text = text.replace("```json", "", 1).replace("```", "").strip()
    start = text.find("[")
    end = text.rfind("]")
    if start >= 0 and end > start:
        return json.loads(text[start:end + 1])
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return json.loads(text[start:end + 1])
    raise ValueError("No JSON found in model response")


def load_examples(path: str):
    if not path:
        return []
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as handle:
        loaded = json.load(handle)
    return loaded if isinstance(loaded, list) else []


def fetch_deduplicated_rows(city: str, days: int):
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    cutoff_iso = (datetime.now(timezone.utc) + timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    query = (
        "select=id,title,start_time,end_time,location,description,source,category,merged_ids"
        f"&city=eq.{urllib.parse.quote(city)}"
        f"&start_time=gte.{urllib.parse.quote(now_iso)}"
        f"&start_time=lt.{urllib.parse.quote(cutoff_iso)}"
        "&order=start_time.asc,id.asc"
        "&limit=5000"
    )
    return supabase_get("deduplicated_chat_events?" + query)


def build_test_slice(rows: List[Dict], limits: Dict[str, int]):
    selected = []
    counts = {category: 0 for category in limits}
    for row in rows:
        category = row.get("category")
        if category not in limits:
            continue
        if counts[category] >= limits[category]:
            continue
        selected.append(row)
        counts[category] += 1
    return selected


def normalize_activity_tag(tag: str):
    cleaned = str(tag).strip().lower().replace("-", "_").replace(" ", "_")
    cleaned = "_".join(part for part in cleaned.split("_") if part)
    base = cleaned.replace("_", "")
    if cleaned in ACTIVITY_SYNONYMS:
        return ACTIVITY_SYNONYMS[cleaned]
    if base in ACTIVITY_SYNONYMS:
        return ACTIVITY_SYNONYMS[base]
    return cleaned


def normalize_token(value: str):
    cleaned = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    return "_".join(part for part in cleaned.split("_") if part)


def normalize_with_vocab(values, allowed, synonyms=None):
    normalized = []
    audit = []
    synonyms = synonyms or {}
    for value in values or []:
        raw = str(value).strip()
        cleaned = normalize_token(raw)
        base = cleaned.replace("_", "")
        mapped = synonyms.get(cleaned, synonyms.get(base, cleaned))
        accepted = mapped in allowed
        if accepted and mapped not in normalized:
            normalized.append(mapped)
        audit.append({
            "raw": raw,
            "normalized": mapped if accepted else None,
            "accepted": accepted,
        })
    return normalized, audit


def normalize_activity_values(values):
    normalized = []
    audit = []
    for value in values or []:
        raw = str(value).strip()
        cleaned = normalize_activity_tag(value)
        if cleaned and cleaned not in normalized:
            normalized.append(cleaned)
        audit.append({
            "raw": raw,
            "normalized": cleaned,
            "accepted": True,
        })
    return normalized[:8], audit


def normalize_quality_score(value):
    try:
        score = float(value)
    except Exception:
        return None
    if score < 0:
        return 0.0
    if score > 1:
        return 1.0
    return round(score, 3)


def normalize_facet_item(item: Dict):
    activity_tags, activity_audit = normalize_activity_values(item.get("activity_tags"))
    participation_modes, participation_audit = normalize_with_vocab(
        item.get("participation_modes"), PARTICIPATION_MODES, PARTICIPATION_SYNONYMS
    )
    format_tags, format_audit = normalize_with_vocab(
        item.get("format_tags"), FORMAT_TAGS, FORMAT_SYNONYMS
    )
    audience_tags, audience_audit = normalize_with_vocab(
        item.get("audience_tags"), AUDIENCE_TAGS, AUDIENCE_SYNONYMS
    )
    cost_tags, cost_audit = normalize_with_vocab(
        item.get("cost_tags"), COST_TAGS, COST_SYNONYMS
    )
    return {
        "normalized": {
            "activity_tags": activity_tags,
            "participation_modes": participation_modes,
            "format_tags": format_tags,
            "audience_tags": audience_tags,
            "cost_tags": cost_tags,
            "quality_score": normalize_quality_score(item.get("quality_score")),
        },
        "audit": {
            "activity_tags": activity_audit,
            "participation_modes": participation_audit,
            "format_tags": format_audit,
            "audience_tags": audience_audit,
            "cost_tags": cost_audit,
        },
    }


def build_prompt(rows: List[Dict]):
    lines = []
    for idx, row in enumerate(rows, start=1):
        lines.append(
            f"""{idx}. id={row.get('id')}
title: {row.get('title', '')}
category: {row.get('category', '')}
location: {row.get('location', '')}
source: {row.get('source', '')}
description: {(row.get('description') or '')[:500]}
merged_ids: {row.get('merged_ids', [])}"""
        )
    return "\n\n".join(lines)


def build_examples_prompt(examples: List[Dict]):
    if not examples:
        return ""
    lines = ["Use these Bloomington examples as guidance for the ontology and tag style:"]
    for idx, example in enumerate(examples, start=1):
        lines.append(
            f"""Example {idx}
title: {example.get('title', '')}
category: {example.get('category', '')}
location: {example.get('location', '')}
description: {example.get('description', '')}
facets: {json.dumps(example.get('facets', {}), ensure_ascii=True)}"""
        )
    return "\n\n".join(lines)


def classify_batch(rows: List[Dict], model: str, examples: List[Dict]):
    system = f"""You classify community events into concierge retrieval facets.

Return JSON only. Output must be a JSON array with one item per input event:
[
  {{
    "index": 1,
    "activity_tags": ["music"],
    "participation_modes": ["participate"],
    "format_tags": ["jam"],
    "audience_tags": ["students"],
    "cost_tags": ["free"],
    "quality_score": 0.87
  }}
]

Allowed participation_modes: {sorted(PARTICIPATION_MODES)}
Allowed format_tags: {sorted(FORMAT_TAGS)}
Allowed audience_tags: {sorted(AUDIENCE_TAGS)}
Allowed cost_tags: {sorted(COST_TAGS)}

Rules:
- activity_tags should be short topical tags, not sentences
- use multiple tags only when they are truly useful for retrieval
- use "participate" for doing/playing/making, "attend" for mainly watching/listening
- use "learn" for instructional or guided events
- use "socialize" for mixers, meetups, clubs, and social gatherings
- use "volunteer" for service and cleanup events
- collapse common format variants to the canonical list
- recital/performance/show -> concert
- lecture/panel/discussion -> talk
- reading/story time -> reading
- race/tournament/challenge/contest -> competition
- mixer/social hour/networking -> social
- meeting/club meeting -> meetup
- expo/gallery show/installation -> exhibition
- follow the few-shot examples closely when deciding attend vs participate vs learn vs socialize
- prefer stable retrieval tags over clever or highly specific tags
- quality_score is 0..1 confidence in the overall facet set
- return JSON only"""

    prompt_parts = []
    examples_prompt = build_examples_prompt(examples)
    if examples_prompt:
        prompt_parts.append(examples_prompt)
    prompt_parts.append("Classify these events:\n\n" + build_prompt(rows))
    prompt = "\n\n".join(prompt_parts)
    raw = anthropic_call(model, system, prompt)
    parsed = parse_json_payload(raw)
    results = {}
    audits = {}
    for item in parsed:
        index = item.get("index")
        if isinstance(index, int) and 1 <= index <= len(rows):
            normalized = normalize_facet_item(item)
            results[index - 1] = normalized["normalized"]
            audits[index - 1] = normalized["audit"]
    return raw, results, audits


def expand_upserts(rows: List[Dict], result_map: Dict[int, Dict], model: str):
    payload = []
    for idx, row in enumerate(rows):
        normalized = result_map.get(idx, {
            "activity_tags": [],
            "participation_modes": [],
            "format_tags": [],
            "audience_tags": [],
            "cost_tags": [],
            "quality_score": None,
        })
        merged_ids = row.get("merged_ids") or [row.get("id")]
        for event_id in merged_ids:
            payload.append({
                "event_id": int(event_id),
                "activity_tags": normalized["activity_tags"],
                "participation_modes": normalized["participation_modes"],
                "format_tags": normalized["format_tags"],
                "audience_tags": normalized["audience_tags"],
                "cost_tags": normalized["cost_tags"],
                "quality_score": normalized["quality_score"],
                "classified_by": model,
            })
    return payload


def chunk(items: List[Dict], size: int):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def summarize_audits(batch, audits):
    summary = []
    for idx, row in enumerate(batch):
        audit = audits.get(idx, {})
        dropped = {}
        mapped = {}
        for facet_name, entries in audit.items():
            dropped_values = [entry["raw"] for entry in entries if not entry["accepted"]]
            mapped_values = [
                {"raw": entry["raw"], "normalized": entry["normalized"]}
                for entry in entries
                if entry["accepted"] and entry["raw"].strip().lower().replace("-", "_").replace(" ", "_") != entry["normalized"]
            ]
            if dropped_values:
                dropped[facet_name] = dropped_values
            if mapped_values:
                mapped[facet_name] = mapped_values
        summary.append({
            "id": row.get("id"),
            "title": row.get("title"),
            "mapped": mapped,
            "dropped": dropped,
        })
    return summary


def main():
    parser = argparse.ArgumentParser(description="Classify event facets via Anthropic")
    parser.add_argument("--city", default="bloomington", help="City slug")
    parser.add_argument("--days", type=int, default=14, help="Future window in days")
    parser.add_argument("--batch-size", type=int, default=20, help="Events per model call")
    parser.add_argument("--limit-rows", type=int, default=0, help="Limit selected deduplicated rows for faster iteration")
    parser.add_argument("--model", default="claude-haiku-4-5-20251001", help="Anthropic model")
    parser.add_argument("--examples", default=DEFAULT_EXAMPLES_PATH, help="Path to few-shot example JSON")
    parser.add_argument("--all", action="store_true", help="Classify all rows in the window, not the test slice")
    parser.add_argument("--dry-run", action="store_true", help="Print results without writing event_facets")
    args = parser.parse_args()

    rows = fetch_deduplicated_rows(args.city, args.days)
    print(f"Fetched {len(rows)} deduplicated rows for {args.city}")
    examples = load_examples(args.examples)
    print(f"Loaded {len(examples)} few-shot examples")

    if args.all:
        selected = rows
        print("Using full window")
    else:
        selected = build_test_slice(rows, CATEGORY_LIMITS)
        print(f"Using stratified test slice of {len(selected)} rows")

    if args.limit_rows and args.limit_rows > 0:
        selected = selected[:args.limit_rows]
        print(f"Trimmed to first {len(selected)} rows for this run")

    if not selected:
        print("No rows selected")
        return

    total_upserts = 0
    wrote_rows = False
    for batch_no, batch in enumerate(chunk(selected, args.batch_size), start=1):
        raw, result_map, audits = classify_batch(batch, args.model, examples)
        payload = expand_upserts(batch, result_map, args.model)
        total_upserts += len(payload)
        print(f"Batch {batch_no}: classified {len(batch)} deduplicated rows -> {len(payload)} event_facets upserts")
        if args.dry_run:
            preview = {
                "raw_response": raw,
                "normalization_audit": summarize_audits(batch, audits),
                "sample_upserts": payload[:5],
            }
            print(json.dumps(preview, indent=2))
        else:
            supabase_upsert("event_facets?on_conflict=event_id", payload)
            wrote_rows = True

    if wrote_rows:
        print("Refreshing deduplicated_chat_events materialized view")
        supabase_rpc("refresh_deduplicated_chat_events")

    print(f"Done. Prepared {total_upserts} event_facets rows.")


if __name__ == "__main__":
    main()
