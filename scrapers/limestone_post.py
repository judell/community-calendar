#!/usr/bin/env python3
"""Scraper for Limestone Post Magazine events via CitySpark API."""

from lib.cityspark import CitySparkScraper


class LimestonePostScraper(CitySparkScraper):
    """Scraper for Limestone Post Magazine events (Bloomington, IN)."""

    name = "Limestone Post"
    domain = "limestonepost.org"
    timezone = "America/Indiana/Indianapolis"
    api_slug = "Limestone"
    ppid = 9251
    lat = 39.1653
    lng = -86.5264
    distance = 20
    calendar_url = "https://limestonepost.org/calendar/"


if __name__ == '__main__':
    LimestonePostScraper.main()
