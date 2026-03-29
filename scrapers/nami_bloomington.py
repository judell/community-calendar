#!/usr/bin/env python3
"""Scraper for NAMI Greater Bloomington Area events (Tribe Events API)."""

import sys

sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from lib.tribe_events import TribeEventsScraper


class NAMIScraper(TribeEventsScraper):
    """Scraper for NAMI Greater Bloomington Area."""

    name = "NAMI Greater Bloomington"
    domain = "namigreaterbloomingtonarea.org"
    api_url = "https://namigreaterbloomingtonarea.org/wp-json/tribe/events/v1/events/"
    timezone = "America/Indiana/Indianapolis"
    default_location = "Bloomington, IN"


if __name__ == '__main__':
    NAMIScraper.main()
