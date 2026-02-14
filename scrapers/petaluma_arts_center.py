#!/usr/bin/env python3
"""
Petaluma Arts Center - scrapes events via Squarespace JSON API

Note: the events collection slug is /events-exhibitions, not /events.
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

from lib.squarespace import SquarespaceScraper


class PetalumaArtsCenterScraper(SquarespaceScraper):
    name = "Petaluma Arts Center"
    domain = "petalumaartscenter.org"
    collection_url = "https://petalumaartscenter.org/events-exhibitions"
    default_location = "Petaluma Arts Center, 230 Lakeville St, Petaluma, CA 94952"


if __name__ == '__main__':
    PetalumaArtsCenterScraper.main()
