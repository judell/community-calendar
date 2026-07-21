#!/usr/bin/env python3
"""Scraper for Jazz House Kids (Montclair, NJ) events (Tribe Events API).

The site's ?ical=1 export intermittently returns HTML instead of ICS,
but the Tribe REST API reliably returns structured events.
"""

import sys

sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from lib.tribe_events import TribeEventsScraper


class JazzHouseKidsScraper(TribeEventsScraper):
    """Scraper for Jazz House Kids."""

    name = "Jazz House Kids"
    domain = "jazzhousekids.org"
    api_url = "https://jazzhousekids.org/wp-json/tribe/events/v1/events/"
    timezone = "America/New_York"
    default_location = "Montclair, NJ"


if __name__ == '__main__':
    JazzHouseKidsScraper.main()
