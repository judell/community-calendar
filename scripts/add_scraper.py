#!/usr/bin/env python3
"""Add a new scraper to the pipeline (DB-first).

This script registers a scraper for a city:
1. Verify the scraper exists and test it — the test runs the exact
   command that will be registered, including --extra-args
2. Add a scraper entry to cities/<city>/pending_feeds.txt

By default the scraper is tested and then registered. --test runs the
same validation and shows what would be registered without writing
anything.

The nightly build's process_pending_feeds step moves the entry into the
feeds table (validated at insert time), and the DB-first runner executes
active scraper rows the same build — the workflow itself carries no
per-scraper lines and is never edited.

Usage:
    python scripts/add_scraper.py sportsbasement santarosa "Sports Basement"
    python scripts/add_scraper.py myscraper davis "My Source" --test
"""

import argparse
import os
import shlex
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


def test_scraper(scraper_path: Path, extra_args: str) -> bool:
    """Run the scraper with the same arguments that will be registered."""
    output_file = Path("/tmp/scraper_test.ics")
    cmd = [sys.executable, str(scraper_path)]
    if extra_args:
        cmd += shlex.split(extra_args)
    cmd += ["--output", str(output_file)]

    print(f"\n🧪 Testing scraper: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
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
    cmd = f"python {scraper_path.relative_to(ROOT)}{extra} --output {output_file}"
    entry = f"\n# {display_name}\n# cmd: {cmd}\n{output_file}\n"

    with open(feeds_path, 'a') as f:
        f.write(entry)

    print(f"✅ Added to pending_feeds.txt: {display_name}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Register a scraper in the DB-first calendar pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/add_scraper.py sportsbasement santarosa "Sports Basement"
  python scripts/add_scraper.py myscraper davis "My Source" --test
  python scripts/add_scraper.py eventbrite petaluma "Blue Zones Project Petaluma" --extra-args '--url "https://www.eventbrite.com/o/78957912343" --name "Blue Zones Project Petaluma"' --output-name bluezones_petaluma
"""
    )
    parser.add_argument('scraper', help='Scraper name (without .py extension)')
    parser.add_argument('city', help='City directory name (e.g., santarosa, davis, bloomington)')
    parser.add_argument('display_name', help='Human-readable source name for display')
    parser.add_argument('--test', action='store_true',
                        help='Validate the scraper (with --extra-args) and show what would be registered, without writing anything')
    parser.add_argument('--dry-run', action='store_true',
                        help='Deprecated alias of --test')
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
    validate_only = args.test or args.dry_run

    # Step 2: Always test — the same command shape as the registration.
    if not test_scraper(scraper_path, args.extra_args):
        if validate_only:
            sys.exit(1)
        if not sys.stdin.isatty():
            print("\n❌ Scraper test failed (non-interactive session — aborting; nothing was written)")
            sys.exit(1)
        print("\n⚠️  Scraper test had issues. Register anyway? [y/N] ", end='')
        response = input().strip().lower()
        if response != 'y':
            sys.exit(1)

    if validate_only:
        print("\n[TEST] Nothing written. Registering would:")
        print(f"  add to pending_feeds.txt: cities/{args.city}/{ics_name}.ics")
        print(f"  registered command: python {scraper_path.relative_to(ROOT)}{extra} --output cities/{args.city}/{ics_name}.ics")
        return

    # Step 3: Add to pending_feeds.txt
    add_to_pending_feeds(args.city, scraper_path, args.extra_args, ics_name, args.display_name)

    print("\n" + "="*60)
    print("✅ Done! Next steps:")
    print("  1. Review the entry: git diff cities/{}/pending_feeds.txt".format(args.city))
    print("  2. Commit and push it (or let your usual flow do so)")
    print("  3. The nightly build registers it in the feeds table and the")
    print("     DB-first runner starts executing it the same build — the")
    print("     workflow is never edited")
    print("="*60)


if __name__ == '__main__':
    main()
