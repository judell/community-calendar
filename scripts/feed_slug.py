#!/usr/bin/env python3
"""Canonical feed-URL -> filename slug.

Single source of truth shared by add_feed.py (test/registration time) and
download_feeds.py (download time) so the two always agree on a feed's .ics
filename. Provider-specific cases fold a disambiguating query param into the
slug (CivicPlus catID, Finalsite calendar_ids, LibCal cid, LiveWhale group_id)
so feeds that share a URL path but differ only in the query string do not
collide on the same filename.
"""

import re
from urllib.parse import urlparse


def slugify(url: str) -> str:
    """Generate a readable, collision-resistant filename slug from a feed URL."""
    parsed = urlparse(url)

    # Meetup: extract group slug
    if 'meetup.com' in parsed.netloc:
        match = re.search(r'meetup\.com/([^/]+)', url)
        if match:
            group = match.group(1)
            group = re.sub(r'[^a-zA-Z0-9]+', '_', group).lower().strip('_')
            return f"meetup_{group}"

    # Tockify: extract calendar name
    if 'tockify.com' in parsed.netloc:
        match = re.search(r'/ics/([^/]+)', url)
        if match:
            return f"tockify_{match.group(1)}"

    # CivicPlus (city/county sites): include catID to avoid collisions
    if '/iCalendar/iCalendar.aspx' in parsed.path:
        domain = parsed.netloc.replace('www.', '').split('.')[0]
        cat_match = re.search(r'catID=(\d+)', parsed.query)
        cat_id = f"_{cat_match.group(1)}" if cat_match else ''
        return f"civicplus_{domain}{cat_id}"

    # Finalsite calendar-manager (e.g. school districts): include calendar_ids
    # to avoid collisions — feeds share the /fs/calendar-manager/events.ics path
    # and differ only by the calendar_ids query string.
    if '/fs/calendar-manager/' in parsed.path:
        domain = parsed.netloc.replace('www.', '').split('.')[0]
        ids = re.findall(r'calendar_ids(?:%5B%5D|\[\])?=(\d+)', url)
        suffix = '_'.join(ids) if ids else ''
        slug = f"{domain}_cal_{suffix}" if suffix else f"{domain}_calendar_manager"
        return re.sub(r'[^a-zA-Z0-9]+', '_', slug).lower().strip('_')[:50]

    # Google Calendar: extract calendar ID prefix
    if 'calendar.google.com' in parsed.netloc:
        match = re.search(r'ical/([^%/]+)', url)
        if match:
            cal_id = match.group(1)
            cal_id = re.sub(r'[^a-zA-Z0-9]+', '_', cal_id).lower().strip('_')
            return f"gcal_{cal_id}"

    # LibCal: extract institution and calendar ID
    if 'libcal.com' in parsed.netloc:
        match = re.match(r'([^.]+)\.libcal\.com', parsed.netloc)
        inst = match.group(1) if match else 'libcal'
        cid_match = re.search(r'cid=(\d+)', url)
        cid = f"_{cid_match.group(1)}" if cid_match else ''
        return f"libcal_{inst}{cid}"

    # CampusLabs / beINvolved
    if 'campuslabs.com' in parsed.netloc:
        match = re.match(r'([^.]+)\.campuslabs\.com', parsed.netloc)
        inst = match.group(1) if match else 'campuslabs'
        return f"campuslabs_{inst}"

    # LiveWhale (e.g., events.iu.edu/live/ical/events/group_id/56)
    if '/live/ical/' in parsed.path:
        domain = parsed.netloc.replace('www.', '').split('.')[0]
        gid_match = re.search(r'group_id/(\d+)', url)
        gid = f"_{gid_match.group(1)}" if gid_match else ''
        return f"{domain}_livewhale{gid}"

    # General case: domain + meaningful path parts
    domain = parsed.netloc.replace('www.', '').split('.')[0]
    path_parts = [p for p in parsed.path.split('/')
                  if p and p not in ('events', 'ical', 'feed', 'calendar',
                                     'list', 'public', 'basic.ics')]

    if path_parts:
        slug = f"{domain}_{'_'.join(path_parts[:2])}"
    else:
        slug = domain

    slug = re.sub(r'[^a-zA-Z0-9]+', '_', slug).lower().strip('_')
    return slug[:50]
