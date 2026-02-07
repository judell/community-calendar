#!/usr/bin/env python3
"""
Scraper for Unitarian Universalist Church of Davis events
https://uudavis.org/calendar/

Uses embedded Google Calendar ICS feeds.
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

from lib import GoogleCalendarScraper


class UUDavisScraper(GoogleCalendarScraper):
    """Scraper for UU Davis events via Google Calendar."""

    name = "UU Davis"
    domain = "uudavis.org"
    default_location = "UU Church of Davis, 27074 Patwin Rd, Davis, CA"
    default_url = "https://uudavis.org/calendar/"

    # Google Calendar IDs extracted from embedded calendar
    calendar_ids = [
        "uudavis@gmail.com",  # Main worship calendar
        "0p5ed7hbg4p7b4atf3lgjmgic@group.calendar.google.com",
        "l7ct33327vaeffd8iu8ij0hjdg@group.calendar.google.com",
        "da9geoarq2p3o4ukb8vqseat8g@group.calendar.google.com",
    ]


if __name__ == '__main__':
    UUDavisScraper.main()
