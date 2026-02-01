#!/usr/bin/env python3
"""
Scraper for Cafe Frida Gallery events.
https://www.cafefridagallery.com/events

Events are server-side rendered in a Wix Repeater component.
Uses only stdlib - no external dependencies.
"""

import urllib.request
import re
import sys
import html
from datetime import datetime
from zoneinfo import ZoneInfo

# Import icalendar - this is used by other scrapers in the project
from icalendar import Calendar, Event, vText

PACIFIC = ZoneInfo('America/Los_Angeles')
LOCATION = "Cafe Frida Gallery, 305 S A St, Santa Rosa, CA"
SOURCE = "Cafe Frida Gallery"
URL = "https://www.cafefridagallery.com/events"


def fetch_html():
    """Fetch HTML from Cafe Frida Gallery website."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    req = urllib.request.Request(URL, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode('utf-8')


def parse_events(html_content):
    """Parse events from HTML using regex (no BeautifulSoup needed)."""
    events = []

    # Find each listitem block containing an event
    # Pattern: role="listitem" ... up to next role="listitem" or end
    listitem_pattern = r'role="listitem"[^>]*>(.*?)(?=role="listitem"|</section>)'
    listitems = re.findall(listitem_pattern, html_content, re.DOTALL)

    for item_html in listitems:
        try:
            # Extract title (comp-l93ch30e - font_7 28px element)
            title_match = re.search(
                r'class="[^"]*comp-l93ch30e[^"]*"[^>]*>.*?<p[^>]*>(.*?)</p>',
                item_html, re.DOTALL
            )
            if not title_match:
                continue
            title = re.sub(r'<[^>]+>', '', title_match.group(1))
            title = html.unescape(title).strip()

            if not title:
                continue

            # Extract date (comp-l93egplp)
            date_match = re.search(
                r'class="[^"]*comp-l93egplp[^"]*"[^>]*>.*?<p[^>]*>(.*?)</p>',
                item_html, re.DOTALL
            )
            date_str = ''
            if date_match:
                date_str = re.sub(r'<[^>]+>', '', date_match.group(1))
                date_str = html.unescape(date_str).strip()

            # Extract time (comp-l94lcdfy)
            time_match = re.search(
                r'class="[^"]*comp-l94lcdfy[^"]*"[^>]*>.*?<p[^>]*>(.*?)</p>',
                item_html, re.DOTALL
            )
            time_str = ''
            if time_match:
                time_str = re.sub(r'<[^>]+>', '', time_match.group(1))
                time_str = html.unescape(time_str).strip()

            # Extract description (comp-l93ch30n)
            desc_match = re.search(
                r'class="[^"]*comp-l93ch30n[^"]*"[^>]*>.*?<p[^>]*>(.*?)</p>',
                item_html, re.DOTALL
            )
            description = ''
            if desc_match:
                description = re.sub(r'<[^>]+>', '', desc_match.group(1))
                description = html.unescape(description).strip()

            # Extract category (comp-l93ch2zz)
            cat_match = re.search(
                r'class="[^"]*comp-l93ch2zz[^"]*"[^>]*>.*?<h6[^>]*>(.*?)</h6>',
                item_html, re.DOTALL
            )
            category = ''
            if cat_match:
                category = re.sub(r'<[^>]+>', '', cat_match.group(1))
                category = html.unescape(category).strip()

            # Parse date: "Sunday, February 1, 2026" or "February 1, 2026"
            event_date = None
            if date_str:
                dm = re.search(r'(\w+)\s+(\d+),\s+(\d{4})', date_str)
                if dm:
                    month_str, day, year = dm.groups()
                    try:
                        event_date = datetime.strptime(f"{month_str} {day} {year}", "%B %d %Y")
                    except ValueError:
                        pass

            if not event_date:
                continue

            # Parse time: "11:30am-1:30pm"
            start_time = None
            end_time = None
            time_str_clean = time_str.lower().replace(' ', '')
            tm = re.match(r'(\d{1,2}):?(\d{2})?(am|pm)-(\d{1,2}):?(\d{2})?(am|pm)', time_str_clean)
            if tm:
                sh, sm, sap, eh, em, eap = tm.groups()
                sm = sm or '00'
                em = em or '00'

                start_hour = int(sh)
                if sap == 'pm' and start_hour != 12:
                    start_hour += 12
                elif sap == 'am' and start_hour == 12:
                    start_hour = 0

                end_hour = int(eh)
                if eap == 'pm' and end_hour != 12:
                    end_hour += 12
                elif eap == 'am' and end_hour == 12:
                    end_hour = 0

                start_time = event_date.replace(hour=start_hour, minute=int(sm), tzinfo=PACIFIC)
                end_time = event_date.replace(hour=end_hour, minute=int(em), tzinfo=PACIFIC)
            else:
                # Default to noon if no time parsed
                start_time = event_date.replace(hour=12, minute=0, tzinfo=PACIFIC)
                end_time = event_date.replace(hour=13, minute=0, tzinfo=PACIFIC)

            events.append({
                'title': title,
                'start': start_time,
                'end': end_time,
                'description': description,
                'category': category,
            })

        except Exception as e:
            print(f"Error parsing event: {e}", file=sys.stderr)
            continue

    return events


def generate_icalendar(events, year, month):
    """Generate ICS calendar from events."""
    cal = Calendar()
    cal.add('prodid', '-//Cafe Frida Gallery Events//cafefridagallery.com//')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', 'Cafe Frida Gallery')
    cal.add('x-wr-timezone', 'America/Los_Angeles')

    for event in events:
        # Filter by year/month
        if event['start'].year != int(year) or event['start'].month != int(month):
            continue

        cal_event = Event()
        cal_event.add('summary', event['title'])
        cal_event.add('dtstart', event['start'])
        cal_event.add('dtend', event['end'])
        cal_event.add('location', vText(LOCATION))

        desc = event['description'] or ''
        if event['category']:
            desc = f"[{event['category']}] {desc}"
        desc = desc.rstrip() + '\n\nSource: ' + SOURCE if desc else 'Source: ' + SOURCE
        cal_event.add('description', desc)

        # Generate UID from title and date
        uid = f"{event['start'].strftime('%Y%m%d')}-{re.sub(r'[^a-z0-9]', '-', event['title'].lower())[:30]}@cafefridagallery.com"
        cal_event.add('uid', uid)
        cal_event.add('url', URL)
        cal_event.add('x-source', SOURCE)

        cal.add_component(cal_event)

    return cal


def main(year, month, output=None):
    print(f"Fetching events from {URL}", file=sys.stderr)
    html_content = fetch_html()

    events = parse_events(html_content)
    print(f"Parsed {len(events)} total events", file=sys.stderr)

    calendar = generate_icalendar(events, year, month)

    # Count events in target month
    month_events = [e for e in events if e['start'].year == int(year) and e['start'].month == int(month)]

    filename = output or f"cafefrida_{year}_{month:02d}.ics"
    with open(filename, 'wb') as f:
        f.write(calendar.to_ical())
    print(f"Generated {filename} with {len(month_events)} events")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Scrape Cafe Frida Gallery events')
    parser.add_argument('--year', type=int, required=True, help='Year to scrape')
    parser.add_argument('--month', type=int, required=True, help='Month to scrape')
    parser.add_argument('--output', '-o', help='Output file path')
    args = parser.parse_args()

    main(args.year, args.month, args.output)
