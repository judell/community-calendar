#!/usr/bin/env python3
"""
Combine multiple ICS files into a single subscribable calendar feed.
Filters to only include events from today forward.
"""

import argparse
import os
import re
from datetime import datetime, timezone
from pathlib import Path


def parse_ics_datetime(dt_str):
    """Parse an ICS datetime string to a datetime object."""
    # Remove any TZID prefix
    if ';' in dt_str:
        dt_str = dt_str.split(':')[-1]
    
    dt_str = dt_str.strip()
    
    # Handle different formats
    try:
        if dt_str.endswith('Z'):
            return datetime.strptime(dt_str, '%Y%m%dT%H%M%SZ').replace(tzinfo=timezone.utc)
        elif 'T' in dt_str:
            return datetime.strptime(dt_str, '%Y%m%dT%H%M%S')
        else:
            return datetime.strptime(dt_str, '%Y%m%d')
    except ValueError:
        return None


def extract_events(ics_content, source_name=None):
    """Extract VEVENT blocks from ICS content."""
    events = []
    
    # Find all VEVENT blocks
    pattern = r'BEGIN:VEVENT\r?\n(.*?)\r?\nEND:VEVENT'
    matches = re.findall(pattern, ics_content, re.DOTALL)
    
    for event_content in matches:
        # Parse DTSTART to check if event is in the future
        dtstart_match = re.search(r'DTSTART[^:]*:([^\r\n]+)', event_content)
        if dtstart_match:
            dt = parse_ics_datetime(dtstart_match.group(1))
            if dt:
                # Add source as X-SOURCE if not present and source_name provided
                if source_name and 'X-SOURCE' not in event_content:
                    event_content = f'X-SOURCE:{source_name}\r\n{event_content}'
                
                events.append({
                    'dtstart': dt,
                    'content': event_content
                })
    
    return events


def combine_ics_files(input_dir, output_file, calendar_name="Combined Calendar"):
    """Combine all ICS files in a directory into one."""
    all_events = []
    now = datetime.now(timezone.utc)
    
    # Process all .ics files
    ics_dir = Path(input_dir)
    for ics_file in ics_dir.glob('*.ics'):
        try:
            content = ics_file.read_text(encoding='utf-8', errors='ignore')
            source_name = ics_file.stem.replace('_', ' ').title()
            events = extract_events(content, source_name)
            
            # Filter to future events only
            future_events = [e for e in events if e['dtstart'].replace(tzinfo=timezone.utc) >= now]
            all_events.extend(future_events)
            
            if future_events:
                print(f"  {len(future_events):4d} future events from {ics_file.name}")
        except Exception as e:
            print(f"  Error processing {ics_file.name}: {e}")
    
    # Sort by start time (normalize to UTC for comparison)
    def normalize_dt(dt):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    all_events.sort(key=lambda x: normalize_dt(x['dtstart']))
    
    # Remove duplicates based on UID
    seen_uids = set()
    unique_events = []
    for event in all_events:
        uid_match = re.search(r'UID:([^\r\n]+)', event['content'])
        if uid_match:
            uid = uid_match.group(1)
            if uid not in seen_uids:
                seen_uids.add(uid)
                unique_events.append(event)
        else:
            unique_events.append(event)
    
    # Build combined ICS
    output = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//Community Calendar//Combined Feed//EN',
        'CALSCALE:GREGORIAN',
        'METHOD:PUBLISH',
        f'X-WR-CALNAME:{calendar_name}',
        'REFRESH-INTERVAL;VALUE=DURATION:PT1H',
        'X-PUBLISHED-TTL:PT1H',
    ]
    
    for event in unique_events:
        output.append('BEGIN:VEVENT')
        output.append(event['content'])
        output.append('END:VEVENT')
    
    output.append('END:VCALENDAR')
    
    # Write output
    Path(output_file).write_text('\r\n'.join(output), encoding='utf-8')
    
    print(f"\nCombined {len(unique_events)} unique future events into {output_file}")
    return len(unique_events)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Combine ICS files into a single feed')
    parser.add_argument('--input-dir', '-i', required=True, help='Directory containing ICS files')
    parser.add_argument('--output', '-o', required=True, help='Output ICS file')
    parser.add_argument('--name', '-n', default='Community Calendar', help='Calendar name')
    
    args = parser.parse_args()
    
    print(f"Combining ICS files from {args.input_dir}...")
    combine_ics_files(args.input_dir, args.output, args.name)
