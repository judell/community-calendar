import argparse
import calendar
import logging
import os
import re
import sys
import warnings
from collections import OrderedDict
from datetime import date, datetime, time

import pytz
import requests
import urllib3
from bs4 import BeautifulSoup
from icalendar import Calendar
from icalendar.prop import vUTCOffset
from jinja2 import Environment, FileSystemLoader

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger()

warnings.simplefilter('ignore', urllib3.exceptions.InsecureRequestWarning)

def truncate_html_description(html_text, max_length=300):
    # Use BeautifulSoup to parse the HTML
    soup = BeautifulSoup(html_text, 'html.parser')
    
    # Extract plain text
    plain_text = soup.get_text()
    
    # Truncate the text to the desired length, adding an ellipsis if necessary
    if len(plain_text) > max_length:
        truncated_text = plain_text[:max_length] + '...'
    else:
        truncated_text = plain_text
    
    return truncated_text

def determine_timezone(vtimezone_info, x_wr_timezone, default_timezone):
    if vtimezone_info:
        # Use the TZID from VTIMEZONE
        tzid = next(iter(vtimezone_info))
        return pytz.timezone(tzid)
    elif x_wr_timezone in pytz.all_timezones:
        # Use X-WR-TIMEZONE if present and valid
        return pytz.timezone(x_wr_timezone)
    elif default_timezone in pytz.all_timezones:
        # Use the provided default_timezone
        logger.info(f"Using default timezone: {default_timezone}")
        return pytz.timezone(default_timezone)
    else:
        # Fall back to UTC if no valid timezone is provided
        logger.warning(f"Invalid default timezone: {default_timezone}. Using UTC.")
        return pytz.UTC
     
def parse_vtimezone(cal):
    timezones = {}
    try:
        for component in cal.walk():
            if component.name == "VTIMEZONE":
                logger.warning(f"Found VTIMEZONE")
                tzid = str(component.get('tzid'))
                if not tzid:
                    logger.warning("VTIMEZONE component missing TZID")
                    continue
                tz_info = {
                    'tzid': tzid,
                    'daylight': None,
                    'standard': None
                }
                for subcomp in component.walk():
                    #logger.info(f"Subcomponent: {subcomp.name}")
                    if subcomp.name in ["DAYLIGHT", "STANDARD"]:
                        try:
                            tz_info[subcomp.name.lower()] = {
                                'tzoffsetfrom': subcomp.get('tzoffsetfrom'),
                                'tzoffsetto': subcomp.get('tzoffsetto'),
                                'tzname': str(subcomp.get('tzname')),
                                'dtstart': subcomp.get('dtstart').dt if subcomp.get('dtstart') else None,
                                'rrule': subcomp.get('rrule')
                            }
                            #logger.info(f"Parsed {subcomp.name}: {tz_info[subcomp.name.lower()]}")
                        except Exception as e:
                            logger.error(f"Error parsing {subcomp.name} component in TZID '{tzid}': {str(e)}")
                            logger.error(f"Error details: {e}")
                            logger.error(f"Subcomponent details: {subcomp}")
                            for key, value in subcomp.items():
                                logger.error(f"  {key}: {value} (type: {type(value)})")
                timezones[tzid] = tz_info
    except Exception as e:
        logger.error(f"Error parsing VTIMEZONE: {str(e)}")
        logger.error(f"Error details: {e}")
    return timezones

def parse_and_localize_event(event, source_tz, target_tz, cal_name):
    dtstart = event.get('dtstart')
    dtend = event.get('dtend')
    
    def convert_to_target_time(dt):
        if dt is None:
            return None
        if isinstance(dt.dt, datetime):
            # If datetime is naive, assume it's in the source timezone
            if dt.dt.tzinfo is None:
                dt_aware = source_tz.localize(dt.dt)
            else:
                dt_aware = dt.dt
            # Convert to target timezone
            return dt_aware.astimezone(target_tz)
        return dt.dt  # Return as-is if it's a date (all-day event)

    local_start = convert_to_target_time(dtstart)
    local_end = convert_to_target_time(dtend)
    
    # Use the date in the target timezone for grouping
    grouping_date = local_start.date() if isinstance(local_start, datetime) else local_start

    url = str(event.get('url'))
    if not url.startswith(('http://', 'https://')):
        url = None

    description = str(event.get('description'))

    return {
        'summary': str(event.get('summary')),
        'start': local_start,
        'end': local_end,
        'location': str(event.get('location')),
        'is_all_day': isinstance(dtstart.dt, date) and not isinstance(dtstart.dt, datetime),
        'description': truncate_html_description(description),
        'url': url,
        'original_start': dtstart.dt,
        'original_end': dtend.dt if dtend else None,
        'grouping_date': grouping_date,
        'source': cal_name
    }

