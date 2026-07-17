#!/usr/bin/env python3
"""Scraper for Third Room Asheville events (SeeTickets widget).

Third Room is at 46 Wall St, Asheville NC.
Calendar page: https://thirdroom.art/calendar/
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import logging
import argparse

from lib.seetickets import SeeTicketsScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ThirdRoomScraper(SeeTicketsScraper):
    """Scraper for Third Room Asheville."""

    name = "Third Room"
    domain = "thirdroom.art"
    events_url = "https://thirdroom.art/calendar/"
    timezone = "America/New_York"
    default_location = "Third Room, 46 Wall St, Asheville, NC 28801"


def main():
    parser = argparse.ArgumentParser(description="Scrape Third Room Asheville events")
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = ThirdRoomScraper()
    scraper.run(args.output)


if __name__ == '__main__':
    main()
