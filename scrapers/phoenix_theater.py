#!/usr/bin/env python3
"""
Phoenix Theater Petaluma - scrapes events via Eventbrite search

The Phoenix Theater is a legendary all-ages punk venue at 201 Washington St, Petaluma.
Events are ticketed via Eventbrite. We search Eventbrite for the venue, then extract
JSON-LD structured data from each event page.
"""

import re
import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

from lib.jsonld import JsonLdScraper


SEARCH_URL = "https://www.eventbrite.com/d/ca--petaluma/phoenix-theater/"


class PhoenixTheaterScraper(JsonLdScraper):
    name = "Phoenix Theater"
    domain = "thephoenixtheater.com"
    default_location = "Phoenix Theater, 201 Washington St, Petaluma, CA"
    location_filter = "phoenix"

    def get_urls(self):
        """Discover event URLs from Eventbrite search."""
        self.logger.info(f"Searching Eventbrite: {SEARCH_URL}")
        html = self.fetch_html(SEARCH_URL)
        if not html:
            return []

        pattern = r'eventbrite\.com/e/([^"?\s]+)'
        matches = re.findall(pattern, html)
        urls = list(set(f"https://www.eventbrite.com/e/{m}" for m in matches))
        self.logger.info(f"Found {len(urls)} potential event URLs")
        return urls

    def _parse_event(self, item):
        """Override to also check venue address for Phoenix Theater."""
        parsed = super()._parse_event(item)
        if not parsed:
            # Try address-based match as fallback
            loc = item.get('location', {})
            if isinstance(loc, dict):
                addr = loc.get('address', {})
                if isinstance(addr, dict):
                    street = addr.get('streetAddress', '')
                    if '201 washington' in street.lower():
                        # Re-parse without location filter
                        old_filter = self.location_filter
                        self.location_filter = None
                        parsed = super()._parse_event(item)
                        self.location_filter = old_filter
        return parsed


if __name__ == '__main__':
    PhoenixTheaterScraper.main()
