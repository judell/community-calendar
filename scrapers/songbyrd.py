#!/usr/bin/env python3
"""
Songbyrd Music House (Washington, DC) — DICE-link harvest.

Songbyrd's events page links to ~76 individual DICE event pages via
link.dice.fm/<id> short URLs. Each DICE page carries a schema.org
MusicEvent JSON-LD block with full details. The lib/dice.py base class
handles the two-stage scrape.

Songkick coverage for Songbyrd is functionally dead (2 upcoming shows
at run time vs 76 actually scheduled), so this scraper is the right
source for Songbyrd's calendar, not scrapers/songkick.py.

Usage:
    python scrapers/songbyrd.py --output cities/dc-music/songbyrd.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

from lib.dice import DiceVenueScraper


class SongbyrdScraper(DiceVenueScraper):
    name = "Songbyrd"
    domain = "songbyrddc.com"
    timezone = "America/New_York"
    venue_url = "https://www.songbyrddc.com/events/"
    default_location = "Songbyrd Music House, 540 Penn St NE, Washington, DC 20002"


if __name__ == '__main__':
    SongbyrdScraper.main()
