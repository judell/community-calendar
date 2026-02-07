#!/usr/bin/env python3
"""
Scraper for UC Davis CampusGroups (Aggie Life) events
https://aggielife.ucdavis.edu/events

CampusGroups platform provides a full ICS feed of all campus events.
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

from typing import Any

from lib import IcsScraper


class UCDavisCampusGroupsScraper(IcsScraper):
    """Scraper for UC Davis CampusGroups/Aggie Life events."""

    name = "UC Davis CampusGroups"
    domain = "aggielife.ucdavis.edu"
    ics_url = "https://aggielife.ucdavis.edu/ical/ucdavis/ical_ucdavis.ics"
    request_timeout = 60

    def transform_event(self, event: dict[str, Any]) -> dict[str, Any]:
        """Clean up location and description fields."""
        # Clean up "Sign in to download the location" placeholder
        location = event.get('location')
        if location and 'sign in' in location.lower():
            event['location'] = None

        # Clean up description - remove the "Event Details" boilerplate
        description = event.get('description')
        if description:
            event['description'] = description.split('\n---\nEvent Details:')[0].strip()

        return event


if __name__ == '__main__':
    UCDavisCampusGroupsScraper.main()
