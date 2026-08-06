#!/usr/bin/env python3
"""Add a new scraper to the pipeline.

This script automates the required steps for integrating a scraper:
1. Verify the scraper exists and optionally test it
2. Add a scraper entry to cities/<city>/pending_feeds.txt

The workflow moves pending entries into the feeds table, then runs scrapers
from active feed rows in the database. For each selected city it reads
`feed_type='scraper'` rows, executes each row's `scraper_cmd`, and writes the
output to that row's `url` path. Legacy workflow commands remain only as a
fallback for older scraper rows that have not been backfilled yet.

Usage:
    python scripts/add_scraper.py sportsbasement santarosa "Sports Basement"
    python scripts/add_scraper.py myscraper davis "My Source" --test

Initial upstream rollout:
    1. Merge the DB-driven scraper runner while legacy workflow commands remain
       available as fallback for older rows not yet backfilled.
    2. Backfill existing scraper rows into the feeds table with
       scripts/backfill_scraper_feeds.py.
    3. Use this script for all new scrapers so they enter through the DB-backed
       path immediately.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Repository root
ROOT = Path(__file__).parent.parent
SCRAPERS_DIR = ROOT / "scrapers"


def find_scraper(name: str) -> Path | None:
    """Find the scraper file."""
    # Try direct path
    direct = SCRAPERS_DIR / f"{name}.py"
    if direct.exists():
        return direct
    
    # Try in subdirectories
    for subdir in SCRAPERS_DIR.iterdir():
        if subdir.is_dir() and not subdir.name.startswith('_'):
            path = subdir / f"{name}.py"
            if path.exists():
                return path
    
    return None


def test_scraper(scraper_path: Path) -> bool:
    """Run the scraper and verify it produces events."""
    print(f"\n🧪 Testing scraper: {scraper_path}")
    
    output_file = Path("/tmp/scraper_test.ics")
    try:
        result = subprocess.run(
            [sys.executable, str(scraper_path), "--output", str(output_file)],
            env={**os.environ, 'SCRAPE_MONTHS': '2'},
            capture_output=True,
            text=True,
            timeout=120,
            cwd=ROOT
        )
        
        if result.returncode != 0:
            print(f"❌ Scraper failed with exit code {result.returncode}")
            print(f"   stderr: {result.stderr[:500]}")
            return False
        
        if not output_file.exists():
            print("❌ Scraper did not produce output file")
            return False
        
        content = output_file.read_text()
        event_count = content.count("BEGIN:VEVENT")
        
        if event_count == 0:
            print("⚠️  Scraper produced 0 events (may be normal if no upcoming events)")
        else:
            print(f"✅ Scraper produced {event_count} events")
        
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Scraper timed out after 120 seconds")
        return False
    except Exception as e:
        print(f"❌ Error running scraper: {e}")
        return False
    finally:
        if output_file.exists():
            output_file.unlink()


def add_to_pending_feeds(city: str, scraper_path: Path, extra_args: str,
                         output_name: str, display_name: str) -> bool:
    """Append the scraper entry to cities/{city}/pending_feeds.txt."""
    feeds_path = ROOT / f"cities/{city}/pending_feeds.txt"

    print(f"\n📝 Adding to {feeds_path.relative_to(ROOT)}")

    if not feeds_path.exists():
        print(f"❌ pending_feeds.txt not found: {feeds_path}")
        return False

    content = feeds_path.read_text()
    output_file = f"cities/{city}/{output_name}.ics"

    if output_file in content:
        print(f"✅ Already in pending_feeds.txt")
        return True

    extra = f" {extra_args}" if extra_args else ""
    cmd = f"python {scraper_path.relative_to(ROOT)}{extra}"
    entry = f"\n# {display_name}\n# cmd: {cmd}\n{output_file}\n"

    with open(feeds_path, 'a') as f:
        f.write(entry)

    print(f"✅ Added to pending_feeds.txt: {display_name}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Add a scraper to the calendar pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/add_scraper.py sportsbasement santarosa "Sports Basement"
  python scripts/add_scraper.py myscraper davis "My Source" --test
  python scripts/add_scraper.py newscraper bloomington "News Source" --dry-run
  python scripts/add_scraper.py eventbrite petaluma "Blue Zones Project Petaluma" --extra-args '--url "https://www.eventbrite.com/o/78957912343" --name "Blue Zones Project Petaluma"' --output-name bluezones_petaluma
"""
    )
    parser.add_argument('scraper', help='Scraper name (without .py extension)')
    parser.add_argument('city', help='City directory name (e.g., santarosa, davis, bloomington)')
    parser.add_argument('display_name', help='Human-readable source name for display')
    parser.add_argument('--test', action='store_true', help='Test the scraper before adding')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--extra-args', default='', help='Extra arguments inserted before --output (e.g. \'--url "https://..." --name "My Source"\')')
    parser.add_argument('--output-name', default='', help='Override the output .ics filename (without .ics extension, default: scraper name)')
    
    args = parser.parse_args()
    
    print(f"🔧 Adding scraper '{args.scraper}' to {args.city} pipeline")
    print(f"   Display name: {args.display_name}")
    
    # Step 1: Find the scraper
    scraper_path = find_scraper(args.scraper)
    if not scraper_path:
        print(f"\n❌ Scraper not found: {args.scraper}")
        print(f"   Looked in: {SCRAPERS_DIR}")
        print(f"   Expected file: {args.scraper}.py")
        sys.exit(1)
    
    print(f"\n✅ Found scraper: {scraper_path}")
    
    ics_name = args.output_name or Path(args.scraper).name
    extra = f" {args.extra_args}" if args.extra_args else ""

    if args.dry_run:
        print("\n[DRY RUN] Would perform the following:")
        print(f"  1. Add to pending_feeds.txt: cities/{args.city}/{ics_name}.ics")
        print("  2. Next build will process the pending scraper into the feeds table")
        print(f"     - city={args.city}")
        print(f"     - url=cities/{args.city}/{ics_name}.ics")
        print(f"     - name={args.display_name}")
        print(f"     - scraper_cmd=python {scraper_path.relative_to(ROOT)}{extra}")
        print("  3. The workflow's scraper runner will query active scraper rows for that city")
        print("  4. It will execute scraper_cmd from the DB row and expect output at the row's url path")
        print("  5. Legacy hardcoded workflow commands are used only as fallback for older rows not yet backfilled")
        return
    
    # Step 2: Test if requested
    if args.test:
        if not test_scraper(scraper_path):
            print("\n⚠️  Scraper test had issues. Continue anyway? [y/N] ", end='')
            response = input().strip().lower()
            if response != 'y':
                sys.exit(1)
    
    # Step 3: Add to pending_feeds.txt
    add_to_pending_feeds(args.city, scraper_path, args.extra_args, ics_name, args.display_name)

    print("\n" + "="*60)
    print("✅ Done! Next steps:")
    print("  1. Review changes: git diff")
    print(f"  2. Commit: git add -A && git commit -m 'Add {args.scraper} scraper'")
    print("  3. Push: git push")
    print("  4. Trigger workflow or wait for daily run")
    print("  5. The workflow will move the pending scraper into the feeds table, then run its scraper_cmd from that row")
    print("="*60)


if __name__ == '__main__':
    main()
