#!/usr/bin/env python3
"""Validate that PRs adding feeds or scrapers have all required pieces.

Rules (DB-first model):
- A scraper pending entry (cities/*/foo.ics + # cmd:) must satisfy the
  feeds table's insert-time trigger contract: scraper_cmd starts with
  "python scrapers/" or "python scripts/", and url is an output path
  (cities/<city>/<name>.ics). The nightly runner executes active DB rows,
  so the workflow carries no per-scraper lines and is not consulted here.
- A new scraper .py added to scrapers/ must be referenced by a
  feeds.txt or pending_feeds.txt entry.
- ICS URL entries in pending_feeds.txt are self-contained, except that a
  personal my-picks capability URL is always rejected.

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

# Mirrors the feeds-table trigger in supabase/ddl/16_feeds.sql
# (validate_scraper_row): a non-removed scraper row's url is an output
# path and its command invokes a repo script. Keep these in sync.
SCRAPER_OUTPUT_RE = re.compile(r"^cities/[a-z0-9-]+/[A-Za-z0-9._-]+\.ics$")
SCRAPER_CMD_RE = re.compile(r"^python (scrapers|scripts)/")

# A personal my-picks URL is a capability URL, never a source to commit
# (GHSA-3pg8-w4j4-6wv8). Same substring the feeds-table CHECK rejects.
CAPABILITY_PATH = "/functions/v1/my-picks"


def get_changed_file_statuses(base_ref: str) -> list[tuple[str, str]]:
    """Get (status, path) pairs for files changed relative to base ref.

    Status is the first letter of git's status code (A=added, M=modified,
    D=deleted, R=renamed, ...).
    """
    result = subprocess.run(
        ["git", "diff", "--name-status", f"{base_ref}...HEAD"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    if result.returncode != 0:
        # Fallback: diff against base_ref directly
        result = subprocess.run(
            ["git", "diff", "--name-status", base_ref],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
    entries = []
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            # Status may carry a score suffix (e.g. R100); keep only the letter.
            # Rename/copy records emit old<TAB>new — use the destination path.
            entries.append((parts[0][0], parts[-1]))
    return entries


def get_changed_files(base_ref: str) -> list[str]:
    """Get files changed relative to base ref."""
    return [path for _, path in get_changed_file_statuses(base_ref)]


def is_relevant(changed_files: list[str]) -> bool:
    """Check if any feed/scraper-related files were touched."""
    for f in changed_files:
        if "pending_feeds.txt" in f:
            return True
        if f.endswith("feeds.txt"):
            return True
        if f.startswith("scrapers/") and f.endswith(".py"):
            return True
    return False


def parse_pending_feeds(path: Path) -> list[dict]:
    """Parse pending_feeds.txt — delegates to process_pending_feeds.parse_pending_feeds
    so the two scripts can't drift."""
    if not path.exists():
        return []
    return _parse_pending_feeds(path)


def script_token(cmd: str | None) -> str | None:
    """The repo-script path a command invokes, or None when it names none.

    The DB trigger only guarantees the "python scrapers/"/"python scripts/"
    prefix, so the token after "python" is whatever the author wrote — not
    necessarily a `.py` file. Callers decide how to treat it.
    """
    match = re.match(r"python\s+(\S+)", cmd or "")
    return match.group(1) if match else None


