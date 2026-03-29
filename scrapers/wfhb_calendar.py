#!/usr/bin/env python3
"""Scraper for WFHB Community Radio calendar (All-in-One Event Calendar)."""

import sys

sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from lib.ai1ec import Ai1ecScraper


class WFHBCalendarScraper(Ai1ecScraper):
    """Scraper for WFHB Community Radio calendar in Bloomington."""

    name = "WFHB Community Calendar"
    domain = "wfhb.org"
    calendar_url = "https://wfhb.org/calendar/"
    timezone = "America/Indiana/Indianapolis"


if __name__ == '__main__':
    WFHBCalendarScraper.main()
