#!/usr/bin/env python3
"""
Mercury Theater Petaluma - scrapes events via Squarespace JSON API

Mercury Theater is at 3333 Petaluma Blvd N (the former Cinnabar Theater space).
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

from lib.squarespace import SquarespaceScraper


class MercuryTheaterScraper(SquarespaceScraper):
    name = "Mercury Theater"
    domain = "mercurytheater.org"
    collection_url = "https://www.mercurytheater.org/mercury-theater-calendar"
    default_location = "Mercury Theater, 3333 Petaluma Blvd N, Petaluma, CA 94952"


if __name__ == '__main__':
    MercuryTheaterScraper.main()