def get_new_scraper_files(base_ref: str) -> list[str]:
    """Get newly added scraper .py files (not lib/ helpers).

    Only files added in this branch (status A) count as new; modified
    scrapers already have their feeds.txt entry in place.
    """
    scrapers = []
    for status, f in get_changed_file_statuses(base_ref):
        if status != "A":
            continue
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

    # A my-picks token is a credential wherever it appears: a URL line, or the
    # "# Name | fallback URL" metadata that download_feeds.py copies into
    # X-SOURCE-URL. feeds.txt is normally generated, but hand-editing it is how
    # the two Bloomington tokens leaked (GHSA-3pg8-w4j4-6wv8).
    for f in changed_files:
        if not f.endswith("feeds.txt"):
            continue
        path = ROOT / f
        if not path.exists():
            continue
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            if CAPABILITY_PATH in line:
                errors.append(
                    f"{f}:{lineno} contains a personal my-picks feed URL. Its "
                    f"token must not be committed: register the curator in the "
                    f"feeds table with curator_user_id instead."
                )

    # Check all pending_feeds.txt files that were changed
    for f in changed_files:
        if "pending_feeds.txt" not in f:
            continue
        path = ROOT / f
        feeds = parse_pending_feeds(path)
        for feed in feeds:
            if feed["feed_type"] != "scraper":
                continue

            # The entry must satisfy the feeds-table insert-time trigger
            # contract, since that is what the DB-first runner executes.
            cmd = feed["scraper_cmd"]
            if not cmd:
                errors.append(
                    f"Scraper entry '{feed['name']}' in {f} has no '# cmd:' "
                    f"line. A scraper entry needs a command beginning "
                    f"'python scrapers/' or 'python scripts/'. "
                    f"Did you forget to run add_scraper.py?"
                )
            elif not SCRAPER_CMD_RE.match(cmd):
                errors.append(
                    f"Scraper entry '{feed['name']}' in {f} has command "
                    f"'{cmd}' that does not satisfy the DB trigger contract: "
                    f"scraper_cmd must begin with 'python scrapers/' or "
                    f"'python scripts/'. Did you forget to run add_scraper.py?"
                )

            output_path = feed["url"]
            if not SCRAPER_OUTPUT_RE.match(output_path):
                errors.append(
                    f"Scraper entry '{feed['name']}' in {f} has output "
                    f"'{output_path}' that does not satisfy the DB trigger "
                    f"contract: url must be an output path like "
                    f"cities/<city>/<file>.ics."
                )

            # The referenced repo script must be an existing file. The DB
            # trigger only checks the prefix, so validate whatever token the
            # command names, or the nightly runner is the first place the
            # mistake surfaces.
            token = script_token(cmd)
            if cmd and SCRAPER_CMD_RE.match(cmd) and token and not (ROOT / token).is_file():
                errors.append(
                    f"Scraper entry '{feed['name']}' references "
                    f"'{token}', which is not a file in the repo."
                )

    # Check new scraper files have corresponding feeds entries
    new_scrapers = get_new_scraper_files(base_ref)
    if new_scrapers:
        # The script paths named by '# cmd:' entries in both pending_feeds.txt
        # and feeds.txt (pending entries move to feeds.txt once the build
        # processes them). Match the exact path, not a substring of the file
        # content: the pending template's commented "scrapers/example.py" must
        # not register a real scrapers/example.py.
        referenced_scripts: set[str] = set()
        feed_files = list(ROOT.glob("cities/*/pending_feeds.txt")) + list(
            ROOT.glob("cities/*/feeds.txt")
        )
        for feed_file in feed_files:
            for feed in parse_pending_feeds(feed_file):
                token = script_token(feed["scraper_cmd"])
                if token:
                    referenced_scripts.add(token)

        for scraper_file in new_scrapers:
            if scraper_file not in referenced_scripts:
                errors.append(
                    f"New scraper '{scraper_file}' has no entry in any "
                    f"feeds.txt or pending_feeds.txt. "
                    f"Did you forget to run add_scraper.py?"
                )

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate PR feed/scraper consistency")
    parser.add_argument(
        "--base-ref", default="origin/main", help="Base ref to diff against (default: origin/main)"
    )
    args = parser.parse_args()

    errors = validate(args.base_ref)

    if errors:
        print(f"\n{'=' * 60}")
        print(f"FAILED: {len(errors)} issue(s) found\n")
        for i, err in enumerate(errors, 1):
            print(f"  {i}. {err}\n")
        print(
            "A scraper entry needs a pending_feeds.txt command beginning "
            "'python scrapers/' (or 'python scripts/') and an output path "
            "cities/<city>/<name>.ics."
        )
        print('Use: python scripts/add_scraper.py <name> <city> "Display Name"')
        print(f"{'=' * 60}")
        sys.exit(1)
    else:
        print("\nAll feed/scraper checks passed.")


if __name__ == "__main__":
    main()
