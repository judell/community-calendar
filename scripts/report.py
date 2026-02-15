#!/usr/bin/env python3
"""
Generate feed health report after aggregation runs.

Scans .ics files in each city directory (produced by the workflow from
both URL downloads and scrapers) and counts future events in each.

Updates report.json with:
- Per-city, per-feed event counts
- Historical data (unlimited)
- Anomaly detection
"""

import argparse
import glob
import json
import os
import re
from datetime import datetime, date, timezone, timedelta
from typing import Optional

# Anomaly thresholds
DROP_THRESHOLD = 0.5  # 50% drop from previous
MIN_EVENTS_FOR_DROP = 5  # Only flag drops if previous had at least this many


def count_future_events_in_ics(filepath: str) -> tuple[int, Optional[str]]:
    """Count VEVENT entries with future DTSTART in an ICS file."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except FileNotFoundError:
        return 0, 'file_not_found'
    except Exception as e:
        return 0, str(e)[:100]

    count = 0
    for match in re.finditer(r'BEGIN:VEVENT\r?\n(.*?)\r?\nEND:VEVENT', content, re.DOTALL):
        event = match.group(1)
        dt_match = re.search(r'DTSTART[^:]*:(\d{8}(?:T\d{6}Z?)?)', event)
        if not dt_match:
            continue
        dt_str = dt_match.group(1)
        try:
            if dt_str.endswith('Z'):
                dt = datetime.strptime(dt_str, '%Y%m%dT%H%M%SZ').replace(tzinfo=timezone.utc)
            elif 'T' in dt_str:
                dt = datetime.strptime(dt_str, '%Y%m%dT%H%M%S').replace(tzinfo=timezone.utc)
            else:
                dt = datetime.strptime(dt_str, '%Y%m%d').replace(tzinfo=timezone.utc)
            if dt >= cutoff:
                count += 1
        except ValueError:
            count += 1  # count if unparseable, to be safe
    return count, None


def detect_anomalies(feed_name: str, current: int, history: list[dict]) -> list[dict]:
    """Detect anomalies for a feed. Returns list of anomaly dicts."""
    anomalies = []

    if not history:
        return anomalies

    prev = None
    for h in reversed(history):
        if h.get('error') is None:
            prev = h
            break

    if prev is None:
        return anomalies

    prev_count = prev['count']

    if current == 0 and prev_count > 0:
        anomalies.append({
            'type': 'zero_events',
            'message': f'Feed returned 0 events (was {prev_count})',
            'severity': 'high'
        })
    elif prev_count >= MIN_EVENTS_FOR_DROP and current < prev_count:
        drop_pct = (prev_count - current) / prev_count
        if drop_pct >= DROP_THRESHOLD:
            anomalies.append({
                'type': 'significant_drop',
                'message': f'Events dropped {drop_pct:.0%} ({prev_count} → {current})',
                'severity': 'medium'
            })

    return anomalies


def load_report(report_path: str) -> dict:
    """Load existing report or create new one."""
    try:
        with open(report_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            'generated': None,
            'cities': {},
            'anomalies': []
        }


def save_report(report: dict, report_path: str):
    """Save report to JSON file."""
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)


def update_report(cities: list[str], report_path: str = 'report.json'):
    """Main function to update the report."""
    report = load_report(report_path)
    today = date.today().isoformat()
    now = datetime.now().isoformat()

    all_anomalies = []

    for city in cities:
        city_dir = f'cities/{city}'

        if city not in report['cities']:
            report['cities'][city] = {'feeds': {}}

        city_data = report['cities'][city]

        # Scan all .ics files in the city directory (skip combined.ics)
        for ics_path in sorted(glob.glob(f'{city_dir}/*.ics')):
            basename = os.path.basename(ics_path).replace('.ics', '')
            if basename == 'combined':
                continue

            feed_name = basename

            if feed_name not in city_data['feeds']:
                city_data['feeds'][feed_name] = {'history': []}

            feed_data = city_data['feeds'][feed_name]
            count, error = count_future_events_in_ics(ics_path)

            if error:
                all_anomalies.append({
                    'date': today,
                    'city': city,
                    'feed': feed_name,
                    'type': 'error',
                    'message': f'Error: {error}',
                    'severity': 'high'
                })
            else:
                anomalies = detect_anomalies(feed_name, count, feed_data['history'])
                for a in anomalies:
                    a['date'] = today
                    a['city'] = city
                    a['feed'] = feed_name
                    all_anomalies.append(a)

            entry = {'date': today, 'count': count}
            if error:
                entry['error'] = error

            if feed_data['history'] and feed_data['history'][-1]['date'] == today:
                feed_data['history'][-1] = entry
            else:
                feed_data['history'].append(entry)

        # Remove feeds from report that no longer have .ics files
        current_basenames = {
            os.path.basename(p).replace('.ics', '')
            for p in glob.glob(f'{city_dir}/*.ics')
        } - {'combined'}
        stale = [k for k in city_data['feeds'] if k not in current_basenames]
        for k in stale:
            del city_data['feeds'][k]

    # Update anomalies (keep all historical anomalies)
    existing_today = {(a['city'], a['feed'], a['type'])
                      for a in report['anomalies']
                      if a.get('date') == today}

    for a in all_anomalies:
        key = (a['city'], a['feed'], a['type'])
        if key not in existing_today:
            report['anomalies'].append(a)

    report['generated'] = now

    save_report(report, report_path)

    # Print summary
    print(f"Report updated: {report_path}")
    print(f"Cities: {len(report['cities'])}")
    total_feeds = sum(len(c['feeds']) for c in report['cities'].values())
    print(f"Total feeds: {total_feeds}")
    if all_anomalies:
        print(f"New anomalies: {len(all_anomalies)}")
        for a in all_anomalies:
            print(f"  [{a['severity']}] {a['city']}/{a['feed']}: {a['message']}")


def main():
    parser = argparse.ArgumentParser(description='Generate feed health report')
    parser.add_argument('--cities', type=str, default='santarosa,bloomington,davis',
                        help='Comma-separated list of cities')
    parser.add_argument('--output', type=str, default='report.json',
                        help='Output JSON file path')
    args = parser.parse_args()
    
    cities = [c.strip() for c in args.cities.split(',')]
    update_report(cities, args.output)


if __name__ == '__main__':
    main()
