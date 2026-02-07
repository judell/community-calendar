#!/usr/bin/env python3
"""
Convert ICS calendar files to JSON format for Supabase ingestion.
"""

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


# Default timezone for converting UTC times
PACIFIC = ZoneInfo('America/Los_Angeles')


def parse_ics_datetime(dt_str):
    """Parse an ICS datetime string to ISO format string (in Pacific time)."""
    if not dt_str:
        return None

    # Handle property parameters like DTSTART;TZID=America/Los_Angeles:20240101T120000
    if ';' in dt_str:
        dt_str = dt_str.split(':')[-1]

    dt_str = dt_str.strip()

    try:
        if dt_str.endswith('Z'):
            # UTC time - convert to Pacific
            dt = datetime.strptime(dt_str, '%Y%m%dT%H%M%SZ')
            dt = dt.replace(tzinfo=timezone.utc).astimezone(PACIFIC)
            return dt.strftime('%Y-%m-%dT%H:%M:%S')
        elif 'T' in dt_str:
            # Local time (already in correct timezone)
            dt = datetime.strptime(dt_str, '%Y%m%dT%H%M%S')
            return dt.strftime('%Y-%m-%dT%H:%M:%S')
        else:
            # All-day event
            dt = datetime.strptime(dt_str, '%Y%m%d')
            return dt.strftime('%Y-%m-%dT%H:%M:%S')
    except ValueError:
        return None


def unfold_ics_lines(content):
    """Unfold ICS continuation lines (lines starting with space or tab)."""
    # ICS spec: long lines are folded by inserting CRLF + space/tab
    content = re.sub(r'\r?\n[ \t]', '', content)
    return content


def extract_field(event_content, field_name):
    """Extract a field value from VEVENT content."""
    # Match field with optional parameters: FIELD;PARAM=VALUE:content or FIELD:content
    pattern = rf'{field_name}[^:]*:([^\r\n]*)'
    match = re.search(pattern, event_content, re.IGNORECASE)
    if match:
        value = match.group(1)
        # Unescape ICS escapes
        value = value.replace('\\n', '\n').replace('\\,', ',').replace('\\;', ';').replace('\\\\', '\\')
        return value.strip()
    return None


def ics_to_json(ics_file, output_file=None, future_only=True, city=None):
    """Convert an ICS file to JSON format for Supabase."""
    content = Path(ics_file).read_text(encoding='utf-8', errors='ignore')

    # Unfold continuation lines
    content = unfold_ics_lines(content)

    events = []
    # Use 24 hours ago to avoid filtering out same-day events due to timezone differences
    from datetime import timedelta
    now = datetime.now(timezone.utc) - timedelta(hours=24)

    # Extract all VEVENT blocks
    pattern = r'BEGIN:VEVENT\r?\n(.*?)\r?\nEND:VEVENT'
    matches = re.findall(pattern, content, re.DOTALL)

    for event_content in matches:
        # Extract fields
        title = extract_field(event_content, 'SUMMARY')
        start_time = parse_ics_datetime(extract_field(event_content, 'DTSTART'))
        end_time = parse_ics_datetime(extract_field(event_content, 'DTEND'))
        location = extract_field(event_content, 'LOCATION')
        description = extract_field(event_content, 'DESCRIPTION')
        url = extract_field(event_content, 'URL')
        source = extract_field(event_content, 'X-SOURCE')
        uid = extract_field(event_content, 'UID')

        # Skip if no title or start time
        if not title or not start_time:
            continue

        # Filter to future events if requested
        if future_only and start_time:
            try:
                event_dt = datetime.fromisoformat(start_time)
                if event_dt.tzinfo is None:
                    event_dt = event_dt.replace(tzinfo=timezone.utc)
                if event_dt < now:
                    continue
            except ValueError:
                pass


        event = {
            'title': title,
            'start_time': start_time,
            'end_time': end_time,
            'location': location or '',
            'description': description or '',
            'url': url or '',
            'city': city or '',
            'source': source or '',
            'source_uid': uid or ''
        }
        events.append(event)

    # Sort by start time
    events.sort(key=lambda x: x['start_time'] or '')

    # Output
    json_output = json.dumps(events, indent=2, ensure_ascii=False)

    if output_file:
        Path(output_file).write_text(json_output, encoding='utf-8')
        print(f"Converted {len(events)} events to {output_file}")
    else:
        print(json_output)

    return events


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert ICS to JSON for Supabase')
    parser.add_argument('input', help='Input ICS file')
    parser.add_argument('-o', '--output', help='Output JSON file (stdout if not specified)')
    parser.add_argument('--city', help='City name (e.g., santarosa, sebastopol)')
    parser.add_argument('--all', action='store_true', help='Include past events (default: future only)')

    args = parser.parse_args()

    ics_to_json(args.input, args.output, future_only=not args.all, city=args.city)
