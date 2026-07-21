#!/usr/bin/env python3
"""Scraper for Outpost in the Burbs (Montclair, NJ) via ThunderTix JSON-LD.

The org's own site is Wix with no feed, but their ThunderTix ticketing
subdomain embeds schema.org Event JSON-LD on the events listing page.
"""

import sys

sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from lib.jsonld import JsonLdScraper


class OutpostBurbsScraper(JsonLdScraper):
    """Scraper for Outpost in the Burbs concerts (ThunderTix)."""

    name = "Outpost in the Burbs"
    domain = "outpostintheburbs.org"
    url = "https://outpostintheburbs.thundertix.com/events"
    timezone = "America/New_York"
    default_location = "First Congregational Church, 40 South Fullerton Ave, Montclair, NJ"


if __name__ == '__main__':
    OutpostBurbsScraper.main()
