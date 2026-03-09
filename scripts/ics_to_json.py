#!/usr/bin/env python3
"""
Convert ICS calendar files to JSON format for Supabase ingestion.
"""

import argparse
import html
import html.parser
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


# Default timezone when city.conf is missing or has no timezone
DEFAULT_TIMEZONE = 'America/Los_Angeles'


def load_city_timezone(city):
    """Load timezone from cities/{city}/city.conf, fall back to default."""
    if not city:
        return ZoneInfo(DEFAULT_TIMEZONE)
    conf = Path(__file__).parent.parent / 'cities' / city / 'city.conf'
    if conf.exists():
        for line in conf.read_text().splitlines():
            if line.startswith('# timezone:'):
                tz_name = line.split(':', 1)[1].strip()
                return ZoneInfo(tz_name)
    return ZoneInfo(DEFAULT_TIMEZONE)


def parse_ics_datetime(dt_str, local_tz=None):
    """Parse an ICS datetime string to ISO format string (in the city's local time)."""
    if not dt_str:
        return None

    if local_tz is None:
        local_tz = ZoneInfo(DEFAULT_TIMEZONE)

    # Handle property parameters like DTSTART;TZID=America/Los_Angeles:20240101T120000
    if ';' in dt_str:
        dt_str = dt_str.split(':')[-1]

    dt_str = dt_str.strip()

    try:
        if dt_str.endswith('Z'):
            # UTC time - convert to city's local time
            dt = datetime.strptime(dt_str, '%Y%m%dT%H%M%SZ')
            dt = dt.replace(tzinfo=timezone.utc).astimezone(local_tz)
            return dt.strftime('%Y-%m-%dT%H:%M:%S')
        elif 'T' in dt_str:
            # Local time (already in correct timezone)
            dt = datetime.strptime(dt_str, '%Y%m%dT%H%M%S')
            return dt.strftime('%Y-%m-%dT%H:%M:%S')
        else:
            # All-day event
            dt = datetime.strptime(dt_str, '%Y%m%d')
            return dt.strftime('%Y-%m-%dT%H:%M:%S')
    except ValueError:
        return None


def unfold_ics_lines(content):
    """Unfold ICS continuation lines (lines starting with space or tab)."""
    # ICS spec: long lines are folded by inserting CRLF + space/tab
    content = re.sub(r'\r?\n[ \t]', '', content)
    return content


class _HTMLStripper(html.parser.HTMLParser):
    """Minimal HTML stripper that collects text nodes."""
    def __init__(self):
        super().__init__()
        self._parts = []

    def handle_data(self, data):
        self._parts.append(data)

    def handle_starttag(self, tag, attrs):
        # Treat block-level / line-break tags as newlines
        if tag in ('br', 'p', 'div', 'li', 'tr'):
            self._parts.append('\n')

    def get_text(self):
        return ''.join(self._parts)


def strip_html(text):
    """Strip HTML tags and unescape entities; collapse whitespace."""
    if not text or '<' not in text:
        return text
    stripper = _HTMLStripper()
    stripper.feed(html.unescape(text))
    result = stripper.get_text()
    # Collapse runs of spaces/tabs, preserve newlines
    result = re.sub(r'[^\S\n]+', ' ', result)
    # Collapse multiple blank lines
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result.strip()


def clean_description(text):
    """Normalize description text to prevent Markdown rendering artifacts.

    Some sources (e.g. WordPress Tribe ICS) embed full page HTML in DESCRIPTION,
    producing deeply-indented lines that render as Markdown code blocks.
    Strip leading/trailing whitespace per line and collapse runs of blank lines.
    """
    lines = text.splitlines()
    cleaned = [line.strip() for line in lines]
    # Collapse consecutive blank lines into one
    result = []
    prev_blank = False
    for line in cleaned:
        is_blank = line == ''
        if is_blank and prev_blank:
            continue
        result.append(line)
        prev_blank = is_blank
    return '\n'.join(result).strip()


def extract_field(event_content, field_name):
    """Extract a field value from VEVENT content."""
    # Match field with optional parameters: FIELD;PARAM=VALUE:content or FIELD:content
    # Use word boundary or end-of-field-name to avoid X-SOURCE matching X-SOURCE-ID
    pattern = rf'^{field_name}(?:;[^:]*)?:([^\r\n]*)'
    match = re.search(pattern, event_content, re.IGNORECASE | re.MULTILINE)
    if match:
        value = match.group(1)
        # Unescape ICS escapes
        value = value.replace('\\n', '\n').replace('\\,', ',').replace('\\;', ';').replace('\\\\', '\\')
        return value.strip()
    return None


