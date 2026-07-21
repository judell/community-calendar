#!/usr/bin/env python3
"""Scraper for NJ Poetry Events (njpoetryevents.com), a statewide Squarespace
calendar of poetry readings and open mics.

Titles follow the pattern "CITY - EVENT NAME" (e.g. "MONTCLAIR - Open Mic
Night"). We parse the city prefix into the location field so the pipeline's
geo-filter keeps only events in the Montclair coverage area.
"""

import re
import sys
from typing import Any, Optional

sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from lib.squarespace import SquarespaceScraper

_TITLE_CITY_RE = re.compile(r'^([A-Z][A-Z .\'-]+?)\s*[-–]\s+(.+)$')


class NJPoetryEventsScraper(SquarespaceScraper):
    """Scraper for the statewide NJ Poetry Events calendar."""

    name = "NJ Poetry Events"
    domain = "njpoetryevents.com"
    collection_url = "https://www.njpoetryevents.com/calendar"
    timezone = "America/New_York"
    default_location = "NJ"

    def _parse_item(self, item: dict, base_url: str) -> Optional[dict[str, Any]]:
        event = super()._parse_item(item, base_url)
        if not event:
            return event
        m = _TITLE_CITY_RE.match(event.get('title', ''))
        if m:
            city = m.group(1).strip().title()
            event['title'] = m.group(2).strip()
            # Squarespace location data is usually absent on this site; the
            # city prefix is the only geo signal, so make it filterable.
            if not event.get('location') or event['location'] == self.default_location:
                event['location'] = f"{city}, NJ"
            elif ', NJ' not in event['location']:
                event['location'] = f"{event['location']}, {city}, NJ"
        return event


if __name__ == '__main__':
    NJPoetryEventsScraper.main()
