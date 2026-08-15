#!/usr/bin/env python3
"""
Generate feed health report after aggregation runs.

Scans .ics files in each city directory (produced by the workflow from
both URL downloads and scrapers) and counts future events in each.

Updates report.json with:
- Per-city, per-feed event counts
- Historical data (unlimited)
- Anomaly detection
"""

import argparse
import glob
import json
import os
import re
from datetime import datetime, date, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

DEFAULT_TIMEZONE = 'America/Los_Angeles'


def get_city_timezone(city):
    """Load timezone string from cities/{city}/city.conf, fall back to default."""
    conf = Path(__file__).parent.parent / 'cities' / city / 'city.conf'
    if conf.exists():
        for line in conf.read_text().splitlines():
            if line.startswith('# timezone:'):
                return line.split(':', 1)[1].strip()
    return DEFAULT_TIMEZONE


# Anomaly thresholds
DROP_THRESHOLD = 0.5  # 50% drop from previous
MIN_EVENTS_FOR_DROP = 5  # Only flag drops if previous had at least this many

# History bounds (bound-archive-branch-growth): anomaly detection needs
# one prior data point and the per-city report sparklines use 30, so 90
# daily entries per feed and 180 days of anomaly log are generous.
MAX_FEED_HISTORY = 90
MAX_ANOMALY_DAYS = 180


def count_future_events_in_ics(filepath: str) -> tuple[int, str | None]:
    """Count VEVENT entries with future DTSTART in an ICS file."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except FileNotFoundError:
        return 0, 'file_not_found'
    except Exception as e:
        return 0, str(e)[:100]

    count = 0
    for match in re.finditer(r'BEGIN:VEVENT\r?\n(.*?)\r?\nEND:VEVENT', content, re.DOTALL):
        event = match.group(1)
        dt_match = re.search(r'DTSTART[^:]*:(\d{8}(?:T\d{6}Z?)?)', event)
        if not dt_match:
            continue
        dt_str = dt_match.group(1)
        try:
            if dt_str.endswith('Z'):
                dt = datetime.strptime(dt_str, '%Y%m%dT%H%M%SZ').replace(tzinfo=timezone.utc)
            elif 'T' in dt_str:
                dt = datetime.strptime(dt_str, '%Y%m%dT%H%M%S').replace(tzinfo=timezone.utc)
            else:
                dt = datetime.strptime(dt_str, '%Y%m%d').replace(tzinfo=timezone.utc)
            if dt >= cutoff:
                count += 1
        except ValueError:
            count += 1  # count if unparseable, to be safe
    return count, None


def detect_anomalies(feed_name: str, current: int, history: list[dict]) -> list[dict]:
    """Detect anomalies for a feed. Returns list of anomaly dicts."""
    anomalies = []

    if not history:
        return anomalies

    prev = None
    for h in reversed(history):
        if h.get('error') is None:
            prev = h
            break

    if prev is None:
        return anomalies

    prev_count = prev['count']

    if current == 0 and prev_count > 0:
        anomalies.append({
            'type': 'zero_events',
            'message': f'Feed returned 0 events (was {prev_count})',
            'severity': 'info'
        })
    elif prev_count >= MIN_EVENTS_FOR_DROP and current < prev_count:
        drop_pct = (prev_count - current) / prev_count
        if drop_pct >= DROP_THRESHOLD:
            anomalies.append({
                'type': 'significant_drop',
                'message': f'Events dropped {drop_pct:.0%} ({prev_count} → {current})',
                'severity': 'medium'
            })

    return anomalies


def classify_ics_content(filepath: str) -> str:
    """Classify what a feed file actually contains, so a zero count
    carries a cause: 'not_ics:html' / 'not_ics:json' / 'not_ics:empty'
    (broken/blocked), 'quiet' (valid calendar, no future events), or
    'ok' (has future events — callers only ask for zero-count feeds)."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except OSError:
        return 'unreadable'
    if 'BEGIN:VCALENDAR' not in content:
        head = content[:512].lstrip().lower()
        if not head:
            return 'not_ics:empty'
        if head.startswith('<!doctype') or head.startswith('<html') or '<html' in head:
            return 'not_ics:html'
        if head.startswith('{') or head.startswith('['):
            return 'not_ics:json'
        return 'not_ics:unknown'
    return 'quiet'


