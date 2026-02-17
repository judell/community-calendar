#!/usr/bin/env python3
"""Add a new scraper to the pipeline.

This script automates the three required steps for integrating a scraper:
1. Verify the scraper exists and test it
2. Add it to the GitHub Actions workflow
3. Add the source name to combine_ics.py

Usage:
    python scripts/add_scraper.py sportsbasement santarosa "Sports Basement"
    python scripts/add_scraper.py myscraper davis "My Source" --test
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

# Repository root
ROOT = Path(__file__).parent.parent
WORKFLOW_PATH = ROOT / ".github/workflows/generate-calendar.yml"
COMBINE_ICS_PATH = ROOT / "scripts/combine_ics.py"
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
            [sys.executable, str(scraper_path), "--output", str(output_file), "--months", "2"],
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


def add_to_workflow(scraper_name: str, city: str, scraper_path: Path) -> bool:
    """Add the scraper to the GitHub Actions workflow."""
    print(f"\n📝 Adding to workflow for city: {city}")
    
    workflow_content = WORKFLOW_PATH.read_text()
    
    # Determine the scraper command path relative to repo root
    rel_path = scraper_path.relative_to(ROOT)
    output_path = f"cities/{city}/{scraper_name}.ics"
    scraper_line = f"        python {rel_path} --output {output_path} || true"
    
    # Check if already in workflow
    if scraper_name in workflow_content and city in workflow_content:
        # More specific check
        if f"{city}/{scraper_name}.ics" in workflow_content:
            print(f"✅ Already in workflow: {output_path}")
            return True
    
    # Find the scrape step for this city
    # Pattern: "Scrape {City} sources" followed by "run: |" and commands
    city_title = city.title()  # santarosa -> Santarosa
    
    # Try different capitalization patterns
    # Build a regex to find "Scrape ... sources" where the city name appears
    # This handles cases like "Raleigh-Durham" for city "raleighdurham"
    patterns = [
        f"Scrape {city_title} sources",
        f"Scrape {city} sources",
        f"Scrape Santa Rosa sources" if city == "santarosa" else None,
        f"Scrape Raleigh-Durham sources" if city == "raleighdurham" else None,
    ]

    # Also try a fuzzy match: find any "Scrape ... sources" line containing the city name
    import re as _re
    scrape_lines = _re.findall(r'Scrape [^\n]+ sources', workflow_content)
    for line in scrape_lines:
        if city.lower().replace('-', '') in line.lower().replace('-', '').replace(' ', ''):
            patterns.append(line)
    
    scrape_section_start = -1
    for pattern in patterns:
        if pattern and pattern in workflow_content:
            scrape_section_start = workflow_content.find(pattern)
            break
    
    if scrape_section_start == -1:
        print(f"❌ Could not find 'Scrape {city} sources' section in workflow")
        print("   You'll need to add the scraper manually to:")
        print(f"   {WORKFLOW_PATH}")
        return False
    
    # Find the "continue-on-error: true" that ends this section
    section_end_marker = "continue-on-error: true"
    section_end = workflow_content.find(section_end_marker, scrape_section_start)
    
    if section_end == -1:
        print("❌ Could not find end of scrape section")
        return False
    
    # Insert before continue-on-error
    # Find the line before continue-on-error (last scraper command)
    before_continue = workflow_content[:section_end].rstrip()
    after_continue = workflow_content[section_end:]
    
    # Check if already there
    if scraper_line.strip() in before_continue:
        print(f"✅ Already in workflow")
        return True
    
    new_content = before_continue + "\n" + scraper_line + "\n      " + after_continue
    
    WORKFLOW_PATH.write_text(new_content)
    print(f"✅ Added to workflow: {scraper_line.strip()}")
    return True


def add_to_combine_ics(scraper_name: str, display_name: str) -> bool:
    """Add the source name to combine_ics.py."""
    print(f"\n📝 Adding source name to combine_ics.py")
    
    content = COMBINE_ICS_PATH.read_text()
    
    # Check if already present
    if f"'{scraper_name}':" in content:
        print(f"✅ Already in SOURCE_NAMES: '{scraper_name}'")
        return True
    
    # Find the SOURCE_NAMES dict and add entry
    # Look for the last entry before the closing brace
    # Pattern: find a line with 'something': 'Something', and add after it
    
    lines = content.split('\n')
    new_lines = []
    added = False
    in_source_names = False
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        
        if 'SOURCE_NAMES = {' in line:
            in_source_names = True
            continue
        
        if in_source_names and not added:
            # Look for a line that looks like an entry and the next line closes or continues
            if re.match(r"\s+'[^']+': '[^']+',$", line):
                # Check if next line closes the dict or is another entry
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if '}' in next_line or re.match(r"\s+'[^']+': '[^']+',$", next_line):
                        # This is a good place to add, but let's find the last entry
                        pass
            
            # If we see the closing brace, add before it
            if line.strip() == '}' or ('}' in line and '=' not in line and ':' not in line):
                # Insert before this line
                new_lines.pop()  # Remove the } line we just added
                indent = '    '  # Standard indent
                new_lines.append(f"{indent}'{scraper_name}': '{display_name}',")
                new_lines.append(line)  # Add the } back
                added = True
                in_source_names = False
    
    if not added:
        # Fallback: try to find and add after a specific known entry
        content = COMBINE_ICS_PATH.read_text()
        # Add after barrel_proof or last entry
        if "'barrel_proof':" in content:
            content = content.replace(
                "'barrel_proof': 'Barrel Proof Lounge',",
                f"'barrel_proof': 'Barrel Proof Lounge',\n    '{scraper_name}': '{display_name}',"
            )
            COMBINE_ICS_PATH.write_text(content)
            added = True
        else:
            print("❌ Could not find where to add SOURCE_NAMES entry")
            print(f"   Please manually add to {COMBINE_ICS_PATH}:")
            print(f"   '{scraper_name}': '{display_name}',")
            return False
    else:
        COMBINE_ICS_PATH.write_text('\n'.join(new_lines))
    
    print(f"✅ Added to SOURCE_NAMES: '{scraper_name}': '{display_name}'")
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
"""
    )
    parser.add_argument('scraper', help='Scraper name (without .py extension)')
    parser.add_argument('city', help='City directory name (e.g., santarosa, davis, bloomington)')
    parser.add_argument('display_name', help='Human-readable source name for display')
    parser.add_argument('--test', action='store_true', help='Test the scraper before adding')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--skip-workflow', action='store_true', help='Skip adding to workflow')
    parser.add_argument('--skip-combine', action='store_true', help='Skip adding to combine_ics.py')
    
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
    
    if args.dry_run:
        print("\n[DRY RUN] Would perform the following:")
        print(f"  1. Add to workflow: python {scraper_path.relative_to(ROOT)} --output cities/{args.city}/{args.scraper}.ics")
        print(f"  2. Add to SOURCE_NAMES: '{args.scraper}': '{args.display_name}'")
        return
    
    # Step 2: Test if requested
    if args.test:
        if not test_scraper(scraper_path):
            print("\n⚠️  Scraper test had issues. Continue anyway? [y/N] ", end='')
            response = input().strip().lower()
            if response != 'y':
                sys.exit(1)
    
    # Step 3: Add to workflow
    if not args.skip_workflow:
        if not add_to_workflow(args.scraper, args.city, scraper_path):
            print("\n⚠️  Failed to add to workflow automatically")
    
    # Step 4: Add to combine_ics.py
    if not args.skip_combine:
        if not add_to_combine_ics(args.scraper, args.display_name):
            print("\n⚠️  Failed to add to combine_ics.py automatically")
    
    print("\n" + "="*60)
    print("✅ Done! Next steps:")
    print("  1. Review changes: git diff")
    print("  2. Commit: git add -A && git commit -m 'Add {scraper} scraper'")
    print("  3. Push: git push")
    print("  4. Trigger workflow or wait for daily run")
    print("="*60)


if __name__ == '__main__':
    main()
