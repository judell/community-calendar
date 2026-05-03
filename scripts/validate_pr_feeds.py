#!/usr/bin/env python3
"""Validate that PRs adding feeds or scrapers have all required pieces.

Checks consistency between pending_feeds.txt, the workflow, and scraper files.

Rules:
- If pending_feeds.txt has a scraper entry (cities/*/foo.ics + # cmd:),
  the workflow must have a matching --output line.
- If a new scraper .py was added to scrapers/, pending_feeds.txt should
  reference it and the workflow should run it.
- ICS URL entries in pending_feeds.txt are self-contained (no other checks).

Runs on PRs. Exits 0 if no feed/scraper files were touched or all checks pass.

Usage:
    python scripts/validate_pr_feeds.py [--base-ref origin/main]
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from process_pending_feeds import parse_pending_feeds as _parse_pending_feeds

ROOT = Path(__file__).parent.parent
WORKFLOW_PATH = ROOT / ".github/workflows/generate-calendar.yml"


def get_changed_files(base_ref: str) -> list[str]:
    """Get files changed relative to base ref."""
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
        capture_output=True, text=True, cwd=ROOT,
    )
    if result.returncode != 0:
        # Fallback: diff against base_ref directly
        result = subprocess.run(
            ["git", "diff", "--name-only", base_ref],
            capture_output=True, text=True, cwd=ROOT,
        )
    return result.stdout.strip().splitlines()


def is_relevant(changed_files: list[str]) -> bool:
    """Check if any feed/scraper-related files were touched."""
    for f in changed_files:
        if "pending_feeds.txt" in f:
            return True
        if f.startswith("scrapers/") and f.endswith(".py"):
            return True
        if f == ".github/workflows/generate-calendar.yml":
            return True
    return False


def parse_pending_feeds(path: Path) -> list[dict]:
    """Parse pending_feeds.txt — delegates to process_pending_feeds.parse_pending_feeds
    so the two scripts can't drift."""
    if not path.exists():
        return []
    return _parse_pending_feeds(str(path))


def get_workflow_scraper_outputs(workflow_text: str) -> set[str]:
    """Extract all --output paths from scraper lines in the workflow."""
    return set(re.findall(r'--output\s+(cities/\S+\.ics)', workflow_text))


def get_new_scraper_files(changed_files: list[str]) -> list[str]:
    """Get newly added scraper .py files (not lib/ helpers)."""
    scrapers = []
    for f in changed_files:
        if f.startswith("scrapers/") and f.endswith(".py"):
            # Skip lib/ and __init__.py
            if "/lib/" in f or f.endswith("__init__.py"):
                continue
            if (ROOT / f).exists():
                scrapers.append(f)
    return scrapers


def validate(base_ref: str) -> list[str]:
    """Run all checks. Returns list of error messages."""
    changed_files = get_changed_files(base_ref)

    if not is_relevant(changed_files):
        print("No feed/scraper files changed — nothing to validate.")
        return []

    print(f"Changed files: {len(changed_files)}")
    for f in changed_files:
        if is_relevant([f]):
            print(f"  {f}")

    errors = []
    workflow_text = WORKFLOW_PATH.read_text()
    workflow_outputs = get_workflow_scraper_outputs(workflow_text)

    # Check all pending_feeds.txt files that were changed
    for f in changed_files:
        if "pending_feeds.txt" not in f:
            continue
        path = ROOT / f
        feeds = parse_pending_feeds(path)
        for feed in feeds:
            if feed["feed_type"] == "scraper":
                # Scraper entry: workflow must have a matching --output line
                output_path = feed["url"]
                if output_path not in workflow_outputs:
                    errors.append(
                        f"Scraper entry '{feed['name']}' in {f} has output "
                        f"'{output_path}' but no matching --output line in "
                        f"the workflow. Did you forget to run add_scraper.py?"
                    )
                # The scraper .py file should exist
                if feed["scraper_cmd"]:
                    # Extract the .py file from the cmd
                    cmd_match = re.search(r'python\s+(\S+\.py)', feed["scraper_cmd"])
                    if cmd_match:
                        scraper_file = ROOT / cmd_match.group(1)
                        if not scraper_file.exists():
                            errors.append(
                                f"Scraper entry '{feed['name']}' references "
                                f"'{cmd_match.group(1)}' but that file doesn't exist."
                            )

    # Check new scraper files have corresponding feeds entries
    new_scrapers = get_new_scraper_files(changed_files)
    if new_scrapers:
        # Collect content from both pending_feeds.txt and feeds.txt
        # (pending entries move to feeds.txt once the build processes them)
        all_feed_content = ""
        for pending in ROOT.glob("cities/*/pending_feeds.txt"):
            all_feed_content += pending.read_text()
        for feeds in ROOT.glob("cities/*/feeds.txt"):
            all_feed_content += feeds.read_text()

        for scraper_file in new_scrapers:
            scraper_basename = Path(scraper_file).stem
            # Check if referenced in workflow
            if scraper_basename not in workflow_text:
                errors.append(
                    f"New scraper '{scraper_file}' is not referenced in the "
                    f"workflow. Did you forget to run add_scraper.py?"
                )
            # Check if referenced in any pending_feeds.txt or feeds.txt
            if scraper_basename not in all_feed_content:
                errors.append(
                    f"New scraper '{scraper_file}' has no entry in any "
                    f"feeds.txt or pending_feeds.txt. "
                    f"Did you forget to run add_scraper.py?"
                )

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate PR feed/scraper consistency")
    parser.add_argument("--base-ref", default="origin/main",
                        help="Base ref to diff against (default: origin/main)")
    args = parser.parse_args()

    errors = validate(args.base_ref)

    if errors:
        print(f"\n{'='*60}")
        print(f"FAILED: {len(errors)} issue(s) found\n")
        for i, err in enumerate(errors, 1):
            print(f"  {i}. {err}\n")
        print("Scrapers need both a workflow entry AND a feeds.txt/pending_feeds.txt entry.")
        print("Use: python scripts/add_scraper.py <name> <city> \"Display Name\"")
        print(f"{'='*60}")
        sys.exit(1)
    else:
        print("\nAll feed/scraper checks passed.")


if __name__ == "__main__":
    main()
