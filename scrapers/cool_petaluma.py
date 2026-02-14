#!/usr/bin/env python3
"""
Cool Petaluma - scrapes events via Squarespace JSON API

Climate/sustainability community events.
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

from lib.squarespace import SquarespaceScraper


class CoolPetalumaScraper(SquarespaceScraper):
    name = "Cool Petaluma"
    domain = "coolpetaluma.org"
    collection_url = "https://coolpetaluma.org/events"
    default_location = "Petaluma, CA"


if __name__ == '__main__':
    CoolPetalumaScraper.main()
