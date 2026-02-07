#!/usr/bin/env python3
"""
Scraper for UC Davis Library events
https://library.ucdavis.edu/events-and-workshops/

Localist platform - provides ICS feed.
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

from lib import IcsScraper


class UCDavisLibraryScraper(IcsScraper):
    """Scraper for UC Davis Library events."""

    name = "UC Davis Library"
    domain = "events.library.ucdavis.edu"
    ics_url = "https://events.library.ucdavis.edu/calendar/1.ics"


if __name__ == '__main__':
    UCDavisLibraryScraper.main()
