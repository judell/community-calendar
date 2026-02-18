#!/usr/bin/env python3
"""
Volunteer Toronto scraper via Toronto Public Library's Bibliocommons.

Volunteer Toronto events are hosted through TPL and tagged with
programId 68b050fad7b6cc3d009b8dcf in the Bibliocommons API.
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

from lib.bibliocommons import BibliocommonsEventsScraper


class VolunteerTorontoScraper(BibliocommonsEventsScraper):
    name = "Volunteer Toronto"
    domain = "tpl.bibliocommons.com"
    timezone = "America/Toronto"
    library_slug = "tpl"

    program_ids = ["68b050fad7b6cc3d009b8dcf"]

    page_limit = 100
    max_pages = 40


if __name__ == "__main__":
    VolunteerTorontoScraper.main()
