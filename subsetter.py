import re
import argparse
from datetime import datetime

def filter_events(year, month, src_location, dst_location, id, cal_name, target, timezone):
    input_file = f'./{src_location}/{id}_{year}_{month}.ics'
    # Read the .ics file
    with open(input_file, 'r') as file:
        lines = file.readlines()

    # Initialize variables
    filtered_events = []
    inside_event = False
    current_event = []

    for line in lines:
        if line.startswith('BEGIN:VEVENT'):
            inside_event = True
            current_event = [line]  # Start a new event
        elif line.startswith('END:VEVENT'):
            current_event.append(line)
            inside_event = False
            # Check if the event is in the target location and matches the specified year and month
            event_date = None
            for event_line in current_event:
                if event_line.startswith('DTSTART'):
                    event_date_str = event_line.split(':')[1].strip()
                    try:
                        # Try parsing with 'Z' (UTC) format
                        event_date = datetime.strptime(event_date_str, '%Y%m%dT%H%M%SZ')
                    except ValueError:
                        # If that fails, try without 'Z'
                        event_date = datetime.strptime(event_date_str, '%Y%m%dT%H%M%S')
                    break

            if event_date and event_date.strftime('%Y') == year and event_date.strftime('%m') == month:
                if any(re.search(f'LOCATION:.*{re.escape(target)}', event_line) for event_line in current_event):
                    filtered_events.extend(current_event)  # Add the event to the list if it's in the target location
        elif inside_event:
            current_event.append(line)  # Continue adding lines to the current event    

    # Write the filtered events to a new .ics file
    output_file = f'./{dst_location}/{id}_{year}_{month}.ics'
    with open(output_file, 'w') as file:
        file.writelines(f"""BEGIN:VCALENDAR
VERSION:2.0
CALSCALE:GREGORIAN
METHOD:PUBLISH
PRODID:-//{cal_name}//
X-WR-CALNAME:{cal_name}
X-WR-TIMEZONE:{timezone}
BEGIN:VTIMEZONE
TZID:{timezone}
X-LIC-LOCATION:{timezone}
BEGIN:STANDARD
TZOFFSETFROM:-0700
TZOFFSETTO:-0800
TZNAME:PST
DTSTART:19701101T020000
RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU
END:STANDARD
BEGIN:DAYLIGHT
TZOFFSETFROM:-0800
TZOFFSETTO:-0700
TZNAME:PDT
DTSTART:19700308T020000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU
END:DAYLIGHT
END:VTIMEZONE
""")
        file.writelines(filtered_events)
        file.writelines("""END:VCALENDAR
""")

    print(f"Filtered events saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Filter .ics file by year, month, and location.')
    parser.add_argument('--year', type=str, required=True, help='Year to filter events by.')
    parser.add_argument('--month', type=str, required=True, help='Month to filter events by (1-12).')
    parser.add_argument('--src_location', type=str, required=True, help='Source location folder name.')
    parser.add_argument('--dst_location', type=str, required=True, help='Destination location folder name.')
    parser.add_argument('--id', type=str, required=True, help='id of the event source.')
    parser.add_argument('--cal_name', type=str, required=True, help='Name for the calendar.')
    parser.add_argument('--target', type=str, required=True, help='Target location to filter events.')
    parser.add_argument('--timezone', type=str, required=True, help='Timezone for the events.')

    args = parser.parse_args()

    filter_events(args.year, args.month, args.src_location, args.dst_location, args.id, args.cal_name, args.target, args.timezone)