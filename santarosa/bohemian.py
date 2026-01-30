import requests
import sys
from icalendar import Calendar, Event, vText
from datetime import datetime

def fetch_all_events(year, month):
    results = []
    skip = 0
    tps = 25  # Adjust this based on the typical batch size returned by the API
    has_more_data = True

    while has_more_data:
        # Define the API endpoint and the request payload
        url = 'https://portal.cityspark.com/v1/events/Bohemian'
        payload = {
            "ppid": 9093,
            "start": f"{year}-{month:02d}-01T00:00:00",
            "end": None,
            "distance": 30,
            "lat": 38.4282591,
            "lng": -122.5548637,
            "sort": "Popularity",
            "skip": skip,
            "tps": "24"  # Adjust if needed
            # Include other necessary fields if required
        }
        headers = {
            'Content-Type': 'application/json'
        }

        # Make the API request
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()

        # Check if the 'Value' key exists and is not None
        if 'Value' in data and data['Value'] is not None:
            for event in data['Value']:
                event_start = datetime.fromisoformat(event['StartUTC'].replace('Z', '+00:00'))
                
                # Check if the event is beyond the end of the specified month
                if event_start.year > int(year) or (event_start.year == int(year) and event_start.month > int(month)):
                    has_more_data = False
                    break

                results.append(event)

            # If we haven't decided to stop yet, increment the skip value
            if has_more_data:
                if len(data['Value']) < tps:
                    has_more_data = False  # No more data left to fetch
                else:
                    skip += tps  # Increment skip to fetch the next batch
        else:
            print(f'No "Value" key found in response for skip={skip}. Stopping.')
            has_more_data = False

    return results

def generate_icalendar(events, year, month):
    cal = Calendar()
    cal.add('prodid', '-//Bohemian Events//bohemian.com//')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', 'Bohemian')
    cal.add('x-wr-timezone', 'US/Pacific')

    for event in events:
        event_start = datetime.fromisoformat(event['StartUTC'].replace('Z', '+00:00'))
        
        if event['EndUTC']:
            event_end = datetime.fromisoformat(event['EndUTC'].replace('Z', '+00:00'))
        else:
            event_end = event_start  # Default to event start if end is None

        if event_start.year == int(year) and event_start.month == int(month):
            cal_event = Event()
            cal_event.add('summary', event['Name'])
            cal_event.add('dtstart', event_start)
            cal_event.add('dtend', event_end)
            cal_event.add('location', vText(event.get('Venue', '')))
            cal_event.add('description', event.get('Description', ''))
            cal_event.add('uid', event['Id'])
            cal_event.add('url', event['Links'][0]['url'] if event.get('Links') else None)
            cal.add_component(cal_event)

    return cal

def main(year, month):
    events = fetch_all_events(year, month)
    calendar = generate_icalendar(events, year, month)
    
    # Save the .ics file
    filename = f"bohemian_{year}_{month:02d}.ics"
    with open(filename, 'wb') as f:
        f.write(calendar.to_ical())
    print(f"iCalendar feed generated: {filename}")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python bohemian.py <year> <month>")
        sys.exit(1)

    year = sys.argv[1]
    month = int(sys.argv[2])

    main(year, month)
