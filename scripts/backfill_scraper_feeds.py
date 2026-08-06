#!/usr/bin/env python3
"""Backfill missing scraper rows in the feeds table from workflow commands.

This is a one-off maintenance tool for legacy scrapers that were added to
the GitHub Actions workflow before scraper metadata was staged through
pending_feeds.txt / process_pending_feeds.py.

It scans .github/workflows/generate-calendar.yml for scraper-like commands that
write .ics files under cities/<city>/, derives the feed metadata, and inserts
only rows that are missing from the feeds table. Existing rows are left
untouched.

Usage:
    python scripts/backfill_scraper_feeds.py --dry-run
    python scripts/backfill_scraper_feeds.py --city bloomington --dry-run
    SUPABASE_URL=... SUPABASE_SERVICE_KEY=... python scripts/backfill_scraper_feeds.py
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shlex
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORKFLOW_PATH = ROOT / ".github/workflows/generate-calendar.yml"

OUTPUT_RE = re.compile(r"cities/([^/]+)/([^/\s]+\.ics)$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city", help="Limit to one city")
    parser.add_argument("--dry-run", action="store_true", help="Print planned inserts without writing")
    return parser.parse_args()


def strip_guard_suffix(line: str) -> str:
    stripped = line.strip()
    if stripped.endswith("|| true"):
        stripped = stripped[:-7].rstrip()
    return stripped


def extract_flag(tokens: list[str], *names: str) -> str | None:
    for idx, token in enumerate(tokens):
        if token in names and idx + 1 < len(tokens):
            return tokens[idx + 1]
    return None


def derive_name_from_ics(output_path: Path) -> str | None:
    if not output_path.exists():
        return None

    try:
        with output_path.open(encoding="utf-8", errors="replace") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if line.startswith("X-SOURCE:"):
                    return html.unescape(line.split(":", 1)[1].strip())
                if line.startswith("X-WR-CALNAME:"):
                    return html.unescape(line.split(":", 1)[1].strip())
    except OSError:
        return None

    return None


def derive_name(tokens: list[str], output_rel: str) -> str:
    explicit = extract_flag(tokens, "--name")
    if explicit:
        return explicit

    from_ics = derive_name_from_ics(ROOT / output_rel)
    if from_ics:
        return from_ics

    return Path(output_rel).stem.replace("_", " ").title()


def workflow_scraper_rows(city_filter: str | None = None) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for raw_line in WORKFLOW_PATH.read_text().splitlines():
        stripped = strip_guard_suffix(raw_line)
        if not stripped.startswith("python "):
            continue
        if "--output" not in stripped and " -o " not in f" {stripped} ":
            continue

        try:
            tokens = shlex.split(stripped)
        except ValueError:
            continue

        script_path = tokens[1] if len(tokens) > 1 else ""
        if not (script_path.startswith("scrapers/") or script_path == "scripts/library_intercept.py"):
            continue

        output_rel = extract_flag(tokens, "--output", "-o")
        if not output_rel:
            continue

        output_match = OUTPUT_RE.match(output_rel)
        if not output_match:
            continue

        city = output_match.group(1)
        if city_filter and city != city_filter:
            continue

        key = (city, output_rel)
        if key in seen:
            continue
        seen.add(key)

        rows.append({
            "city": city,
            "url": output_rel,
            "name": derive_name(tokens, output_rel),
            "feed_type": "scraper",
            "scraper_cmd": stripped,
        })

    return rows


def fetch_existing_rows(supabase_url: str, service_key: str, city_filter: str | None = None) -> set[tuple[str, str]]:
    query = (
        f"{supabase_url}/rest/v1/feeds"
        f"?select=city,url"
        f"&feed_type=eq.scraper"
    )
    if city_filter:
        query += f"&city=eq.{urllib.parse.quote(city_filter)}"

    req = urllib.request.Request(
        query,
        headers={
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
        },
    )
    with urllib.request.urlopen(req) as resp:
        rows = json.loads(resp.read().decode())
    return {(row["city"], row["url"]) for row in rows}


def insert_rows(rows: list[dict[str, str]], supabase_url: str, service_key: str) -> tuple[int, int]:
    inserted = 0
    errors = 0

    for row in rows:
        body = json.dumps({
            "city": row["city"],
            "url": row["url"],
            "name": row["name"],
            "feed_type": "scraper",
            "scraper_cmd": row["scraper_cmd"],
            "status": "active",
        }).encode()
        req = urllib.request.Request(
            f"{supabase_url}/rest/v1/feeds",
            data=body,
            headers={
                "apikey": service_key,
                "Authorization": f"Bearer {service_key}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req):
                inserted += 1
                print(f"+ {row['city']}: {row['name']} [{row['url']}]")
        except urllib.error.HTTPError as exc:
            errors += 1
            detail = exc.read().decode()
            print(f"! {row['city']}: {row['url']} -> HTTP {exc.code} {detail}")

    return inserted, errors


def main() -> int:
    args = parse_args()
    supabase_url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_KEY")

    rows = workflow_scraper_rows(args.city)
    if not rows:
        scope = args.city or "all cities"
        print(f"No workflow scraper rows found for {scope}")
        return 0

    existing: set[tuple[str, str]] = set()
    db_state_known = False
    if supabase_url and service_key:
        existing = fetch_existing_rows(supabase_url, service_key, args.city)
        db_state_known = True
    elif not args.dry_run:
        print("Set SUPABASE_URL and SUPABASE_SERVICE_KEY, or use --dry-run")
        return 1

    missing = [row for row in rows if (row["city"], row["url"]) not in existing]
    skipped = len(rows) - len(missing)

    print(f"Workflow scraper rows: {len(rows)}")
    if db_state_known:
        print(f"Existing scraper rows: {skipped}")
        print(f"Missing scraper rows: {len(missing)}")
    else:
        print("Existing scraper rows: unknown (no DB credentials)")
        print(f"Candidate scraper rows: {len(missing)}")

    for row in missing:
        print(f"  {row['city']}: {row['name']} [{row['url']}]")

    if args.dry_run:
        return 0

    inserted, errors = insert_rows(missing, supabase_url, service_key)
    print(f"Inserted: {inserted}")
    print(f"Errors: {errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
