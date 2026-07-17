#!/usr/bin/env python3
"""
Scraper for Bloomington Brewing Co. (bloomingtonbrew.com) events.

The site is Squarespace. The events collection at /events?format=json
returns itemCount=73 but items=[] (Squarespace empty-collection quirk,
consistent with the discovery notes pattern). However:

1. The sitemap at /sitemap.xml lists every event page.
2. Each event page supports the ?format=ical Squarespace per-event ICS endpoint.

Strategy: parse sitemap → collect /events/* slugs → fetch each as
?format=ical → merge into one calendar. Only upcoming events are kept.

The domain resolves only over HTTP (SSL handshake fails on macOS LibreSSL
due to a Squarespace legacy TLS config; the site has a canonical HTTPS URL
but we use HTTP for fetching, which Squarespace redirects correctly).

Usage:
    python scrapers/bloomington_brewing.py --output cities/bloomington/bloomington_brewing.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from zoneinfo import ZoneInfo

from icalendar import Calendar as ICalendar

from lib.base import BaseScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Use HTTP — HTTPS triggers LibreSSL handshake failure on macOS with this server
BASE_URL = "http://bloomingtonbrew.com"
SITEMAP_URL = f"{BASE_URL}/sitemap.xml"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,text/calendar,*/*',
}
TZ = ZoneInfo("America/Indiana/Indianapolis")

# Match /events/<year>/<month>/<day>/<slug> paths (not the /events listing itself)
_EVENT_PATH_RE = re.compile(r'/events/\d{4}/.+')


class BloomingtonBrewingScraper(BaseScraper):
    """Scraper for Bloomington Brewing Co. via Squarespace per-event ICS."""

    name = "Bloomington Brewing Co."
    domain = "bloomingtonbrew.com"
    timezone = "America/Indiana/Indianapolis"

    def _fetch(self, url: str) -> bytes | None:
        req = Request(url, headers=HEADERS)
        try:
            with urlopen(req, timeout=30) as resp:
                return resp.read()
        except (HTTPError, URLError) as e:
            self.logger.warning(f"Failed to fetch {url}: {e}")
            return None

    def _get_event_urls(self) -> list[str]:
        """Parse sitemap.xml to discover all event page URLs."""
        data = self._fetch(SITEMAP_URL)
        if not data:
            self.logger.error("Could not fetch sitemap")
            return []

        text = data.decode('utf-8')
        # Extract <loc> entries that match event paths
        locs = re.findall(r'<loc>(https?://[^<]+)</loc>', text)
        event_urls = []
        seen = set()
        for loc in locs:
            # Normalize to HTTP base (sitemap may say www.bloomingtonbrew.com)
            path = re.sub(r'https?://(?:www\.)?bloomingtonbrew\.com', '', loc)
            if _EVENT_PATH_RE.match(path) and path not in seen:
                seen.add(path)
                event_urls.append(f"{BASE_URL}{path}")

        self.logger.info(f"Found {len(event_urls)} event URLs in sitemap")
        return event_urls

    def _fetch_event_ics(self, url: str) -> list[dict[str, Any]]:
        """Fetch a single event page as ?format=ical and parse the VEVENT."""
        ical_url = f"{url}?format=ical"
        data = self._fetch(ical_url)
        if not data:
            return []

        now = datetime.now(timezone.utc)
        events = []
        try:
            cal = ICalendar.from_ical(data)
        except Exception as e:
            self.logger.debug(f"iCal parse error for {url}: {e}")
            return []

        for comp in cal.walk('VEVENT'):
            dtstart_prop = comp.get('dtstart')
            if not dtstart_prop:
                continue

            dt = dtstart_prop.dt

            # Normalize to aware datetime for comparison
            if hasattr(dt, 'hour'):
                start_aware = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            else:
                import datetime as _dt
                start_aware = _dt.datetime.combine(dt, _dt.time.min).replace(tzinfo=timezone.utc)

            if start_aware < now:
                continue

            dtstart_local = start_aware.astimezone(TZ)

            dtend = None
            dtend_prop = comp.get('dtend')
            if dtend_prop:
                end_dt = dtend_prop.dt
                if hasattr(end_dt, 'hour'):
                    end_aware = end_dt if end_dt.tzinfo else end_dt.replace(tzinfo=timezone.utc)
                else:
                    import datetime as _dt
                    end_aware = _dt.datetime.combine(end_dt, _dt.time.min).replace(tzinfo=timezone.utc)
                dtend = end_aware.astimezone(TZ)

            title = str(comp.get('summary', 'Untitled'))
            location = str(comp.get('location', ''))
            description = str(comp.get('description', ''))

            events.append({
                'title': title,
                'dtstart': dtstart_local,
                'dtend': dtend,
                'location': location,
                'description': description[:500],
                'url': url,
            })

        return events

    def fetch_events(self) -> list[dict[str, Any]]:
        event_urls = self._get_event_urls()
        if not event_urls:
            return []

        all_events = []
        self.logger.info(f"Fetching {len(event_urls)} event ICS files (parallel)...")

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self._fetch_event_ics, url): url for url in event_urls}
            for future in as_completed(futures):
                events = future.result()
                if events:
                    all_events.extend(events)

        self.logger.info(f"Found {len(all_events)} future events")
        return all_events


def main():
    parser = argparse.ArgumentParser(description="Scrape Bloomington Brewing Co. events")
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    scraper = BloomingtonBrewingScraper()
    scraper.run(args.output)


if __name__ == '__main__':
    main()
