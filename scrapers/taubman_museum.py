#!/usr/bin/env python3
"""
Scraper for Taubman Museum of Art events.
https://taubmanmuseum.org/events/

Uses the WordPress Tribe ICS feed for event metadata (title, dates, URL),
then fetches each event page to extract a clean description from
.events-main-text-block .col-text — avoiding the full-page HTML dump
that the ICS DESCRIPTION field contains.
"""

import sys
import time
import logging

from bs4 import BeautifulSoup

sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from lib.ics import IcsScraper
from lib.utils import fetch_with_retry, append_source

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = 'https://taubmanmuseum.org'
BASE_URL_WWW = 'https://www.taubmanmuseum.org'
ICS_URL = f'{BASE_URL}/events/?ical=1'
LOCATION = 'Taubman Museum of Art, 110 Salem Ave SE, Roanoke, VA 24011'


def fetch_event_page(url: str) -> tuple[str, str]:
    """Fetch an event page and return (description, image_url).

    Description comes from div.events-main-text <p> tags.
    Image comes from div.banner-main img.
    """
    try:
        html = fetch_with_retry(url, max_retries=3, base_delay=1.0)
        soup = BeautifulSoup(html, 'html.parser')

        desc = ''
        block = soup.select_one('div.events-main-text')
        if block:
            paragraphs = [p.get_text(separator=' ', strip=True) for p in block.find_all('p')]
            desc = '\n\n'.join(p for p in paragraphs if p)

        image_url = ''
        img = soup.select_one('.banner-main img')
        if img:
            image_url = img.get('src', '')
            if image_url and not image_url.startswith('http'):
                image_url = BASE_URL + image_url

        return desc, image_url
    except Exception as e:
        logging.warning(f"Could not fetch event page {url}: {e}")
    return '', ''


class TaubmanMuseumScraper(IcsScraper):
    name = 'Taubman Museum of Art'
    domain = 'taubmanmuseum.org'
    ics_url = ICS_URL
    timezone = 'America/New_York'
    default_location = LOCATION

    def transform_event(self, event):
        url = event.get('url') or ''
        if url and (url.startswith(BASE_URL) or url.startswith(BASE_URL_WWW)):
            desc, image_url = fetch_event_page(url)
            event['description'] = append_source(desc, url)
            if image_url:
                event['image_url'] = image_url
            time.sleep(0.5)  # be polite
        elif url:
            event['description'] = append_source(event.get('description') or '', url)

        if not event.get('location'):
            event['location'] = LOCATION

        return event


def main():
    TaubmanMuseumScraper.setup_logging()
    args = TaubmanMuseumScraper.parse_args('Scrape Taubman Museum of Art events')
    scraper = TaubmanMuseumScraper()
    events = scraper.fetch_events()
    logging.info(f"Fetched {len(events)} events")
    cal = scraper.create_calendar(events)
    ical_data = cal.to_ical().decode('utf-8')
    if args.output:
        with open(args.output, 'w') as f:
            f.write(ical_data)
        logging.info(f"Wrote {args.output}")
    else:
        print(ical_data)


if __name__ == '__main__':
    main()
