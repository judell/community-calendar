"""Base scraper for CKAN open data portals.

CKAN (Comprehensive Knowledge Archive Network) is an open-source data portal
used by governments worldwide (Toronto, Ottawa, Edmonton, data.gov, etc.).
The datastore API is standardized: same pagination, same JSON envelope.

Subclasses provide a resource_id and map_record() to convert rows to events.
"""

import requests
from abc import abstractmethod
from typing import Any, Optional

from .base import BaseScraper

HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; community-calendar/1.0)'}


class CKANScraper(BaseScraper):
    """Base scraper for CKAN datastore APIs.

    Subclasses must set:
    - ckan_base_url: str - e.g. "https://ckan0.cf.opendata.inter.prod-toronto.ca"
    - resource_id: str - the datastore resource ID
    - map_record(record) -> Optional[dict] - convert a CKAN row to an event dict
    """

    ckan_base_url: str = ""
    resource_id: str = ""
    page_size: int = 500

    @abstractmethod
    def map_record(self, record: dict) -> Optional[dict[str, Any]]:
        """Convert a CKAN datastore record to an event dict.

        Return None to skip the record.
        """
        pass

    def build_filters(self) -> dict:
        """Optional: return CKAN filters dict to narrow the query."""
        return {}

    def build_sort(self) -> str:
        """Optional: return sort string for the query."""
        return ""

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch all records from CKAN datastore, paginating automatically."""
        events = []
        offset = 0
        filters = self.build_filters()
        sort = self.build_sort()

        while True:
            params: dict[str, Any] = {
                'resource_id': self.resource_id,
                'limit': self.page_size,
                'offset': offset,
            }
            if filters:
                import json
                params['filters'] = json.dumps(filters)
            if sort:
                params['sort'] = sort

            url = f"{self.ckan_base_url}/api/3/action/datastore_search"
            self.logger.info(f"Fetching offset={offset}")

            resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            if not data.get('success'):
                self.logger.error(f"CKAN API error: {data}")
                break

            records = data['result']['records']
            if not records:
                break

            for record in records:
                event = self.map_record(record)
                if event:
                    events.append(event)

            offset += len(records)
            total = data['result'].get('total', 0)
            self.logger.info(f"  Got {len(records)} records ({offset}/{total})")

            if offset >= total:
                break

        self.logger.info(f"Total: {len(events)} events from {offset} records")
        return events
