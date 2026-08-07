#!/usr/bin/env python3
"""Validate the calendar pipeline output.

Runs at the end of the workflow to catch silent failures:
- Missing or empty ICS files
- Missing or empty events.json
- events.json not matching combined.ics
- Critical sources missing
- Suspiciously low event counts

Usage:
    python scripts/validate_pipeline.py --cities santarosa,bloomington,davis
    python scripts/validate_pipeline.py --cities santarosa --strict
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

# Minimum expected events per city (warn if below)
MIN_EVENTS = {
    'santarosa': 500,
    'bloomington': 200,
    'davis': 200,
}

# Critical sources that should always have events
CRITICAL_SOURCES = {
    'santarosa': ['North Bay Bohemian', 'Press Democrat', 'Sonoma County Library'],
    'bloomington': [],
    'davis': [],
}


class ValidationError:
    def __init__(self, level: str, city: str, message: str):
        self.level = level  # 'error', 'warning'
        self.city = city
        self.message = message
    
    def __str__(self):
        icon = '❌' if self.level == 'error' else '⚠️'
        return f"{icon} [{self.level.upper()}] {self.city}: {self.message}"

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "city": self.city,
            "message": self.message,
        }


def build_validation_summary(errors: list[ValidationError]) -> dict:
    """Return a compact machine-readable summary for a validation run."""
    error_count = sum(1 for error in errors if error.level == 'error')
    warning_count = sum(1 for error in errors if error.level == 'warning')
    by_city: dict[str, dict[str, int]] = {}
    for error in errors:
        city_counts = by_city.setdefault(error.city, {"errors": 0, "warnings": 0})
        if error.level == "error":
            city_counts["errors"] += 1
        elif error.level == "warning":
            city_counts["warnings"] += 1
    return {
        "errors": error_count,
        "warnings": warning_count,
        "by_city": by_city,
        "results": [error.to_dict() for error in errors],
        "passed": error_count == 0,
    }


def _normalize_issue_source(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r'[^a-z0-9]+', '', text.lower().removesuffix("scraper"))


def _scraper_script_key(scraper_entry: dict) -> str:
    cmd = scraper_entry.get("cmd") or ""
    match = re.search(r'([\w-]+)\.py', cmd)
    return _normalize_issue_source(match.group(1)) if match else ""


def _scraper_issue_keys(scraper_entry: dict) -> set[str]:
    keys = set()
    output_path = scraper_entry.get("output", {}).get("path", "")
    if output_path:
        keys.add(_normalize_issue_source(Path(output_path).stem))
    keys.add(_scraper_script_key(scraper_entry))
    keys.add(_normalize_issue_source(scraper_entry.get("name")))
    return {key for key in keys if key}


def validate_scraper_health(city_result: dict) -> list[ValidationError]:
    """Validate scraper-level health from the local audit runner."""
    errors: list[ValidationError] = []
    city = city_result["city"]
    build_issues = city_result.get("build_issues", [])

    # When several sources share one scraper script (e.g. eight publishers all
    # running eventbrite_filtered.py), the script-derived key is ambiguous and
    # would attribute every shared-script issue to every source. Drop it from
    # matching for those sources; the RUN-label attribution in
    # report.parse_build_errors ties issues to the specific source name.
    script_key_counts: dict[str, int] = {}
    for scraper in city_result.get("scrapers", []):
        key = _scraper_script_key(scraper)
        if key:
            script_key_counts[key] = script_key_counts.get(key, 0) + 1

    for scraper in city_result.get("scrapers", []):
        issue_keys = _scraper_issue_keys(scraper)
        script_key = _scraper_script_key(scraper)
        if script_key and script_key_counts.get(script_key, 0) > 1:
            issue_keys.discard(script_key)
        scraper_issues = [
            issue for issue in build_issues
            if _normalize_issue_source(issue.get("source")) in issue_keys
        ]
        scraper["issues"] = scraper_issues

        error_issues = [issue for issue in scraper_issues if issue.get("level") == "error"]
        warning_issues = [issue for issue in scraper_issues if issue.get("level") == "warning"]
        output_status = scraper["output"]["status"]
        name = scraper["name"]

        if scraper["returncode"] != 0:
            errors.append(ValidationError("error", city, f"{name}: command failed with exit {scraper['returncode']}"))
        if output_status == "missing":
            errors.append(ValidationError("error", city, f"{name}: output file missing"))
        if output_status == "not_ics":
            content_kind = scraper["output"].get("content_kind", "unknown")
            errors.append(ValidationError(
                "error", city,
                f"{name}: output is not ICS ({content_kind}) despite exit 0"))
        if error_issues:
            errors.append(ValidationError("error", city, f"{name}: {len(error_issues)} logged error(s)"))
        if warning_issues:
            errors.append(ValidationError("warning", city, f"{name}: {len(warning_issues)} logged warning(s)"))

    for feed in city_result.get("live_feeds", []):
        if feed["output"]["status"] == "not_ics":
            content_kind = feed["output"].get("content_kind", "unknown")
            errors.append(ValidationError(
                "warning", city,
                f"{feed['name']}: live feed returned non-ICS content ({content_kind}); "
                "endpoint is broken, blocked, or serving an error page"))
    return errors


def validate_city(city: str, cities_dir: Path) -> list[ValidationError]:
    """Validate a single city's output."""
    errors = []
    city_dir = cities_dir / city
    
    if not city_dir.exists():
        errors.append(ValidationError('error', city, f"City directory not found: {city_dir}"))
        return errors
    
    # Check combined.ics exists and has content
    combined_ics = city_dir / 'combined.ics'
    if not combined_ics.exists():
        errors.append(ValidationError('error', city, "combined.ics not found"))
    elif combined_ics.stat().st_size < 100:
        errors.append(ValidationError('error', city, "combined.ics is empty or too small"))
    else:
        # Count events in combined.ics
        content = combined_ics.read_text()
        ics_event_count = content.count('BEGIN:VEVENT')
        if ics_event_count == 0:
            errors.append(ValidationError('error', city, "combined.ics has no events"))
        elif ics_event_count < MIN_EVENTS.get(city, 100):
            errors.append(ValidationError('warning', city, 
                f"combined.ics has only {ics_event_count} events (expected >= {MIN_EVENTS.get(city, 100)})"))
    
    # Check events.json exists and has content
    events_json = city_dir / 'events.json'
    if not events_json.exists():
        errors.append(ValidationError('error', city, "events.json not found"))
    elif events_json.stat().st_size < 100:
        errors.append(ValidationError('error', city, "events.json is empty or too small"))
    else:
        try:
            events = json.loads(events_json.read_text())
            json_event_count = len(events)
            
            if json_event_count == 0:
                errors.append(ValidationError('error', city, "events.json has no events"))
            elif json_event_count < MIN_EVENTS.get(city, 100):
                errors.append(ValidationError('warning', city,
                    f"events.json has only {json_event_count} events (expected >= {MIN_EVENTS.get(city, 100)})"))
            
            # Check that events.json roughly matches combined.ics
            if 'ics_event_count' in dir():
                diff = abs(ics_event_count - json_event_count)
                if diff > 100:
                    errors.append(ValidationError('warning', city,
                        f"Event count mismatch: combined.ics has {ics_event_count}, events.json has {json_event_count}"))
            
            # Check critical sources are present
            sources = set(e.get('source', '') for e in events)
            for critical in CRITICAL_SOURCES.get(city, []):
                if critical not in sources:
                    errors.append(ValidationError('warning', city,
                        f"Critical source missing: {critical}"))
            
            # Check for source diversity (not all from one source)
            if len(sources) < 3:
                errors.append(ValidationError('warning', city,
                    f"Low source diversity: only {len(sources)} sources"))
                    
        except json.JSONDecodeError as e:
            errors.append(ValidationError('error', city, f"events.json is invalid JSON: {e}"))
    
    # Check for empty and non-ICS files (individual sources). A file that has
    # bytes but no BEGIN:VCALENDAR is not a quiet calendar — it is typically a
    # 403 block page, an HTML error page, or a JSON error body saved as .ics.
    empty_ics = []
    non_ics = []
    for ics_file in city_dir.glob('*.ics'):
        if ics_file.name == 'combined.ics':
            continue
        if ics_file.stat().st_size < 50:
            empty_ics.append(ics_file.name)
        elif 'BEGIN:VCALENDAR' not in ics_file.read_text(errors='ignore'):
            non_ics.append(ics_file.name)

    if empty_ics:
        errors.append(ValidationError('warning', city,
            f"{len(empty_ics)} empty ICS files: {', '.join(empty_ics[:5])}{'...' if len(empty_ics) > 5 else ''}"))
    if non_ics:
        errors.append(ValidationError('warning', city,
            f"{len(non_ics)} non-ICS files (HTML/error pages saved as .ics): "
            f"{', '.join(non_ics[:5])}{'...' if len(non_ics) > 5 else ''}"))

    return errors


