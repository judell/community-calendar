#!/usr/bin/env python3
"""Scraper for Buskirk-Chumley Theater events."""

import re
import sys
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from lib.base import BaseScraper


class BuskirkChumleyScraper(BaseScraper):
    """Scraper for Buskirk-Chumley Theater."""

    name = "Buskirk-Chumley Theater"
    domain = "buskirkchumley.org"
    base_url = "https://buskirkchumley.org"
    events_url = "https://buskirkchumley.org/events/"
    timezone = "America/Indiana/Indianapolis"

    # Month name to number mapping
    MONTHS = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12
    }

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from the events page."""
        self.logger.info(f"Fetching events from {self.events_url}")
        
        # Site blocks some user agents but accepts curl
        headers = {
            'User-Agent': 'curl/8.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        session = requests.Session()
        session.headers.update(headers)
        response = session.get(self.events_url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        events = []
        tz = ZoneInfo(self.timezone)
        seen_urls = set()
        
        # Find all event tiles (div with data-id attribute containing tile)
        for tile_container in soup.select('div[data-id] .tile'):
            event = self._parse_tile(tile_container, tz)
            if event and event['url'] not in seen_urls:
                seen_urls.add(event['url'])
                events.append(event)
        
        self.logger.info(f"Found {len(events)} events")
        return events

    def _parse_tile(self, tile: BeautifulSoup, tz: ZoneInfo) -> dict[str, Any] | None:
        """Parse a single event tile."""
        try:
            # Get the thumb div which contains date info
            thumb = tile.select_one('.thumb')
            if not thumb:
                return None
            
            # Extract date from the ul/li structure
            # <ul><li>14</li><li>February<br /><small>Saturday</small></li></ul>
            date_items = thumb.select('ul li')
            if len(date_items) < 2:
                return None
            
            day = int(date_items[0].get_text(strip=True))
            
            # The month li contains: "February<br/><small>Saturday</small>"
            # We need to get just the first text node (month name)
            month_li = date_items[1]
            # Get direct text content before the <br/> or <small>
            month_text = ''
            for content in month_li.children:
                if isinstance(content, str):
                    month_text = content.strip().lower()
                    break
            
            if not month_text or month_text not in self.MONTHS:
                self.logger.warning(f"Unknown month: {month_text!r}")
                return None
            month = self.MONTHS[month_text]
            
            # Determine year - if month is before current month, assume next year
            now = datetime.now(tz)
            year = now.year
            if month < now.month or (month == now.month and day < now.day):
                year += 1
            
            # Get details div for title and time
            details = tile.select_one('.details')
            if not details:
                return None
            
            # Get title from the anchor tag
            title_link = details.select_one('a')
            if not title_link:
                return None
            
            title = title_link.get_text(strip=True)
            url = title_link.get('href', '')
            if url and not url.startswith('http'):
                url = f"{self.base_url}{url}"
            
            # Get presenter/organizer from span
            presenter_el = details.select_one('span')
            presenter = presenter_el.get_text(strip=True) if presenter_el else 'BCT'
            
            # Parse time from the <p> tag
            # Format: "Doors: 6:30 PM / Show: 7:00 PM<br />@ Buskirk-Chumley Theater"
            time_p = details.select_one('p')
            show_time = self._parse_time(time_p.get_text(strip=True) if time_p else '')
            
            # Create datetime
            dtstart = datetime(year, month, day, show_time[0], show_time[1], tzinfo=tz)
            dtend = dtstart + timedelta(hours=2)  # Assume 2 hour events
            
            # Create unique ID
            slug = re.sub(r'[^a-z0-9]+', '-', title.lower())[:30]
            uid = f"{dtstart.strftime('%Y%m%d')}-{slug}@{self.domain}"
            
            # Build description
            desc_parts = [title]
            if presenter and presenter != 'BCT':
                desc_parts.append(f"Presented by: {presenter}")
            if time_p:
                desc_parts.append(time_p.get_text(strip=True).replace('<br/>', '\n'))
            desc_parts.append(f"\nMore info: {url}")
            
            return {
                'title': title,
                'dtstart': dtstart,
                'dtend': dtend,
                'url': url,
                'location': 'Buskirk-Chumley Theater, 114 E Kirkwood Ave, Bloomington, IN 47408',
                'description': '\n'.join(desc_parts),
                'uid': uid,
            }
            
        except Exception as e:
            self.logger.warning(f"Error parsing tile: {e}")
            return None

    def _parse_time(self, text: str) -> tuple[int, int]:
        """Parse show time from text like 'Doors: 6:30 PM / Show: 7:00 PM'.
        
        Returns (hour, minute) tuple. Defaults to 19:00 if parsing fails.
        """
        # Look for "Show: X:XX PM/AM" pattern
        match = re.search(r'Show:\s*(\d{1,2}):(\d{2})\s*(AM|PM)', text, re.IGNORECASE)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            ampm = match.group(3).upper()
            
            if ampm == 'PM' and hour < 12:
                hour += 12
            elif ampm == 'AM' and hour == 12:
                hour = 0
            
            return (hour, minute)
        
        # Fallback: look for any time pattern
        match = re.search(r'(\d{1,2}):(\d{2})\s*(AM|PM)', text, re.IGNORECASE)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            ampm = match.group(3).upper()
            
            if ampm == 'PM' and hour < 12:
                hour += 12
            elif ampm == 'AM' and hour == 12:
                hour = 0
            
            return (hour, minute)
        
        # Default to 7 PM
        return (19, 0)


if __name__ == '__main__':
    BuskirkChumleyScraper.main()
