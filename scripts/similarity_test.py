#!/usr/bin/env python3
"""Test harness for evaluating text similarity algorithms on event titles.

Reads a city's events.json, groups events by timeslot, and shows how the
calendar would look with similarity-based clustering vs current (random) order.

Usage:
    # Preview calendar order for a specific date
    python scripts/similarity_test.py --city santarosa --date 2026-02-19

    # Compare algorithms side by side
    python scripts/similarity_test.py --city santarosa --date 2026-02-20 --algorithm all

    # Preview all dates (just show timeslots where clustering changes order)
    python scripts/similarity_test.py --city santarosa --changes-only

    # Pair analysis mode (original behavior)
    python scripts/similarity_test.py --city santarosa --pairs
"""

import argparse
import json
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path


def similarity_sequencematcher(a, b):
    """stdlib SequenceMatcher ratio (0-1)."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def similarity_levenshtein(a, b):
    """Levenshtein distance normalized to 0-1 similarity."""
    a, b = a.lower(), b.lower()
    if not a and not b:
        return 1.0
    m, n = len(a), len(b)
    d = list(range(n + 1))
    for i in range(1, m + 1):
        prev = d[0]
        d[0] = i
        for j in range(1, n + 1):
            temp = d[j]
            if a[i-1] == b[j-1]:
                d[j] = prev
            else:
                d[j] = 1 + min(prev, d[j], d[j-1])
            prev = temp
    distance = d[n]
    return 1.0 - distance / max(m, n)


def similarity_token_set(a, b):
    """Token set ratio: compare word sets, ignore order. 0-1 similarity."""
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
        SequenceMatcher(None, sorted_inter, combined_a).ratio() if combined_a else 1.0,
        SequenceMatcher(None, sorted_inter, combined_b).ratio() if combined_b else 1.0,
        SequenceMatcher(None, combined_a, combined_b).ratio(),
    ]
    return max(ratios)


ALGORITHMS = {
    'sequencematcher': similarity_sequencematcher,
    'levenshtein': similarity_levenshtein,
    'token_set': similarity_token_set,
}


def load_events(city):
    path = Path(f'cities/{city}/events.json')
    if not path.exists():
        raise FileNotFoundError(f'No events.json found at {path}')
    with open(path) as f:
        return json.load(f)


def group_by_timeslot(events):
    """Group events by start_time (YYYY-MM-DDTHH:MM)."""
    groups = defaultdict(list)
    for e in events:
        st = e.get('start_time', '')
        if not st:
            continue
        key = st[:16]
        groups[key].append(e)
    return groups


def cluster_events(events, sim_func, threshold):
    """Cluster events by title similarity using union-find. Return list of clusters."""
    n = len(events)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        parent[find(a)] = find(b)

    for i in range(n):
        for j in range(i + 1, n):
            title_a = events[i].get('title', '')
            title_b = events[j].get('title', '')
            if title_a and title_b and sim_func(title_a, title_b) >= threshold:
                union(i, j)

    clusters = defaultdict(list)
    for i in range(n):
        clusters[find(i)].append(events[i])

    # Sort within each cluster alphabetically by title
    for c in clusters.values():
        c.sort(key=lambda e: (e.get('title', '') or '').lower())

    # Sort clusters by first title
    sorted_clusters = sorted(clusters.values(),
        key=lambda c: (c[0].get('title', '') or '').lower())

    return sorted_clusters


def format_event(e):
    """Format an event for display."""
    return f'{e.get("title", "(no title)")}  ({e.get("source", "")})'


def preview_date(events, date, algos, threshold):
    """Show calendar preview for a specific date."""
    # Filter to date
    day_events = [e for e in events if (e.get('start_time', '') or '')[:10] == date]
    if not day_events:
        print(f'No events found for {date}')
        return

    # Group by timeslot
    slots = group_by_timeslot(day_events)

    print(f'=== {date} ({len(day_events)} events) ===')
    print()

    for time_key in sorted(slots.keys()):
        slot_events = slots[time_key]
        if len(slot_events) < 2:
            continue

        time_display = time_key[11:]  # HH:MM

        # Show current order (alphabetical, which is what you'd get without clustering)
        alpha_order = sorted(slot_events, key=lambda e: (e.get('title', '') or '').lower())

        for algo_name, sim_func in algos.items():
            clusters = cluster_events(slot_events, sim_func, threshold)
            clustered_order = [e for c in clusters for e in c]

            # Check if clustering changed the order vs alphabetical
            alpha_titles = [e.get('title', '') for e in alpha_order]
            clustered_titles = [e.get('title', '') for e in clustered_order]
            changed = alpha_titles != clustered_titles

            marker = ' *' if changed else ''
            print(f'  {time_display} [{algo_name}]{marker}')

            cluster_idx = 0
            for cluster in clusters:
                if len(cluster) > 1:
                    cluster_idx += 1
                    for e in cluster:
                        print(f'    [{cluster_idx}] {format_event(e)}')
                else:
                    print(f'        {format_event(cluster[0])}')
            print()


def preview_changes(events, algos, threshold):
    """Show only timeslots where clustering changes the order vs alphabetical."""
    slots = group_by_timeslot(events)
    changes_found = 0

    for time_key in sorted(slots.keys()):
        slot_events = slots[time_key]
        if len(slot_events) < 2:
            continue

        alpha_order = sorted(slot_events, key=lambda e: (e.get('title', '') or '').lower())
        alpha_titles = [e.get('title', '') for e in alpha_order]

        for algo_name, sim_func in algos.items():
            clusters = cluster_events(slot_events, sim_func, threshold)
            clustered_order = [e for c in clusters for e in c]
            clustered_titles = [e.get('title', '') for e in clustered_order]

            if alpha_titles != clustered_titles:
                changes_found += 1
                print(f'{time_key} [{algo_name}]')
                print(f'  Alphabetical:')
                for t in alpha_titles:
                    print(f'    {t}')
                print(f'  Clustered:')
                cluster_idx = 0
                for cluster in clusters:
                    if len(cluster) > 1:
                        cluster_idx += 1
                        for e in cluster:
                            print(f'    [{cluster_idx}] {e.get("title", "")}')
                    else:
                        print(f'        {cluster[0].get("title", "")}')
                print()

    print(f'Total timeslots where clustering differs from alphabetical: {changes_found}')


def show_pairs(events, algos, threshold, limit):
    """Original pair analysis mode."""
    slots = group_by_timeslot(events)

    for algo_name, sim_func in algos.items():
        all_pairs = []
        for key, slot_events in sorted(slots.items()):
            if len(slot_events) < 2:
                continue
            for i in range(len(slot_events)):
                for j in range(i + 1, len(slot_events)):
                    title_a = slot_events[i].get('title', '')
                    title_b = slot_events[j].get('title', '')
                    if not title_a or not title_b:
                        continue
                    score = sim_func(title_a, title_b)
                    if score >= threshold:
                        all_pairs.append({
                            'score': score,
                            'group': key,
                            'title_a': title_a,
                            'title_b': title_b,
                            'source_a': slot_events[i].get('source', ''),
                            'source_b': slot_events[j].get('source', ''),
                        })

        all_pairs.sort(key=lambda p: -p['score'])
        print(f'=== {algo_name} ===')
        print(f'Pairs above {threshold}: {len(all_pairs)}')
        print()

        for p in all_pairs[:limit]:
            print(f'  [{p["group"]}] {p["score"]:.3f}')
            print(f'    {p["title_a"]}  ({p["source_a"]})')
            print(f'    {p["title_b"]}  ({p["source_b"]})')
            print()

        if len(all_pairs) > limit:
            print(f'  ... and {len(all_pairs) - limit} more pairs')
            print()

        if all_pairs:
            scores = [p['score'] for p in all_pairs]
            buckets = defaultdict(int)
            for s in scores:
                bucket = f'{int(s * 10) / 10:.1f}-{int(s * 10) / 10 + 0.1:.1f}'
                buckets[bucket] += 1
            print(f'  Score distribution:')
            for bucket in sorted(buckets.keys()):
                print(f'    {bucket}: {buckets[bucket]}')
            print()


def main():
    parser = argparse.ArgumentParser(description='Test title similarity algorithms on event data')
    parser.add_argument('--city', required=True, help='City name (directory under cities/)')
    parser.add_argument('--algorithm', default='all', choices=list(ALGORITHMS.keys()) + ['all'],
                        help='Similarity algorithm to use (default: all)')
    parser.add_argument('--threshold', type=float, default=0.6, help='Minimum similarity score (default: 0.6)')
    parser.add_argument('--date', help='Preview calendar for a specific date (YYYY-MM-DD)')
    parser.add_argument('--changes-only', action='store_true',
                        help='Show only timeslots where clustering differs from alphabetical')
    parser.add_argument('--pairs', action='store_true', help='Show pair analysis (original mode)')
    parser.add_argument('--limit', type=int, default=50, help='Max pairs to show in --pairs mode (default: 50)')
    args = parser.parse_args()

    events = load_events(args.city)
    print(f'Loaded {len(events)} events for {args.city}')
    print(f'Threshold: {args.threshold}')
    print()

    algos = ALGORITHMS if args.algorithm == 'all' else {args.algorithm: ALGORITHMS[args.algorithm]}

    if args.date:
        preview_date(events, args.date, algos, args.threshold)
    elif args.changes_only:
        preview_changes(events, algos, args.threshold)
    elif args.pairs:
        show_pairs(events, algos, args.threshold, args.limit)
    else:
        # Default: preview all dates
        dates = sorted(set((e.get('start_time', '') or '')[:10] for e in events if e.get('start_time')))
        for date in dates:
            preview_date(events, date, algos, args.threshold)


if __name__ == '__main__':
    main()
