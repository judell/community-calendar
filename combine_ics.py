#!/usr/bin/env python3
"""
Combine multiple ICS files into a single subscribable calendar feed.
Filters to only include events from today forward.
"""

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path

# Map filenames to friendly source names
SOURCE_NAMES = {
    'arlene_francis_theater': 'Arlene Francis Center',
    'luther_burbank_center': 'Luther Burbank Center',
    'schulz_museum': 'Charles M. Schulz Museum',
    'sonoma_com': 'Sonoma.com',
    'golocal_coop': 'GoLocal Cooperative',
    'sonoma_county_aa': 'Sonoma County AA',
    'sonoma_county_dsa': 'Sonoma County DSA',
    'museumsc': 'Museum of Sonoma County',
    'library_intercept': 'Sonoma County Library',
    'sonoma_county_gov': 'Sonoma County Government',
    'sonoma_parks': 'Sonoma County Parks',
    'cal_theatre': 'Cal Theatre',
    'copperfields': "Copperfield's Books",
    'bohemian': 'North Bay Bohemian',
    'eventbrite': 'Eventbrite',
    'pressdemocrat': 'Press Democrat',
    'SRCity': 'City of Santa Rosa',
}

# Fallback URLs for sources that don't provide event URLs
SOURCE_URLS = {
    'arlene_francis_theater': 'https://arlenefranciscenter.org/calendar/',
    'luther_burbank_center': 'https://lutherburbankcenter.org/events/',
    'schulz_museum': 'https://schulzmuseum.org/events/',
    'sonoma_com': 'https://www.sonoma.com/events/',
    'golocal_coop': 'https://golocal.coop/events/',
    'sonoma_county_aa': 'https://sonomacountyaa.org/events/',
    'sonoma_county_dsa': 'https://dsasonomacounty.org/events/',
    'library_intercept': 'https://sonomalibrary.org/events',
    'sonoma_county_gov': 'https://sonomacounty.ca.gov/calendar/',
    'sonoma_parks': 'https://parks.sonomacounty.ca.gov/events/',
    'cal_theatre': 'https://www.facebook.com/CalTheatrePT/',
    'copperfields': 'https://www.copperfieldsbooks.com/events',
    'SRCity': 'https://srcity.org/calendar.aspx',
}


def get_source_name(filename):
    """Get friendly source name from filename."""
    stem = Path(filename).stem
    if stem.startswith('SRCity_'):
        return 'City of Santa Rosa'
    return SOURCE_NAMES.get(stem, stem.replace('_', ' ').title())


def get_fallback_url(filename):
    """Get fallback URL for a source."""
    stem = Path(filename).stem
    if stem.startswith('SRCity_'):
        return SOURCE_URLS.get('SRCity')
    return SOURCE_URLS.get(stem)


def parse_ics_datetime(dt_str):
    """Parse an ICS datetime string to a datetime object."""
    if ';' in dt_str:
        dt_str = dt_str.split(':')[-1]
    
    dt_str = dt_str.strip()
    
    try:
        if dt_str.endswith('Z'):
            return datetime.strptime(dt_str, '%Y%m%dT%H%M%SZ').replace(tzinfo=timezone.utc)
        elif 'T' in dt_str:
            return datetime.strptime(dt_str, '%Y%m%dT%H%M%S')
        else:
            return datetime.strptime(dt_str, '%Y%m%d')
    except ValueError:
        return None


def extract_events(ics_content, source_name=None, fallback_url=None):
    """Extract VEVENT blocks from ICS content."""
    events = []

    pattern = r'BEGIN:VEVENT\r?\n(.*?)\r?\nEND:VEVENT'
    matches = re.findall(pattern, ics_content, re.DOTALL)

    for event_content in matches:
        dtstart_match = re.search(r'DTSTART[^:]*:([^\r\n]+)', event_content)
        if dtstart_match:
            dt = parse_ics_datetime(dtstart_match.group(1))
            if dt:
                # Add fallback URL if no URL exists
                if fallback_url and 'URL:' not in event_content:
                    event_content = f'URL:{fallback_url}\r\n{event_content}'

                # Add or update source in description
                if source_name:
                    # Check if DESCRIPTION exists
                    desc_match = re.search(r'DESCRIPTION:([^\r\n]*(?:\r?\n [^\r\n]*)*)', event_content)
                    source_line = f'Source: {source_name}'
                    
                    if desc_match:
                        old_desc = desc_match.group(1)
                        # Don't add if source already mentioned
                        if 'Source:' not in old_desc:
                            new_desc = old_desc.rstrip() + '\\n\\n' + source_line
                            event_content = event_content.replace(
                                f'DESCRIPTION:{old_desc}',
                                f'DESCRIPTION:{new_desc}'
                            )
                    else:
                        # Add DESCRIPTION with source
                        event_content = f'DESCRIPTION:{source_line}\r\n{event_content}'
                    
                    # Also add X-SOURCE header
                    if 'X-SOURCE' not in event_content:
                        event_content = f'X-SOURCE:{source_name}\r\n{event_content}'
                
                events.append({
                    'dtstart': dt,
                    'content': event_content
                })
    
    return events


def combine_ics_files(input_dir, output_file, calendar_name="Combined Calendar"):
    """Combine all ICS files in a directory into one."""
    all_events = []
    # Use 24 hours ago to avoid filtering out same-day events due to timezone differences
    from datetime import timedelta
    now = datetime.now(timezone.utc) - timedelta(hours=24)
    
    ics_dir = Path(input_dir)
    for ics_file in sorted(ics_dir.glob('*.ics')):
        # Skip the output file if it exists
        if ics_file.name == Path(output_file).name:
            continue
            
        try:
            content = ics_file.read_text(encoding='utf-8', errors='ignore')
            source_name = get_source_name(ics_file.name)
            fallback_url = get_fallback_url(ics_file.name)
            events = extract_events(content, source_name, fallback_url)
            
            # Filter to future events only
            future_events = [e for e in events if e['dtstart'].replace(tzinfo=timezone.utc) >= now]
            all_events.extend(future_events)
            
            if future_events:
                print(f"  {len(future_events):4d} future events from {ics_file.name} ({source_name})")
        except Exception as e:
            print(f"  Error processing {ics_file.name}: {e}")
    
    # Sort by start time
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
