#!/usr/bin/env python3
"""
Petaluma River Park - scrapes events via Squarespace JSON API

Community park events including weekly walks, markets, and fitness classes.
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

from lib.squarespace import SquarespaceScraper


class PetalumaRiverParkScraper(SquarespaceScraper):
    name = "Petaluma River Park"
    domain = "petalumariverpark.org"
    collection_url = "https://petalumariverpark.org/calendar"
    default_location = "Petaluma River Park, Petaluma, CA"


if __name__ == '__main__':
    PetalumaRiverParkScraper.main()
