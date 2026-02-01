import requests
import sys
from icalendar import Calendar, Event, vText
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

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
        url = 'https://portal.cityspark.com/v1/events/Bohemian'
        payload = {
            "ppid": 9093,
            "start": start_str,
            "end": end_str,
            "distance": 30,
            "lat": 38.4282591,
            "lng": -122.5548637,
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
            if event['Id'] in seen_ids:
                continue
            seen_ids.add(event['Id'])
            
            # Only include events in target month (API may return edge cases)
            if event_start.year == int(year) and event_start.month == int(month):
                results.append(event)

        if len(data['Value']) < tps:
            break
        skip += tps
    
    return results

def generate_icalendar(events, year, month):
    cal = Calendar()
    cal.add('prodid', '-//Bohemian Events//bohemian.com//')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', 'Bohemian')
    cal.add('x-wr-timezone', 'America/Los_Angeles')

    pacific = ZoneInfo('America/Los_Angeles')

    for event in events:
        # Parse UTC time and convert to Pacific
        event_start_utc = datetime.fromisoformat(event['StartUTC'].replace('Z', '+00:00'))
        event_start = event_start_utc.astimezone(pacific)

        if event['EndUTC']:
            event_end_utc = datetime.fromisoformat(event['EndUTC'].replace('Z', '+00:00'))
            event_end = event_end_utc.astimezone(pacific)
        else:
            event_end = event_start  # Default to event start if end is None

        if event_start.year == int(year) and event_start.month == int(month):
            cal_event = Event()
            cal_event.add('summary', event['Name'])
            cal_event.add('dtstart', event_start)
            cal_event.add('dtend', event_end)
            cal_event.add('location', vText(event.get('Venue', '')))
            desc = event.get('Description', '') or ''
            desc = desc.rstrip() + '\n\nSource: North Bay Bohemian' if desc else 'Source: North Bay Bohemian'
            cal_event.add('description', desc)
            cal_event.add('uid', event['Id'])
            cal_event.add('url', event['Links'][0]['url'] if event.get('Links') else None)
            cal_event.add('x-source', 'North Bay Bohemian')
            cal.add_component(cal_event)

    return cal

def main(year, month, output=None):
    events = fetch_all_events(year, month)
    calendar = generate_icalendar(events, year, month)

    # Save the .ics file
    filename = output or f"bohemian_{year}_{month:02d}.ics"
    with open(filename, 'wb') as f:
        f.write(calendar.to_ical())
    print(f"iCalendar feed generated: {filename}")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Scrape North Bay Bohemian events')
    parser.add_argument('--year', type=int, required=True, help='Year to scrape')
    parser.add_argument('--month', type=int, required=True, help='Month to scrape')
    parser.add_argument('--output', '-o', help='Output file path')
    args = parser.parse_args()

    main(args.year, args.month, args.output)
