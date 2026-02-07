#!/usr/bin/env python3
"""
Scraper for Davis Downtown events
https://davisdowntown.com/events/

WordPress site with The Events Calendar plugin - provides ICS feed.
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

from lib import IcsScraper


class DavisDowntownScraper(IcsScraper):
    """Scraper for Davis Downtown events."""

    name = "Davis Downtown"
    domain = "davisdowntown.com"
    ics_url = "https://davisdowntown.com/events/?ical=1"


if __name__ == '__main__':
    DavisDowntownScraper.main()
