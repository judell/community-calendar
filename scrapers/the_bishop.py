#!/usr/bin/env python3
"""Scraper for The Bishop Bar events."""

import re
import sys
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from lib.base import BaseScraper


class TheBishopScraper(BaseScraper):
    """Scraper for The Bishop Bar in Bloomington."""

    name = "The Bishop"
    domain = "thebishopbar.com"
    base_url = "https://thebishopbar.com"
    events_url = "https://thebishopbar.com/events"
    timezone = "America/Indiana/Indianapolis"

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from the events page and subsequent months."""
        events = []
        seen_urls = set()
        
        # Fetch current month and next few months
        urls_to_fetch = [self.events_url]
        
        # Add next 3 months
        now = datetime.now()
        for i in range(1, 4):
            future = now + timedelta(days=30 * i)
            urls_to_fetch.append(f"{self.events_url}/{future.year}-{future.month:02d}")
        
        for url in urls_to_fetch:
            self.logger.info(f"Fetching events from {url}")
            try:
                page_events = self._fetch_page(url)
                for event in page_events:
                    if event['url'] not in seen_urls:
                        seen_urls.add(event['url'])
                        events.append(event)
            except Exception as e:
                self.logger.warning(f"Error fetching {url}: {e}")
                
        self.logger.info(f"Found {len(events)} events total")
        return events

    def _fetch_page(self, url: str) -> list[dict[str, Any]]:
        """Fetch events from a single page."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        events = []
        tz = ZoneInfo(self.timezone)
        
        # Find all date spans with ISO 8601 datetime
        for date_span in soup.select('.date-display-single[content]'):
            content = date_span.get('content', '')
            if not content:
                continue
            
            # Parse ISO datetime: "2026-02-26T21:00:00-05:00"
            try:
                dt = datetime.fromisoformat(content)
            except ValueError:
                continue
            
            # Find parent container and extract title
            parent = date_span.find_parent(class_='views-row') or date_span.find_parent('div')
            if not parent:
                continue
            
            # Get title from views-field-title
            title_el = parent.select_one('.views-field-title a h2, .views-field-title a')
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            
            # Get URL
            link = parent.select_one('.views-field-title a')
            url = link.get('href', '') if link else ''
            if url and not url.startswith('http'):
                url = f"{self.base_url}{url}"
            
            # Get ticket link if available
            ticket_link = parent.select_one('.buy-tickets')
            ticket_url = ticket_link.get('href', '') if ticket_link else ''
            
            # Create unique ID
            slug = re.sub(r'[^a-z0-9]+', '-', title.lower())[:30]
            uid = f"{dt.strftime('%Y%m%d')}-{slug}"
            
            # Build description
            desc = title
            if ticket_url:
                desc += f"\n\nTickets: {ticket_url}"
            
            events.append({
                'title': title,
                'dtstart': dt.astimezone(tz),
                'dtend': (dt + timedelta(hours=3)).astimezone(tz),
                'url': url,
                'location': 'The Bishop, 123 S Walnut St, Bloomington, IN',
                'description': desc,
                'uid': uid,
            })
                
        return events


if __name__ == '__main__':
    TheBishopScraper.main()
