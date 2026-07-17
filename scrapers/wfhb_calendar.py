#!/usr/bin/env python3
"""Scraper for WFHB Community Radio calendar (Events Manager)."""

import sys

sys.path.insert(0, str(__file__).rsplit("/", 2)[0])
from lib.em_events import EmEventsScraper


class WFHBCalendarScraper(EmEventsScraper):
    """Scraper for WFHB Community Radio calendar in Bloomington."""

    name = "WFHB Community Calendar"
    domain = "wfhb.org"
    ajax_url = "https://wfhb.org/wp-admin/admin-ajax.php"
    timezone = "America/Indiana/Indianapolis"
    default_location = "Bloomington, IN"
    batch_size = 50
    max_pages = 15


if __name__ == "__main__":
    WFHBCalendarScraper.main()