def main():
    parser = argparse.ArgumentParser(description='Validate calendar pipeline output')
    parser.add_argument('--cities', '-c', required=True,
                        help='Comma-separated list of cities to validate')
    parser.add_argument('--strict', action='store_true',
                        help='Treat warnings as errors (exit non-zero)')
    parser.add_argument('--cities-dir', default='cities',
                        help='Path to cities directory')
    args = parser.parse_args()
    
    cities = [c.strip() for c in args.cities.split(',')]
    cities_dir = Path(args.cities_dir)
    
    all_errors = []
    
    print("=" * 60)
    print("Pipeline Validation Report")
    print("=" * 60)
    
    for city in cities:
        print(f"\nValidating {city}...")
        errors = validate_city(city, cities_dir)
        all_errors.extend(errors)
        
        if not errors:
            print(f"  ✅ {city}: All checks passed")
        else:
            for error in errors:
                print(f"  {error}")
    
    print("\n" + "=" * 60)
    
    error_count = sum(1 for e in all_errors if e.level == 'error')
    warning_count = sum(1 for e in all_errors if e.level == 'warning')
    
    print(f"Summary: {error_count} errors, {warning_count} warnings")
    
    if error_count > 0:
        print("\n❌ VALIDATION FAILED")
        sys.exit(1)
    elif warning_count > 0 and args.strict:
        print("\n⚠️ VALIDATION FAILED (strict mode)")
        sys.exit(1)
    else:
        print("\n✅ VALIDATION PASSED")
        sys.exit(0)


if __name__ == '__main__':
    main()
