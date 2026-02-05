#!/usr/bin/env python3
"""Scraper for North Bay Bohemian events via CitySpark API."""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])  # Add scrapers/ to path

from lib.cityspark import BohemianScraper

if __name__ == '__main__':
    BohemianScraper.main()
