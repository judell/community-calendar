#!/usr/bin/env python3
"""
Generate feed health report after aggregation runs.

Updates report.json with:
- Per-city, per-feed event counts
- Historical data (unlimited)
- Anomaly detection
"""

import argparse
import json
import os
import re
from datetime import datetime, date
from pathlib import Path
from typing import Optional
import urllib.request
import urllib.error

# Anomaly thresholds
DROP_THRESHOLD = 0.5  # 50% drop from previous
MIN_EVENTS_FOR_DROP = 5  # Only flag drops if previous had at least this many


def count_events_in_ics(filepath: str) -> tuple[int, Optional[str]]:
    """Count VEVENT entries in an ICS file. Returns (count, error)."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        count = content.count('BEGIN:VEVENT')
        return count, None
    except FileNotFoundError:
        return 0, 'file_not_found'
    except Exception as e:
        return 0, str(e)[:100]


def fetch_and_count_url(url: str, timeout: int = 30) -> tuple[int, Optional[str]]:
    """Fetch ICS from URL and count events. Returns (count, error)."""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; CalendarBot/1.0)'
        })
        with urllib.request.urlopen(req, timeout=timeout) as response:
            content = response.read().decode('utf-8', errors='ignore')
        count = content.count('BEGIN:VEVENT')
        return count, None
    except urllib.error.HTTPError as e:
        return 0, f'http_{e.code}'
    except urllib.error.URLError as e:
        return 0, f'url_error: {str(e.reason)[:50]}'
    except TimeoutError:
        return 0, 'timeout'
    except Exception as e:
        return 0, str(e)[:100]


def parse_feeds_file(feeds_path: str) -> list[dict]:
    """Parse a feeds.txt file and return list of feed info."""
    feeds = []
    try:
        with open(feeds_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Determine if URL or local file
                if line.startswith('http://') or line.startswith('https://'):
                    name = extract_feed_name_from_url(line)
                    feeds.append({'type': 'url', 'path': line, 'name': name})
                else:
                    name = extract_feed_name_from_path(line)
                    feeds.append({'type': 'file', 'path': line, 'name': name})
    except FileNotFoundError:
        pass
    return feeds


def extract_feed_name_from_url(url: str) -> str:
    """Extract a readable name from a feed URL."""
    # Google calendar
    if 'google.com/calendar' in url:
        match = re.search(r'/ical/([^/]+)/', url)
        if match:
            return match.group(1).split('@')[0].replace('%40', '@')
    
    # Domain-based name
    match = re.search(r'https?://(?:www\.)?([^/]+)', url)
    if match:
        domain = match.group(1)
        # Clean up
        domain = domain.replace('.org', '').replace('.com', '').replace('.gov', '')
        return domain
    
    return url[:50]


def extract_feed_name_from_path(path: str) -> str:
    """Extract a readable name from a local file path."""
    filename = os.path.basename(path)
    name = filename.replace('.ics', '')
    return name


def detect_anomalies(feed_name: str, current: int, history: list[dict]) -> list[dict]:
    """Detect anomalies for a feed. Returns list of anomaly dicts."""
    anomalies = []
    
    if not history:
        return anomalies
    
    # Get previous non-error entry
    prev = None
    for h in reversed(history):
        if h.get('error') is None:
            prev = h
            break
    
    if prev is None:
        return anomalies
    
    prev_count = prev['count']
    
    # Went to zero
    if current == 0 and prev_count > 0:
        anomalies.append({
            'type': 'zero_events',
            'message': f'Feed returned 0 events (was {prev_count})',
            'severity': 'high'
        })
    
    # Significant drop
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
        feeds_file = f'cities/{city}/feeds.txt'
        feeds = parse_feeds_file(feeds_file)
        
        if city not in report['cities']:
            report['cities'][city] = {'feeds': {}}
        
        city_data = report['cities'][city]
        
        for feed in feeds:
            feed_name = feed['name']
            feed_path = feed['path']
            feed_type = feed['type']
            
            # Get or create feed entry
            if feed_name not in city_data['feeds']:
                city_data['feeds'][feed_name] = {
                    'path': feed_path,
                    'type': feed_type,
                    'history': []
                }
            
            feed_data = city_data['feeds'][feed_name]
            
            # Update path in case it changed
            feed_data['path'] = feed_path
            feed_data['type'] = feed_type
            
            # Count events
            if feed_type == 'url':
                count, error = fetch_and_count_url(feed_path)
            else:
                count, error = count_events_in_ics(feed_path)
            
            # Check for anomalies
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
            
            # Add to history
            entry = {
                'date': today,
                'count': count,
            }
            if error:
                entry['error'] = error
            
            # Don't duplicate if already ran today
            if feed_data['history'] and feed_data['history'][-1]['date'] == today:
                feed_data['history'][-1] = entry
            else:
                feed_data['history'].append(entry)
    
    # Update anomalies (keep all historical anomalies)
    # Add new ones that aren't duplicates of today
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
