#!/usr/bin/env python3
"""Validate and fix SOURCE_NAMES/SOURCE_URLS keys in combine_ics.py.

Computes the correct slug for every feed URL (using download_feeds.slugify)
and every scraper output (from the workflow YAML), then checks whether
SOURCE_NAMES has a matching entry. Reports mismatches and can auto-fix
key renames where the friendly name is already known.

Usage:
    python scripts/validate_source_names.py              # report only
    python scripts/validate_source_names.py --fix        # rewrite combine_ics.py
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from download_feeds import slugify


def get_feed_slugs():
    """Compute slug -> (city, url) for all feeds across all cities."""
    cities_dir = Path('cities')
    slugs = {}
    for feeds_file in sorted(cities_dir.glob('*/feeds.txt')):
        city = feeds_file.parent.name
        for line in feeds_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith('#') or not line.startswith('http'):
                continue
            slug = slugify(line)
            slugs[slug] = (city, line)
    return slugs


def get_scraper_slugs():
    """Extract scraper output filenames from the workflow YAML."""
    workflow = Path('.github/workflows/generate-calendar.yml')
    if not workflow.exists():
        return {}
    text = workflow.read_text()
    slugs = {}
    for m in re.finditer(r'--output\s+cities/([^/]+)/([^\s]+)\.ics', text):
        city = m.group(1)
        slug = m.group(2)
        slugs[slug] = (city, f'scraper:{slug}')
    return slugs


def build_url_to_key_map(text):
    """Build a reverse map from SOURCE_URLS values -> keys."""
    url_to_key = {}
    in_source_urls = False
    for line in text.splitlines():
        if 'SOURCE_URLS' in line and '=' in line and '{' in line:
            in_source_urls = True
            continue
        if in_source_urls:
            if line.strip() == '}':
                break
            m = re.match(r"\s+'([^']+)'\s*:\s*'([^']+)'", line)
            if m:
                url_to_key[m.group(2)] = m.group(1)
    return url_to_key


def find_rename_pairs(feed_slugs, scraper_slugs, text):
    """Find (old_key, new_slug, friendly_name) triples where we can rename."""
    all_slugs = {**feed_slugs, **scraper_slugs}

    # Parse SOURCE_NAMES from text
    source_names = {}
    in_sn = False
    for line in text.splitlines():
        if line.strip().startswith('SOURCE_NAMES') and '=' in line and '{' in line:
            in_sn = True
            continue
        if in_sn:
            if line.strip() == '}':
                break
            m = re.match(r"\s+'([^']+)'\s*:\s*['\"](.+?)['\"]", line)
            if m:
                source_names[m.group(1)] = m.group(2)

    # Strategy 1: Match via SOURCE_URLS - if an old key has a URL that maps
    # to a feed URL, and slugify(feed_url) gives a different slug, rename
    url_to_key = build_url_to_key_map(text)

    renames = {}  # old_key -> new_slug
    for slug, (city, url) in feed_slugs.items():
        if slug in source_names:
            continue  # already correct
        # Check if this URL (or a variant) appears in SOURCE_URLS
        for surl, old_key in url_to_key.items():
            if old_key == slug:
                continue  # already matches
            # Meetup: SOURCE_URLS has /meetup-slug/, feed has /meetup-slug/events/ical/
            if 'meetup.com' in url and 'meetup.com' in surl:
                # Extract group slug from both
                m1 = re.search(r'meetup\.com/([^/]+)', url)
                m2 = re.search(r'meetup\.com/([^/]+)', surl)
                if m1 and m2 and m1.group(1) == m2.group(1):
                    if old_key in source_names and old_key != slug:
                        renames[old_key] = slug
                        continue
            # Google Calendar: compare decoded calendar IDs
            if 'calendar.google.com' in url and 'calendar.google.com' in (surl or ''):
                if old_key != slug and old_key in source_names:
                    renames[old_key] = slug
                    continue

    # Strategy 2: Direct substring matching for legacy calendar_ -> gcal_ renames
    orphaned = [k for k in source_names if k not in all_slugs]
    for old_key in orphaned:
        if old_key.startswith('calendar_'):
            # Try to find a gcal_ slug that matches
            old_core = old_key.replace('calendar_', '').replace('_40group_calend', '').replace('_40gmail_com_public', '')
            for slug in all_slugs:
                if slug.startswith('gcal_') and old_core[:15] in slug and slug not in source_names:
                    renames[old_key] = slug
                    break

    # Strategy 3: Match orphaned short meetup keys to full meetup slugs
    for old_key in orphaned:
        if old_key in renames:
            continue
        if old_key.startswith('meetup_'):
            old_suffix = old_key[7:]  # strip meetup_
            for slug, (city, url) in feed_slugs.items():
                if not slug.startswith('meetup_'):
                    continue
                if slug in source_names:
                    continue
                new_suffix = slug[7:]
                # old is a prefix or substring of new
                if new_suffix.startswith(old_suffix) or old_suffix in new_suffix:
                    renames[old_key] = slug
                    break

    # Strategy 4: Match orphaned keys where the slug is just a different form
    # e.g., 'putahcreek' vs 'putahcreekcouncil', 'visityolo' vs 'visityolo_event'
    for old_key in orphaned:
        if old_key in renames:
            continue
        for slug in all_slugs:
            if slug in source_names:
                continue
            if slug.startswith(old_key) and slug not in renames.values():
                renames[old_key] = slug
                break

    return renames, source_names


def main():
    parser = argparse.ArgumentParser(description='Validate SOURCE_NAMES keys')
    parser.add_argument('--fix', action='store_true', help='Auto-fix key renames in combine_ics.py')
    args = parser.parse_args()

    combine_path = Path('scripts/combine_ics.py')
    text = combine_path.read_text()

    feed_slugs = get_feed_slugs()
    scraper_slugs = get_scraper_slugs()
    all_slugs = {**feed_slugs, **scraper_slugs}

    renames, source_names = find_rename_pairs(feed_slugs, scraper_slugs, text)

    # Classify all keys
    matched = [s for s in all_slugs if s in source_names]
    missing = [(s, all_slugs[s]) for s in sorted(all_slugs) if s not in source_names and s not in renames.values()]
    orphaned_unrenameable = [k for k in sorted(source_names) if k not in all_slugs and k not in renames]

    print(f"\nKey renames needed ({len(renames)}):")
    print(f"{'='*70}")
    for old, new in sorted(renames.items()):
        name = source_names.get(old, '?')
        print(f"  '{old}' -> '{new}'  ({name})")

    if missing:
        print(f"\nSlugs with no SOURCE_NAMES entry ({len(missing)}):")
        print(f"{'='*70}")
        for slug, (city, src) in missing[:30]:
            print(f"  {slug:50s} ({city})")
        if len(missing) > 30:
            print(f"  ... and {len(missing)-30} more")

    if orphaned_unrenameable:
        print(f"\nOrphaned SOURCE_NAMES keys - no matching feed/scraper ({len(orphaned_unrenameable)}):")
        print(f"{'='*70}")
        for key in orphaned_unrenameable:
            print(f"  '{key}': '{source_names[key]}'")

    print(f"\nSummary: {len(matched)} matched, {len(renames)} renameable, "
          f"{len(missing)} missing (need friendly name), {len(orphaned_unrenameable)} orphaned")

    if args.fix and renames:
        for old_key, new_slug in sorted(renames.items()):
            text = text.replace(f"'{old_key}'", f"'{new_slug}'")
            print(f"  Fixed: '{old_key}' -> '{new_slug}'")
        combine_path.write_text(text)
        print(f"\nWrote {len(renames)} renames to {combine_path}")


if __name__ == '__main__':
    main()
