#!/usr/bin/env python3
"""
Scraper for Unitarian Universalist Church of Davis events
https://uudavis.org/calendar/

Uses embedded Google Calendar ICS feeds.
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

from datetime import datetime
from typing import Any

import requests
from icalendar import Calendar

from lib.base import BaseScraper


class UUDavisScraper(BaseScraper):
    """Scraper for UU Davis events via Google Calendar."""

    name = "UU Davis"
    domain = "uudavis.org"

    # Google Calendar ICS URLs extracted from embedded calendar
    CALENDAR_IDS = [
        "uudavis@gmail.com",  # Main worship calendar
        "0p5ed7hbg4p7b4atf3lgjmgic@group.calendar.google.com",
        "l7ct33327vaeffd8iu8ij0hjdg@group.calendar.google.com", 
        "da9geoarq2p3o4ukb8vqseat8g@group.calendar.google.com",
    ]

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from all Google Calendar ICS feeds."""
        all_events = []
        
        for cal_id in self.CALENDAR_IDS:
            url = f"https://calendar.google.com/calendar/ical/{cal_id.replace('@', '%40')}/public/basic.ics"
            self.logger.info(f"Fetching {url}")
            
            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                events = self._parse_ics(response.text)
                all_events.extend(events)
                self.logger.info(f"Found {len(events)} events from {cal_id}")
            except Exception as e:
                self.logger.warning(f"Error fetching {cal_id}: {e}")
        
        # Deduplicate by UID
        seen_uids = set()
        unique_events = []
        for event in all_events:
            uid = event.get('uid', '')
            if uid not in seen_uids:
                seen_uids.add(uid)
                unique_events.append(event)
        
        self.logger.info(f"Total unique events: {len(unique_events)}")
        return unique_events

    def _parse_ics(self, ics_content: str) -> list[dict[str, Any]]:
        """Parse events from ICS content."""
        events = []
        try:
            cal = Calendar.from_ical(ics_content)
        except Exception as e:
            self.logger.warning(f"Error parsing ICS: {e}")
            return events

        for component in cal.walk():
            if component.name == "VEVENT":
                try:
                    title = str(component.get('summary', ''))
                    if not title:
                        continue

                    dtstart = component.get('dtstart')
                    dtend = component.get('dtend')
                    
                    if dtstart:
                        dt_start = dtstart.dt
                    else:
                        continue

                    dt_end = dtend.dt if dtend else None

                    location = str(component.get('location', '')) or None
                    description = str(component.get('description', '')) or None
                    uid = str(component.get('uid', ''))
                    
                    # Default URL to church website
                    url = "https://uudavis.org/calendar/"

                    events.append({
                        'title': title,
                        'dtstart': dt_start,
                        'dtend': dt_end,
                        'location': location or "UU Church of Davis, 27074 Patwin Rd, Davis, CA",
                        'description': description,
                        'url': url,
                        'uid': uid,
                    })

                except Exception as e:
                    self.logger.warning(f"Error parsing event: {e}")
                    continue

        return events


if __name__ == '__main__':
    UUDavisScraper.main()
