#!/usr/bin/env python3
"""Parameterized Bookmanager bookstore events scraper.

Usage:
    python scrapers/bookmanager.py \\
        --san 1684035 \\
        --domain bakkaphoenixbooks.com \\
        --name "Bakka Phoenix Books" \\
        --output cities/toronto/bakka_phoenix.ics

The ``san`` is the Standard Address Number Bookmanager assigns each store; it
appears in the store's events page HTML as ``var san="..."``.
"""

import argparse
import logging
import sys

sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

from lib.bookmanager import BookmanagerEventsScraper


def main():
    parser = argparse.ArgumentParser(
        description="Scrape events from a Bookmanager-hosted bookstore"
    )
    parser.add_argument('--san', required=True, help='Bookmanager SAN (var san="..." in /events HTML)')
    parser.add_argument('--domain', required=True, help='Store website host (e.g. bakkaphoenixbooks.com)')
    parser.add_argument('--name', required=True, help='Display name for source attribution')
    parser.add_argument('--timezone', default='America/Toronto', help='IANA timezone (default America/Toronto)')
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    BookmanagerEventsScraper.setup_logging()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = BookmanagerEventsScraper(
        san=args.san,
        name=args.name,
        domain=args.domain,
        timezone=args.timezone,
    )
    scraper.run(args.output)


if __name__ == '__main__':
    main()
