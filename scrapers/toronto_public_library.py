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

    # Kids/family topical scope:
    # School Age Children (6-12), Teens (13-17)
    audience_ids = [
        "6894f7dab7a97e36001ab2b9",
        "67eab59153f2873000a90aa8",
    ]

    # Keep bounded runtime for CI while still covering broad upcoming set.
    page_limit = 100
    max_pages = 80


if __name__ == "__main__":
    TorontoPublicLibraryScraper.main()
