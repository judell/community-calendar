import re
import argparse
from datetime import datetime

def filter_events(year, month):
    input_file = f'../santarosa/eventbrite_{year}_{month}.ics'
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
            # Check if the event is in Sebastopol and matches the specified year and month
            event_date = None
            for event_line in current_event:
                if event_line.startswith('DTSTART'):
                    event_date_str = event_line.split(':')[1].strip()
                    event_date = datetime.strptime(event_date_str, '%Y%m%dT%H%M%SZ')
                    break

            if event_date and event_date.strftime('%Y') == year and event_date.strftime('%m') == month:
                if any('LOCATION:Sebastopol' in event_line for event_line in current_event):
                    filtered_events.extend(current_event)  # Add the event to the list if it's in Sebastopol
        elif inside_event:
            current_event.append(line)  # Continue adding lines to the current event    

    # Write the filtered events to a new .ics file
    output_file = f'eventbrite_{year}_{month}.ics'
    with open(output_file, 'w') as file:
        file.writelines("""BEGIN:VCALENDAR
VERSION:2.0
CALSCALE:GREGORIAN
METHOD:PUBLISH
PRODID:-//Eventbrite Santa Rosa Events//
X-WR-CALNAME:Eventbrite Santa Rosa Events
X-WR-TIMEZONE:US/Pacific
BEGIN:VTIMEZONE
TZID:US/Pacific
X-LIC-LOCATION:US/Pacific
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

    args = parser.parse_args()

    filter_events(args.year, args.month)
