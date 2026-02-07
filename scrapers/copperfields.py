#!/usr/bin/env python3
"""
Scraper for Copperfield's Books events
https://copperfieldsbooks.com/upcoming-events

Drupal site with clean HTML structure.
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import re
from datetime import datetime, timedelta
from typing import Any

import requests
from bs4 import BeautifulSoup

from lib.base import BaseScraper
from lib.utils import DEFAULT_HEADERS, MONTH_MAP


class CopperfieldsScraper(BaseScraper):
    """Scraper for Copperfield's Books events."""

    name = "Copperfield's Books"
    domain = "copperfieldsbooks.com"

    BASE_URL = 'https://copperfieldsbooks.com'
    EVENTS_URL = f'{BASE_URL}/upcoming-events'

    STORE_LOCATIONS = {
        'petaluma': '140 Kentucky Street, Petaluma, CA 94952',
        'sebastopol': '138 N Main St, Sebastopol, CA 95472',
        'healdsburg': '104 Matheson Street, Healdsburg, CA 95448',
        'san rafael': '850 Fourth Street, San Rafael, CA 94901',
        'napa': '1300 First Street Suite 398, Napa, CA 94558',
        'calistoga': '1330 Lincoln Avenue, Calistoga, CA 94515',
        'montgomery village': '2316 Montgomery Drive, Santa Rosa, CA 95405',
    }

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch and parse events from the events page."""
        self.logger.info(f"Fetching {self.EVENTS_URL}")
        response = requests.get(self.EVENTS_URL, headers=DEFAULT_HEADERS, timeout=30)
        response.raise_for_status()

        return self._parse_events(response.text)

    def _parse_events(self, html_content: str) -> list[dict[str, Any]]:
        """Parse events from the events listing page."""
        soup = BeautifulSoup(html_content, 'html.parser')
        events = []
        seen_events = set()

        # Infer year from current date
        now = datetime.now()

        for row in soup.find_all('div', class_='views-row'):
            try:
                # Get event title and link
                title_elem = row.find('h2') or row.find('h3') or row.find(class_='title')
                if not title_elem:
                    continue

                link = title_elem.find('a') or row.find('a', href=re.compile(r'/event/'))
                if not link:
                    continue

                title = title_elem.get_text(strip=True)
                event_url = link.get('href', '')
                if not event_url.startswith('http'):
                    event_url = self.BASE_URL + event_url

                # Dedupe
                if event_url in seen_events:
                    continue
                seen_events.add(event_url)

                # Get date from the date element
                date_elem = row.find(class_=re.compile(r'date'))
                if not date_elem:
                    continue

                date_text = date_elem.get_text(' ', strip=True)

                # Parse date: "Feb 03" or similar
                date_match = re.search(r'([A-Za-z]{3})\s+(\d{1,2})', date_text)
                if not date_match:
                    continue

                month_abbr = date_match.group(1)
                day = int(date_match.group(2))

                month = MONTH_MAP.get(month_abbr.lower())
                if not month:
                    continue

                # Infer year - if month is in the past, it might be next year
                year = now.year
                if month < now.month:
                    year = now.year + 1

                # Get location from tags or text
                location = None
                location_text = row.get_text(' ', strip=True).lower()
                for loc_name, address in self.STORE_LOCATIONS.items():
                    if loc_name in location_text:
                        location = f"Copperfield's Books, {address}"
                        break

                if not location:
                    location = "Copperfield's Books"

                # Get time if available - default to evening
                time_elem = row.find(class_=re.compile(r'time'))
                if time_elem:
                    time_text = time_elem.get_text(strip=True)
                    time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)', time_text, re.IGNORECASE)
                    if time_match:
                        hour = int(time_match.group(1))
                        minute = int(time_match.group(2) or 0)
                        ampm = time_match.group(3).lower()
                        if ampm == 'pm' and hour != 12:
                            hour += 12
                        elif ampm == 'am' and hour == 12:
                            hour = 0
                        dt_start = datetime(year, month, day, hour, minute)
                    else:
                        dt_start = datetime(year, month, day, 18, 0)
                else:
                    dt_start = datetime(year, month, day, 18, 0)

                dt_end = dt_start + timedelta(hours=2)

                # Get event type tags
                tags = []
                for tag_elem in row.find_all(class_=re.compile(r'tag|category|type')):
                    tag_text = tag_elem.get_text(strip=True)
                    if tag_text and len(tag_text) < 50:
                        tags.append(tag_text)

                # Get description snippet
                desc_elem = row.find('p') or row.find(class_=re.compile(r'desc|body|summary'))
                description = ''
                if desc_elem:
                    description = desc_elem.get_text(' ', strip=True)[:500]

                if tags:
                    description = f"{', '.join(tags)}. {description}"

                description += f"\n\nMore info: {event_url}"

                events.append({
                    'title': title,
                    'url': event_url,
                    'dtstart': dt_start,
                    'dtend': dt_end,
                    'location': location,
                    'description': description.strip()
                })

                self.logger.info(f"Found event: {title} on {dt_start}")

            except Exception as e:
                self.logger.warning(f"Error parsing event: {e}")
                continue

        return events


if __name__ == '__main__':
    CopperfieldsScraper.main()
