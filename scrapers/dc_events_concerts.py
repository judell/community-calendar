#!/usr/bin/env python3
"""
dc.events — Washington DC's WordPress-based music aggregator.

The /concerts/ listing page embeds ~25 schema.org MusicEvent JSON-LD blocks
per page (one per upcoming show). The lib/jsonld.py base class extracts and
parses them directly.

Coverage spans DC + suburbs (Birchmere, Northwest Stadium, etc.); the city
geo-filter (cities/dc-music/city.conf, state=DC) drops the non-DC entries
at ingest.

Usage:
    python scrapers/dc_events_concerts.py --output cities/dc-music/dc_events_concerts.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

from lib.jsonld import JsonLdScraper


class DcEventsConcertsScraper(JsonLdScraper):
    name = "dc.events Concerts"
    domain = "dc.events"
    url = "https://dc.events/concerts/"
    timezone = "America/New_York"
    default_location = "Washington, DC"


if __name__ == '__main__':
    DcEventsConcertsScraper.main()