def extract_image_url(event_content):
    """Extract first image URL from ATTACH or vendor image fields."""
    # Match ATTACH with image FMTTYPE
    pattern = r'^ATTACH;[^:]*FMTTYPE=image/[^:]*:(.+)'
    match = re.search(pattern, event_content, re.IGNORECASE | re.MULTILINE)
    if match:
        return match.group(1).strip()
    # Match Tockify featured image
    pattern = r'^X-TKF-FEATURED-IMAGE:(.+)'
    match = re.search(pattern, event_content, re.IGNORECASE | re.MULTILINE)
    if match:
        return match.group(1).strip()
    # Match LiveWhale image (IU events) - unescape \, and request a larger size
    pattern = r'^X-LIVEWHALE-IMAGE:(.+)'
    match = re.search(pattern, event_content, re.IGNORECASE | re.MULTILINE)
    if match:
        url = match.group(1).strip().replace('\\,', ',')
        # Replace thumbnail dimensions with a larger display size
        url = re.sub(r'/width/\d+/height/\d+/', '/width/400/height/300/', url)
        return url
    # Match RFC 7986 IMAGE field (e.g. Skedda/Aqus events)
    # Prefer FULLSIZE, accept any display type
    for display in ('fullsize', 'badge', 'thumbnail', ''):
        pat = rf'^IMAGE;[^:]*DISPLAY={display}[^:]*:(https?://.+)' if display else r'^IMAGE;[^:]*:(https?://.+)'
        match = re.search(pat, event_content, re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip()
    # Match WordPress X-WP-IMAGES-URL (format: size\;url\;w\;h\,...,size\;url\;...)
    pattern = r'^X-WP-IMAGES-URL:(.+)'
    match = re.search(pattern, event_content, re.IGNORECASE | re.MULTILINE)
    if match:
        raw = match.group(1).strip()
        # Parse comma-separated entries: size\;url\;w\;h
        for size in ('large', 'full', 'medium'):
            m = re.search(rf'(?:^|,){size}\\;(https?://[^\\,]+)', raw, re.IGNORECASE)
            if m:
                return m.group(1)
    # Match Bedework image (Duke) - relative URL, base is calendar.duke.edu
    pattern = r'^X-BEDEWORK-IMAGE:(/public/Images/.+)'
    match = re.search(pattern, event_content, re.IGNORECASE | re.MULTILINE)
    if match:
        return 'https://calendar.duke.edu' + match.group(1).strip()
    return None


def token_set_similarity(a, b):
    """Compare word sets, ignore order. Returns 0-1.
    'Family Storytime' vs 'Bilingual Family Storytime' scores high because
    the shared words dominate. Uses overlap/min-size ratio."""
    from difflib import SequenceMatcher as SM
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a and not words_b:
        return 1.0
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    sorted_inter = ' '.join(sorted(intersection))
    remaining_a = ' '.join(sorted(words_a - intersection))
    remaining_b = ' '.join(sorted(words_b - intersection))
    combined_a = (sorted_inter + ' ' + remaining_a).strip()
    combined_b = (sorted_inter + ' ' + remaining_b).strip()
    ratios = [
        SM(None, sorted_inter, combined_a).ratio() if combined_a else 1.0,
        SM(None, sorted_inter, combined_b).ratio() if combined_b else 1.0,
        SM(None, combined_a, combined_b).ratio(),
    ]
    return max(ratios)


def cluster_by_title_similarity(events, threshold=0.85):
    """Cluster events within same timeslot by title similarity.
    Uses union-find to group similar titles, sorts clusters alphabetically.

    Tuning
    ------
    Threshold controls how similar titles must be to cluster together.
    Genuine duplicates (same event from different sources) score 0.98-1.0:
      "One-On-One Tech Help" vs "Tech Help"                          → 1.000
      "Vineyard Garden Wine Tasting" vs "Picnic Lunch and ..."       → 1.000
      "Bilingual Family Storytime" vs "Family Storytime"             → 1.000

    False matches (different events sharing common words) score 0.56-0.78:
      "Community Coffee Tasting" vs "Community Yoga"                 → 0.783
      "BiblioBus at ... Farmers Market" vs "VALLEJO FARMERS MARKET"  → 0.778
      "Mushroom Hike" vs "Mushroom Identification"                   → 0.762
      "Karaoke Sundays" vs "Sabroso Sundays"                        → 0.733
      "Honky Tonk Open Mic" vs "Open Mic Night"                     → 0.727

    Threshold of 0.85 cleanly separates the two groups.
    """
    from collections import defaultdict

    # Group by timeslot
    slots = defaultdict(list)
    slot_order = []
    for e in events:
        key = e.get('start_time', '') or ''
        if key not in slots:
            slot_order.append(key)
        slots[key].append(e)

    result = []
    for key in slot_order:
        group = slots[key]
        if len(group) <= 1:
            result.extend(group)
            continue

        # Union-find
        parent = list(range(len(group)))
        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        def union(a, b):
            parent[find(a)] = find(b)

        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                ta = group[i].get('title', '')
                tb = group[j].get('title', '')
                if not ta or not tb or token_set_similarity(ta, tb) < threshold:
                    continue
                # Don't cluster events at different locations
                la = group[i].get('location', '') or ''
                lb = group[j].get('location', '') or ''
                if la and lb and la != lb:
                    continue
                union(i, j)

        clusters = defaultdict(list)
        for i in range(len(group)):
            clusters[find(i)].append(group[i])

        for c in clusters.values():
            c.sort(key=lambda e: (e.get('title', '') or '').lower())

        sorted_clusters = sorted(clusters.values(),
            key=lambda c: (c[0].get('title', '') or '').lower())

        cluster_idx = 0
        for cluster in sorted_clusters:
            if len(cluster) > 1:
                for e in cluster:
                    e['cluster_id'] = cluster_idx
                cluster_idx += 1
            result.extend(cluster)

    return result


def ics_to_json(ics_file, output_file=None, future_only=True, city=None):
    """Convert an ICS file to JSON format for Supabase."""
    local_tz = load_city_timezone(city)
    content = Path(ics_file).read_text(encoding='utf-8', errors='ignore')

    # Unfold continuation lines
    content = unfold_ics_lines(content)

    events = []
    # Use 24 hours ago to avoid filtering out same-day events due to timezone differences
    from datetime import timedelta
    now = datetime.now(timezone.utc) - timedelta(hours=24)

    # Extract all VEVENT blocks
    pattern = r'BEGIN:VEVENT\r?\n(.*?)\r?\nEND:VEVENT'
    matches = re.findall(pattern, content, re.DOTALL)

    for event_content in matches:
        # Extract fields
        title = extract_field(event_content, 'SUMMARY')
        start_time = parse_ics_datetime(extract_field(event_content, 'DTSTART'), local_tz)
        end_time = parse_ics_datetime(extract_field(event_content, 'DTEND'), local_tz)
        location = extract_field(event_content, 'LOCATION')
        if location:
            location = strip_html(location)
        description = extract_field(event_content, 'DESCRIPTION')
        if description:
            description = strip_html(description)
            description = clean_description(description)
        url = extract_field(event_content, 'URL')
        source = extract_field(event_content, 'X-SOURCE')
        source_id = extract_field(event_content, 'X-SOURCE-ID')
        source_urls_raw = extract_field(event_content, 'X-SOURCE-URLS')
        uid = extract_field(event_content, 'UID')

        # Extract image URL from ATTACH or X-TKF-FEATURED-IMAGE
        image_url = extract_image_url(event_content)

        # Extract ICS CATEGORIES (raw tags for LLM classification)
        ics_cats_raw = extract_field(event_content, 'CATEGORIES')
        ics_categories = [c.strip() for c in ics_cats_raw.split(',')] if ics_cats_raw else []

        # Skip if no title or start time
        if not title or not start_time:
            continue

        # Filter to future events if requested
        if future_only and start_time:
            try:
                event_dt = datetime.fromisoformat(start_time)
                if event_dt.tzinfo is None:
                    event_dt = event_dt.replace(tzinfo=timezone.utc)
                if event_dt < now:
                    continue
            except ValueError:
                pass


        source_urls = {}
        if source_urls_raw:
            try:
                source_urls = json.loads(source_urls_raw)
            except json.JSONDecodeError:
                pass

        event = {
            'title': title,
            'start_time': start_time,
            'end_time': end_time,
            'location': location or '',
            'description': description or '',
            'url': url or '',
            'city': city or '',
            'source': source or '',
            'source_id': source_id or '',
            'source_uid': uid or '',
            'source_urls': source_urls if source_urls else None,
            'cluster_id': None,
            'ics_categories': ics_categories if ics_categories else None,
            'image_url': image_url
        }
        events.append(event)

    # Sort by start time, then cluster similar titles within each timeslot
    events.sort(key=lambda x: x['start_time'] or '')
    events = cluster_by_title_similarity(events)

    # Output
    json_output = json.dumps(events, indent=2, ensure_ascii=False)

    if output_file:
        Path(output_file).write_text(json_output, encoding='utf-8')
        print(f"Converted {len(events)} events to {output_file}")
    else:
        print(json_output)

    return events


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert ICS to JSON for Supabase')
    parser.add_argument('input', help='Input ICS file')
    parser.add_argument('-o', '--output', help='Output JSON file (stdout if not specified)')
    parser.add_argument('--city', help='City name (e.g., santarosa, sebastopol)')
    parser.add_argument('--all', action='store_true', help='Include past events (default: future only)')

    args = parser.parse_args()

    ics_to_json(args.input, args.output, future_only=not args.all, city=args.city)
