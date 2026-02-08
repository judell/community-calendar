#!/usr/bin/env python3
"""Scraper for The Comedy Attic events."""

import re
import sys
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from lib.base import BaseScraper


class ComedyAtticScraper(BaseScraper):
    """Scraper for The Comedy Attic in Bloomington."""

    name = "The Comedy Attic"
    domain = "comedyattic.com"
    events_url = "https://comedyattic.com/events"
    timezone = "America/Indiana/Indianapolis"

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from the events page."""
        self.logger.info(f"Fetching events from {self.events_url}")
        
        response = requests.get(self.events_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        events = []
        tz = ZoneInfo(self.timezone)
        
        # Find all event items
        for item in soup.select('.event-list-item'):
            # Get title and link
            header = item.select_one('.el-header a')
            if not header:
                continue
                
            title = header.get_text(strip=True)
            url = header.get('href', '')
            if url and not url.startswith('http'):
                url = f"https://comedyattic.com{url}"
            
            # Get all dates for this event
            for date_el in item.select('.event-date'):
                date_text = date_el.get_text(strip=True)
                
                # Parse date formats:
                # "Thu, Feb 12, 2026" or "Thu Feb 12 2026, 8:00 PM"
                dt = self._parse_date(date_text, tz)
                if not dt:
                    continue
                
                # Default show time is 8 PM if not specified
                if dt.hour == 0:
                    dt = dt.replace(hour=20)
                
                # Create unique ID from date + title slug
                slug = re.sub(r'[^a-z0-9]+', '-', title.lower())[:30]
                uid = f"{dt.strftime('%Y%m%d')}-{slug}"
                
                events.append({
                    'title': title,
                    'dtstart': dt,
                    'dtend': dt.replace(hour=dt.hour + 2),  # ~2 hour shows
                    'url': url,
                    'location': 'The Comedy Attic, 123 S Walnut St, Bloomington, IN',
                    'description': title,
                    'uid': uid,
                })
                
        self.logger.info(f"Found {len(events)} events")
        return events

    def _parse_date(self, text: str, tz: ZoneInfo) -> datetime | None:
        """Parse date string into datetime."""
        # Clean up whitespace
        text = ' '.join(text.split())
        
        # Try various formats
        formats = [
            # "Thu, Feb 12, 2026"
            ("%a, %b %d, %Y", False),
            # "Thu Feb 12 2026, 8:00 PM"  
            ("%a %b %d %Y, %I:%M %p", True),
            # "Thu Feb  5 2026, 8:00 PM" (extra space)
            ("%a %b %d %Y, %I:%M %p", True),
        ]
        
        for fmt, has_time in formats:
            try:
                dt = datetime.strptime(text, fmt)
                return dt.replace(tzinfo=tz)
            except ValueError:
                continue
        
        # Try with regex for more flexibility
        match = re.match(
            r'\w+,?\s+(\w+)\s+(\d+),?\s+(\d{4})(?:,?\s+(\d+):(\d+)\s*(AM|PM))?',
            text
        )
        if match:
            month_str, day, year = match.group(1), int(match.group(2)), int(match.group(3))
            hour = int(match.group(4)) if match.group(4) else 0
            minute = int(match.group(5)) if match.group(5) else 0
            ampm = match.group(6)
            
            # Convert month name
            months = {
                'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
            }
            month = months.get(month_str[:3])
            if not month:
                return None
            
            # Handle AM/PM
            if ampm and ampm.upper() == 'PM' and hour < 12:
                hour += 12
            elif ampm and ampm.upper() == 'AM' and hour == 12:
                hour = 0
                
            return datetime(year, month, day, hour, minute, tzinfo=tz)
            
        return None


if __name__ == '__main__':
    ComedyAtticScraper.main()
