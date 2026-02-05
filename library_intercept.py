import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event
from datetime import datetime
import pytz
import re
import argparse
from dateutil.relativedelta import relativedelta

# Library-specific configurations
LIBRARY_CONFIGS = {
    'santarosa': {
        'base_url': 'https://events.sonomalibrary.org/events/list?page=',
        'url_prefix': 'https://events.sonomalibrary.org',
        'timezone': 'America/Los_Angeles',
        'prodid': '-//Santa Rosa Library Events//',
        'calname': 'Santa Rosa Library'
    },
    'bloomington': {
        'base_url': 'https://www.bloomingtonlibrary.org/events/list?page=',
        'url_prefix': 'https://www.bloomingtonlibrary.org',
        'timezone': 'America/Indiana/Indianapolis',
        'prodid': '-//Bloomington Library Events//',
        'calname': 'Bloomington Library'
    }
}

def scrape_events(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    events = soup.find_all('div', class_='lc-list-event-content-container')
    return events

def parse_event(event, target_month_end, url_prefix):
    try:
        title_element = event.find('h2')
        if not title_element or not title_element.find('a'):
            print("Debug - Event missing title or URL")
            return None
        title = title_element.text.strip()
        url = url_prefix + title_element.find('a')['href']

        date_element = event.find('div', class_='lc-list-event-info-item--date')
        if not date_element:
            print("Debug - Event missing date information")
            return None
        date_str = date_element.text.strip()

        location_element = event.find('div', class_='lc-list-event-location')
        location = location_element.text.strip() if location_element else "Location not specified"

        description_element = event.find('div', class_='lc-list-event-description')
        description = description_element.text.strip() if description_element else "No description available"

        # Clean up the date string
        date_str = ' '.join(date_str.split())

        # Parse date and time
        date_pattern = r'(\w+, \w+ \d{1,2}, \d{4}) at (\d{1,2}:\d{2}(?:am|pm)) - (\d{1,2}:\d{2}(?:am|pm))'
        match = re.match(date_pattern, date_str)

        if not match:
            print(f"Debug - Failed to parse date or time from: {date_str}")
            return None

        date_str, start_time_str, end_time_str = match.groups()

        date = datetime.strptime(date_str, '%A, %B %d, %Y')
        start_time = datetime.strptime(start_time_str, '%I:%M%p')
        end_time = datetime.strptime(end_time_str, '%I:%M%p')

        start_datetime = date.replace(hour=start_time.hour, minute=start_time.minute)
        end_datetime = date.replace(hour=end_time.hour, minute=end_time.minute)

        # Skip events in or after the next month
        if start_datetime >= target_month_end:
            return None

        return {
            'summary': title,
            'description': description,
            'location': location,
            'dtstart': start_datetime,
            'dtend': end_datetime,
            'url': url
        }
    except Exception as e:
        print(f"Debug - Error parsing event: {str(e)}")
        return None

def create_ical(events, library_config):
    cal = Calendar()
    cal.add('prodid', library_config['prodid'])
    cal.add('x-wr-calname', library_config['calname'])

    tz = pytz.timezone(library_config['timezone'])

    for event_data in events:
        if event_data is None:
            continue
        event = Event()
        event.add('summary', event_data['summary'])
        event.add('description', event_data['description'])
        event.add('location', event_data['location'])
        event.add('dtstart', tz.localize(event_data['dtstart']))
        event.add('dtend', tz.localize(event_data['dtend']))
        event.add('url', event_data['url'])
        cal.add_component(event)

    return cal

def main(year, month, location):
    library_config = LIBRARY_CONFIGS.get(location)
    if not library_config:
        raise ValueError(f"Unsupported location: {location}")

    base_url = library_config['base_url']
    page = 1
    all_events = []
    target_month_start = datetime(year, month, 1)
    # Use first day of next month for comparison (events on last day of month should be included)
    target_month_end = target_month_start + relativedelta(months=1)

    while True:
        url = base_url + str(page)
        print(f"Scraping page {page}")
        events = scrape_events(url)

        if not events:
            break

        parsed_events = [parse_event(event, target_month_end, library_config['url_prefix']) for event in events]
        parsed_events = [event for event in parsed_events if event is not None]

        if not parsed_events:
            # If all events on the page are after the target month or couldn't be parsed, stop scraping
            break

        all_events.extend(parsed_events)
        page += 1

    ical = create_ical(all_events, library_config)

    output_file = f"./{location}/library_intercept_{year}_{month:02d}.ics"
    with open(output_file, 'wb') as f:
        f.write(ical.to_ical())

    print(f"Exported {len(all_events)} events to {output_file}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scrape library events for a specific year and month.')
    parser.add_argument('--location', type=str, required=True, choices=['santarosa', 'bloomington'], help='Library to scrape')
    parser.add_argument('--year', type=int, required=True, help='Target year (e.g., 2024)')
    parser.add_argument('--month', type=int, required=True, help='Target month (1-12)')
    args = parser.parse_args()

    if args.month < 1 or args.month > 12:
        raise ValueError("Month must be between 1 and 12")

    main(args.year, args.month, args.location)