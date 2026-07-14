#!/usr/bin/env python3
"""Add a new ICS feed to the pipeline.

This script automates the steps for integrating an ICS feed:
1. Test the feed URL to verify it returns valid ICS with events
2. Add the URL to cities/<city>/pending_feeds.txt

In the main repo, the workflow processes pending_feeds.txt into the feeds
table, then regenerates feeds.txt from the database.

Usage:
    python scripts/add_feed.py "https://example.com/events/?ical=1" toronto "Example Events"
    python scripts/add_feed.py "https://meetup.com/group/events/ical/" toronto "Meetup Group" --test
    python scripts/add_feed.py URL city "Source Name" --dry-run
"""

import argparse
import subprocess
import sys
from pathlib import Path

from feed_slug import slugify

# Repository root
ROOT = Path(__file__).parent.parent


def test_feed(url: str) -> tuple[bool, int]:
    """Test that a feed URL returns valid ICS with events."""
    print(f"\n🧪 Testing feed: {url}")
    
    try:
        result = subprocess.run(
            ['curl', '-sL', '-A', 'Mozilla/5.0', '--max-time', '30', url],
            capture_output=True,
            text=True,
            timeout=35
        )
        
        content = result.stdout
        
        if not content:
            print("❌ No response from URL")
            return False, 0
        
        if 'BEGIN:VCALENDAR' not in content:
            print("❌ Response is not valid ICS (no BEGIN:VCALENDAR)")
            if len(content) < 500:
                print(f"   Response: {content[:500]}")
            return False, 0
        
        event_count = content.count('BEGIN:VEVENT')
        
        if event_count == 0:
            print("⚠️  Valid ICS but 0 events (may be normal if no upcoming events)")
        else:
            print(f"✅ Valid ICS with {event_count} events")
        
        return True, event_count
        
    except subprocess.TimeoutExpired:
        print("❌ Request timed out after 30 seconds")
        return False, 0
    except Exception as e:
        print(f"❌ Error testing feed: {e}")
        return False, 0


def needs_user_agent(url: str) -> bool:
    """Check if URL likely needs a User-Agent header."""
    # Meetup and some WordPress sites need User-Agent
    return any(x in url for x in ['meetup.com', 'site3.ca', 'ontarionature.org'])


def add_to_pending_feeds(url: str, city: str, display_name: str) -> bool:
    """Add the feed URL to cities/{city}/pending_feeds.txt."""
    feeds_path = ROOT / f"cities/{city}/pending_feeds.txt"
    
    print(f"\n📝 Adding to {feeds_path.relative_to(ROOT)}")
    
    if not feeds_path.exists():
        print(f"❌ pending_feeds.txt not found: {feeds_path}")
        return False
    
    content = feeds_path.read_text()
    
    # Check if URL already present
    if url in content:
        print(f"✅ Already in pending_feeds.txt")
        return True
    
    # Append the new feed with structured comment
    entry = f"\n# {display_name}\n{url}\n"
    
    with open(feeds_path, 'a') as f:
        f.write(entry)
    
    print(f"✅ Added to pending_feeds.txt: {display_name}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Add an ICS feed to the calendar pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/add_feed.py "https://example.com/events/?ical=1" toronto "Example Events"
  python scripts/add_feed.py "https://meetup.com/mygroup/events/ical/" toronto "My Group" --test
  python scripts/add_feed.py URL city "Source Name" --dry-run
"""
    )
    parser.add_argument('url', help='ICS feed URL')
    parser.add_argument('city', help='City directory name (e.g., toronto, santarosa)')
    parser.add_argument('display_name', help='Human-readable source name')
    parser.add_argument('--test', action='store_true', help='Test the feed before adding')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--slug', help='Override the auto-generated filename slug')
    
    args = parser.parse_args()
    
    # Generate slug
    slug = args.slug or slugify(args.url)
    
    print(f"🔧 Adding feed to {args.city} pipeline")
    print(f"   URL: {args.url}")
    print(f"   Name: {args.display_name}")
    print(f"   Slug: {slug}")
    
    # Test the feed
    if args.test or args.dry_run:
        valid, event_count = test_feed(args.url)
        if not valid and not args.dry_run:
            print("\n⚠️  Feed test failed. Continue anyway? [y/N] ", end='')
            response = input().strip().lower()
            if response != 'y':
                sys.exit(1)
    
    if args.dry_run:
        print("\n[DRY RUN] Would perform the following:")
        print(f"  1. Add to cities/{args.city}/pending_feeds.txt: {args.url}")
        print("  2. Next build will move it into the feeds table")
        print(f"  3. download_feeds.py will save as: {slug}.ics")
        return

    # Add to pending_feeds.txt
    if not add_to_pending_feeds(args.url, args.city, args.display_name):
        print("\n⚠️  Failed to add to pending_feeds.txt automatically")
        print(f"   Manually add to cities/{args.city}/pending_feeds.txt:")
        print(f"   # {args.display_name}")
        print(f"   {args.url}")

    print("\n" + "="*60)
    print("✅ Done! Next steps:")
    print("  1. Review changes: git diff")
    print(f"  2. Update SOURCES_CHECKLIST.md if needed")
    print(f"  3. Commit: git add -A && git commit -m 'Add {args.display_name} feed'")
    print("  4. Push: git push")
    print(f"\n  The build will insert it into the feeds table and save as: {slug}.ics")
    print("="*60)


if __name__ == '__main__':
    main()
