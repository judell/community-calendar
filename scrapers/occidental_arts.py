#!/usr/bin/env python3
"""
Scraper for Occidental Center for the Arts events
https://www.occidentalcenterforthearts.org/upcoming-events
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import time
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from lib.base import BaseScraper
from lib.utils import fetch_with_retry


class OccidentalArtsScraper(BaseScraper):
    """Scraper for Occidental Center for the Arts events."""

    name = "Occidental Arts"
    domain = "occidentalcenterforthearts.org"

    BASE_URL = 'https://www.occidentalcenterforthearts.org'
    EVENTS_URL = f'{BASE_URL}/upcoming-events'

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch and parse events from the events page."""
        self.logger.info(f"Fetching {self.EVENTS_URL}")
        main_page = fetch_with_retry(self.EVENTS_URL)

        soup = BeautifulSoup(main_page, 'html.parser')
        events = []

        for event_elem in soup.find_all('article', class_='eventlist-event'):
            try:
                event = self._parse_event(event_elem)
                if event:
                    # Fetch description from iCal link if available
                    if event.get('ical_link'):
                        try:
                            ical_content = fetch_with_retry(event['ical_link'])
                            event['description'] = self._parse_ical_description(ical_content)
                        except Exception:
                            pass
                        del event['ical_link']

                    events.append(event)
                    self.logger.info(f"Found event: {event['title']} on {event['dtstart']}")

                time.sleep(1)  # Rate limiting
            except Exception as e:
                self.logger.warning(f"Error parsing event: {e}")

        return events

    def _parse_event(self, event_elem) -> dict[str, Any] | None:
        """Parse a single event from the listing."""
        title_link = event_elem.find('a', class_='eventlist-title-link')
        if not title_link:
            return None

        title = title_link.text.strip()
        url = urljoin(self.BASE_URL, title_link['href'])

        date_elem = event_elem.find('time', class_='event-date')
        if not date_elem or 'datetime' not in date_elem.attrs:
            self.logger.warning(f"Skipping event {title} due to missing date")
            return None

        event_date = datetime.strptime(date_elem['datetime'], '%Y-%m-%d')

        # Parse times
        time_start = event_elem.find('time', class_='event-time-localized-start')
        time_end = event_elem.find('time', class_='event-time-localized-end')

        dt_start = event_date
        dt_end = event_date + timedelta(days=1)

        if time_start and time_end:
            start_time = time_start.text.strip()
            end_time = time_end.text.strip()

            try:
                hour, minute = map(int, start_time.replace('AM', '').replace('PM', '').strip().split(':'))
                dt_start = event_date.replace(
                    hour=hour % 12 + (12 if 'PM' in start_time else 0),
                    minute=minute
                )
            except ValueError:
                pass

            try:
                hour, minute = map(int, end_time.replace('AM', '').replace('PM', '').strip().split(':'))
                dt_end = event_date.replace(
                    hour=hour % 12 + (12 if 'PM' in end_time else 0),
                    minute=minute
                )
            except ValueError:
                pass

        ical_link_elem = event_elem.find('a', class_='eventlist-meta-export-ical')
        ical_link = urljoin(self.BASE_URL, ical_link_elem['href']) if ical_link_elem else None

        return {
            'title': title,
            'url': url,
            'dtstart': dt_start,
            'dtend': dt_end,
            'description': '',
            'location': 'Occidental Center for the Arts, 3550 Bohemian Hwy, Occidental, CA 95465',
            'ical_link': ical_link
        }

    def _parse_ical_description(self, ical_content: str) -> str:
        """Extract description from iCal content."""
        for line in ical_content.split('\n'):
            if line.startswith('DESCRIPTION:'):
                return line.split(':', 1)[1]
        return ""


if __name__ == '__main__':
    OccidentalArtsScraper.main()
