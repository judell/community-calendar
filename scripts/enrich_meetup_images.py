#!/usr/bin/env python3
"""
Enrich ICS files with event images scraped from event pages via og:image.

By default, processes meetup_*.ics files in a directory and only follows
meetup.com URLs.  Use --any-url to process any ICS file and fetch og:image
from whatever URL is in each event.

Usage:
    python scripts/enrich_meetup_images.py --dir cities/roanoke
    python scripts/enrich_meetup_images.py cities/roanoke/meetup_make_roanoke.ics
    python scripts/enrich_meetup_images.py --any-url cities/bloomington/buskirk_chumley.ics
"""

import argparse
import logging
import re
import time
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
REQUEST_TIMEOUT = 15
DELAY = 0.5  # seconds between requests


def fetch_og_image(url: str) -> str:
    """Fetch a Meetup event page and return the og:image URL, or ''."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        # Try both attribute orderings for the og:image meta tag
        match = re.search(
            r'<meta\s+property=["\']og:image["\']\s+content=["\'](https?://[^"\']+)["\']',
            resp.text
        )
        if not match:
            match = re.search(
                r'<meta\s+content=["\'](https?://[^"\']+)["\']\s+property=["\']og:image["\']',
                resp.text
            )
        return match.group(1) if match else ''
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return ''


def unfold(content: str) -> str:
    """Unfold ICS continuation lines (RFC 5545 line folding)."""
    return re.sub(r'\r?\n[ \t]', '', content)


def enrich_ics_file(path: Path, any_url: bool = False) -> int:
    """Enrich an ICS file with image URLs. Returns number of images added.

    If any_url is False (default), only follows meetup.com event URLs.
    If any_url is True, fetches og:image from any URL found in each event.
    """
    raw = path.read_text(encoding='utf-8', errors='ignore')
    content = unfold(raw).replace('\r\n', '\n').replace('\r', '\n')

    vevent_pattern = re.compile(r'(BEGIN:VEVENT\n.*?)(END:VEVENT)', re.DOTALL)
    added = 0

    def enrich_vevent(m):
        nonlocal added
        block = m.group(1)

        # Skip if already has an image attachment
        if re.search(r'^ATTACH;[^:]*FMTTYPE=image/', block, re.MULTILINE | re.IGNORECASE):
            return m.group(0)

        # Extract the event URL
        url_match = re.search(r'^URL(?:;[^:]*)?:(.+)', block, re.MULTILINE)
        if not url_match:
            return m.group(0)
        url = url_match.group(1).strip()
        if not any_url and 'meetup.com' not in url:
            return m.group(0)

        logger.info(f"  Fetching image for: {url}")
        image_url = fetch_og_image(url)
        time.sleep(DELAY)

        if not image_url:
            logger.info(f"    No image found")
            return m.group(0)

        logger.info(f"    -> {image_url}")
        added += 1
        return block + f'ATTACH;FMTTYPE=image/jpeg:{image_url}\n' + m.group(2)

    new_content = vevent_pattern.sub(enrich_vevent, content)

    if added > 0:
        path.write_text(new_content, encoding='utf-8')
        logger.info(f"{path.name}: added {added} image(s)")
    else:
        logger.info(f"{path.name}: no new images")

    return added


def main():
    parser = argparse.ArgumentParser(description='Enrich ICS files with event images via og:image')
    parser.add_argument('--dir', help='Directory to scan for meetup_*.ics files')
    parser.add_argument('--any-url', action='store_true',
                        help='Fetch og:image from any URL, not just meetup.com')
    parser.add_argument('files', nargs='*', help='Specific ICS file(s) to process')
    args = parser.parse_args()

    paths = []
    if args.dir:
        paths.extend(sorted(Path(args.dir).glob('meetup_*.ics')))
    for f in args.files:
        paths.append(Path(f))

    if not paths:
        parser.error('Specify --dir or one or more ICS file paths')

    total = 0
    for path in paths:
        if not path.exists():
            logger.warning(f"File not found: {path}")
            continue
        logger.info(f"Processing {path.name}...")
        total += enrich_ics_file(path, any_url=args.any_url)

    logger.info(f"Done. Total images added: {total}")


if __name__ == '__main__':
    main()
