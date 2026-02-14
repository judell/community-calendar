#!/usr/bin/env python3
"""
Brewsters Beer Garden Petaluma - scrapes events via Squarespace JSON API
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

from lib.squarespace import SquarespaceScraper


class BrewstersScraper(SquarespaceScraper):
    name = "Brewsters Beer Garden"
    domain = "brewstersbeergarden.com"
    collection_url = "https://brewstersbeergarden.com/calendar1"
    default_location = "Brewsters Beer Garden, 229 Water St, Petaluma, CA 94952"


if __name__ == '__main__':
    BrewstersScraper.main()
