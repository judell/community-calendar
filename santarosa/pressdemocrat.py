import requests
import sys
from icalendar import Calendar, Event, vText
from datetime import datetime, timedelta

# Press Democrat uses CitySpark API (same as Bohemian)
# ppid: 8662, slug: SRPressDemocrat

def fetch_all_events(year, month):
    """Fetch all events for the given year/month from CitySpark API.
    
    The API returns events sorted by date descending (newest first),
    so we paginate through all results and filter for the target month.
    """
    results = []
    seen_ids = set()
    tps = 100  # API caps at 100 anyway
    
    # Calculate month boundaries
    month_start = datetime(int(year), int(month), 1)
    if month == 12:
        end_year, end_month = year + 1, 1
    else:
        end_year, end_month = year, month + 1
    month_end = datetime(int(end_year), int(end_month), 1)
    
    # Use API's date filtering
    start_str = month_start.strftime("%Y-%m-%dT%H:%M:%S")
    end_str = month_end.strftime("%Y-%m-%dT%H:%M:%S")
    
    skip = 0
    while True:
        url = 'https://portal.cityspark.com/v1/events/SRPressDemocrat'
        payload = {
            "ppid": 8662,
            "start": start_str,
            "end": end_str,
            "distance": 40,
            "lat": 38.5212368,
            "lng": -122.8540282,
            "sort": "Date",
            "skip": skip,
            "tps": str(tps)
        }
        headers = {'Content-Type': 'application/json'}

        response = requests.post(url, json=payload, headers=headers)
        data = response.json()

        if 'Value' not in data or data['Value'] is None or len(data['Value']) == 0:
            break

        for event in data['Value']:
            event_start = datetime.fromisoformat(event['StartUTC'].replace('Z', '+00:00'))
            
            # Skip duplicates
            event_id = event.get('Id', event.get('PId', ''))
            if event_id in seen_ids:
                continue
            seen_ids.add(event_id)
            
            # Only include events in target month (API may return edge cases)
            if event_start.year == int(year) and event_start.month == int(month):
                results.append(event)

        if len(data['Value']) < tps:
            break
        skip += tps
    
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
            desc = event.get('Description', '') or ''
            desc = desc.rstrip() + '\n\nSource: Press Democrat' if desc else 'Source: Press Democrat'
            cal_event.add('description', desc)
            cal_event.add('uid', event.get('Id', event.get('PId', '')))
            if event.get('Links') and len(event['Links']) > 0:
                cal_event.add('url', event['Links'][0].get('url', ''))
            cal_event.add('x-source', 'Press Democrat')
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
