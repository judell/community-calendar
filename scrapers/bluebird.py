#!/usr/bin/env python3
"""Scraper for The Bluebird Nightclub events (SeeTickets widget)."""

import sys

sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from lib.seetickets import SeeTicketsScraper


class BluebirdScraper(SeeTicketsScraper):
    """Scraper for The Bluebird Nightclub in Bloomington."""

    name = "The Bluebird"
    domain = "thebluebird.ws"
    events_url = "https://www.thebluebird.ws/"
    timezone = "America/Indiana/Indianapolis"
    default_location = "Bluebird Nightclub, 216 N Walnut St, Bloomington, IN"


if __name__ == '__main__':
    BluebirdScraper.main()
