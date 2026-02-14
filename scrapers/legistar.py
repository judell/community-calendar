#!/usr/bin/env python3
"""
Convert Legistar WebAPI JSON to ICS format.
Usage: python scripts/legistar_to_ics.py --client santa-rosa -o output.ics
"""

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
import urllib.request
import urllib.parse
import hashlib

def fetch_events(client, months_ahead=12):
    """Fetch future events from Legistar WebAPI."""
    today = datetime.now().strftime('%Y-%m-%d')
    future = (datetime.now() + timedelta(days=months_ahead * 30)).strftime('%Y-%m-%d')
    
    # OData filter for future events
    filter_param = f"EventDate ge datetime'{today}'"
    params = {
        '$filter': filter_param,
        '$orderby': 'EventDate asc',
    }
    
    url = f"https://webapi.legistar.com/v1/{client}/events?{urllib.parse.urlencode(params)}"
    
    req = urllib.request.Request(url, headers={'Accept': 'application/json'})
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())

def escape_ics(text):
    """Escape text for ICS format."""
    if not text:
        return ''
    return text.replace('\\', '\\\\').replace(',', '\\,').replace(';', '\\;').replace('\n', '\\n').replace('\r', '')

def fold_line(line, max_len=75):
    """Fold long lines per ICS spec."""
    if len(line) <= max_len:
        return line
    result = [line[:max_len]]
    line = line[max_len:]
    while line:
        result.append(' ' + line[:max_len-1])
        line = line[max_len-1:]
    return '\r\n'.join(result)

def events_to_ics(events, source_name="Legistar"):
    """Convert events to ICS format."""
    lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//Community Calendar//Legistar Scraper//EN',
        f'X-WR-CALNAME:{source_name}',
    ]
    
    for event in events:
        # Skip cancelled events
        if event.get('EventAgendaStatusName') == 'Cancelled':
            continue
            
        event_date = event.get('EventDate', '')[:10]  # YYYY-MM-DD
        event_time = event.get('EventTime', '')
        
        # Parse time (e.g., "2:00 PM" or "02:00  PM")
        try:
            # Clean up time string
            time_str = ' '.join(event_time.split())  # normalize whitespace
            dt = datetime.strptime(f"{event_date} {time_str}", "%Y-%m-%d %I:%M %p")
            dtstart = dt.strftime('%Y%m%dT%H%M%S')
            dtend = (dt + timedelta(hours=2)).strftime('%Y%m%dT%H%M%S')  # Assume 2hr meetings
        except (ValueError, AttributeError):
            # Fall back to all-day event
            dtstart = event_date.replace('-', '')
            dtend = dtstart
        
        body_name = event.get('EventBodyName', 'Meeting')
        location = event.get('EventLocation', '').replace('\r\n', ', ').replace('\n', ', ')
        url = event.get('EventInSiteURL', '')
        
        # Create unique ID
        uid_base = f"{event.get('EventId')}-{event.get('EventGuid', '')}"
        uid = hashlib.md5(uid_base.encode()).hexdigest() + '@legistar.com'
        
        # Build description
        desc_parts = [f"Board/Commission: {body_name}"]
        if event.get('EventAgendaFile'):
            desc_parts.append(f"Agenda: {event['EventAgendaFile']}")
        if event.get('EventComment'):
            desc_parts.append(f"Note: {event['EventComment']}")
        desc_parts.append(f"\nSource: {source_name}")
        description = '\\n'.join(desc_parts)
        
        lines.extend([
            'BEGIN:VEVENT',
            f'UID:{uid}',
            f'DTSTART:{dtstart}',
            f'DTEND:{dtend}',
            fold_line(f'SUMMARY:{escape_ics(body_name)}'),
            fold_line(f'LOCATION:{escape_ics(location)}'),
            fold_line(f'DESCRIPTION:{escape_ics(description)}'),
            f'URL:{url}',
            f'DTSTAMP:{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")}',
            'END:VEVENT',
        ])
    
    lines.append('END:VCALENDAR')
    return '\r\n'.join(lines)

def main():
    parser = argparse.ArgumentParser(description='Convert Legistar events to ICS')
    parser.add_argument('--client', required=True, help='Legistar client name (e.g., santa-rosa)')
    parser.add_argument('--source', default=None, help='Source name for display')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)')
    parser.add_argument('--months', type=int, default=12, help='Months ahead to fetch')
    args = parser.parse_args()
    
    source_name = args.source or f"City of {args.client.replace('-', ' ').title()} Legistar"
    
    events = fetch_events(args.client, args.months)
    print(f"Fetched {len(events)} events from Legistar", file=sys.stderr)
    
    ics = events_to_ics(events, source_name)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(ics)
        print(f"Wrote {args.output}", file=sys.stderr)
    else:
        print(ics)

if __name__ == '__main__':
    main()
