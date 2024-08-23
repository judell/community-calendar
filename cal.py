import argparse
import requests
from icalendar import Calendar
from icalendar.prop import vUTCOffset
from datetime import datetime, date, time
import pytz
from jinja2 import Environment, FileSystemLoader
import warnings
import calendar
import urllib3
from pprint import pprint
import logging
import sys
from collections import OrderedDict
import re
import os

logging.basicConfig(level=logging.INFO)

warnings.simplefilter('ignore', urllib3.exceptions.InsecureRequestWarning)

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
        logging.info(f"Using default timezone: {default_timezone}")
        return pytz.timezone(default_timezone)
    else:
        # Fall back to UTC if no valid timezone is provided
        logging.warning(f"Invalid default timezone: {default_timezone}. Using UTC.")
        return pytz.UTC
     
def parse_vtimezone(cal):
    timezones = {}
    try:
        for component in cal.walk():
            if component.name == "VTIMEZONE":
                logging.warning(f"Found VTIMEZONE")
                tzid = str(component.get('tzid'))
                if not tzid:
                    logging.warning("VTIMEZONE component missing TZID")
                    continue
                tz_info = {
                    'tzid': tzid,
                    'daylight': None,
                    'standard': None
                }
                for subcomp in component.walk():
                    #logging.info(f"Subcomponent: {subcomp.name}")
                    if subcomp.name in ["DAYLIGHT", "STANDARD"]:
                        try:
                            tz_info[subcomp.name.lower()] = {
                                'tzoffsetfrom': subcomp.get('tzoffsetfrom'),
                                'tzoffsetto': subcomp.get('tzoffsetto'),
                                'tzname': str(subcomp.get('tzname')),
                                'dtstart': subcomp.get('dtstart').dt if subcomp.get('dtstart') else None,
                                'rrule': subcomp.get('rrule')
                            }
                            #logging.info(f"Parsed {subcomp.name}: {tz_info[subcomp.name.lower()]}")
                        except Exception as e:
                            logging.error(f"Error parsing {subcomp.name} component in TZID '{tzid}': {str(e)}")
                            logging.error(f"Error details: {e}")
                            logging.error(f"Subcomponent details: {subcomp}")
                            for key, value in subcomp.items():
                                logging.error(f"  {key}: {value} (type: {type(value)})")
                timezones[tzid] = tz_info
    except Exception as e:
        logging.error(f"Error parsing VTIMEZONE: {str(e)}")
        logging.error(f"Error details: {e}")
    return timezones

