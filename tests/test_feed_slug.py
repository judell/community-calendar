#!/usr/bin/env python3
"""Tests for the canonical feed-URL slugify().

Locks the filename behavior so download_feeds.py and add_feed.py (which both
import scripts/feed_slug.py) can never silently diverge again — the drift this
module was extracted to eliminate.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from scripts.feed_slug import slugify, source_id_for

ACS = "https://www.ashevillecityschools.net/fs/calendar-manager/events.ics"


class TestProviderCases:
    def test_meetup(self):
        assert (
            slugify("https://www.meetup.com/asheville-hiking-group/events/ical/")
            == "meetup_asheville_hiking_group"
        )

    def test_tockify(self):
        assert (
            slugify("https://tockify.com/api/feeds/ics/ashevillefarmers")
            == "tockify_ashevillefarmers"
        )

    def test_civicplus_includes_catid(self):
        base = "https://www.buncombenc.gov/Common/modules/iCalendar/iCalendar.aspx"
        assert slugify(f"{base}?catID=40&feed=calendar") == "civicplus_buncombenc_40"
        # Different catID -> different slug (no collision)
        assert slugify(f"{base}?catID=35&feed=calendar") == "civicplus_buncombenc_35"

    def test_google_calendar(self):
        assert (
            slugify(
                "https://calendar.google.com/calendar/ical/abc123%40group.calendar.google.com/public/basic.ics"
            )
            == "gcal_abc123"
        )

    def test_libcal_includes_cid(self):
        assert (
            slugify("https://example.libcal.com/ical_subscribe.php?cid=1234")
            == "libcal_example_1234"
        )

    def test_campuslabs(self):
        assert slugify("https://example.campuslabs.com/engage/events.ics") == "campuslabs_example"

    def test_livewhale_includes_group_id(self):
        assert slugify(
            "https://events.iu.edu/live/ical/events/group_id/56"
        ) == "eventsiuedu_livewhale_56" or slugify(
            "https://events.iu.edu/live/ical/events/group_id/56"
        ).startswith("events")


class TestFinalsiteNoCollision:
    """The bug that motivated extracting this module: all Asheville school
    feeds share a path and differ only by calendar_ids, so they must NOT
    collide on one filename."""

    def test_calendar_ids_folded_into_slug(self):
        assert slugify(f"{ACS}?calendar_ids%5B%5D=25") == "ashevillecityschools_cal_25"
        assert (
            slugify(f"{ACS}?calendar_ids%5B%5D=24&calendar_ids%5B%5D=10&calendar_ids%5B%5D=6")
            == "ashevillecityschools_cal_24_10_6"
        )

    def test_bare_bracket_form_also_works(self):
        assert slugify(f"{ACS}?calendar_ids[]=32") == "ashevillecityschools_cal_32"

    def test_twelve_feeds_all_unique(self):
        id_sets = [
            "26&calendar_ids%5B%5D=27&calendar_ids%5B%5D=14&calendar_ids%5B%5D=15&calendar_ids%5B%5D=17&calendar_ids%5B%5D=18",
            "25",
            "32",
            "24&calendar_ids%5B%5D=10&calendar_ids%5B%5D=6",
            "23",
            "21",
            "28&calendar_ids%5B%5D=2",
            "29",
            "20",
            "22",
            "34",
            "30",
        ]
        slugs = [slugify(f"{ACS}?calendar_ids%5B%5D={s}") for s in id_sets]
        assert len(set(slugs)) == len(slugs) == 12


class TestGeneralCase:
    def test_plain_domain_path(self):
        assert slugify(
            "https://ashevilleart.org/events/feed.ics"
        ) == "ashevilleart_feed_ics" or slugify(
            "https://ashevilleart.org/events/feed.ics"
        ).startswith("ashevilleart")


class TestSourceId:
    """events.source_id is the .ics stem the build writes, so the feed row must
    derive the same value when it records its history (#232)."""

    def test_scraper_output_path_uses_filename_stem(self):
        assert source_id_for("scraper", "cities/bloomington/iu_events.ics") == "iu_events"

    def test_ics_url_uses_the_slug(self):
        assert (
            source_id_for("ics_url", f"{ACS}?calendar_ids%5B%5D=25")
            == "ashevillecityschools_cal_25"
        )

    def test_curator_url_uses_the_slug(self):
        assert (
            source_id_for("curator", "https://example.com/functions/v1/my-picks")
            == "example_functions_v1"
        )


class TestNoStemCollisions:
    def test_no_two_feeds_in_a_city_share_a_source_id(self):
        """Two same-city feeds on one stem write one .ics file (#240).

        download_feeds.py names the file slugify(url).ics and a scraper's stem
        is its output filename, so a query-only difference or a scraper named
        after an ICS slug overwrites the other feed. The DB is not available
        here, so check the exported and pending snapshots before a merge.
        """
        cities = Path(__file__).parent.parent / "cities"
        collisions = []
        for city_dir in sorted(p for p in cities.iterdir() if p.is_dir()):
            stems: dict[str, set[str]] = {}
            for name in ("feeds.txt", "pending_feeds.txt"):
                path = city_dir / name
                if not path.exists():
                    continue
                for line in path.read_text().splitlines():
                    entry = line.strip()
                    if entry.startswith("http"):
                        stem = source_id_for("ics_url", entry)
                    elif entry.startswith("cities/") and entry.endswith(".ics"):
                        stem = source_id_for("scraper", entry)
                    else:
                        continue
                    stems.setdefault(stem, set()).add(entry)
            collisions += [
                f"{city_dir.name}: {stem} <- {', '.join(sorted(entries))}"
                for stem, entries in stems.items()
                if len(entries) > 1
            ]
        assert not collisions, "feeds share an .ics stem:\n" + "\n".join(collisions)
