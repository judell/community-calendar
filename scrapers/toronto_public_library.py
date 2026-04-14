#!/usr/bin/env python3
"""Toronto Public Library scraper using generic Bibliocommons base."""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

from lib.bibliocommons import BibliocommonsEventsScraper


class TorontoPublicLibraryScraper(BibliocommonsEventsScraper):
    name = "Toronto Public Library"
    domain = "tpl.bibliocommons.com"
    timezone = "America/Toronto"
    library_slug = "tpl"

    # No audience filter — accept all 6 TPL audience buckets
    # (Preschool 0-5, School Age 6-12, Teens 13-17, Younger Adults 18-24,
    #  Adults 18+, Older Adults) plus any events with no audience tag.
    # No type filter either — all 19 event types pass through.
    audience_ids: list[str] = []

    # Keep bounded runtime for CI while still covering broad upcoming set.
    page_limit = 100
    max_pages = 80


if __name__ == "__main__":
    TorontoPublicLibraryScraper.main()
