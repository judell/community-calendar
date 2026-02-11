#!/usr/bin/env python3
"""
Barrel Proof Lounge scraper - scrapes directly from their website

This scraper extracts events from the Barrel Proof Lounge homepage which 
displays accurate event times (via their Eventbrite widget, but with times
that match their internal system).

Usage:
  python barrel_proof.py --output cities/santarosa/barrel_proof.ics
"""

import argparse
import re
import sys
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
import html as html_module

HOMEPAGE_URL = "https://barrelprooflounge.com/"
VENUE_NAME = "Barrel Proof Lounge"
VENUE_ADDRESS = "501 Mendocino Ave, Santa Rosa, CA 95401"

def fetch_page(url):
    """Fetch a URL and return HTML"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=30) as resp:
            return resp.read().decode('utf-8')
    except (HTTPError, URLError) as e:
        print(f"  Error fetching {url}: {e}", file=sys.stderr)
        return None

def parse_events(html):
    """Parse event data from the homepage HTML"""
    events = []
    
    # The site uses Eventbrite widgets with structure:
    # - Image with alt="EVENT TITLE"
    # - Title link: <a id="wfea-popup-title-..." title="...">EVENT TITLE</a>
    # - Date: visible as "February 10, 2026, 5:00 pm – 7:00 pm"
    # - Description in a div
    
    # Find all event blocks by looking for wfea event patterns
    # Pattern: data-eb-id="EVENTID" ... title ... date ... description
    
    # Split into event sections - each event starts with a figure/image block
    event_blocks = re.split(r'<figure[^>]*class="[^"]*wfea[^"]*"', html)
    
    for block in event_blocks[1:]:  # Skip content before first event
        # Extract event title from link or image alt
        title_match = re.search(r'title="[^"]*(?:link to |for )([^"]+)"', block)
        if not title_match:
            title_match = re.search(r'alt="([^"]+)"', block)
        if not title_match:
            continue
            
        title = html_module.unescape(title_match.group(1).strip())
        
        # Extract datetime: "February 10, 2026, 5:00 pm – 7:00 pm"
        datetime_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d+),\s+(20\d{2}),\s+(\d+):(\d+)\s+(am|pm)(?:\s*[–-]\s*(?:(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d+),\s+(20\d{2}),\s+)?(\d+):(\d+)\s+(am|pm))?'
        
        dt_match = re.search(datetime_pattern, block, re.IGNORECASE)
        if not dt_match:
            continue
            
        # Parse start datetime
        month_names = {'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
                       'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12}
        
        try:
            month = month_names[dt_match.group(1).lower()]
            day = int(dt_match.group(2))
            year = int(dt_match.group(3))
            hour = int(dt_match.group(4))
            minute = int(dt_match.group(5))
            ampm = dt_match.group(6).lower()
            
            if ampm == 'pm' and hour != 12:
                hour += 12
            elif ampm == 'am' and hour == 12:
                hour = 0
                
            start_dt = datetime(year, month, day, hour, minute)
            
            # Parse end time if present
            if dt_match.group(10):  # End hour exists
                end_hour = int(dt_match.group(10))
                end_minute = int(dt_match.group(11))
                end_ampm = dt_match.group(12).lower()
                
                if end_ampm == 'pm' and end_hour != 12:
                    end_hour += 12
                elif end_ampm == 'am' and end_hour == 12:
                    end_hour = 0
                
                # Check if end date is specified
                if dt_match.group(7):  # End month exists
                    end_month = month_names[dt_match.group(7).lower()]
                    end_day = int(dt_match.group(8))
                    end_year = int(dt_match.group(9))
                    end_dt = datetime(end_year, end_month, end_day, end_hour, end_minute)
                else:
                    # Same day
                    end_dt = datetime(year, month, day, end_hour, end_minute)
                    # Handle overnight events
                    if end_dt < start_dt:
                        end_dt = end_dt + timedelta(days=1)
            else:
                # Default 2 hour event
                end_dt = start_dt + timedelta(hours=2)
        except (ValueError, TypeError) as e:
            print(f"  Warning: Could not parse date for {title}: {e}", file=sys.stderr)
            continue
        
        # Extract description from nearby text
        desc = ""
        # Look for text between closing </h2> and next major tag, or in a div
        desc_match = re.search(r'</h2>\s*</header>\s*<div[^>]*>\s*([^<]+)', block)
        if desc_match:
            desc = html_module.unescape(desc_match.group(1).strip())
        
        # Get eventbrite URL
        eb_match = re.search(r'data-eb-id="(\d+)"', block)
        if eb_match:
            eb_id = eb_match.group(1)
            url = f"https://www.eventbrite.com/e/{eb_id}"
        else:
            url = HOMEPAGE_URL
        
        events.append({
            'title': title,
            'start': start_dt,
            'end': end_dt,
            'description': desc,
            'url': url
        })
    
    return events

def event_to_ics(event):
    """Convert event dict to ICS VEVENT"""
    title = event['title'].replace(',', '\\,').replace(';', '\\;')
    desc = event['description'].replace('\n', '\\n').replace(',', '\\,').replace(';', '\\;')
    desc = desc[:500] + '...' if len(desc) > 500 else desc
    
    uid = f"barrelproof-{event['start'].strftime('%Y%m%d%H%M')}-{hash(event['title']) % 100000}"
    
    lines = [
        'BEGIN:VEVENT',
        f'UID:{uid}@barrelprooflounge.com',
        f'DTSTART:{event["start"].strftime("%Y%m%dT%H%M%S")}',
        f'DTEND:{event["end"].strftime("%Y%m%dT%H%M%S")}',
        f'SUMMARY:{title}',
        f'LOCATION:{VENUE_NAME}\\, {VENUE_ADDRESS}',
    ]
    
    if desc:
        lines.append(f'DESCRIPTION:{desc}\\n\\nSource: Barrel Proof Lounge')
    else:
        lines.append('DESCRIPTION:Source: Barrel Proof Lounge')
    
    lines.extend([
        f'URL:{event["url"]}',
        'END:VEVENT'
    ])
    return '\n'.join(lines)

def main():
    parser = argparse.ArgumentParser(description='Scrape Barrel Proof Lounge events')
    parser.add_argument('--output', '-o', help='Output ICS file')
    args = parser.parse_args()
    
    print(f"Fetching: {HOMEPAGE_URL}", file=sys.stderr)
    html = fetch_page(HOMEPAGE_URL)
    if not html:
        print("Failed to fetch homepage", file=sys.stderr)
        sys.exit(1)
    
    events = parse_events(html)
    print(f"Found {len(events)} events", file=sys.stderr)
    
    for e in events:
        print(f"  {e['start'].strftime('%m/%d %I:%M%p')} - {e['title'][:60]}", file=sys.stderr)
    
    ics_events = [event_to_ics(e) for e in events]
    
    ics_content = '\n'.join([
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//Community Calendar//Barrel Proof Lounge Scraper//EN',
        'X-WR-CALNAME:Barrel Proof Lounge',
        *ics_events,
        'END:VCALENDAR'
    ])
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(ics_content)
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(ics_content)

if __name__ == '__main__':
    main()
