import argparse
import requests
from datetime import datetime, date
from icalendar import Calendar, Event
import pytz
from dateutil.parser import parse as dateutil_parse

def fetch_events(base_url, params, year, month):
    all_events = []
    target_date = date(year, month, 1)
    found_target_month = False
    reached_next_month = False

    while not reached_next_month:
        response = requests.get(base_url, params=params)
        data = response.json()

        if not data.get("rawEvents"):
            break  # No more events, exit the loop

        for event in data["rawEvents"]:
            event_date = parse_date(event['start_date'])
            
            if event_date.year > year or (event_date.year == year and event_date.month > month):
                reached_next_month = True
                break
            
            if event_date.year == year and event_date.month == month:
                all_events.append(event)
                found_target_month = True
            elif found_target_month:
                # We've passed our target month
                reached_next_month = True
                break

        params["page"] += 1

    return all_events

def parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d").date()

def create_ical_event(event, timezone):
    ical_event = Event()
    ical_event.add('summary', event['title'])
    ical_event.add('description', event.get('description', ''))

    # Format location
    location = ", ".join(filter(None, [
        event['venue'].get('name'),
        event['venue'].get('address_1'),
        event['venue'].get('address_2'),
        event['venue'].get('town')
    ]))
    ical_event.add('location', location)

    # Parse and add start time
    start = parse_datetime(event['start_date'], event.get('start_time'), timezone)
    ical_event.add('dtstart', start)

    # Parse and add end time if available, otherwise use start time
    if event.get('end_date') or event.get('end_time'):
        end = parse_datetime(event.get('end_date', event['start_date']), event.get('end_time'), timezone)
        ical_event.add('dtend', end)
    else:
        ical_event.add('dtend', start)

    return ical_event

def parse_datetime(date_str, time_str, timezone):
    if time_str:
        # Use dateutil.parser to parse the combined date and time string
        dt = dateutil_parse(f"{date_str}T{time_str}")
    else:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    
    # Localize the datetime to the specified timezone
    return timezone.localize(dt.replace(tzinfo=None))

def generate_ics(events, timezone, output_file):
    cal = Calendar()
    cal.add('prodid', '-//Press Democrat//Event Calendar//EN')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', 'Press Democrat')
    cal.add('x-wr-timezone', str(timezone))

    for event in events:
        ical_event = create_ical_event(event, timezone)
        cal.add_component(ical_event)

    with open(output_file, 'wb') as f:
        f.write(cal.to_ical())

def main():
    parser = argparse.ArgumentParser(description="Generate an ICS file from API events for a specific month.")
    parser.add_argument("year", type=int, help="Year for event filtering (e.g., 2023)")
    parser.add_argument("month", type=int, help="Month for event filtering (1-12)")
    parser.add_argument("--output", help="Output ICS file path", type=str, default='events.ics')
    args = parser.parse_args()

    base_url = "https://discovery.evvnt.com/api/publisher/10553/home_page_events"
    params = {
        "hitsPerPage": 30,
        "multipleEventInstances": "true",
        "publisher_id": 10553,
        "page": 0
    }

    timezone = pytz.timezone('US/Pacific')

    events = fetch_events(base_url, params, args.year, args.month)
    generate_ics(events, timezone, args.output)
    print(f"ICS file generated: {args.output}")
    print(f"Total events included: {len(events)}")

if __name__ == "__main__":
    main()