#!/usr/bin/env python3
"""
Scraper for Santa Rosa Cycling Club events
https://srcc.com/Calendar

Uses RSS feed at https://srcc.com/Calendar/RSS
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])  # Add scrapers/ to path

import re
from datetime import timedelta
from html import unescape
from typing import Any, Optional

from bs4 import BeautifulSoup

from lib.rss import RssScraper


class SRCCScraper(RssScraper):
    """Scraper for Santa Rosa Cycling Club events."""
    
    name = "Santa Rosa Cycling Club"
    domain = "srcc.com"
    rss_url = "https://srcc.com/Calendar/RSS"
    
    def parse_entry(self, entry: dict, year: int, month: int) -> Optional[dict[str, Any]]:
        """Parse a single RSS entry into event data."""
        dt_start = self.parse_rss_date(entry)
        if not dt_start:
            return None
        
        # Filter by target month
        if dt_start.year != year or dt_start.month != month:
            return None
        
        # Parse title - format: "Event Name (Day, Month DD, YYYY)"
        title = entry.get('title', '')
        title = re.sub(r'\s*\([^)]+\d{4}\)\s*$', '', title).strip()
        
        if not title:
            return None
        
        # Get description and extract location
        description_html = entry.get('description', '')
        location = self._extract_location(description_html)
        description = self._clean_description(description_html)
        
        # Assume rides are ~3 hours
        dt_end = dt_start + timedelta(hours=3)
        
        return {
            'title': title,
            'dtstart': dt_start,
            'dtend': dt_end,
            'url': entry.get('link', ''),
            'location': location,
            'description': description,
        }
    
    def _extract_location(self, description_html: str) -> Optional[str]:
        """Extract location from the description HTML."""
        if not description_html:
            return None
        
        soup = BeautifulSoup(description_html, 'html.parser')
        text = soup.get_text(' ', strip=True)
        
        # Common patterns: "Starts at Esposti Park, Windsor"
        match = re.search(r'Starts? at\s+([^.]+?)(?:\s*\d{4,}|\s*Led by|\s*Route:|$)', text, re.IGNORECASE)
        if match:
            location = re.sub(r'\s+', ' ', match.group(1).strip())
            if 10 < len(location) < 200:
                return location
        
        return None
    
    def _clean_description(self, description_html: str) -> str:
        """Clean HTML description for display."""
        if not description_html:
            return ''
        
        soup = BeautifulSoup(description_html, 'html.parser')
        text = unescape(soup.get_text(' ', strip=True))
        text = re.sub(r'\s+', ' ', text)
        
        # Truncate at common boilerplate phrases
        for cutoff in ['PLEASE arrive at LEAST', 'Visitors are welcome', 'All riders MUST wear']:
            idx = text.find(cutoff)
            if idx > 0:
                text = text[:idx].strip()
                break
        
        # Limit length
        if len(text) > 500:
            text = text[:500] + '...'
        
        return text


if __name__ == '__main__':
    SRCCScraper.main()
