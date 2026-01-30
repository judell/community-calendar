import requests
import sys
from icalendar import Calendar, Event, vText
from datetime import datetime

# Press Democrat uses CitySpark API (same as Bohemian)
# ppid: 8662, slug: SRPressDemocrat

def fetch_all_events(year, month):
    results = []
    skip = 0
    tps = 25
    has_more_data = True

    while has_more_data:
        url = 'https://portal.cityspark.com/v1/events/SRPressDemocrat'
        payload = {
            "ppid": 8662,
            "start": f"{year}-{month:02d}-01T00:00:00",
            "end": None,
            "distance": 40,
            "lat": 38.5212368,
            "lng": -122.8540282,
            "sort": "Popularity",
            "skip": skip,
            "tps": "24"
        }
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.post(url, json=payload, headers=headers)
        data = response.json()

        if 'Value' in data and data['Value'] is not None:
            for event in data['Value']:
                event_start = datetime.fromisoformat(event['StartUTC'].replace('Z', '+00:00'))
                
                if event_start.year > int(year) or (event_start.year == int(year) and event_start.month > int(month)):
                    has_more_data = False
                    break

                results.append(event)

            if has_more_data:
                if len(data['Value']) < tps:
                    has_more_data = False
                else:
                    skip += tps
        else:
            print(f'No "Value" key found in response for skip={skip}. Stopping.')
            has_more_data = False

    return results

def generate_icalendar(events, year, month):
    cal = Calendar()
    cal.add('prodid', '-//Press Democrat Events//pressdemocrat.com//')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', 'Press Democrat')
    cal.add('x-wr-timezone', 'US/Pacific')

    for event in events:
        event_start = datetime.fromisoformat(event['StartUTC'].replace('Z', '+00:00'))
        
        if event['EndUTC']:
            event_end = datetime.fromisoformat(event['EndUTC'].replace('Z', '+00:00'))
        else:
            event_end = event_start

        if event_start.year == int(year) and event_start.month == int(month):
            cal_event = Event()
            cal_event.add('summary', event['Name'])
            cal_event.add('dtstart', event_start)
            cal_event.add('dtend', event_end)
            cal_event.add('location', vText(event.get('Venue', '')))
            cal_event.add('description', event.get('Description', ''))
            cal_event.add('uid', event.get('Id', event.get('PId', '')))
            if event.get('Links') and len(event['Links']) > 0:
                cal_event.add('url', event['Links'][0].get('url', ''))
            cal.add_component(cal_event)

    return cal

def main(year, month):
    events = fetch_all_events(year, month)
    calendar = generate_icalendar(events, year, month)
    
    filename = f"pressdemocrat_{year}_{month:02d}.ics"
    with open(filename, 'wb') as f:
        f.write(calendar.to_ical())
    print(f"iCalendar feed generated: {filename}")
    print(f"Total events: {len(events)}")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python pressdemocrat.py <year> <month>")
        sys.exit(1)

    year = sys.argv[1]
    month = int(sys.argv[2])

    main(year, month)
