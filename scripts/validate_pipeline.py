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
    
    # Check for empty ICS files (individual sources)
    empty_ics = []
    for ics_file in city_dir.glob('*.ics'):
        if ics_file.name == 'combined.ics':
            continue
        if ics_file.stat().st_size < 50:
            empty_ics.append(ics_file.name)
    
    if empty_ics:
        errors.append(ValidationError('warning', city,
            f"{len(empty_ics)} empty ICS files: {', '.join(empty_ics[:5])}{'...' if len(empty_ics) > 5 else ''}"))
    
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
