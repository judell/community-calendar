#!/usr/bin/env python3
"""
Scraper for Shopify sites that sell event tickets as products.

Parses event details from product titles (pipe-delimited) and body_html.

Usage:
    python scrapers/shopify_events.py \
        --url "https://cicadacinema.com" \
        --name "Cicada Cinema" \
        --output cities/bloomington/cicada_cinema.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import json
import logging
import re
from datetime import datetime
from typing import Any
from urllib.parse import urlparse
from urllib.request import urlopen, Request

from lib.base import BaseScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Month name to number
MONTHS = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12,
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
    'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
}


def parse_time(time_str: str) -> tuple[int, int] | None:
    """Parse time string like '7PM', '8:30pm', '9 PM'."""
    time_str = time_str.strip().lower().replace(' ', '')
    m = re.match(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)', time_str)
    if not m:
        return None
    hour = int(m.group(1))
    minute = int(m.group(2) or 0)
    if m.group(3) == 'pm' and hour != 12:
        hour += 12
    if m.group(3) == 'am' and hour == 12:
        hour = 0
    return (hour, minute)


def parse_title_date(title: str) -> dict[str, Any] | None:
    """Parse pipe-delimited title: 'Film Name | Date | Venue | Time'."""
    parts = [p.strip() for p in title.split('|')]
    if len(parts) < 3:
        return None

    event_title = parts[0]
    date_str = parts[1]
    venue = parts[2] if len(parts) > 2 else ''
    time_str = parts[3] if len(parts) > 3 else ''

    # Parse date: "March 19" or "March 19th"
    date_str = re.sub(r'(st|nd|rd|th)\b', '', date_str).strip()
    m = re.match(r'(\w+)\s+(\d{1,2})', date_str)
    if not m:
        return None

    month_name = m.group(1).lower()
    day = int(m.group(2))
    month = MONTHS.get(month_name)
    if not month:
        return None

    # Infer year: use current year, or next year if date is in the past
    now = datetime.now()
    year = now.year
    try:
        dt = datetime(year, month, day)
    except ValueError:
        return None
    if dt.date() < now.date():
        dt = datetime(year + 1, month, day)

    # Parse time
    if time_str:
        parsed = parse_time(time_str)
        if parsed:
            dt = dt.replace(hour=parsed[0], minute=parsed[1])

    return {
        'title': event_title,
        'date': dt,
        'venue': venue,
    }


class ShopifyEventsScraper(BaseScraper):
    """Scraper for Shopify sites selling event tickets as products."""

    def __init__(self, url, source_name):
        parsed = urlparse(url)
        self.base_url = f"{parsed.scheme}://{parsed.netloc}"
        self.name = source_name
        self.domain = parsed.netloc.replace('www.', '')
        super().__init__()

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch products from Shopify JSON API and parse as events."""
        url = f"{self.base_url}/products.json"
        logger.info(f"Fetching {url}")
        req = Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())

        events = []
        for product in data.get('products', []):
            title = product.get('title', '')
            parsed = parse_title_date(title)
            if not parsed:
                logger.warning(f"Could not parse title: {title}")
                continue

            # Extract description from body_html (strip tags)
            body = product.get('body_html', '')
            desc = re.sub(r'<[^>]+>', ' ', body).strip()
            desc = re.sub(r'\s+', ' ', desc)

            # Extract price from variants
            variants = product.get('variants', [])
            price = variants[0].get('price', '') if variants else ''
            if price:
                desc = f"${price} - {desc}" if desc else f"${price}"

            events.append({
                'title': parsed['title'],
                'dtstart': parsed['date'],
                'dtend': None,
                'location': parsed['venue'],
                'description': desc,
                'url': f"{self.base_url}/products/{product.get('handle', '')}",
                'uid': f"shopify-{product['id']}@{self.domain}",
            })

        return events


def main():
    parser = argparse.ArgumentParser(description='Scrape Shopify event ticket products')
    parser.add_argument('--url', required=True, help='Shopify site URL')
    parser.add_argument('--name', required=True, help='Source name')
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = ShopifyEventsScraper(args.url, args.name)
    scraper.run(args.output)


if __name__ == '__main__':
    main()