def group_events_by_time(events):
    grouped_events = OrderedDict()
    grouped_events["All Day"] = []

    for event in events:
        if event['is_all_day']:
            grouped_events["All Day"].append(event)
        else:
            start_time = event['start'].strftime('%I:%M %p')
            if start_time not in grouped_events:
                grouped_events[start_time] = []
            grouped_events[start_time].append(event)

    # Remove "All Day" key if there are no all-day events
    if not grouped_events["All Day"]:
        del grouped_events["All Day"]

    # Custom sorting function that respects AM/PM
    def sort_key(time_str):
        if time_str == "All Day":
            return datetime.min  # Ensures "All Day" comes first
        return datetime.strptime(time_str, '%I:%M %p')

    # Sort the keys using the custom sorting function
    sorted_keys = sorted(grouped_events.keys(), key=sort_key)

    # Create a new OrderedDict with sorted keys
    return OrderedDict((k, grouped_events[k]) for k in sorted_keys)

def group_events_by_date(events, year, month):
    grouped_events = OrderedDict()
    for event in events:
        date_key = event['grouping_date']
        
        if date_key.year == year and date_key.month == month:
            if date_key not in grouped_events:
                grouped_events[date_key] = []
            
            grouped_events[date_key].append(event)

    # Group events by time for each day
    for event_date in grouped_events:
        grouped_events[event_date] = group_events_by_time(grouped_events[event_date])
    
    return grouped_events

def create_calendar_weeks(year, month, grouped_events):
    cal = calendar.monthcalendar(year, month)
    calendar_weeks = []
    
    for week in cal:
        calendar_week = []
        for day in week:
            if day == 0:
                calendar_week.append((0, []))
            else:
                date_key = datetime(year, month, day).date()
                events = grouped_events.get(date_key, OrderedDict())
                calendar_week.append((day, events))
        calendar_weeks.append(calendar_week)
    
    return calendar_weeks

def render_html_calendar(grouped_events, year, month, feeds, output_dir='.'):
    env = Environment(loader=FileSystemLoader('.'))
    calendar_template = env.get_template('calendar_template.html')
    list_template = env.get_template('list_template.html')

    calendar_weeks = create_calendar_weeks(year, month, grouped_events)
    month_year = datetime(year, month, 1).strftime('%B %Y')

    # Render calendar view
    rendered_calendar = calendar_template.render(
        calendar_weeks=calendar_weeks,
        month_year=month_year,
        feeds=sorted(feeds, key=lambda x: x['name']),
        year=year,
        month=month
    )

    # Render list view
    rendered_list = list_template.render(
        grouped_events=grouped_events,
        calendar_weeks=calendar_weeks,  # Add this line
        month_year=month_year,
        feeds=sorted(feeds, key=lambda x: x['name']),
        year=year,
        month=month
    )

    # Save calendar view
    calendar_filename = f"{year:04d}-{month:02d}.html"
    calendar_path = os.path.join(output_dir, calendar_filename)
    with open(calendar_path, 'w') as f:
        f.write(rendered_calendar)
    print(f"Calendar view generated: {calendar_path}")

    # Save list view
    list_filename = f"{year:04d}-{month:02d}-l.html"
    list_path = os.path.join(output_dir, list_filename)
    with open(list_path, 'w') as f:
        f.write(rendered_list)
    print(f"List view generated: {list_path}")

def determine_timezone(vtimezone_info, x_wr_timezone, default_timezone):
    def vutcoffset_to_minutes(offset):
        if isinstance(offset, vUTCOffset):
            return int(offset.td.total_seconds() / 60)
        elif isinstance(offset, int):
            return offset
        else:
            logger.warning(f"Warning: Unexpected offset type {type(offset)}. Using default timezone.")
            return None

    if vtimezone_info and vtimezone_info.get('daylight') and vtimezone_info.get('standard'):
        daylight_offset = vtimezone_info['daylight'].get('tzoffsetto')
        standard_offset = vtimezone_info['standard'].get('tzoffsetto')
        
        offset = daylight_offset or standard_offset
        offset_minutes = vutcoffset_to_minutes(offset)
        if offset_minutes is not None:
            return pytz.FixedOffset(offset_minutes)
    
    if x_wr_timezone in pytz.all_timezones:
        return pytz.timezone(x_wr_timezone)
    
    if default_timezone in pytz.all_timezones:
        logger.warning(f"Using default timezone: {default_timezone}")
        return pytz.timezone(default_timezone)
    
    logger.warning("Unable to determine timezone and invalid default timezone. Using UTC.")
    return pytz.UTC

