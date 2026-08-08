#!/usr/bin/env python3
"""Run the relevant calendar build pipeline locally for one city or all cities.

This is a read-only-by-default diagnostic runner intended for cleanup work.
It executes workflow-first scrapers locally, downloads live feeds using a
temporary feeds.txt snapshot, combines outputs, converts to JSON, validates the
results, and writes a structured audit report.

It deliberately skips build steps that mutate upstream state, such as:
- processing pending_feeds.txt into the DB
- marking feeds active
- uploading events to Supabase
- refreshing RPC-backed materialized state

Usage:
    python scripts/local_build.py --city santarosa
    python scripts/local_build.py --cities santarosa,bloomington
    python scripts/local_build.py --all
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import re
import shlex
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from backfill_scraper_feeds import workflow_scraper_rows
from feed_slug import slugify
from process_pending_feeds import parse_pending_feeds
from report import parse_build_errors, update_report
from run_scrapers_from_db import load_scraper_rows as load_db_scraper_rows
from validate_pipeline import build_validation_summary, validate_city, validate_scraper_health


WORKFLOW_PYTHON_VERSION = "3.10"
RUNTIME_PACKAGES = {
    "icalendar": "icalendar",
    "recurring-ical-events": "recurring_ical_events",
    "lxml": "lxml",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--city", help="Run one city")
    scope.add_argument("--cities", help="Comma-separated list of cities")
    scope.add_argument("--all", action="store_true", help="Run all cities discovered under cities/")
    parser.add_argument("--months", default=os.environ.get("SCRAPE_MONTHS", "3"),
                        help="SCRAPE_MONTHS value for scraper commands (default: 3)")
    parser.add_argument("--output-report", default="local-build-report.json",
                        help="Path to structured audit report JSON")
    parser.add_argument("--build-log", default="local-build.log",
                        help="Path to build log")
    parser.add_argument("--feed-report", default="local-feed-report.json",
                        help="Path to feed health report JSON")
    parser.add_argument("--validation-report", default="local-validation-report.json",
                        help="Path to validation report JSON")
    parser.add_argument("--keep-db-export", action="store_true",
                        help="Keep DB-exported feeds.txt files instead of restoring tracked copies")
    parser.add_argument("--db-first", action="store_true", default=True,
                        help="Execute scrapers from active feeds-table rows (DB-first). "
                             "This is the default since the workflow switch.")
    parser.add_argument("--workflow-mode", action="store_true",
                        help="Legacy escape hatch: execute scrapers from the workflow "
                             "manifest instead of the DB. Only meaningful on historical "
                             "checkouts or forks whose workflows still carry scraper lines.")
    args = parser.parse_args()
    if args.workflow_mode:
        args.db_first = False
    return args


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


def _parse_requirement_spec(line: str) -> tuple[str, list[tuple[str, str]]] | None:
    line = line.strip()
    if not line or line.startswith("#") or line.startswith("-r "):
        return None
    match = re.match(r"^([A-Za-z0-9_.-]+)(.*)$", line)
    if not match:
        return None
    name = match.group(1)
    remainder = match.group(2).strip()
    constraints: list[tuple[str, str]] = []
    if remainder:
        for part in remainder.split(","):
            part = part.strip()
            op_match = re.match(r"^(==|!=|<=|>=|<|>)(.+)$", part)
            if op_match:
                constraints.append((op_match.group(1), op_match.group(2).strip()))
    return name, constraints


def _version_tuple(version: str) -> tuple[int | str, ...]:
    parts = re.findall(r"\d+|[A-Za-z]+", version)
    normalized: list[int | str] = []
    for part in parts:
        normalized.append(int(part) if part.isdigit() else part.lower())
    return tuple(normalized)


def _version_matches(installed: str, constraints: list[tuple[str, str]]) -> bool:
    current = _version_tuple(installed)
    for op, expected in constraints:
        target = _version_tuple(expected)
        if op == "==" and current != target:
            return False
        if op == "!=" and current == target:
            return False
        if op == "<" and not (current < target):
            return False
        if op == "<=" and not (current <= target):
            return False
        if op == ">" and not (current > target):
            return False
        if op == ">=" and not (current >= target):
            return False
    return True


def collect_runtime_info() -> dict:
    requirements_path = ROOT / "requirements.txt"
    requirement_checks: list[dict] = []
    issues: list[dict] = []

    python_version = ".".join(str(part) for part in sys.version_info[:3])
    if not python_version.startswith(f"{WORKFLOW_PYTHON_VERSION}."):
        issues.append({
            "level": "warning",
            "type": "python_version_mismatch",
            "message": (
                f"Local runner is using Python {python_version}; "
                f"GitHub Actions uses Python {WORKFLOW_PYTHON_VERSION}."
            ),
        })

    requirements_by_name: dict[str, list[tuple[str, str]]] = {}
    if requirements_path.exists():
        for line in requirements_path.read_text().splitlines():
            parsed = _parse_requirement_spec(line)
            if parsed:
                requirements_by_name[parsed[0]] = parsed[1]

    for requirement_name, importlib_name in RUNTIME_PACKAGES.items():
        try:
            installed = importlib.metadata.version(importlib_name)
        except importlib.metadata.PackageNotFoundError:
            installed = None

        constraints = requirements_by_name.get(requirement_name, [])
        matches = bool(installed) and _version_matches(installed, constraints)
        requirement_checks.append({
            "package": requirement_name,
            "installed_version": installed,
            "constraints": "".join(f"{op}{version}" for op, version in constraints) or None,
            "matches_requirements": matches,
        })
        if installed is None:
            issues.append({
                "level": "error",
                "type": "missing_dependency",
                "message": f"Local runner is missing required package {requirement_name}.",
            })
        elif constraints and not matches:
            issues.append({
                "level": "warning",
                "type": "dependency_version_mismatch",
                "message": (
                    f"{requirement_name} {installed} does not satisfy "
                    f"requirements.txt ({''.join(f'{op}{version}' for op, version in constraints)})."
                ),
            })

    return {
        "python_version": python_version,
        "python_executable": sys.executable,
        "workflow_python_version": WORKFLOW_PYTHON_VERSION,
        "requirements": requirement_checks,
        "issues": issues,
    }


def discover_all_cities() -> list[str]:
    return sorted(
        path.parent.name
        for path in ROOT.glob("cities/*/feeds.txt")
        if path.parent.is_dir()
    )


def selected_cities(args: argparse.Namespace) -> list[str]:
    if args.city:
        return [args.city.strip()]
    if args.cities:
        return [city.strip() for city in args.cities.split(",") if city.strip()]
    return discover_all_cities()


def titleize_city(city: str) -> str:
    return " ".join(part.capitalize() for part in city.replace("-", " ").split())


def query_feeds(city: str, feed_types: tuple[str, ...] | None = None,
                statuses: tuple[str, ...] | None = None) -> list[dict] | None:
    supabase_url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not supabase_url or not service_key:
        return None

    select_cols = "id,city,url,name,status,feed_type,scraper_cmd,fallback_url"
    query = (
        f"{supabase_url}/rest/v1/feeds"
        f"?select={select_cols}"
        f"&city=eq.{urllib.parse.quote(city)}"
        f"&order=feed_type.asc,name.asc"
    )
    if feed_types:
        query += f"&feed_type=in.({','.join(feed_types)})"
    if statuses:
        query += f"&status=in.({','.join(statuses)})"

    req = urllib.request.Request(
        query,
        headers={
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.URLError:
        return None


def render_feeds_snapshot(city: str, rows: list[dict]) -> str:
    ics_urls = [row for row in rows if row["feed_type"] == "ics_url"]
    scrapers = [row for row in rows if row["feed_type"] == "scraper"]
    curators = [row for row in rows if row["feed_type"] == "curator"]

    out: list[str] = [
        f"# {titleize_city(city)} - local build source inventory",
        "# Generated temporarily by scripts/local_build.py.",
        "# Restored after the run unless --keep-db-export is used.",
        "",
    ]

    if ics_urls:
        out.append("# --- Live feeds ---")
        for row in ics_urls:
            comment = row["name"]
            if row.get("fallback_url"):
                comment += f" | {row['fallback_url']}"
            out.append(f"# {comment}")
            out.append(row["url"])
        out.append("")

    if scrapers:
        out.append("# --- Scrapers ---")
        for row in scrapers:
            out.append(f"# {row['name']}")
            if row.get("scraper_cmd"):
                out.append(f"# cmd: {row['scraper_cmd']}")
            if row["url"].startswith(("http://", "https://")):
                # Legacy URL-keyed scraper rows must not appear as bare URL
                # lines: download_feeds.py fetches every https:// line, which
                # turns a scraper registration into a junk pseudo live feed
                # (and can clobber a real scraper output on slug collision).
                out.append(f"# legacy-url: {row['url']}")
            else:
                out.append(row["url"])
        out.append("")

    if curators:
        out.append("# --- Curator feeds ---")
        for row in curators:
            comment = row["name"]
            if row.get("fallback_url"):
                comment += f" | {row['fallback_url']}"
            out.append(f"# {comment}")
            out.append(row["url"])
        out.append("")

    return "\n".join(out).rstrip() + "\n"


@contextmanager
def temporary_file_contents(path: Path, text: str, keep: bool = False):
    original_exists = path.exists()
    original_text = path.read_text() if original_exists else None
    path.write_text(text)
    try:
        yield
    finally:
        if not keep:
            if original_exists and original_text is not None:
                path.write_text(original_text)
            elif path.exists():
                path.unlink()


def clean_known_outputs(city: str, workflow_rows: list[dict], live_feed_rows: list[dict]) -> None:
    paths = {ROOT / row["url"] for row in workflow_rows}
    for row in live_feed_rows:
        if row["feed_type"] not in {"ics_url", "curator"}:
            continue
        filename = slugify(row["url"]) + ".ics"
        paths.add(ROOT / "cities" / city / filename)

    paths.update({
        ROOT / "cities" / city / "combined.ics",
        ROOT / "cities" / city / "events.json",
    })
    for path in paths:
        if path.exists():
            path.unlink()


def count_events(ics_path: Path) -> int:
    try:
        return ics_path.read_text(errors="ignore").count("BEGIN:VEVENT")
    except OSError:
        return 0


def sniff_content_kind(content: str) -> str:
    """Best-effort label for what a non-ICS file actually contains."""
    head = content[:512].lstrip().lower()
    if not head:
        return "empty"
    if head.startswith("<!doctype") or head.startswith("<html") or "<html" in head:
        return "html"
    if head.startswith("{") or head.startswith("["):
        return "json"
    return "unknown"


def summarize_output(path: Path) -> dict:
    """Classify an output file by its content, not just its event count.

    A zero-event file that is a real (if quiet) calendar is different from a
    403 block page, an HTML error page, or a JSON error body saved with an
    ``.ics`` extension; the latter get status ``not_ics`` so broken sources
    stop hiding inside the zero-event review queue.
    """
    exists = path.exists()
    if not exists:
        return {
            "path": str(path.relative_to(ROOT)),
            "exists": False,
            "size": 0,
            "events": 0,
            "status": "missing",
        }

    try:
        content = path.read_text(errors="ignore")
    except OSError:
        content = ""
    events = content.count("BEGIN:VEVENT")
    is_calendar = "BEGIN:VCALENDAR" in content
    summary = {
        "path": str(path.relative_to(ROOT)),
        "exists": True,
        "size": path.stat().st_size,
        "events": events,
        "status": (
            "not_ics" if not is_calendar else
            "no_events" if events == 0 else
            "ok"
        ),
    }
    if summary["status"] == "not_ics":
        summary["content_kind"] = sniff_content_kind(content)
    return summary


def normalize_cmd(cmd: str | None) -> str:
    if not cmd:
        return ""
    cmd = cmd.strip()
    if cmd.startswith("cmd:"):
        cmd = cmd[4:].strip()
    return cmd


def canonicalize_scraper_cmd(cmd: str | None) -> str:
    """Normalize scraper commands for drift comparison.

    The DB typically stores the scraper invocation without the workflow-only
    ``--output ...`` suffix, so strip that detail before comparing.
    """
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


def localize_workflow_cmd(cmd: str) -> str:
    """Rewrite workflow shell commands for the local Python executable."""
    normalized = normalize_cmd(cmd)
    if not normalized:
        return normalized

    try:
        tokens = shlex.split(normalized)
    except ValueError:
        return normalized

    if tokens and tokens[0] == "python":
        tokens[0] = sys.executable

    return shlex.join(tokens)


def classify_command_failure(stderr: str, stdout: str) -> str:
    text = f"{stdout}\n{stderr}".lower()
    if "the following arguments are required" in text or "unrecognized arguments" in text:
        return "arg_error"
    if "http error" in text or "403 client error" in text or "404 client error" in text:
        return "http_error"
    if "timed out" in text or "timeout" in text:
        return "timeout"
    if "connection refused" in text or "connection reset" in text or "remote end closed connection" in text:
        return "connection_error"
    if "traceback" in text:
        return "traceback"
    return "command_failed"


class BuildLogger:
    def __init__(self, path: Path):
        self.path = path
        self.path.write_text("")

    def write(self, line: str) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line.rstrip("\n") + "\n")
        print(line)

    def section(self, city: str, phase: str, message: str) -> None:
        self.write(f"[{city}][{phase}] {message}")


def run_command(logger: BuildLogger, city: str, phase: str, cmd: list[str] | str,
                env: dict[str, str], source: str | None = None, shell: bool = False) -> dict:
    label = source or (cmd if isinstance(cmd, str) else " ".join(cmd))
    logger.section(city, phase, f"RUN {label}")
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        env=env,
        shell=shell,
        executable="/bin/bash" if shell else None,
        capture_output=True,
        text=True,
    )
    if result.stdout:
        for line in result.stdout.splitlines():
            logger.section(city, phase, line)
    if result.stderr:
        for line in result.stderr.splitlines():
            logger.section(city, phase, line)
    logger.section(city, phase, f"EXIT {result.returncode} {label}")
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def build_scraper_drift(city: str, workflow_rows: list[dict], db_rows: list[dict] | None) -> list[dict]:
    if db_rows is None:
        return []

    workflow_by_url = {row["url"]: row for row in workflow_rows}
    db_scrapers = [row for row in db_rows if row["feed_type"] == "scraper"]
    db_by_url = {row["url"]: row for row in db_scrapers}
    drift: list[dict] = []

    for url, workflow_row in workflow_by_url.items():
        db_row = db_by_url.get(url)
        if not db_row:
            drift.append({
                "type": "workflow_scraper_missing_from_db",
                "city": city,
                "url": url,
                "name": workflow_row["name"],
            })
            continue
        if db_row.get("status") == "removed":
            drift.append({
                "type": "removed_db_scraper_still_in_workflow",
                "city": city,
                "url": url,
                "name": workflow_row["name"],
            })
        if (db_row.get("name") != workflow_row["name"]
                and workflow_row.get("name_source") != "filename"):
            # Filename-derived workflow names are a weak fallback (the output
            # was missing or carried no X-SOURCE); comparing them against DB
            # names produces false mismatches, so only trustworthy derivations
            # count as drift.
            drift.append({
                "type": "scraper_name_mismatch",
                "city": city,
                "url": url,
                "name": workflow_row["name"],
                "workflow_name": workflow_row["name"],
                "db_name": db_row.get("name"),
            })
        workflow_cmd = canonicalize_scraper_cmd(workflow_row["scraper_cmd"])
        db_cmd = canonicalize_scraper_cmd(db_row.get("scraper_cmd"))
        if db_cmd != workflow_cmd:
            drift.append({
                "type": "scraper_command_mismatch",
                "city": city,
                "url": url,
                "name": workflow_row["name"],
                "workflow_cmd": workflow_cmd,
                "db_cmd": db_cmd,
            })

    for url, db_row in db_by_url.items():
        if db_row.get("status") in {"active", "pending"} and url not in workflow_by_url:
            drift.append({
                "type": "db_scraper_missing_from_workflow",
                "city": city,
                "url": url,
                "name": db_row["name"],
                "status": db_row["status"],
            })

    return drift


def pending_entries_for_city(city: str) -> list[dict]:
    path = ROOT / "cities" / city / "pending_feeds.txt"
    if not path.exists():
        return []
    return parse_pending_feeds(path)


def run_city(city: str, logger: BuildLogger, args: argparse.Namespace) -> dict:
    workflow_rows = workflow_scraper_rows(city)
    db_rows = query_feeds(city)
    snapshot_rows = [row for row in (db_rows or []) if row["feed_type"] in {"ics_url", "curator", "scraper"} and row["status"] in {"active", "pending"}]
    pending_entries = pending_entries_for_city(city)

    # DB-first mode: the active feeds-table scraper rows are the execution
    # set (with loud, counted feeds.txt fallback for credential-less forks);
    # workflow rows are still parsed for the drift comparison.
    if args.db_first:
        execution_rows, execution_info = load_db_scraper_rows(city)
        if execution_info["fallback_used"]:
            logger.section(city, "scraper",
                           f"[db-first] fallback=feeds.txt reason={execution_info.get('fallback_reason')}")
    else:
        execution_rows = workflow_rows
        execution_info = {"mode": "workflow", "fallback_used": False}

    city_result: dict = {
        "city": city,
        "workflow_scrapers": len(workflow_rows),
        "db_rows_available": db_rows is not None,
        "execution": {**execution_info, "rows": len(execution_rows)},
        "drift": [],
        "pending_entries": pending_entries,
        "scrapers": [],
        "live_feeds": [],
        "combine": {},
        "convert": {},
        "rss": {},
        "validation": {},
        "notes": [],
    }

    # Legacy URL-keyed scraper rows are a registration problem worth surfacing
    # on their own: they duplicate a real producer under an http(s) key.
    scraper_output_paths = {ROOT / row["url"] for row in execution_rows}
    for row in snapshot_rows:
        if row["feed_type"] == "scraper" and row["url"].startswith(("http://", "https://")):
            city_result["notes"].append({
                "type": "legacy_url_keyed_scraper_row",
                "name": row["name"],
                "url": row["url"],
                "message": (
                    f"DB scraper row {row['name']} is keyed by an http(s) URL instead of an "
                    "output path; it is excluded from the live-feed download and should be "
                    "retired or re-keyed."
                ),
            })

    # A live feed whose slugified output filename lands on a workflow scraper's
    # output path would overwrite freshly scraped events during the download
    # phase. Exclude such feeds from the snapshot and report the collision.
    guarded_rows: list[dict] = []
    for row in snapshot_rows:
        if row["feed_type"] in {"ics_url", "curator"}:
            slug_path = ROOT / "cities" / city / f"{slugify(row['url'])}.ics"
            if slug_path in scraper_output_paths:
                city_result["notes"].append({
                    "type": "live_feed_filename_collision",
                    "name": row["name"],
                    "url": row["url"],
                    "path": str(slug_path.relative_to(ROOT)),
                    "message": (
                        f"Live feed {row['name']} would download onto scraper output "
                        f"{slug_path.name}; excluded from the snapshot to protect scraped events."
                    ),
                })
                continue
        guarded_rows.append(row)
    snapshot_rows = guarded_rows

    feeds_path = ROOT / "cities" / city / "feeds.txt"
    temp_feeds_text = None
    tracked_feeds_differs = False
    if snapshot_rows:
        temp_feeds_text = render_feeds_snapshot(city, snapshot_rows)
        tracked_feeds_differs = not feeds_path.exists() or feeds_path.read_text() != temp_feeds_text
        city_result["tracked_feeds_differs_from_db"] = tracked_feeds_differs

    clean_known_outputs(city, execution_rows, snapshot_rows)

    env = os.environ.copy()
    env["SCRAPE_MONTHS"] = args.months

    @contextmanager
    def maybe_db_export():
        if temp_feeds_text is None:
            yield
            return
        with temporary_file_contents(feeds_path, temp_feeds_text, keep=args.keep_db_export):
            yield

    with maybe_db_export():
        for row in execution_rows:
            output_path = ROOT / row["url"]
            local_cmd = localize_workflow_cmd(row["scraper_cmd"])
            result = run_command(
                logger,
                city,
                "scraper",
                local_cmd,
                env,
                source=row["name"],
                shell=True,
            )
            output_summary = summarize_output(output_path)
            scraper_entry = {
                "name": row["name"],
                "cmd": row["scraper_cmd"],
                "local_cmd": local_cmd,
                "output": output_summary,
                "returncode": result["returncode"],
            }
            if result["returncode"] != 0:
                scraper_entry["failure_type"] = classify_command_failure(result["stderr"], result["stdout"])
            city_result["scrapers"].append(scraper_entry)

        download_env = env.copy()
        download_env.pop("SUPABASE_URL", None)
        download_env.pop("SUPABASE_SERVICE_KEY", None)
        download_result = run_command(
            logger,
            city,
            "download",
            [sys.executable, "scripts/download_feeds.py", city],
            download_env,
        )
        city_result["download_returncode"] = download_result["returncode"]

        feed_inventory: list[tuple[str, str | None, str | None]] = []
        if feeds_path.exists():
            from download_feeds import parse_feeds_txt  # local import to avoid circular startup cost
            feed_inventory = list(parse_feeds_txt(str(feeds_path)))

        for url, friendly_name, fallback_url in feed_inventory:
            output_path = ROOT / "cities" / city / f"{slugify(url)}.ics"
            city_result["live_feeds"].append({
                "name": friendly_name or url,
                "url": url,
                "fallback_url": fallback_url,
                "output": summarize_output(output_path),
            })

        combine_result = run_command(
            logger,
            city,
            "combine",
            [
                sys.executable,
                "scripts/combine_ics.py",
                "--input-dir", f"cities/{city}",
                "--output", f"cities/{city}/combined.ics",
                "--name", f"{titleize_city(city)} Community Calendar",
            ],
            env,
        )
        city_result["combine"] = {
            "returncode": combine_result["returncode"],
            "output": summarize_output(ROOT / "cities" / city / "combined.ics"),
        }

        convert_result = run_command(
            logger,
            city,
            "convert",
            [
                sys.executable,
                "scripts/ics_to_json.py",
                f"cities/{city}/combined.ics",
                "-o", f"cities/{city}/events.json",
                "--city", city,
            ],
            env,
        )
        events_path = ROOT / "cities" / city / "events.json"
        event_count = 0
        if events_path.exists():
            try:
                event_count = len(json.loads(events_path.read_text()))
            except json.JSONDecodeError:
                pass
        city_result["convert"] = {
            "returncode": convert_result["returncode"],
            "events_json_exists": events_path.exists(),
            "event_count": event_count,
        }

        rss_result = run_command(
            logger,
            city,
            "rss",
            [sys.executable, "scripts/generate_rss.py", city],
            env,
        )
        city_result["rss"] = {"returncode": rss_result["returncode"]}

    # Drift is computed after the build, from re-derived workflow rows, so
    # display-name derivation reads fresh X-SOURCE headers from this run's
    # outputs instead of falling back to filename-derived names (which produce
    # false name-mismatch drift when outputs are stale or missing).
    #
    # Since the DB-first switch the workflow carries no scraper lines; an
    # empty manifest would make every active DB row look "missing from the
    # workflow", so the comparison only runs when a manifest actually exists
    # (historical checkouts / not-yet-switched forks).
    workflow_rows_post = workflow_scraper_rows(city)
    if workflow_rows_post:
        city_result["drift"] = build_scraper_drift(city, workflow_rows_post, db_rows)
    else:
        city_result["drift"] = []
        city_result["drift_skipped"] = "workflow carries no scraper manifest (DB-first)"

    return city_result


def summarize_city_result(city_result: dict) -> dict:
    scraper_failures = sum(1 for row in city_result["scrapers"] if row["returncode"] != 0)
    scraper_missing = sum(1 for row in city_result["scrapers"] if row["output"]["status"] == "missing")
    scraper_zero_event = sum(1 for row in city_result["scrapers"] if row["output"]["status"] == "no_events")
    scraper_not_ics = sum(1 for row in city_result["scrapers"] if row["output"]["status"] == "not_ics")
    live_feed_missing = sum(1 for row in city_result["live_feeds"] if row["output"]["status"] == "missing")
    live_feed_zero_event = sum(1 for row in city_result["live_feeds"] if row["output"]["status"] == "no_events")
    live_feed_not_ics = sum(1 for row in city_result["live_feeds"] if row["output"]["status"] == "not_ics")
    return {
        "scraper_failures": scraper_failures,
        "scraper_missing_outputs": scraper_missing,
        "scraper_zero_event_outputs": scraper_zero_event,
        "scraper_not_ics_outputs": scraper_not_ics,
        "live_feed_missing_outputs": live_feed_missing,
        "live_feed_zero_event_outputs": live_feed_zero_event,
        "live_feed_not_ics_outputs": live_feed_not_ics,
        "drift_items": len(city_result["drift"]),
        "note_items": len(city_result.get("notes", [])),
    }


def build_action_report(city_result: dict, runtime: dict | None = None) -> dict:
    """Summarize the next actions implied by a city audit."""
    actions = {
        "fix": [],
        "review": [],
        "retire": [],
    }

    for issue in city_result.get("drift", []):
        if issue["type"] == "scraper_command_mismatch":
            actions["fix"].append({
                "type": issue["type"],
                "name": issue["name"],
                "path": issue["url"],
                "message": (
                    f"Reconcile workflow/DB scraper command mismatch for {issue['name']}."
                ),
                "workflow_cmd": issue.get("workflow_cmd"),
                "db_cmd": issue.get("db_cmd"),
            })
        elif issue["type"] == "scraper_name_mismatch":
            actions["fix"].append({
                "type": issue["type"],
                "name": issue["name"],
                "path": issue["url"],
                "message": (
                    f"Reconcile workflow/DB scraper display name mismatch for {issue['name']}."
                ),
                "workflow_name": issue.get("workflow_name"),
                "db_name": issue.get("db_name"),
            })
        elif issue["type"] == "db_scraper_missing_from_workflow":
            actions["fix"].append({
                "type": issue["type"],
                "name": issue["name"],
                "path": issue["url"],
                "message": (
                    f"Add active DB scraper {issue['name']} back to the workflow, or retire it in the DB."
                ),
            })
        elif issue["type"] == "workflow_scraper_missing_from_db":
            actions["fix"].append({
                "type": issue["type"],
                "name": issue["name"],
                "path": issue["url"],
                "message": (
                    f"Register workflow scraper {issue['name']} in the DB, or remove it from the workflow."
                ),
            })
        elif issue["type"] == "removed_db_scraper_still_in_workflow":
            actions["retire"].append({
                "type": issue["type"],
                "name": issue["name"],
                "path": issue["url"],
                "message": (
                    f"Remove retired scraper {issue['name']} from the workflow."
                ),
            })

    for feed in city_result.get("live_feeds", []):
        status = feed["output"]["status"]
        if status == "missing":
            actions["fix"].append({
                "type": "missing_live_feed_output",
                "name": feed["name"],
                "path": feed["output"]["path"],
                "url": feed["url"],
                "message": (
                    f"Live feed {feed['name']} did not download; investigate the source or retire it if the endpoint is dead."
                ),
            })
        elif status == "not_ics":
            content_kind = feed["output"].get("content_kind", "unknown")
            actions["fix"].append({
                "type": "non_ics_live_feed",
                "name": feed["name"],
                "path": feed["output"]["path"],
                "url": feed["url"],
                "message": (
                    f"Live feed {feed['name']} returned non-ICS content ({content_kind}); "
                    "the endpoint is broken, blocked, or serving an error page."
                ),
            })
        elif status == "no_events":
            actions["review"].append({
                "type": "zero_event_live_feed",
                "name": feed["name"],
                "path": feed["output"]["path"],
                "url": feed["url"],
                "message": (
                    f"Live feed {feed['name']} returned zero future events; review before changing anything."
                ),
            })

    for scraper in city_result.get("scrapers", []):
        status = scraper["output"]["status"]
        if scraper["returncode"] != 0 or status == "missing":
            actions["fix"].append({
                "type": "scraper_failure",
                "name": scraper["name"],
                "path": scraper["output"]["path"],
                "message": (
                    f"Scraper {scraper['name']} failed or did not produce output."
                ),
                "failure_type": scraper.get("failure_type"),
            })
        elif status == "not_ics":
            content_kind = scraper["output"].get("content_kind", "unknown")
            actions["fix"].append({
                "type": "non_ics_scraper_output",
                "name": scraper["name"],
                "path": scraper["output"]["path"],
                "message": (
                    f"Scraper {scraper['name']} wrote non-ICS content ({content_kind}); "
                    "its output is broken even though the command exited 0."
                ),
            })
        elif status == "no_events":
            actions["review"].append({
                "type": "zero_event_scraper_output",
                "name": scraper["name"],
                "path": scraper["output"]["path"],
                "message": (
                    f"Scraper {scraper['name']} produced zero events; review before deciding to fix or retire."
                ),
            })

    for note in city_result.get("notes", []):
        actions["fix"].append({
            "type": note["type"],
            "name": note.get("name"),
            "message": note["message"],
        })

    for issue in city_result.get("build_issues", []):
        bucket = "fix" if issue.get("level") == "error" else "review"
        actions[bucket].append({
            "type": issue.get("issue_type") or "build_issue",
            "source": issue.get("source"),
            "message": issue.get("message"),
        })

    for result in city_result.get("validation", {}).get("results", []):
        if result["level"] == "error":
            actions["fix"].append({
                "type": "validation_error",
                "message": result["message"],
            })
        elif result["level"] == "warning":
            actions["review"].append({
                "type": "validation_warning",
                "message": result["message"],
            })

    if runtime:
        for issue in runtime.get("issues", []):
            bucket = "fix" if issue.get("level") == "error" else "review"
            actions[bucket].append({
                "type": issue.get("type", "runtime_issue"),
                "message": issue.get("message"),
            })

    return actions


def print_action_report(city_result: dict) -> None:
    actions = city_result.get("action_report", {})
    print(f"Action report for {city_result['city']}:")
    for bucket in ("fix", "review", "retire"):
        items = actions.get(bucket, [])
        print(f"  {bucket}: {len(items)}")
        for item in items[:5]:
            print(f"    - {item['message']}")
        if len(items) > 5:
            print(f"    - ... {len(items) - 5} more")


def main() -> int:
    dotenv_loaded = load_dotenv(ROOT / ".env")
    args = parse_args()
    cities = selected_cities(args)
    logger = BuildLogger(ROOT / args.build_log)
    runtime = collect_runtime_info()

    build_started = datetime.now(timezone.utc).isoformat()
    results = []
    validation_errors = []
    city_validation_errors: dict[str, list] = {}

    if dotenv_loaded:
        logger.section("global", "env", f"Loaded {len(dotenv_loaded)} variables from .env")
    logger.section(
        "global",
        "runtime",
        f"Python {runtime['python_version']} ({runtime['python_executable']})",
    )
    for issue in runtime["issues"]:
        logger.section("global", "runtime", f"{issue['level'].upper()} {issue['message']}")

    for city in cities:
        logger.section(city, "build", "START")
        city_result = run_city(city, logger, args)
        city_errors = validate_city(city, ROOT / "cities")
        city_validation_errors[city] = list(city_errors)
        city_result["validation"] = {
            "results": [error.to_dict() for error in city_errors],
            "summary": build_validation_summary(city_errors),
        }
        city_result["summary"] = summarize_city_result(city_result)
        results.append(city_result)
        validation_errors.extend(city_errors)
        logger.section(city, "build", "END")

    update_report(cities, str(ROOT / args.feed_report))
    build_errors = parse_build_errors(str(ROOT / args.build_log))
    for city_result in results:
        city_result["build_issues"] = [issue for issue in build_errors if issue.get("city") == city_result["city"]]
        city_errors = validate_scraper_health(city_result)
        combined_city_errors = city_validation_errors[city_result["city"]] + city_errors
        city_result["validation"]["results"] = [error.to_dict() for error in combined_city_errors]
        city_result["validation"]["summary"] = build_validation_summary(combined_city_errors)
        validation_errors.extend(city_errors)
        city_result["action_report"] = build_action_report(city_result, runtime=runtime)
        city_result["summary"] = summarize_city_result(city_result)
    validation_summary = build_validation_summary(validation_errors)

    audit = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "build_started_at": build_started,
        "runtime": runtime,
        "dotenv_loaded": dotenv_loaded,
        "cities": results,
        "build_issues": build_errors,
        "validation": validation_summary,
        "db_available": bool(os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SERVICE_KEY")),
        "summary": {
            "cities": len(cities),
            "scraper_failures": sum(city["summary"]["scraper_failures"] for city in results),
            "scraper_missing_outputs": sum(city["summary"]["scraper_missing_outputs"] for city in results),
            "scraper_zero_event_outputs": sum(city["summary"]["scraper_zero_event_outputs"] for city in results),
            "scraper_not_ics_outputs": sum(city["summary"]["scraper_not_ics_outputs"] for city in results),
            "live_feed_missing_outputs": sum(city["summary"]["live_feed_missing_outputs"] for city in results),
            "live_feed_zero_event_outputs": sum(city["summary"]["live_feed_zero_event_outputs"] for city in results),
            "live_feed_not_ics_outputs": sum(city["summary"]["live_feed_not_ics_outputs"] for city in results),
            "drift_items": sum(city["summary"]["drift_items"] for city in results),
            "validation_errors": validation_summary["errors"],
            "validation_warnings": validation_summary["warnings"],
            "build_issue_count": len(build_errors),
            "build_error_count": sum(1 for issue in build_errors if issue.get("level") == "error"),
            "build_warning_count": sum(1 for issue in build_errors if issue.get("level") == "warning"),
            "runtime_issue_count": len(runtime["issues"]),
            "runtime_error_count": sum(1 for issue in runtime["issues"] if issue.get("level") == "error"),
            "runtime_warning_count": sum(1 for issue in runtime["issues"] if issue.get("level") == "warning"),
            "db_first_fallbacks": sum(
                1 for city_result in results
                if city_result.get("execution", {}).get("fallback_used")
            ),
        },
    }

    (ROOT / args.output_report).write_text(json.dumps(audit, indent=2))
    (ROOT / args.validation_report).write_text(json.dumps(validation_summary, indent=2))

    print("\n" + "=" * 60)
    print("Local Build Summary")
    print("=" * 60)
    for city_result in results:
        summary = city_result["summary"]
        print(
            f"{city_result['city']}: "
            f"{summary['scraper_failures']} scraper failures, "
            f"{summary['scraper_missing_outputs']} missing scraper outputs, "
            f"{summary['scraper_zero_event_outputs']} zero-event scraper outputs, "
            f"{summary['scraper_not_ics_outputs']} non-ICS scraper outputs, "
            f"{summary['live_feed_missing_outputs']} missing live-feed outputs, "
            f"{summary['live_feed_zero_event_outputs']} zero-event live-feed outputs, "
            f"{summary['live_feed_not_ics_outputs']} non-ICS live-feed outputs, "
            f"{summary['drift_items']} drift items"
        )
        print_action_report(city_result)
    print(
        f"Validation: {validation_summary['errors']} errors, "
        f"{validation_summary['warnings']} warnings"
    )
    print(
        f"Build log issues: {len(build_errors)} "
        f"({audit['summary']['build_error_count']} errors, "
        f"{audit['summary']['build_warning_count']} warnings)"
    )
    print(
        f"Runtime issues: {audit['summary']['runtime_issue_count']} "
        f"({audit['summary']['runtime_error_count']} errors, "
        f"{audit['summary']['runtime_warning_count']} warnings)"
    )
    print(f"Audit report: {args.output_report}")
    print(f"Feed report: {args.feed_report}")
    print(f"Validation report: {args.validation_report}")

    has_failures = any([
        validation_summary["errors"] > 0,
        audit["summary"]["scraper_failures"] > 0,
        audit["summary"]["scraper_missing_outputs"] > 0,
        audit["summary"]["scraper_not_ics_outputs"] > 0,
        audit["summary"]["live_feed_missing_outputs"] > 0,
        audit["summary"]["live_feed_not_ics_outputs"] > 0,
        audit["summary"]["build_error_count"] > 0,
        # In --db-first mode a feeds.txt fallback on a credentialed
        # instance means the DB was not actually driving execution.
        args.db_first and audit["summary"]["db_first_fallbacks"] > 0,
    ])
    return 1 if has_failures else 0


if __name__ == "__main__":
    sys.exit(main())
