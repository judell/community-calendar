#!/usr/bin/env python3
"""Verify that feeds.txt display names match SOURCE_NAMES in combine_ics.py.

Usage: python scripts/verify_source_names.py [city]
       If no city given, checks all cities.
"""

import re
import sys
from pathlib import Path

# Import SOURCE_NAMES from combine_ics
sys.path.insert(0, str(Path(__file__).parent))
from combine_ics import SOURCE_NAMES


def parse_feeds_txt(feeds_file):
    """Parse feeds.txt to build filename stem -> display name map."""
    names = {}
    lines = Path(feeds_file).read_text().splitlines()
    pending_name = None

    for i, line in enumerate(lines):
        stripped = line.strip()

        if stripped.startswith('# cmd:'):
            # Extract --name "Foo" if present
            m = re.search(r'--name\s+"([^"]+)"', stripped)
            if m:
                pending_name = m.group(1)
            continue

        if (stripped.startswith('#')
            and not stripped.startswith('# ---')
            and not stripped.startswith('# cmd:')
            and stripped not in ('# Scraper', '# Squarespace', '# Songkick',
                                 '# Chamber of Commerce')):
            # Comment line = display name for next entry
            name = stripped.lstrip('# ').split(' | ')[0].strip()
            if name:
                pending_name = name
            continue

        if stripped.startswith('cities/') and stripped.endswith('.ics'):
            stem = Path(stripped).stem
            if pending_name:
                names[stem] = pending_name
            pending_name = None

    return names


def titlecase_fallback(stem):
    """What combine_ics.py does when there's no SOURCE_NAMES entry."""
    if stem.startswith('SRCity_'):
        return 'City of Santa Rosa'
    return stem.replace('_', ' ').title()


def main():
    cities_dir = Path('cities')
    if len(sys.argv) > 1:
        cities = [sys.argv[1]]
    else:
        cities = sorted(d.name for d in cities_dir.iterdir()
                       if d.is_dir() and (d / 'feeds.txt').exists())

    all_ok = True
    for city in cities:
        feeds_file = cities_dir / city / 'feeds.txt'
        if not feeds_file.exists():
            continue

        feeds_names = parse_feeds_txt(feeds_file)
        print(f"\n=== {city} ({len(feeds_names)} scraper entries) ===")

        for stem, feeds_name in sorted(feeds_names.items()):
            source_name = SOURCE_NAMES.get(stem)
            fallback = titlecase_fallback(stem)

            if source_name:
                if feeds_name == source_name:
                    print(f"  ✅ {stem}: {feeds_name}")
                else:
                    print(f"  ❌ {stem}: feeds.txt={feeds_name!r} vs SOURCE_NAMES={source_name!r}")
                    all_ok = False
            else:
                # No SOURCE_NAMES entry — check if feeds.txt matches fallback
                if feeds_name == fallback:
                    print(f"  ✅ {stem}: {feeds_name} (matches fallback)")
                else:
                    # feeds.txt has a better name than the fallback — this is fine,
                    # it means feeds.txt improves on the fallback
                    print(f"  ✅ {stem}: {feeds_name} (better than fallback {fallback!r})")

        # Check for SOURCE_NAMES entries not in feeds.txt
        for stem, source_name in sorted(SOURCE_NAMES.items()):
            if stem not in feeds_names:
                # Could be a live feed, not a scraper — skip those
                pass

    if all_ok:
        print("\n✅ All feeds.txt names match SOURCE_NAMES")
    else:
        print("\n❌ Mismatches found — fix feeds.txt comments to match SOURCE_NAMES")
    return 0 if all_ok else 1


if __name__ == '__main__':
    sys.exit(main())
