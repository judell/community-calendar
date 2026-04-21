#!/usr/bin/env python3

import argparse
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 512
DEFAULT_CITY = "bloomington"
DEFAULT_DAYS = 30
DEFAULT_MATCH_COUNT = 20


def utc_now():
    return dt.datetime.now(dt.timezone.utc)


def load_config():
    config_path = Path(__file__).resolve().parents[1] / "xmlui" / "config.json"
    with config_path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    globals_obj = config.get("appGlobals", {})
    return globals_obj.get("supabaseUrl"), globals_obj.get("supabasePublishableKey")


def post_json(url, payload, headers):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def generate_embedding(query, openai_key):
    payload = {
        "model": EMBEDDING_MODEL,
        "input": query,
        "dimensions": EMBEDDING_DIMENSIONS,
    }
    headers = {"Authorization": f"Bearer {openai_key}"}
    response = post_json("https://api.openai.com/v1/embeddings", payload, headers)
    data = response.get("data") or []
    if not data:
        raise RuntimeError("Embedding API returned no data")
    return data[0]["embedding"]


def run_mode(mode, args, supabase_url, supabase_key, embedding):
    if mode == "fts":
        full_text_weight = 1
        semantic_weight = 0
        query_embedding = None
    elif mode == "semantic":
        if embedding is None:
            raise RuntimeError("semantic mode requires OPENAI_API_KEY")
        full_text_weight = 0
        semantic_weight = 1
        query_embedding = embedding
    elif mode == "hybrid":
        if embedding is None:
            raise RuntimeError("hybrid mode requires OPENAI_API_KEY")
        full_text_weight = 1
        semantic_weight = 1
        query_embedding = embedding
    else:
        raise RuntimeError(f"Unknown mode: {mode}")

    start = utc_now()
    end = start + dt.timedelta(days=args.days)
    payload = {
        "query_text": args.query,
        "query_embedding": query_embedding,
        "filter_city": args.city,
        "window_start": start.isoformat().replace("+00:00", "Z"),
        "window_end": end.isoformat().replace("+00:00", "Z"),
        "match_count": args.match_count,
        "full_text_weight": full_text_weight,
        "semantic_weight": semantic_weight,
        "rrf_k": 50,
    }
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
    }
    url = f"{supabase_url}/rest/v1/rpc/hybrid_search_events"
    return post_json(url, payload, headers)


def print_results(mode, rows, target_id, show):
    print(f"\n== {mode.upper()} ==")
    if not rows:
        print("(no results)")
        return

    shown = rows[:show]
    for index, row in enumerate(shown, start=1):
        marker = ""
        if target_id is not None and int(row["id"]) == target_id:
            marker = "  <-- target"
        print(
            f"{index:>2}. {row['id']} | {row['title']} | "
            f"fts={row.get('full_text_rank')} sem={row.get('semantic_rank')} "
            f"rrf={row.get('rrf_score')}{marker}"
        )

    if target_id is not None:
        match = next((idx for idx, row in enumerate(rows, start=1) if int(row["id"]) == target_id), None)
        if match is None:
            print(f"target {target_id}: not present")
        else:
            print(f"target {target_id}: present at rank {match}")


def main():
    parser = argparse.ArgumentParser(description="Probe hybrid_search_events without the reply model.")
    parser.add_argument("query", help="Retrieval query to test")
    parser.add_argument("--city", default=DEFAULT_CITY)
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS)
    parser.add_argument("--match-count", type=int, default=DEFAULT_MATCH_COUNT)
    parser.add_argument("--show", type=int, default=10)
    parser.add_argument("--mode", choices=["fts", "semantic", "hybrid", "all"], default="all")
    parser.add_argument("--target-id", type=int, default=None)
    args = parser.parse_args()

    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_PUBLISHABLE_KEY")
    if not supabase_url or not supabase_key:
        config_url, config_key = load_config()
        supabase_url = supabase_url or config_url
        supabase_key = supabase_key or config_key

    if not supabase_url or not supabase_key:
        print("Missing Supabase URL or publishable key", file=sys.stderr)
        sys.exit(1)

    openai_key = os.environ.get("OPENAI_API_KEY")
    embedding = None
    if args.mode in {"semantic", "hybrid", "all"} and openai_key:
        embedding = generate_embedding(args.query, openai_key)

    modes = ["fts", "semantic", "hybrid"] if args.mode == "all" else [args.mode]
    for mode in modes:
        if mode in {"semantic", "hybrid"} and embedding is None:
            print(f"\n== {mode.upper()} ==")
            print("skipped: OPENAI_API_KEY not set")
            continue
        try:
            rows = run_mode(mode, args, supabase_url, supabase_key, embedding)
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            print(f"\n== {mode.upper()} ==")
            print(f"HTTP {error.code}: {body}")
            continue
        print_results(mode, rows, args.target_id, args.show)


if __name__ == "__main__":
    main()
