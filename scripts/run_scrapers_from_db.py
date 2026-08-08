#!/usr/bin/env python3
"""Run a city's scrapers from the feeds table (DB-first execution).

The active scraper rows in the ``feeds`` table are the ONLY execution
set. The tracked ``cities/<city>/feeds.txt`` is a generated, read-only,
human-readable reference for what the database canonically drives — it
is never edited by hand and never an execution authority.

Fallback: when database credentials are absent or the query fails (the
fork-without-credentials case), the runner may parse the tracked
``feeds.txt`` scraper section instead. Fallback use is loud — logged as
``[db-first] fallback=feeds.txt reason=...`` and reported — and counts
as migration debt on the main instance, never silent success.

Usage:
    python scripts/run_scrapers_from_db.py --city santarosa
    python scripts/run_scrapers_from_db.py --city santarosa --list
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_dotenv(path: Path) -> list[str]:
    """Load simple KEY=VALUE lines from .env without overriding existing env."""
    loaded: list[str] = []
    if not path.exists():
        return loaded
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key or key in os.environ:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ[key] = value
        loaded.append(key)
    return loaded


def ensure_output_flag(cmd: str, output_path: str) -> str:
    """Return cmd guaranteed to carry an output flag for this row's path.

    Rows synced from the workflow store the full command including
    ``--output``; older short-form rows may omit it, in which case the
    row's own url (the output path) is appended.
    """
    try:
        tokens = shlex.split(cmd)
    except ValueError:
        tokens = cmd.split()
    if "--output" in tokens or "-o" in tokens:
        return cmd
    return f"{cmd} --output {shlex.quote(output_path)}"


def query_db_scraper_rows(city: str) -> tuple[list[dict] | None, str | None]:
    """Fetch active scraper rows for a city. Returns (rows, error)."""
    supabase_url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not supabase_url or not service_key:
        return None, "missing SUPABASE_URL/SUPABASE_SERVICE_KEY"

    query = (
        f"{supabase_url}/rest/v1/feeds"
        f"?select=id,city,url,name,scraper_cmd,status"
        f"&city=eq.{urllib.parse.quote(city)}"
        f"&feed_type=eq.scraper"
        f"&status=in.(active,pending)"
        f"&order=name.asc"
    )
    req = urllib.request.Request(
        query,
        headers={
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = json.loads(resp.read().decode())
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as exc:
        return None, f"feeds query failed: {exc}"

    rows = []
    for row in raw:
        if not row.get("scraper_cmd"):
            # The validation trigger forbids this for non-removed rows;
            # surface loudly rather than skipping silently if it appears.
            print(f"[db-first] WARNING skipping command-less scraper row id={row.get('id')} {row.get('name')}")
            continue
        rows.append({
            "city": row["city"],
            "url": row["url"],
            "name": row["name"],
            "feed_type": "scraper",
            "scraper_cmd": ensure_output_flag(row["scraper_cmd"].strip(), row["url"]),
            "name_source": "db",
        })
    return rows, None


def parse_feeds_txt_scraper_rows(city: str) -> list[dict]:
    """Fallback: parse the scraper section of the generated feeds.txt.

    feeds.txt is a read-only reference exported from the DB; this parse
    exists only for forks without database credentials.
    """
    feeds_path = ROOT / "cities" / city / "feeds.txt"
    rows: list[dict] = []
    if not feeds_path.exists():
        return rows
    pending_name = None
    pending_cmd = None
    for raw_line in feeds_path.read_text().splitlines():
        line = raw_line.strip()
        if line.startswith("# cmd:"):
            pending_cmd = line[len("# cmd:"):].strip()
            continue
        if line.startswith("#"):
            body = line.lstrip("# ").split(" | ")[0].strip()
            if body and not line.startswith("# ---"):
                pending_name = body
            continue
        if line.startswith("cities/") and line.endswith(".ics"):
            if pending_cmd:
                rows.append({
                    "city": city,
                    "url": line,
                    "name": pending_name or Path(line).stem,
                    "feed_type": "scraper",
                    "scraper_cmd": ensure_output_flag(pending_cmd, line),
                    "name_source": "feeds_txt",
                })
            pending_name = None
            pending_cmd = None
            continue
        pending_name = None
        pending_cmd = None
    return rows


def load_scraper_rows(city: str) -> tuple[list[dict], dict]:
    """Load the execution set for a city: DB rows, or loud feeds.txt fallback.

    Returns (rows, execution_info) where execution_info records the mode
    and any fallback use for reporting.
    """
    rows, error = query_db_scraper_rows(city)
    if rows is not None:
        return rows, {"mode": "db", "fallback_used": False}

    print(f"[db-first] fallback=feeds.txt reason={error}")
    fallback_rows = parse_feeds_txt_scraper_rows(city)
    return fallback_rows, {
        "mode": "feeds.txt-fallback",
        "fallback_used": True,
        "fallback_reason": error,
    }


def localize_cmd(cmd: str) -> str:
    """Rewrite the stored command for the local Python executable."""
    try:
        tokens = shlex.split(cmd)
    except ValueError:
        return cmd
    if tokens and tokens[0] == "python":
        tokens[0] = sys.executable
    return shlex.join(tokens)


def run_rows(city: str, rows: list[dict], months: str) -> int:
    """Execute rows with RUN/EXIT log bracketing; return count of failures."""
    env = os.environ.copy()
    env["SCRAPE_MONTHS"] = months
    failures = 0
    for row in rows:
        label = row["name"]
        local_cmd = localize_cmd(row["scraper_cmd"])
        print(f"[{city}][scraper] RUN {label}")
        result = subprocess.run(
            local_cmd,
            cwd=ROOT,
            env=env,
            shell=True,
            executable="/bin/bash",
            capture_output=True,
            text=True,
        )
        for stream in (result.stdout, result.stderr):
            for line in stream.splitlines():
                print(f"[{city}][scraper] {line}")
        print(f"[{city}][scraper] EXIT {result.returncode} {label}")
        if result.returncode != 0:
            failures += 1
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city", required=True, help="City to run")
    parser.add_argument("--months", default=os.environ.get("SCRAPE_MONTHS", "3"),
                        help="SCRAPE_MONTHS value for scraper commands (default: 3)")
    parser.add_argument("--list", action="store_true",
                        help="List the execution set without running anything")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    rows, execution = load_scraper_rows(args.city)

    print(f"[db-first] city={args.city} mode={execution['mode']} rows={len(rows)}")
    if args.list:
        for row in rows:
            print(f"  {row['name']}: {row['scraper_cmd']}")
        return 0

    if not rows:
        print(f"[db-first] no scraper rows for {args.city}")
        return 0

    failures = run_rows(args.city, rows, args.months)
    print(f"[db-first] city={args.city} ran={len(rows)} failures={failures} "
          f"fallback_used={execution['fallback_used']}")
    # Scraper failures do not fail the build (|| true semantics); a
    # fallback on a credentialed instance is the reportable condition,
    # surfaced via the printed telemetry and local_build's report.
    return 0


if __name__ == "__main__":
    sys.exit(main())