def fetch_and_process_calendar(url, default_timezone):
    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()
        content = response.text

        # Extract calendar name
        match = re.search(r'X-WR-CALNAME:(.*?)(?:\r\n|\r|\n)', content)
        cal_name = match.group(1).strip() if match else "Unnamed Calendar"

        logger.info(f'{cal_name}, {url}')

        # Process the calendar content
        cal = Calendar.from_ical(content)

        vtimezone_info = parse_vtimezone(cal)
        x_wr_timezone = cal.get('X-WR-TIMEZONE')

        source_tz = determine_timezone(vtimezone_info, x_wr_timezone, default_timezone)
        target_tz = pytz.timezone(default_timezone)

        logger.info(f"Calendar: {cal_name}")
        logger.info(f"Source timezone: {source_tz}")
        logger.info(f"Target timezone: {target_tz}")

        processed_events = []
        oldest_day = None
        newest_day = None

        for event in cal.walk('VEVENT'):
            if 'CATEGORIES' in event:
                logger.info(f"CATEGORIES {event['CATEGORIES'].to_ical().decode('utf-8')} [[{event['SUMMARY']}]]")
            processed_event = parse_and_localize_event(event, source_tz, target_tz, cal_name)
            processed_events.append(processed_event)

            event_date = processed_event['start'].date() if isinstance(processed_event['start'], datetime) else processed_event['start']

            if oldest_day is None or event_date < oldest_day:
                oldest_day = event_date
            if newest_day is None or event_date > newest_day:
                newest_day = event_date

        total_events = len(processed_events)
        logger.info(f"Processed {total_events} events")

        return cal_name, processed_events, total_events, oldest_day, newest_day

    except Exception as e:
        logger.error(f"Error processing URL {url}: {str(e)}")
        return "Unnamed Calendar", [], 0, None, None

def read_and_process_feeds(file_path, default_timezone):
    feeds = []
    all_events = []
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith('#'):
                url = line
                name, events, total_events, oldest_day, newest_day = fetch_and_process_calendar(url, default_timezone)
                feeds.append({
                    'name': name,
                    'url': url,
                    'total_events': total_events,
                    'oldest_day': oldest_day.strftime('%Y-%m-%d') if oldest_day else 'N/A',
                    'newest_day': newest_day.strftime('%Y-%m-%d') if newest_day else 'N/A'
                })
                all_events.extend(events)
    return feeds, all_events

def generate_calendar(file_path, year, month, default_timezone, output_dir='.'):
    feeds, all_events = read_and_process_feeds(file_path, default_timezone)
    grouped_events = group_events_by_date(all_events, year, month)
    render_html_calendar(grouped_events, year, month, feeds, output_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate an HTML calendar from iCalendar feeds or perform a dry run.")
    parser.add_argument("--dry-run", help="Perform a dry run on a single iCalendar URL", type=str)
    parser.add_argument("--generate", action="store_true", help="Generate an HTML calendar from feeds.txt, a list of iCalendar feeds")
    parser.add_argument("--timezone", help="Default timezone (default: America/Indiana/Indianapolis)", 
                        type=str, default='America/Indiana/Indianapolis')
    parser.add_argument("--year", help="Year for calendar generation", type=int, default=datetime.now().year)
    parser.add_argument("--month", help="Month for calendar generation", type=int, default=datetime.now().month)
    parser.add_argument("--location", help="Folder containing feeds.txt and for output (required for --generate)", type=str)
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    if args.generate and not args.location:
        print("Error: --location is required when using --generate")
        parser.print_help()
        sys.exit(1)

    if args.location and not os.path.isdir(args.location):
        print(f"Error: The specified location '{args.location}' is not a valid directory.")
        sys.exit(1)

    if args.dry_run:
        name, events, total_events, oldest_day, newest_day = fetch_and_process_calendar(args.dry_run, args.timezone)
        print(f"Calendar Name: {name}")
        print(f"Number of events: {total_events}")
        print(f"Oldest event date: {oldest_day.strftime('%Y-%m-%d') if oldest_day else 'N/A'}")
        print(f"Newest event date: {newest_day.strftime('%Y-%m-%d') if newest_day else 'N/A'}")
        print("\nFirst few events:")
        for event in events[:5]:
            print(f"  - {event['summary']}")
            if event['is_all_day']:
                print(f"    All-day event on {event['start']}")
            else:
                print(f"    Original Start: {event['original_start']}")
                print(f"    Adjusted Start: {event['start']}")
            print()  # Add a blank line between events for readability
    elif args.generate:
        feeds_file = os.path.join(args.location, 'feeds.txt')
        if not os.path.isfile(feeds_file):
            print(f"Error: feeds.txt not found in the specified location '{args.location}'.")
            sys.exit(1)
        generate_calendar(feeds_file, args.year, args.month, args.timezone, args.location)
    else:
        print("Please specify either --dry-run or --generate")
        parser.print_help()
        sys.exit(1)