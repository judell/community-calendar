#!/usr/bin/env python3
"""
Scraper for venues using the Ludus ticketing platform (ludus.com).

Ludus hosts storefronts at <org>.ludus.com for community theaters and school
performing arts programs. All *.ludus.com subdomains sit behind Cloudflare
bot management and require full browser headers (including sec-ch-ua /
sec-fetch-* client hint headers) to serve a real response.

The canonical page for scraping is /index.php — the root "/" may return an
embed-widget variant with show listings omitted.

Show data is embedded server-side in the PHP-rendered HTML as:
  - div.show_item[data-show-id]  — one per production
  - span.patron_heading_label     — show title
  - div.show_listing_notice       — description text
  - div#showtimes_item{N}[data-past-date, data-manual-soldout, data-on-off]
                                  — one per performance
  - label[for=showtime_radio{N}]  — date+time string "Day, Month DD, YYYY H:MM AM/PM"

Known targets (Bloomington, IN):
  Off Night Productions: https://offnight.ludus.com
  Monroe County Civic Theater (MCCT): https://mcct.ludus.com

Usage:
    python scrapers/ludus.py \\
        --url "https://offnight.ludus.com" \\
        --name "Off Night Productions" \\
        --default-location "Bloomington, IN" \\
        --output cities/bloomington/off_night.ics

    python scrapers/ludus.py \\
        --url "https://mcct.ludus.com" \\
        --name "Monroe County Civic Theater" \\
        --default-location "Bloomington, IN" \\
        --output cities/bloomington/mcct.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import html as html_mod
import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from lib.base import BaseScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Full browser headers required to bypass Cloudflare bot management on *.ludus.com.
# The sec-ch-ua / sec-fetch-* client-hint headers are the key — standard curl/urllib
# omits them and receives a 403 challenge page instead of the real HTML.
BROWSER_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/126.0.0.0 Safari/537.36'
    ),
    'Accept': (
        'text/html,application/xhtml+xml,application/xml;'
        'q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,'
        'application/signed-exchange;v=b3;q=0.7'
    ),
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
}

# Date format used in Ludus label text: "Sunday, August 16, 2026 2:00 PM"
_DATE_FMT = '%A, %B %d, %Y %I:%M %p'


class LudusScraper(BaseScraper):
    """Scraper for Ludus ticketing platform storefronts (*.ludus.com)."""

    def __init__(
        self,
        url: str,
        source_name: str,
        tz: str = 'America/Indiana/Indianapolis',
        default_location: str = '',
    ):
        # Normalise: strip trailing slash, resolve to /index.php
        parsed = urlparse(url.rstrip('/'))
        self.base_url = f'{parsed.scheme}://{parsed.netloc}'
        self.index_url = f'{self.base_url}/index.php'

        self.name = source_name
        self.domain = parsed.netloc
        self.timezone = tz
        self.default_location = default_location

        super().__init__()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fetch_html(self, url: str) -> Optional[str]:
        """Fetch a URL with full browser headers; return text or None."""
        try:
            resp = requests.get(url, headers=BROWSER_HEADERS, timeout=30)
            resp.raise_for_status()
            # Sanity check: detect CF challenge page that slipped through
            if 'Just a moment' in resp.text and 'cloudflare' in resp.text.lower():
                self.logger.error(
                    f'Cloudflare challenge returned for {url}. '
                    'The platform may have tightened its bot rules.'
                )
                return None
            return resp.text
        except requests.RequestException as exc:
            self.logger.error(f'Failed to fetch {url}: {exc}')
            return None

    @staticmethod
    def _clean_text(raw: str) -> str:
        """Strip HTML tags, unescape entities, collapse whitespace."""
        text = html_mod.unescape(raw)
        text = re.sub(r'<[^>]+>', ' ', text)
        return re.sub(r'\s+', ' ', text).strip()

    def _parse_showtime_date(self, label_text: str) -> Optional[datetime]:
        """
        Parse a label string like 'Sunday, August 16, 2026 2:00 PM'
        into a tz-aware datetime.  Returns None on parse failure.
        """
        from zoneinfo import ZoneInfo
        try:
            dt_naive = datetime.strptime(label_text.strip(), _DATE_FMT)
            return dt_naive.replace(tzinfo=ZoneInfo(self.timezone))
        except ValueError:
            self.logger.debug(f'Could not parse date string: {label_text!r}')
            return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch_events(self) -> list[dict[str, Any]]:
        """
        Fetch the Ludus /index.php storefront and return one event dict
        per *upcoming* performance (past-date=0, not sold out, not hidden).
        """
        self.logger.info(f'Fetching Ludus storefront: {self.index_url}')
        html = self._fetch_html(self.index_url)
        if html is None:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        show_items = soup.find_all('div', class_='show_item')

        if not show_items:
            self.logger.info('No show_item elements found — venue may be between productions.')
            return []

        self.logger.info(f'Found {len(show_items)} production(s) on page')
        now = datetime.now(timezone.utc)
        events: list[dict[str, Any]] = []

        for show_div in show_items:
            show_id = show_div.get('data-show-id', '')

            # Title
            title_el = show_div.find('span', class_='patron_heading_label')
            title = title_el.get_text(strip=True) if title_el else 'Untitled'

            # Description: strip the "Purchase tickets to <title> here!" boilerplate
            desc = ''
            notice_el = show_div.find(class_='show_listing_notice')
            if notice_el:
                desc = self._clean_text(str(notice_el))[:500]

            # Image
            image_url: Optional[str] = None
            cover_el = show_div.find(class_='show_item_cover_photo')
            if cover_el:
                style = cover_el.get('style', '')
                img_m = re.search(r"url\('([^']+)'\)", style)
                if img_m:
                    image_url = img_m.group(1)

            # Ticket URL for this production (links to showtime selection)
            ticket_url = f'{self.base_url}/select.php?show_id={show_id}' if show_id else self.base_url

            # Performances
            showtime_divs = show_div.find_all(
                'div', id=lambda x: x and x.startswith('showtimes_item')
            )

            for st_div in showtime_divs:
                # Skip past or hidden/disabled performances
                if st_div.get('data-past-date', '0') != '0':
                    continue
                if st_div.get('data-on-off', '0') != '0':
                    continue
                # Sold-out shows are still events worth knowing about
                sold_out = st_div.get('data-manual-soldout', '0') != '0'

                # Date/time from radio label
                label_el = st_div.find('label')
                if not label_el:
                    continue
                date_str = label_el.get_text(strip=True)
                dtstart = self._parse_showtime_date(date_str)
                if dtstart is None:
                    continue

                # Skip genuinely past events (belt + suspenders)
                if dtstart < now:
                    continue

                event: dict[str, Any] = {
                    'title': title,
                    'dtstart': dtstart,
                    'url': ticket_url,
                    'location': self.default_location,
                    'description': ('[SOLD OUT] ' if sold_out else '') + desc,
                }
                if image_url:
                    event['image_url'] = image_url

                events.append(event)
                self.logger.debug(f'  + {title}: {date_str}')

        self.logger.info(f'Extracted {len(events)} upcoming performance(s)')
        return events


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Scrape a Ludus ticketing platform storefront (*.ludus.com)'
    )
    parser.add_argument(
        '--url', required=True,
        help='Base URL of the Ludus storefront, e.g. https://offnight.ludus.com'
    )
    parser.add_argument('--name', required=True, help='Display name for the source')
    parser.add_argument(
        '--timezone', default='America/Indiana/Indianapolis',
        help='IANA timezone (default: America/Indiana/Indianapolis)'
    )
    parser.add_argument(
        '--default-location', default='',
        help='Fallback venue location string when not in event data'
    )
    parser.add_argument('--output', '-o', help='Output .ics file path')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = LudusScraper(
        url=args.url,
        source_name=args.name,
        tz=args.timezone,
        default_location=args.default_location,
    )
    scraper.run(args.output)


if __name__ == '__main__':
    main()