def load_report(report_path: str) -> dict:
    """Load existing report or create new one."""
    try:
        with open(report_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            'generated': None,
            'cities': {},
            'anomalies': []
        }


def save_report(report: dict, report_path: str):
    """Save report to JSON file."""
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)


def update_report(cities: list[str], report_path: str = 'report.json'):
    """Main function to update the report."""
    report = load_report(report_path)
    today = date.today().isoformat()
    now = datetime.now().isoformat()

    all_anomalies = []

    for city in cities:
        city_dir = f'cities/{city}'

        if city not in report['cities']:
            report['cities'][city] = {'feeds': {}}

        city_data = report['cities'][city]

        # Scan all .ics files in the city directory (skip combined.ics)
        for ics_path in sorted(glob.glob(f'{city_dir}/*.ics')):
            basename = os.path.basename(ics_path).replace('.ics', '')
            if basename == 'combined':
                continue

            feed_name = basename

            if feed_name not in city_data['feeds']:
                city_data['feeds'][feed_name] = {'history': []}

            feed_data = city_data['feeds'][feed_name]
            count, error = count_future_events_in_ics(ics_path)

            if error:
                all_anomalies.append({
                    'date': today,
                    'city': city,
                    'feed': feed_name,
                    'type': 'error',
                    'message': f'Error: {error}',
                    'severity': 'high'
                })
            else:
                anomalies = detect_anomalies(feed_name, count, feed_data['history'])
                for a in anomalies:
                    a['date'] = today
                    a['city'] = city
                    a['feed'] = feed_name
                    all_anomalies.append(a)

            entry = {'date': today, 'count': count}
            if error:
                entry['error'] = error
            if count == 0 and not error:
                feed_data['content'] = classify_ics_content(ics_path)
            else:
                feed_data.pop('content', None)

            if feed_data['history'] and feed_data['history'][-1]['date'] == today:
                feed_data['history'][-1] = entry
            else:
                feed_data['history'].append(entry)
            feed_data['history'] = feed_data['history'][-MAX_FEED_HISTORY:]

        # Remove feeds from report that no longer have .ics files
        current_basenames = {
            os.path.basename(p).replace('.ics', '')
            for p in glob.glob(f'{city_dir}/*.ics')
        } - {'combined'}
        stale = [k for k in city_data['feeds'] if k not in current_basenames]
        for k in stale:
            del city_data['feeds'][k]

    # Update anomalies (keep all historical anomalies)
    existing_today = {(a['city'], a['feed'], a['type'])
                      for a in report['anomalies']
                      if a.get('date') == today}

    for a in all_anomalies:
        key = (a['city'], a['feed'], a['type'])
        if key not in existing_today:
            report['anomalies'].append(a)

    anomaly_cutoff = (date.today() - timedelta(days=MAX_ANOMALY_DAYS)).isoformat()
    report['anomalies'] = [a for a in report['anomalies']
                           if (a.get('date') or '') >= anomaly_cutoff]

    # URL quality analysis from events.json
    for city in cities:
        city_dir = f'cities/{city}'
        events_json = f'cities/{city}/events.json'
        try:
            with open(events_json, 'r') as f:
                events = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            continue

        urls_with_url = [e for e in events if e.get('url')]
        total = len(urls_with_url)
        unique_urls = len(set(e['url'] for e in urls_with_url))

        # Group by domain
        from urllib.parse import urlparse
        by_domain = {}
        for e in urls_with_url:
            try:
                domain = urlparse(e['url']).hostname or e['url']
            except Exception:
                domain = e['url']
            if domain not in by_domain:
                by_domain[domain] = {'urls': set(), 'count': 0}
            by_domain[domain]['urls'].add(e['url'])
            by_domain[domain]['count'] += 1

        # Generic URLs: domains where all events share one URL, with >5 events
        generic_domains = []
        generic_count = 0
        for domain, info in by_domain.items():
            if len(info['urls']) == 1 and info['count'] > 5:
                generic_domains.append({
                    'domain': domain,
                    'events': info['count'],
                    'url': list(info['urls'])[0]
                })
                generic_count += info['count']
        generic_domains.sort(key=lambda g: -g['events'])

        # HTTP domains
        http_domains = set()
        http_count = 0
        for e in urls_with_url:
            if e['url'].startswith('http://'):
                try:
                    http_domains.add(urlparse(e['url']).hostname)
                except Exception:
                    pass
                http_count += 1

        # Source specificity
        by_source = {}
        for e in urls_with_url:
            src = e.get('source') or '(none)'
            if src not in by_source:
                by_source[src] = {'count': 0, 'urls': set()}
            by_source[src]['count'] += 1
            by_source[src]['urls'].add(e['url'])
        source_specificity = sorted([
            {
                'source': src,
                'events': info['count'],
                'unique_urls': len(info['urls']),
                'specificity_pct': round(len(info['urls']) / info['count'] * 100)
            }
            for src, info in by_source.items()
        ], key=lambda x: -x['events'])[:15]

        # Category breakdown
        by_category = {}
        for e in events:
            cat = e.get('category') or '(uncategorized)'
            by_category[cat] = by_category.get(cat, 0) + 1
        category_breakdown = sorted(
            [{'category': cat, 'count': cnt} for cat, cnt in by_category.items()],
            key=lambda x: -x['count']
        )

        # Image coverage
        with_image = sum(1 for e in events if e.get('image_url'))
        by_source_images = {}
        for e in events:
            src = e.get('source') or '(none)'
            if src not in by_source_images:
                by_source_images[src] = {'total': 0, 'with_image': 0}
            by_source_images[src]['total'] += 1
            if e.get('image_url'):
                by_source_images[src]['with_image'] += 1
        image_by_source = sorted(
            [{'source': src, 'total': info['total'], 'with_image': info['with_image']}
             for src, info in by_source_images.items() if info['with_image'] > 0],
            key=lambda x: -x['with_image']
        )

        report['cities'][city]['categories'] = category_breakdown
        report['cities'][city]['images'] = {
            'total': len(events),
            'with_image': with_image,
            'by_source': image_by_source
        }

        # Geo-filtered events (from combine_ics.py sidecar)
        geo_filtered_path = f'{city_dir}/geo_filtered.json'
        try:
            with open(geo_filtered_path, 'r') as f:
                geo_filtered = json.load(f)
            if geo_filtered:
                report['cities'][city]['geo_filtered'] = geo_filtered
            else:
                report['cities'][city].pop('geo_filtered', None)
        except (FileNotFoundError, json.JSONDecodeError):
            report['cities'][city].pop('geo_filtered', None)

        prev_build = report['cities'][city].get('build') or {}
        report['cities'][city]['build'] = {
            'generated': now,
            'total_events': len(events),
            'prev_total_events': prev_build.get('total_events'),
        }

        report['cities'][city]['url_quality'] = {
            'total_with_url': total,
            'total_events': len(events),
            'unique_urls': unique_urls,
            'generic_count': generic_count,
            'generic_domains': generic_domains,
            'http_count': http_count,
            'http_domains': len(http_domains),
            'source_specificity': source_specificity
        }

    # Timezone anomaly detection
    for city in cities:
        events_json = f'cities/{city}/events.json'
        try:
            with open(events_json, 'r') as f:
                events = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            continue

        tz_name = get_city_timezone(city)
        tz = ZoneInfo(tz_name)
        ref = datetime(2026, 3, 15, 12, 0, 0, tzinfo=tz)
        offset_hours = int(ref.utcoffset().total_seconds() / 3600)

        by_source = {}
        for e in events:
            st = e.get('start_time', '')
            if 'T' not in st:
                continue
            src = e.get('source', 'unknown')
            # Honor UTC offsets: a correct instant expressed in another
            # zone (e.g. an Eventbrite feed emitting Eastern) must be
            # judged by its hour in the city's timezone, not the raw
            # string hour. Naive timestamps keep the raw-hour reading.
            try:
                dt = datetime.fromisoformat(st.replace('Z', '+00:00'))
                if dt.tzinfo is not None:
                    dt = dt.astimezone(tz)
                hour, minute = dt.hour, dt.minute
            except ValueError:
                continue
            by_source.setdefault(src, []).append({
                'hour': hour, 'minute': minute,
                'title': e.get('title', '')[:60],
                'start_time': st[:16]
            })

        tz_anomalies = []
        for src, entries in by_source.items():
            if len(entries) < 3:
                continue
            suspicious = [e for e in entries if 0 <= e['hour'] < 5]
            if len(suspicious) < 2:
                continue
            shifted = [((e['hour'] - offset_hours) % 24) for e in suspicious]
            daytime = sum(1 for h in shifted if 8 <= h <= 18)
            if daytime >= len(suspicious) * 0.7:
                samples = []
                for e, sh in zip(suspicious[:5], shifted[:5]):
                    samples.append({
                        'start_time': e['start_time'],
                        'shows': f"{e['hour']:02d}:{e['minute']:02d}",
                        'likely': f"{sh:02d}:{e['minute']:02d}",
                        'title': e['title']
                    })
                tz_anomalies.append({
                    'source': src,
                    'count': len(suspicious),
                    'total': len(entries),
                    'offset': offset_hours,
                    'samples': samples
                })

        if tz_anomalies:
            report['cities'][city]['tz_anomalies'] = tz_anomalies

    # TZID inventory: distinct timezones found in each city's ICS files
    for city in cities:
        city_dir = f'cities/{city}'
        city_tz = get_city_timezone(city)
        tzid_counts = {}  # tzid → {count, files}
        for ics_path in sorted(glob.glob(f'{city_dir}/*.ics')):
            basename = os.path.basename(ics_path)
            if basename == 'combined.ics':
                continue
            try:
                with open(ics_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception:
                continue
            for m in re.finditer(r'DTSTART;TZID=([^:;]+)', content):
                tzid = m.group(1)
                if tzid not in tzid_counts:
                    tzid_counts[tzid] = {'count': 0, 'files': set()}
                tzid_counts[tzid]['count'] += 1
                tzid_counts[tzid]['files'].add(basename)
            # Count bare datetimes (no TZID, no Z)
            bare = len(re.findall(r'^DTSTART:\d{8}T\d{6}$', content, re.MULTILINE))
            if bare:
                key = '(bare — assumes city tz)'
                if key not in tzid_counts:
                    tzid_counts[key] = {'count': 0, 'files': set()}
                tzid_counts[key]['count'] += bare
                tzid_counts[key]['files'].add(basename)
            # Count UTC datetimes
            utc = len(re.findall(r'^DTSTART:\d{8}T\d{6}Z$', content, re.MULTILINE))
            if utc:
                key = 'UTC (Z suffix)'
                if key not in tzid_counts:
                    tzid_counts[key] = {'count': 0, 'files': set()}
                tzid_counts[key]['count'] += utc
                tzid_counts[key]['files'].add(basename)

        if tzid_counts:
            inventory = []
            for tzid, info in sorted(tzid_counts.items(), key=lambda x: -x[1]['count']):
                inventory.append({
                    'tzid': tzid,
                    'count': info['count'],
                    'files': len(info['files']),
                    'matches_city': tzid == city_tz,
                    'sample_files': sorted(info['files'])[:5]
                })
            report['cities'][city]['tzid_inventory'] = {
                'city_timezone': city_tz,
                'distinct_tzids': len(inventory),
                'tzids': inventory
            }

    # Prune cities that no longer exist in cities.json so retired
    # cities stop lingering in the aggregate forever.
    cities_json = Path(__file__).parent.parent / 'cities.json'
    try:
        active_cities = set(json.loads(cities_json.read_text()).keys())
    except (OSError, json.JSONDecodeError):
        active_cities = None
    if active_cities:
        for stale in [c for c in report['cities'] if c not in active_cities]:
            del report['cities'][stale]
        report['anomalies'] = [a for a in report['anomalies']
                               if a.get('city') in active_cities]

    report['generated'] = now

    save_report(report, report_path)

    # Print summary
    print(f"Report updated: {report_path}")
    print(f"Cities: {len(report['cities'])}")
    total_feeds = sum(len(c['feeds']) for c in report['cities'].values())
    print(f"Total feeds: {total_feeds}")
    if all_anomalies:
        print(f"New anomalies: {len(all_anomalies)}")
        for a in all_anomalies:
            print(f"  [{a['severity']}] {a['city']}/{a['feed']}: {a['message']}")


def classify_log_issue(message: str, level: str) -> str:
    text = message.lower()
    if "the following arguments are required" in text or "unrecognized arguments" in text:
        return "arg_error"
    if "http error" in text or "client error" in text:
        return "http_error"
    if "failed to resolve" in text or "name or service not known" in text:
        return "dns_error"
    if "connectionerror" in text or "connection refused" in text or "connection reset" in text:
        return "connection_error"
    if "timed out" in text or "timeout" in text:
        return "timeout"
    if "broken property" in text or "error parsing vevent" in text:
        return "parse_warning"
    if "traceback" in text:
        return "traceback"
    return "warning" if level == "warning" else "error"


def parse_build_errors(log_path: str) -> list[dict]:
    """Parse build.log for source-level error and warning issues."""
    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except FileNotFoundError:
        return []

    errors = []
    today = date.today().isoformat()

    structured_log_pattern = re.compile(
        r'^\[(?P<city>[^\]]+)\]\[(?P<phase>[^\]]+)\]\s+'
        r'(?P<timestamp>\d{4}-\d{2}-\d{2} [^ ]+)?'
        r'(?:\s+-\s+)?(?P<logger>[A-Za-z0-9_]+)\s+-\s+'
        r'(?P<level>ERROR|WARNING)\s+-\s+(?P<message>.*)$'
    )

    # local_build.py brackets each command's output with RUN/EXIT marker lines
    # labeled by the source's display name. Attributing issues to the active
    # RUN label keeps errors from a shared scraper script (one script, many
    # sources) tied to the specific source that logged them instead of being
    # matched to every source using that script.
    run_marker_pattern = re.compile(
        r'^\[(?P<city>[^\]]+)\]\[(?P<phase>[^\]]+)\]\s+RUN\s+(?P<label>.+)$'
    )
    exit_marker_pattern = re.compile(
        r'^\[(?P<city>[^\]]+)\]\[(?P<phase>[^\]]+)\]\s+EXIT\s+-?\d+\s+(?P<label>.+)$'
    )
    active_run_label = None

    # Legacy patterns that indicate issues
    error_patterns = [
        re.compile(r'error: the following arguments are required', re.IGNORECASE),
        re.compile(r'HTTP Error \d+', re.IGNORECASE),
        re.compile(r'ConnectionError', re.IGNORECASE),
        re.compile(r'Timeout', re.IGNORECASE),
        re.compile(r': error:', re.IGNORECASE),
        re.compile(r'(?<!Timeout)Error:', re.IGNORECASE),
    ]

    # Pattern to extract Python script name from a line
    py_file_pattern = re.compile(r'(\w[\w-]*\.py)')

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        run_match = run_marker_pattern.match(line)
        if run_match:
            active_run_label = run_match.group('label').strip()
            i += 1
            continue
        exit_match = exit_marker_pattern.match(line)
        if exit_match:
            active_run_label = None
            i += 1
            continue

        structured_match = structured_log_pattern.match(line)
        if structured_match:
            level = structured_match.group('level').lower()
            logger = structured_match.group('logger')
            message = structured_match.group('message')
            errors.append({
                'date': today,
                'line': line.strip(),
                'city': structured_match.group('city'),
                'phase': structured_match.group('phase'),
                'logger': logger,
                'source': active_run_label or logger.removesuffix('Scraper'),
                'level': level,
                'issue_type': classify_log_issue(message, level),
                'message': message,
            })
            i += 1
            continue

        # Check for traceback blocks
        if 'Traceback (most recent call last)' in line:
            # Collect the full traceback through the final error line
            tb_lines = [line]
            j = i + 1
            last_error_line = line
            while j < len(lines):
                tb_line = lines[j].rstrip()
                tb_lines.append(tb_line)
                if tb_line and not tb_line.startswith(' ') and j > i + 1:
                    last_error_line = tb_line
                    break
                j += 1

            # Extract source from traceback file references
            source = None
            for tb in tb_lines:
                m = re.search(r'File ".*?/(\w[\w-]*\.py)"', tb)
                if m:
                    source = m.group(1).replace('.py', '')

            errors.append({
                'date': today,
                'line': last_error_line,
                'source': active_run_label or source,
                'level': 'error',
                'issue_type': 'traceback',
            })
            i = j + 1
            continue

        # Check single-line error patterns
        for pattern in error_patterns:
            if pattern.search(line):
                # Extract source script name
                source = None
                m = py_file_pattern.search(line)
                if m:
                    source = m.group(1).replace('.py', '')
                # Also check the preceding line for script name context
                if not source and i > 0:
                    m = py_file_pattern.search(lines[i - 1])
                    if m:
                        source = m.group(1).replace('.py', '')

                errors.append({
                    'date': today,
                    'line': line.strip(),
                    'source': active_run_label or source,
                    'level': 'error',
                    'issue_type': classify_log_issue(line, 'error'),
                })
                break

        i += 1

    # Deduplicate by (line, source)
    seen = set()
    unique = []
    for e in errors:
        key = (e['line'], e.get('source'), e.get('level'))
        if key not in seen:
            seen.add(key)
            unique.append(e)

    return unique


def parse_feeds_reference(city: str) -> dict:
    """Map feed stems to their source using the generated read-only
    cities/<city>/feeds.txt, so report problems can carry a
    reproduction command (curl for live feeds, the registered command
    for scrapers)."""
    path = Path(__file__).parent.parent / 'cities' / city / 'feeds.txt'
    ref = {}
    if not path.exists():
        return ref
    try:
        from feed_slug import slugify
    except ImportError:
        return ref
    pending_name = None
    pending_cmd = None
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if line.startswith('# cmd:'):
            pending_cmd = line[len('# cmd:'):].strip()
            continue
        if line.startswith('#'):
            body = line.lstrip('# ').split(' | ')[0].strip()
            if body and not line.startswith('# ---'):
                pending_name = body
            continue
        if line.startswith('http'):
            ref[slugify(line)] = {'kind': 'feed', 'name': pending_name or '', 'url': line}
            pending_name = pending_cmd = None
        elif line.startswith('cities/') and line.endswith('.ics'):
            ref[Path(line).stem] = {'kind': 'scraper', 'name': pending_name or '', 'cmd': pending_cmd}
            pending_name = pending_cmd = None
        else:
            pending_name = pending_cmd = None
    return ref


def _norm_key(text):
    return re.sub(r'[^a-z0-9]+', '', (text or '').lower())


def build_city_slice(report: dict, city: str, prev_error_lines: set) -> dict:
    """Assemble the per-city report slice: last-build status, ranked
    action items answering "has a feed gone silent (and why)", "are
    there new errors", "are there tz anomalies" — plus the full detail
    sections for drill-down."""
    data = report['cities'].get(city, {})
    feeds = data.get('feeds', {})
    stems = {_norm_key(name) for name in feeds}

    def error_matches_city(e):
        if e.get('city') == city:
            return True
        src = _norm_key(e.get('source'))
        return bool(src) and src in stems

    errors = [e for e in report.get('errors', []) if error_matches_city(e)]
    new_errors = [e for e in errors if e.get('line') not in prev_error_lines]
    ongoing_errors = [e for e in errors if e.get('line') in prev_error_lines]

    silent = []
    for name, fd in sorted(feeds.items()):
        hist = fd.get('history', [])
        if not hist or hist[-1].get('count') != 0 or hist[-1].get('error'):
            continue
        was_count, was_date = None, None
        for h in reversed(hist):
            if h.get('count'):
                was_count, was_date = h['count'], h['date']
                break
        since = hist[-1]['date']
        for h in reversed(hist):
            if h.get('count') == 0 and not h.get('error'):
                since = h['date']
            else:
                break
        silent.append({
            'feed': name,
            'was': was_count,
            'was_date': was_date,
            'silent_since': since,
            'content': fd.get('content', 'quiet'),
        })

    week_ago = (date.today() - timedelta(days=7)).isoformat()
    recent_anoms = [a for a in report.get('anomalies', [])
                    if a.get('city') == city and (a.get('date') or '') >= week_ago]
    tz = data.get('tz_anomalies', [])
    ref = parse_feeds_reference(city)

    def repro_for(stem):
        src = ref.get(stem)
        if not src:
            return None
        if src['kind'] == 'feed':
            return {
                'display': src.get('name') or stem,
                'source': src['url'],
                'command': f"curl -sL -A 'Mozilla/5.0' '{src['url']}' | grep -c 'BEGIN:VEVENT'",
            }
        return {
            'display': src.get('name') or stem,
            'source': src.get('cmd'),
            'command': src.get('cmd'),
        }

    def _was_phrase(s):
        if s.get('was') is None:
            return "no good build in recorded history"
        return f"was {s['was']} events on {s['was_date']}"

    items = []
    for e in new_errors:
        stem = _norm_key(e.get('source'))
        match = next((n for n in feeds if _norm_key(n) == stem), None)
        items.append({
            'severity': 1, 'kind': 'new_error',
            'title': f"New error: {e.get('source') or e.get('feed') or 'build'}",
            'detail': (e.get('message') or e.get('line') or '')[:300],
            'feed': match,
            'repro': repro_for(match) if match else None,
        })
    for s in silent:
        if str(s['content']).startswith('not_ics'):
            kind = str(s['content']).split(':', 1)[-1]
            items.append({
                'severity': 1, 'kind': 'broken_feed',
                'title': f"{s['feed']} is serving {kind}, not ICS",
                'detail': f"{_was_phrase(s)}; broken since {s['silent_since']}",
                'feed': s['feed'],
                'repro': repro_for(s['feed']),
            })
    newly_zero = {a.get('feed') for a in recent_anoms if a.get('type') == 'zero_events'}
    for s in silent:
        if not str(s['content']).startswith('not_ics') and s['feed'] in newly_zero:
            items.append({
                'severity': 2, 'kind': 'newly_silent',
                'title': f"{s['feed']} went silent (valid calendar, 0 events)",
                'detail': _was_phrase(s),
                'feed': s['feed'],
                'repro': repro_for(s['feed']),
            })
    for a in recent_anoms:
        if a.get('type') == 'significant_drop':
            items.append({
                'severity': 2, 'kind': 'drop',
                'title': f"{a.get('feed')}: {a.get('message')}",
                'detail': a.get('date'),
                'feed': a.get('feed'),
                'repro': repro_for(a.get('feed')),
            })
    for z in tz:
        stem = _norm_key(z.get('source'))
        match = next((n for n in feeds if _norm_key(n) == stem), None)
        items.append({
            'severity': 3, 'kind': 'tz_anomaly',
            'title': f"{z.get('source')}: {z.get('count')}/{z.get('total')} events at suspicious hours",
            'detail': f"likely a {z.get('offset')}h offset error",
            'feed': match,
            'repro': repro_for(match) if match else None,
            'samples': z.get('samples'),
        })
    for e in ongoing_errors:
        items.append({
            'severity': 3, 'kind': 'ongoing_error',
            'title': f"Ongoing error: {e.get('source') or e.get('feed') or 'build'}",
            'detail': (e.get('message') or e.get('line') or '')[:300],
        })
    items.sort(key=lambda i: i['severity'])

    # Long-silent feeds are not surfaced as problems — they are a watch
    # list rendered in the drill-downs.
    watching = [
        {**s, 'repro': repro_for(s['feed'])}
        for s in silent
        if not str(s['content']).startswith('not_ics') and s['feed'] not in newly_zero
    ]

    build = dict(data.get('build') or {})
    if build.get('total_events') is not None and build.get('prev_total_events') is not None:
        build['delta'] = build['total_events'] - build['prev_total_events']

    slim_feeds = {}
    for name, fd in sorted(feeds.items()):
        hist = fd.get('history', [])
        slim_feeds[name] = {
            'count': hist[-1]['count'] if hist else None,
            'error': hist[-1].get('error') if hist else None,
            'content': fd.get('content'),
            'history': hist[-30:],
        }

    return {
        'city': city,
        'generated': report.get('generated'),
        'build': build,
        'problems': items,
        'watching': watching,
        'silent_feeds': silent,
        'new_errors': new_errors,
        'ongoing_errors': ongoing_errors,
        'tz_anomalies': tz,
        'recent_anomalies': recent_anoms,
        'detail': {
            'feeds': slim_feeds,
            'url_quality': data.get('url_quality'),
            'tzid_inventory': data.get('tzid_inventory'),
            'geo_filtered': data.get('geo_filtered'),
            'categories': data.get('categories'),
            'images': data.get('images'),
        },
    }


def write_city_slices(report: dict, cities: list[str], prev_error_lines: set,
                      slice_dir: str, template_path: str | None):
    """Write report/<city>/report.json (+ index.html from the template)."""
    template = None
    if template_path and Path(template_path).exists():
        template = Path(template_path).read_text()
    for city in cities:
        if city not in report.get('cities', {}):
            continue
        out = Path(slice_dir) / city
        out.mkdir(parents=True, exist_ok=True)
        slice_data = build_city_slice(report, city, prev_error_lines)
        (out / 'report.json').write_text(json.dumps(slice_data, indent=2, default=str))
        if template:
            (out / 'index.html').write_text(template)
        print(f"  wrote {out}/report.json")


def main():
    parser = argparse.ArgumentParser(description='Generate feed health report')
    parser.add_argument('--cities', type=str, default='santarosa,bloomington,davis',
                        help='Comma-separated list of cities')
    parser.add_argument('--output', type=str, default='report.json',
                        help='Output JSON file path')
    parser.add_argument('--build-log', type=str, default=None,
                        help='Path to build.log for error extraction')
    parser.add_argument('--slice-dir', type=str, default=None,
                        help='Write per-city report slices (and pages) under this directory')
    parser.add_argument('--template', type=str, default=None,
                        help='HTML template copied to <slice-dir>/<city>/index.html')
    args = parser.parse_args()

    cities = [c.strip() for c in args.cities.split(',')]
    # Snapshot the prior build's error lines before this run overwrites
    # them, so slices can distinguish NEW errors from ongoing ones.
    prev_error_lines = {e.get('line') for e in load_report(args.output).get('errors', [])}
    update_report(cities, args.output)

    # Parse build errors if log provided
    if args.build_log:
        report = load_report(args.output)
        build_errors = parse_build_errors(args.build_log)
        report['errors'] = build_errors
        save_report(report, args.output)
        if build_errors:
            error_count = sum(1 for e in build_errors if e.get('level') == 'error')
            warning_count = sum(1 for e in build_errors if e.get('level') == 'warning')
            print(f"Build issues found: {len(build_errors)} ({error_count} errors, {warning_count} warnings)")
            for e in build_errors:
                print(f"  [{e.get('level', '?')}:{e.get('source', '?')}] {e['line'][:120]}")
        else:
            print("No build issues found in log.")

    if args.slice_dir:
        report = load_report(args.output)
        write_city_slices(report, cities, prev_error_lines, args.slice_dir, args.template)


if __name__ == '__main__':
    main()
