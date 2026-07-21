#!/usr/bin/env python3
"""Scraper for Skyline Theatre Company (Bloomfield, NJ) events (Tribe Events API).

ModSecurity blocks the ?ical=1 export (406), but the Tribe REST API works.
"""

import sys

sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from lib.tribe_events import TribeEventsScraper


class SkylineTheatreScraper(TribeEventsScraper):
    """Scraper for Skyline Theatre Company."""

    name = "Skyline Theatre Company"
    domain = "skylinetheatrecompany.org"
    api_url = "https://skylinetheatrecompany.org/wp-json/tribe/events/v1/events/"
    timezone = "America/New_York"
    default_location = "Bloomfield, NJ"


if __name__ == '__main__':
    SkylineTheatreScraper.main()