def parse_and_localize_event(event, source_tz, target_tz):
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
    
    return {
        'summary': str(event.get('summary')),
        'start': local_start,
        'end': local_end,
        'location': str(event.get('location')),
        'description': str(event.get('description')),
        'is_all_day': isinstance(dtstart.dt, date) and not isinstance(dtstart.dt, datetime),
        'url': str(event.get('url'))
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

    # Sort the keys, ensuring "All Day" stays first if it exists
    sorted_keys = sorted(grouped_events.keys(), key=lambda x: x if x != "All Day" else "")

    # Create a new OrderedDict with sorted keys
    return OrderedDict((k, grouped_events[k]) for k in sorted_keys)

def group_events_by_date(events, year, month):
    grouped_events = OrderedDict()
    for event in events:
        dtstart = event['start']
        
        if dtstart is None:
            logging.warning(f"Event with summary '{event.get('summary')}' has no start time. Skipping.")
            continue
        
        # Convert date to datetime if necessary
        if isinstance(dtstart, date) and not isinstance(dtstart, datetime):
            dtstart = datetime.combine(dtstart, time.min)
        
        if dtstart.tzinfo is not None:
            dtstart = dtstart.astimezone(pytz.UTC).replace(tzinfo=None)
        
        date_key = dtstart.date()
        
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
    template = env.get_template('calendar_template.html')
    
    calendar_weeks = create_calendar_weeks(year, month, grouped_events)
    month_year = datetime(year, month, 1).strftime('%B %Y')

    rendered_html = template.render(
        calendar_weeks=calendar_weeks,
        month_year=month_year,
        feeds=sorted(feeds, key=lambda x: x['name'])
    )

    output_filename = f"{year:04d}-{month:02d}.html"
    output_path = os.path.join(output_dir, output_filename)

    with open(output_path, 'w') as f:
        f.write(rendered_html)

    print(f"Calendar generated: {output_path}")

def determine_timezone(vtimezone_info, x_wr_timezone, default_timezone):
    def vutcoffset_to_minutes(offset):
        if isinstance(offset, vUTCOffset):
            return int(offset.td.total_seconds() / 60)
        elif isinstance(offset, int):
            return offset
        else:
            logging.warning(f"Warning: Unexpected offset type {type(offset)}. Using default timezone.")
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
        logging.warning(f"Using default timezone: {default_timezone}")
        return pytz.timezone(default_timezone)
    
    logging.warning("Unable to determine timezone and invalid default timezone. Using UTC.")
    return pytz.UTC

def fetch_and_process_calendar(url, default_timezone):
    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()
        content = response.text

        # Extract calendar name
        match = re.search(r'X-WR-CALNAME:(.*?)(?:\r\n|\r|\n)', content)
        cal_name = match.group(1).strip() if match else "Unnamed Calendar"

        # Process the calendar content
        cal = Calendar.from_ical(content)

        vtimezone_info = parse_vtimezone(cal)
        x_wr_timezone = cal.get('X-WR-TIMEZONE')

        source_tz = determine_timezone(vtimezone_info, x_wr_timezone, default_timezone)
        target_tz = pytz.timezone(default_timezone)

        logging.info(f"Calendar: {cal_name}")
        logging.info(f"Source timezone: {source_tz}")
        logging.info(f"Target timezone: {target_tz}")

        processed_events = []
        oldest_day = None
        newest_day = None

        for event in cal.walk('VEVENT'):
            processed_event = parse_and_localize_event(event, source_tz, target_tz)
            processed_events.append(processed_event)

            event_date = processed_event['start'].date() if isinstance(processed_event['start'], datetime) else processed_event['start']

            if oldest_day is None or event_date < oldest_day:
                oldest_day = event_date
            if newest_day is None or event_date > newest_day:
                newest_day = event_date

        total_events = len(processed_events)
        logging.info(f"Processed {total_events} events")

        return cal_name, processed_events, total_events, oldest_day, newest_day

    except Exception as e:
        logging.error(f"Error processing URL {url}: {str(e)}")
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
    parser.add_argument("--generate", action="store_true", help="Generate the HTML calendar")
    parser.add_argument("--timezone", help="Default timezone (default: America/Indiana/Indianapolis)", 
                        type=str, default='America/Indiana/Indianapolis')
    parser.add_argument("--year", help="Year for calendar generation", type=int, default=datetime.now().year)
    parser.add_argument("--month", help="Month for calendar generation", type=int, default=datetime.now().month)
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    if args.dry_run:
        name, events, total_events, oldest_day, newest_day = fetch_and_process_calendar(args.dry_run, args.timezone)
        print(f"Calendar Name: {name}")
        print(f"Number of events: {total_events}")
        print(f"Oldest event date: {oldest_day.strftime('%Y-%m-%d') if oldest_day else 'N/A'}")
        print(f"Newest event date: {newest_day.strftime('%Y-%m-%d') if newest_day else 'N/A'}")
        print("\nFirst few events:")
        for event in events[:5]:  # Display details of first 5 events
            print(f"  - {event['summary']} on {event['start']}")
    elif args.generate:
        generate_calendar('feeds.txt', args.year, args.month, args.timezone)
    else:
        print("Please specify either --dry-run or --generate")
        parser.print_help()
        sys.exit(1)
