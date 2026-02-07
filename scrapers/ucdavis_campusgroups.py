#!/usr/bin/env python3
"""
Scraper for UC Davis CampusGroups (Aggie Life) events
https://aggielife.ucdavis.edu/events

CampusGroups platform provides a full ICS feed of all campus events.
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

from datetime import datetime
from typing import Any

import requests
from icalendar import Calendar

from lib.base import BaseScraper


class UCDavisCampusGroupsScraper(BaseScraper):
    """Scraper for UC Davis CampusGroups/Aggie Life events."""

    name = "UC Davis CampusGroups"
    domain = "aggielife.ucdavis.edu"

    ICS_URL = "https://aggielife.ucdavis.edu/ical/ucdavis/ical_ucdavis.ics"

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from ICS feed."""
        self.logger.info(f"Fetching {self.ICS_URL}")

        try:
            response = requests.get(self.ICS_URL, timeout=60, allow_redirects=True)
            response.raise_for_status()
            return self._parse_ics(response.text)
        except Exception as e:
            self.logger.error(f"Error fetching ICS: {e}")
            return []

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
                    # Clean up "Sign in to download the location" placeholder
                    if location and 'sign in' in location.lower():
                        location = None
                    
                    description = str(component.get('description', '')) or None
                    # Clean up description - remove the "Event Details" boilerplate
                    if description:
                        description = description.split('\n---\nEvent Details:')[0].strip()
                    
                    url = str(component.get('url', '')) or None
                    
                    # Get organizer info if available
                    organizer = component.get('organizer')
                    if organizer and description:
                        org_name = organizer.params.get('cn', '')
                        if org_name and org_name not in description:
                            description = f"Hosted by: {org_name}\n\n{description}"

                    events.append({
                        'title': title,
                        'dtstart': dt_start,
                        'dtend': dt_end,
                        'location': location,
                        'description': description,
                        'url': url,
                    })

                    self.logger.debug(f"Found event: {title}")

                except Exception as e:
                    self.logger.warning(f"Error parsing event: {e}")
                    continue

        self.logger.info(f"Parsed {len(events)} events from ICS")
        return events


if __name__ == '__main__':
    UCDavisCampusGroupsScraper.main()
