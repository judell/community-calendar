#!/usr/bin/env python3
"""Migrate SOURCE_NAMES/SOURCE_URLS metadata into feeds.txt structured comments.

For each feed URL in feeds.txt, computes the slugify() result, looks up
the friendly name and fallback URL from combine_ics.py's dicts (trying
both the correct slug and the old mismatched key), and writes a structured
comment above the URL.

Usage:
    python scripts/migrate_feeds_metadata.py              # dry-run
    python scripts/migrate_feeds_metadata.py --write      # actually write
    python scripts/migrate_feeds_metadata.py --city davis  # single city
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from download_feeds import slugify

ROOT = Path(__file__).parent.parent


def load_dicts():
    """Load SOURCE_NAMES and SOURCE_URLS from combine_ics.py."""
    text = (ROOT / 'scripts/combine_ics.py').read_text()

    def extract_dict(name):
        pattern = rf'^{name}\s*=\s*(\{{.*?^\}})'
        m = re.search(pattern, text, re.MULTILINE | re.DOTALL)
        if not m:
            return {}
        try:
            return eval(m.group(1))
        except Exception as e:
            print(f"Warning: could not parse {name}: {e}")
            return {}

    return extract_dict('SOURCE_NAMES'), extract_dict('SOURCE_URLS')


def build_reverse_maps(source_names, source_urls):
    """Build reverse lookup maps to find old keys from URL patterns.

    Returns:
        url_to_name: {meetup_slug_or_gcal_id: friendly_name}
        url_to_fallback: {meetup_slug_or_gcal_id: fallback_url}
    """
    # Build a map from SOURCE_URLS values to their keys
    url_key_map = {}
    for key, url in source_urls.items():
        url_key_map[url] = key

    # Build reverse maps keyed by URL patterns that we can match against feed URLs
    name_by_url = {}  # source_url_value -> friendly_name
    for key, url in source_urls.items():
        if key in source_names:
            name_by_url[url] = source_names[key]

    return name_by_url, url_key_map


def find_name_for_feed(url, slug, source_names, source_urls, name_by_url):
    """Find the friendly name for a feed URL, trying multiple strategies."""
    # Strategy 1: Direct slug match in SOURCE_NAMES
    if slug in source_names:
        return source_names[slug], source_urls.get(slug)

    # Strategy 2: Match via SOURCE_URLS - find an entry whose URL matches this feed
    # For Meetup: SOURCE_URLS has https://www.meetup.com/group-slug/
    if 'meetup.com' in url:
        m = re.search(r'meetup\.com/([^/]+)', url)
        if m:
            group = m.group(1).lower().rstrip('/')
            for surl, name in name_by_url.items():
                sm = re.search(r'meetup\.com/([^/]+)', surl)
                if sm and sm.group(1).lower().rstrip('/') == group:
                    fallback = surl
                    return name, fallback

    # Strategy 3: For Google Calendar, try matching calendar ID
    if 'calendar.google.com' in url:
        m = re.search(r'ical/([^%/]+)', url)
        if m:
            cal_id_prefix = m.group(1).lower()[:20]
            for key in source_names:
                if cal_id_prefix[:10] in key.lower():
                    return source_names[key], source_urls.get(key)

    # Strategy 4: For WordPress/generic feeds, try matching domain
    from urllib.parse import urlparse
    domain = urlparse(url).netloc.replace('www.', '').split('.')[0]
    for key in source_names:
        if key == domain or key.startswith(domain + '_'):
            return source_names[key], source_urls.get(key)

    # Strategy 5: Fuzzy match - slug without underscores vs key without underscores
    slug_flat = slug.replace('_', '')
    for key in source_names:
        key_flat = key.replace('_', '')
        if slug_flat == key_flat or slug_flat.startswith(key_flat) or key_flat.startswith(slug_flat):
            return source_names[key], source_urls.get(key)

    return None, None


def migrate_city(city_dir, source_names, source_urls, name_by_url, write):
    feeds_file = city_dir / 'feeds.txt'
    if not feeds_file.exists():
        return 0

    city = city_dir.name
    lines = feeds_file.read_text().splitlines()
    new_lines = []
    changes = 0
    unmapped = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()
        raw_line = lines[i]

        if line.startswith('https://'):
            url = line
            slug = slugify(url)
            name, fallback = find_name_for_feed(url, slug, source_names, source_urls, name_by_url)

            if not name:
                unmapped.append((slug, url))
                new_lines.append(raw_line)
                i += 1
                continue

            # Build structured comment
            if fallback:
                comment = f"# {name} | {fallback}"
            else:
                comment = f"# {name}"

            # Check if previous line is already a good comment
            prev_is_comment = (new_lines and new_lines[-1].strip().startswith('#')
                               and not new_lines[-1].strip().startswith('# ---'))

            if prev_is_comment:
                old_comment = new_lines[-1].strip()
                if old_comment != comment:
                    new_lines[-1] = comment
                    changes += 1
            else:
                new_lines.append(comment)
                changes += 1

            new_lines.append(raw_line)
            i += 1
            continue

        new_lines.append(raw_line)
        i += 1

    if unmapped:
        print(f"  [{city}] {len(unmapped)} feeds need friendly names:")
        for slug, url in unmapped[:5]:
            print(f"    {slug}")
        if len(unmapped) > 5:
            print(f"    ... and {len(unmapped)-5} more")

    if changes and write:
        feeds_file.write_text('\n'.join(new_lines) + '\n')
        print(f"  [{city}] Wrote {changes} changes")
    elif changes:
        print(f"  [{city}] {changes} changes (dry-run)")

    return changes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--city', help='Only migrate a specific city')
    args = parser.parse_args()

    source_names, source_urls = load_dicts()
    name_by_url, url_key_map = build_reverse_maps(source_names, source_urls)
    print(f"Loaded {len(source_names)} SOURCE_NAMES, {len(source_urls)} SOURCE_URLS")

    cities_dir = ROOT / 'cities'
    total = 0

    dirs = [cities_dir / args.city] if args.city else sorted(cities_dir.iterdir())
    for city_dir in dirs:
        if city_dir.is_dir() and (city_dir / 'feeds.txt').exists():
            total += migrate_city(city_dir, source_names, source_urls, name_by_url, args.write)

    print(f"\nTotal: {total} changes" + (" (dry-run)" if not args.write else ""))


if __name__ == '__main__':
    main()
