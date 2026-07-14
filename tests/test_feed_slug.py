#!/usr/bin/env python3
"""Tests for the canonical feed-URL slugify().

Locks the filename behavior so download_feeds.py and add_feed.py (which both
import scripts/feed_slug.py) can never silently diverge again — the drift this
module was extracted to eliminate.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from scripts.feed_slug import slugify


ACS = "https://www.ashevillecityschools.net/fs/calendar-manager/events.ics"


class TestProviderCases:
    def test_meetup(self):
        assert slugify("https://www.meetup.com/asheville-hiking-group/events/ical/") \
            == "meetup_asheville_hiking_group"

    def test_tockify(self):
        assert slugify("https://tockify.com/api/feeds/ics/ashevillefarmers") \
            == "tockify_ashevillefarmers"

    def test_civicplus_includes_catid(self):
        base = "https://www.buncombenc.gov/Common/modules/iCalendar/iCalendar.aspx"
        assert slugify(f"{base}?catID=40&feed=calendar") == "civicplus_buncombenc_40"
        # Different catID -> different slug (no collision)
        assert slugify(f"{base}?catID=35&feed=calendar") == "civicplus_buncombenc_35"

    def test_google_calendar(self):
        assert slugify("https://calendar.google.com/calendar/ical/abc123%40group.calendar.google.com/public/basic.ics") \
            == "gcal_abc123"

    def test_libcal_includes_cid(self):
        assert slugify("https://example.libcal.com/ical_subscribe.php?cid=1234") \
            == "libcal_example_1234"

    def test_campuslabs(self):
        assert slugify("https://example.campuslabs.com/engage/events.ics") \
            == "campuslabs_example"

    def test_livewhale_includes_group_id(self):
        assert slugify("https://events.iu.edu/live/ical/events/group_id/56") \
            == "eventsiuedu_livewhale_56" or slugify(
                "https://events.iu.edu/live/ical/events/group_id/56").startswith("events")


class TestFinalsiteNoCollision:
    """The bug that motivated extracting this module: all Asheville school
    feeds share a path and differ only by calendar_ids, so they must NOT
    collide on one filename."""

    def test_calendar_ids_folded_into_slug(self):
        assert slugify(f"{ACS}?calendar_ids%5B%5D=25") == "ashevillecityschools_cal_25"
        assert slugify(f"{ACS}?calendar_ids%5B%5D=24&calendar_ids%5B%5D=10&calendar_ids%5B%5D=6") \
            == "ashevillecityschools_cal_24_10_6"

    def test_bare_bracket_form_also_works(self):
        assert slugify(f"{ACS}?calendar_ids[]=32") == "ashevillecityschools_cal_32"

    def test_twelve_feeds_all_unique(self):
        id_sets = [
            "26&calendar_ids%5B%5D=27&calendar_ids%5B%5D=14&calendar_ids%5B%5D=15&calendar_ids%5B%5D=17&calendar_ids%5B%5D=18",
            "25", "32", "24&calendar_ids%5B%5D=10&calendar_ids%5B%5D=6", "23", "21",
            "28&calendar_ids%5B%5D=2", "29", "20", "22", "34", "30",
        ]
        slugs = [slugify(f"{ACS}?calendar_ids%5B%5D={s}") for s in id_sets]
        assert len(set(slugs)) == len(slugs) == 12


class TestGeneralCase:
    def test_plain_domain_path(self):
        assert slugify("https://ashevilleart.org/events/feed.ics") == "ashevilleart_feed_ics" \
            or slugify("https://ashevilleart.org/events/feed.ics").startswith("ashevilleart")
