#!/usr/bin/env python3
"""
Scraper for UC Davis Athletics events
https://ucdavisaggies.com/calendar

Sidearm Sports platform - provides ICS feed.
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

from typing import Any

from lib import IcsScraper


class UCDavisAthleticsScraper(IcsScraper):
    """Scraper for UC Davis Athletics events."""

    name = "UC Davis Athletics"
    domain = "ucdavisaggies.com"
    ics_url = "https://ucdavisaggies.com/calendar.ashx/calendar.ics"
    default_location = "UC Davis"
    request_timeout = 30

    def transform_event(self, event: dict[str, Any]) -> dict[str, Any]:
        """Clean up HTML entities in URL."""
        if event.get('url'):
            event['url'] = event['url'].replace('&amp;', '&')
        return event


if __name__ == '__main__':
    UCDavisAthleticsScraper.main()
