#!/usr/bin/env python3
"""Scraper for Pushcart Players (Verona, NJ) events (Tribe Events API).

The site's ?ical=1 export returns an empty calendar, but the Tribe REST
API returns structured events.
"""

import sys

sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from lib.tribe_events import TribeEventsScraper


class PushcartPlayersScraper(TribeEventsScraper):
    """Scraper for Pushcart Players children's theater."""

    name = "Pushcart Players"
    domain = "pushcartplayers.org"
    api_url = "https://pushcartplayers.org/wp-json/tribe/events/v1/events/"
    timezone = "America/New_York"
    default_location = "Verona, NJ"


if __name__ == '__main__':
    PushcartPlayersScraper.main()
