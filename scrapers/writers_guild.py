#!/usr/bin/env python3
"""Scraper for Writers Guild at Bloomington events (Sugar Calendar)."""

import sys

sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from lib.sugar_calendar import SugarCalendarScraper


class WritersGuildScraper(SugarCalendarScraper):
    """Scraper for Writers Guild at Bloomington."""

    name = "Writers Guild at Bloomington"
    domain = "writersguildbloomington.com"
    events_url = "https://writersguildbloomington.com/events/"
    timezone = "America/Indiana/Indianapolis"
    default_location = "Bloomington, IN"


if __name__ == '__main__':
    WritersGuildScraper.main()
