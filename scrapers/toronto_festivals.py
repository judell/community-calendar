#!/usr/bin/env python3
"""
Scraper for City of Toronto Festivals & Events.

Source: Toronto's official Festivals & Events open data, transformed to
schema.org/Event JSON-LD by a daily-refreshed CivicTechTO GitHub Actions pipeline.
https://github.com/CivicTechTO/toronto-opendata-festivalsandevents-jsonld-proxy
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import json
import logging
from urllib.request import urlopen, Request

from lib.jsonld import JsonLdScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

FEED_URL = "https://civictechto.github.io/toronto-opendata-festivalsandevents-jsonld-proxy/upcoming.jsonld"


class TorontoFestivalsScraper(JsonLdScraper):
    name = "City of Toronto Festivals & Events"
    domain = "toronto.ca"
    url = FEED_URL
    default_location = "Toronto, ON"
    timezone = "America/Toronto"

    def fetch_events(self):
        """Fetch JSON-LD array directly (not embedded in HTML)."""
        self.logger.info(f"Fetching {FEED_URL}")
        req = Request(FEED_URL, headers=self.headers)
        with urlopen(req, timeout=15) as resp:
            events = json.loads(resp.read().decode('utf-8'))

        self.logger.info(f"Found {len(events)} events in feed")

        parsed = []
        for item in events:
            event = self._parse_event(item)
            if event:
                parsed.append(event)

        self.logger.info(f"Total: {len(parsed)} future events")
        return parsed


if __name__ == '__main__':
    TorontoFestivalsScraper.main()
