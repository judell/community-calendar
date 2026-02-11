#!/usr/bin/env python3
"""Sports Basement Community Events scraper.

Scrapes events from Sports Basement's Elfsight calendar widget.
https://shop.sportsbasement.com/pages/calendar

Usage:
    # All locations
    python sportsbasement.py
    
    # Filter to Santa Rosa
    python sportsbasement.py --location "Santa Rosa"
    
    # Filter to multiple locations
    python sportsbasement.py --location "Santa Rosa" "Novato"
    
    # Filter by event type
    python sportsbasement.py --type "Run Events" --location "Santa Rosa"
    
    # List available locations/types
    python sportsbasement.py --list-locations
    python sportsbasement.py --list-types
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.lib.elfsight import ElfsightCalendarScraper


class SportsBasementScraper(ElfsightCalendarScraper):
    """Scraper for Sports Basement community events calendar."""
    
    name = "Sports Basement"
    domain = "sportsbasement.com"
    
    # Elfsight widget configuration
    widget_id = "c18b022b-4e3e-4ab7-9baa-a3214cef181f"
    source_page = "https://shop.sportsbasement.com/pages/calendar"


if __name__ == '__main__':
    SportsBasementScraper.main()
