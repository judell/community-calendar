#!/usr/bin/env python3
"""Backfill and sync scraper rows in the feeds table from workflow commands.

This is a one-off maintenance tool for legacy scrapers that were added to
the GitHub Actions workflow before scraper metadata was staged through
pending_feeds.txt / process_pending_feeds.py.

It scans .github/workflows/generate-calendar.yml for scraper-like commands that
write .ics files under cities/<city>/, derives the feed metadata, and can:

- insert scraper rows that are missing from the feeds table
- update existing scraper metadata to match the workflow command
- mark DB-only scraper rows as removed when the workflow is treated as the
  current source of truth

Usage:
    python scripts/backfill_scraper_feeds.py --dry-run
    python scripts/backfill_scraper_feeds.py --city bloomington --dry-run
    SUPABASE_URL=... SUPABASE_SERVICE_KEY=... python scripts/backfill_scraper_feeds.py
    python scripts/backfill_scraper_feeds.py --city bloomington --sync-existing --dry-run
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
    parser.add_argument(
        "--sync-existing",
        action="store_true",
        help=(
            "Also update existing scraper rows to match workflow commands and "
            "mark DB-only scraper rows as removed."
        ),
    )
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


def derive_name(tokens: list[str], output_rel: str) -> tuple[str, str]:
    """Derive a display name and its provenance.

    Provenance matters: a name read from an explicit ``--name`` flag or an
    output file's ``X-SOURCE`` header is trustworthy, but the filename fallback
    fires whenever the output is missing (for example when a sync dry run is
    taken before a local build regenerates outputs) and must never overwrite
    an existing DB name.
    """
    explicit = extract_flag(tokens, "--name")
    if explicit:
        return explicit, "flag"

    from_ics = derive_name_from_ics(ROOT / output_rel)
    if from_ics:
        return from_ics, "ics"

    return Path(output_rel).stem.replace("_", " ").title(), "filename"


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

        name, name_source = derive_name(tokens, output_rel)
        rows.append({
            "city": city,
            "url": output_rel,
            "name": name,
            "name_source": name_source,
            "feed_type": "scraper",
            "scraper_cmd": stripped,
        })

    return rows


def normalize_cmd(cmd: str | None) -> str:
    if not cmd:
        return ""
    cmd = cmd.strip()
    if cmd.startswith("cmd:"):
        cmd = cmd[4:].strip()
    return cmd


def canonicalize_scraper_cmd(cmd: str | None) -> str:
    normalized = normalize_cmd(cmd)
    if not normalized:
        return ""

    try:
        tokens = shlex.split(normalized)
    except ValueError:
        return normalized

    while "--output" in tokens:
        index = tokens.index("--output")
        del tokens[index:index + 2]
    while "-o" in tokens:
        index = tokens.index("-o")
        del tokens[index:index + 2]

    return shlex.join(tokens)


def fetch_existing_rows(supabase_url: str, service_key: str, city_filter: str | None = None) -> list[dict]:
    query = (
        f"{supabase_url}/rest/v1/feeds"
        f"?select=id,city,url,name,status,scraper_cmd"
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
        return json.loads(resp.read().decode())


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


def patch_row(row_id: int, payload: dict[str, str], supabase_url: str, service_key: str) -> None:
    req = urllib.request.Request(
        f"{supabase_url}/rest/v1/feeds?id=eq.{row_id}",
        data=json.dumps(payload).encode(),
        headers={
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        },
        method="PATCH",
    )
    with urllib.request.urlopen(req):
        return


def build_sync_plan(
    workflow_rows: list[dict[str, str]],
    existing_rows: list[dict],
    sync_existing: bool,
) -> dict[str, list[dict]]:
    existing_by_key = {(row["city"], row["url"]): row for row in existing_rows}
    workflow_by_key = {(row["city"], row["url"]): row for row in workflow_rows}

    plan = {
        "insert": [],
        "update": [],
        "retire": [],
        "weak_name_skips": [],
    }

    for row in workflow_rows:
        existing = existing_by_key.get((row["city"], row["url"]))
        if not existing:
            plan["insert"].append(row)
            continue
        if not sync_existing:
            continue

        payload: dict[str, str] = {}
        if existing.get("name") != row["name"]:
            if row.get("name_source") == "filename" and existing.get("name"):
                plan["weak_name_skips"].append({
                    "city": row["city"],
                    "url": row["url"],
                    "db_name": existing.get("name"),
                    "derived_name": row["name"],
                })
            else:
                payload["name"] = row["name"]
        if canonicalize_scraper_cmd(existing.get("scraper_cmd")) != canonicalize_scraper_cmd(row["scraper_cmd"]):
            payload["scraper_cmd"] = row["scraper_cmd"]
        if existing.get("status") == "removed":
            payload["status"] = "active"

        if payload:
            plan["update"].append({
                "id": existing["id"],
                "city": row["city"],
                "url": row["url"],
                "name": row["name"],
                "payload": payload,
            })

    if sync_existing:
        for row in existing_rows:
            key = (row["city"], row["url"])
            if key not in workflow_by_key and row.get("status") != "removed":
                plan["retire"].append({
                    "id": row["id"],
                    "city": row["city"],
                    "url": row["url"],
                    "name": row["name"],
                    "payload": {"status": "removed"},
                })

    return plan


def apply_sync_plan(plan: dict[str, list[dict]], supabase_url: str, service_key: str) -> tuple[int, int, int, int]:
    inserted, errors = insert_rows(plan["insert"], supabase_url, service_key)
    updated = 0
    retired = 0

    for row in plan["update"]:
        try:
            patch_row(row["id"], row["payload"], supabase_url, service_key)
            updated += 1
            print(f"~ {row['city']}: {row['name']} [{row['url']}] -> {json.dumps(row['payload'], sort_keys=True)}")
        except urllib.error.HTTPError as exc:
            errors += 1
            detail = exc.read().decode()
            print(f"! {row['city']}: {row['url']} -> HTTP {exc.code} {detail}")

    for row in plan["retire"]:
        try:
            patch_row(row["id"], row["payload"], supabase_url, service_key)
            retired += 1
            print(f"- {row['city']}: {row['name']} [{row['url']}] -> removed")
        except urllib.error.HTTPError as exc:
            errors += 1
            detail = exc.read().decode()
            print(f"! {row['city']}: {row['url']} -> HTTP {exc.code} {detail}")

    return inserted, updated, retired, errors


def main() -> int:
    args = parse_args()
    supabase_url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_KEY")

    rows = workflow_scraper_rows(args.city)
    if not rows:
        scope = args.city or "all cities"
        print(f"No workflow scraper rows found for {scope}")
        return 0

    existing_rows: list[dict] = []
    db_state_known = False
    if supabase_url and service_key:
        existing_rows = fetch_existing_rows(supabase_url, service_key, args.city)
        db_state_known = True
    elif not args.dry_run:
        print("Set SUPABASE_URL and SUPABASE_SERVICE_KEY, or use --dry-run")
        return 1

    plan = build_sync_plan(rows, existing_rows, args.sync_existing)
    existing_keys = {(row["city"], row["url"]) for row in existing_rows}
    skipped = len(rows) - len(plan["insert"])

    print(f"Workflow scraper rows: {len(rows)}")
    if db_state_known:
        print(f"Existing scraper rows: {skipped}")
        print(f"Missing scraper rows: {len(plan['insert'])}")
        if args.sync_existing:
            print(f"Rows to update: {len(plan['update'])}")
            print(f"Rows to retire: {len(plan['retire'])}")
            print(f"Weak-name skips: {len(plan['weak_name_skips'])}")
    else:
        print("Existing scraper rows: unknown (no DB credentials)")
        print(f"Candidate scraper rows: {len(plan['insert'])}")

    for row in plan["insert"]:
        print(f"  {row['city']}: {row['name']} [{row['url']}]")
    for row in plan["update"]:
        print(f"  UPDATE {row['city']}: {row['name']} [{row['url']}] -> {json.dumps(row['payload'], sort_keys=True)}")
    for row in plan["retire"]:
        print(f"  RETIRE {row['city']}: {row['name']} [{row['url']}]")
    for row in plan["weak_name_skips"]:
        print(
            f"  SKIP name {row['city']}: kept DB name {row['db_name']!r} "
            f"[{row['url']}] (workflow derivation fell back to filename {row['derived_name']!r}; "
            "run the local build first if you expected an X-SOURCE-based name)"
        )

    if args.dry_run:
        return 0

    inserted, updated, retired, errors = apply_sync_plan(plan, supabase_url, service_key)
    print(f"Inserted: {inserted}")
    print(f"Updated: {updated}")
    print(f"Retired: {retired}")
    print(f"Errors: {errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
