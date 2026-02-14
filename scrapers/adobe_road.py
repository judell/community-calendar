#!/usr/bin/env python3
"""
Adobe Road Winery Petaluma - scrapes events via JSON-LD structured data

Adobe Road Winery uses WordPress with Modern Events Calendar (MEC).
The /mec-category/petaluma-events/ page has JSON-LD Event schema embedded.
The MEC plugin produces malformed JSON (unescaped HTML in descriptions),
which the JsonLdScraper base class handles automatically.
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

from lib.jsonld import JsonLdScraper


class AdobeRoadScraper(JsonLdScraper):
    name = "Adobe Road Winery"
    domain = "adoberoadwines.com"
    url = "https://adoberoadwines.com/mec-category/petaluma-events/"
    default_location = "Adobe Road Winery, 1995 S McDowell Blvd, Petaluma, CA 94954"


if __name__ == '__main__':
    AdobeRoadScraper.main()
