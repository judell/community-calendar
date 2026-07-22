#!/usr/bin/env python3
"""
Classify events in events.json files using the Anthropic API (Claude Haiku).

Reads events.json, classifies events missing a category, writes back with
categories added. Designed to run during the build pipeline before publishing.

Curator overrides from Supabase are used as few-shot examples when available.

Usage:
    python3 scripts/classify_events_json.py cities/toronto/events.json
    python3 scripts/classify_events_json.py cities/*/events.json
    python3 scripts/classify_events_json.py cities/toronto/events.json --dry-run
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
_SUPABASE_URL = os.environ.get("SUPABASE_URL")
_SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
if not _SUPABASE_URL or not _SUPABASE_KEY:
    print("Set SUPABASE_URL and SUPABASE_KEY environment variables")
    sys.exit(1)

# Type-safe: these are guaranteed to be strings after the check above
SUPABASE_URL: str = _SUPABASE_URL
SUPABASE_KEY: str = _SUPABASE_KEY

CATEGORIES_FILE = Path(__file__).parent.parent / "categories.json"
with CATEGORIES_FILE.open() as f:
    CATEGORIES = [c["name"] for c in json.load(f)]

VALID_CATEGORIES = set(CATEGORIES)
BATCH_SIZE = 50
RATE_LIMIT_TPM = 10000  # Tokens per minute limit
RATE_LIMIT_WINDOW = 60  # Rate limit window in seconds
FALLBACK_DELAY = 15  # Fallback delay in seconds between batches
MAX_RETRIES = 3  # Maximum retry attempts for rate limit errors
RETRY_BASE_DELAY = 30  # Base delay for exponential backoff (seconds)
HTTP_RATE_LIMIT = 429  # HTTP status code for rate limiting
HTTP_SERVER_ERROR_MIN = 500  # Start of 5xx range
HTTP_SERVER_ERROR_MAX = 600  # End of 5xx range


class RateLimitTracker:
    """Track API rate limits and calculate smart delays."""

    def __init__(self, tokens_per_minute=RATE_LIMIT_TPM):
        self.tokens_per_minute = tokens_per_minute
        self.last_request_time: float | None = None
        self.tokens_used_in_window = 0
        self.window_start: float | None = None

    def parse_headers(self, headers):
        """Parse rate limit info from API response headers."""
        try:
            tokens_limit = int(headers.get("anthropic-ratelimit-tokens-limit", 0))
            tokens_remaining = int(
                headers.get("anthropic-ratelimit-tokens-remaining", 0)
            )
            reset_time = headers.get("anthropic-ratelimit-tokens-reset", "")

            if tokens_limit > 0:
                # Update tokens_per_minute from API if limit differs
                if tokens_limit != self.tokens_per_minute:
                    self.tokens_per_minute = tokens_limit
                tokens_used = tokens_limit - tokens_remaining
                return {
                    "tokens_used": tokens_used,
                    "tokens_remaining": tokens_remaining,
                    "tokens_limit": tokens_limit,
                    "reset_time": reset_time,
                }
        except (ValueError, TypeError):
            pass
        return None

    def calculate_delay(self, estimated_next_tokens=2000):
        """Calculate how long to wait before next request."""
        now = time.time()

        # If this is the first request, no delay needed
        if self.last_request_time is None:
            self.last_request_time = now
            self.window_start = now
            return 0

        # Check if we're in a new rate limit window
        # Type-safe: window_start is guaranteed to be float here
        assert self.window_start is not None
        time_since_window_start = now - self.window_start
        if time_since_window_start >= RATE_LIMIT_WINDOW:
            # Reset the window
            self.tokens_used_in_window = 0
            self.window_start = now
            self.last_request_time = now
            return 0

        # Calculate if we have budget for the next request
        tokens_available = self.tokens_per_minute - self.tokens_used_in_window

        if tokens_available < estimated_next_tokens:
            # Need to wait until the window resets
            delay = RATE_LIMIT_WINDOW - time_since_window_start + 1
            return max(0, delay)

        # We have budget, but add a small delay to be conservative
        conservative_delay = (RATE_LIMIT_WINDOW - time_since_window_start) / 10
        return min(5, conservative_delay)

    def record_request(self, tokens_used):
        """
        Record that a request was made.

        Note: tokens_used from API headers is cumulative (total used in window),
        not incremental. Store it directly rather than adding.
        """
        now = time.time()
        self.last_request_time = now

        # Initialize window if needed
        if self.window_start is None:
            self.window_start = now

        # Check if we're in a new window
        # Type-safe: window_start is guaranteed to be float here
        assert self.window_start is not None
        if now - self.window_start >= RATE_LIMIT_WINDOW:
            self.tokens_used_in_window = tokens_used
            self.window_start = now
        else:
            # tokens_used is cumulative from API, replace (don't add)
            self.tokens_used_in_window = tokens_used

    def get_status(self):
        """Get current rate limit status for logging."""
        if self.window_start is None:
            return "No requests yet"

        tokens_remaining = max(0, self.tokens_per_minute - self.tokens_used_in_window)

        return (
            f"{self.tokens_used_in_window}/{self.tokens_per_minute} tokens "
            f"used in window, {tokens_remaining} remaining"
        )


def anthropic_call(api_key, model, prompt, retry_count=0):
    """Call Anthropic Messages API with retry logic for rate limits."""
    body = json.dumps(
        {
            "model": model,
            "max_tokens": 4096,
            "temperature": 0,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode()

    req = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=body,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            # Keep resp.headers as-is (case-insensitive)
            response_headers = resp.headers
            return result["content"][0]["text"].strip(), response_headers
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")

        # Handle rate limit errors (429) with exponential backoff
        if e.code == HTTP_RATE_LIMIT and retry_count < MAX_RETRIES:
            # Prefer retry-after header when present
            retry_after = e.headers.get("retry-after")
            if retry_after:
                try:
                    retry_delay = int(retry_after)
                except (ValueError, TypeError):
                    retry_delay = RETRY_BASE_DELAY * (2**retry_count)
            else:
                retry_delay = RETRY_BASE_DELAY * (2**retry_count)

            msg = (
                f"  Rate limit hit ({HTTP_RATE_LIMIT}), retrying in "
                f"{retry_delay}s (attempt {retry_count + 1}/{MAX_RETRIES})..."
            )
            print(msg, file=sys.stderr, flush=True)
            time.sleep(retry_delay)
            return anthropic_call(api_key, model, prompt, retry_count + 1)

        # Handle server errors (5xx) with retry
        is_server_error = HTTP_SERVER_ERROR_MIN <= e.code < HTTP_SERVER_ERROR_MAX
        if is_server_error and retry_count < MAX_RETRIES:
            retry_delay = RETRY_BASE_DELAY
            msg = (
                f"  Server error ({e.code}), retrying in {retry_delay}s "
                f"(attempt {retry_count + 1}/{MAX_RETRIES})..."
            )
            print(msg, file=sys.stderr, flush=True)
            time.sleep(retry_delay)
            return anthropic_call(api_key, model, prompt, retry_count + 1)

        # For other errors or exhausted retries, fail
        print(f"API error {e.code}: {error_body}", file=sys.stderr)
        raise


def fetch_overrides():
    """Fetch curator overrides from Supabase as few-shot examples.

    Most recent first. Event context comes from the denormalized
    snapshot columns (event_title/event_location/event_city), so
    overrides whose event was deleted (event_id NULL) still teach;
    the events(...) embed is kept as a fallback for rows written
    before the snapshot-columns migration.
    """
    path = (
        "category_overrides"
        "?select=category,event_title,event_location,event_city,"
        "events(title,location)"
        "&order=created_at.desc"
    )
    url = SUPABASE_URL + "/rest/v1/" + path
    req = urllib.request.Request(
        url,
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": "Bearer " + SUPABASE_KEY,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception:
        return []


FEW_SHOT_CAP = 20


def build_few_shot(overrides, city=None):
    """Build few-shot examples string from curator overrides.

    Overrides arrive most-recent-first; same-city overrides are
    preferred when the pool exceeds FEW_SHOT_CAP. Falls back to the
    embedded events row for overrides predating the snapshot columns.
    """
    if not overrides:
        return ""
    if city:
        ordered = [o for o in overrides if o.get("event_city") == city] + [
            o for o in overrides if o.get("event_city") != city
        ]
    else:
        ordered = overrides
    lines = ["\nHere are examples of how the curator has classified similar events:"]
    count = 0
    for o in ordered:
        ev = o.get("events") or {}
        title = o.get("event_title") or ev.get("title", "")
        location = o.get("event_location") or ev.get("location", "")
        if not title:
            continue
        cat = o.get("category", "")
        lines.append(f'  Title: "{title}" Location: "{location}" → {cat}')
        count += 1
        if count >= FEW_SHOT_CAP:
            break
    return "\n".join(lines) if len(lines) > 1 else ""


def classify_batch(events, few_shot, api_key, model):
    """
    Classify a batch of events.

    Returns (dict mapping index to category, response headers).
    """
    event_lines = []
    for i, event in enumerate(events):
        title = event.get("title", "")
        location = event.get("location", "")
        description = (event.get("description") or "")[:300]
        ics_cats = event.get("ics_categories")
        ics_str = ""
        if ics_cats:
            if isinstance(ics_cats, list):
                ics_str = ", ".join(ics_cats)
            else:
                ics_str = str(ics_cats)
        event_lines.append(
            f'{i + 1}. Title: "{title}" Location: "{location}"'
            + (f' ICS tags: "{ics_str}"' if ics_str else "")
            + (f' Description: "{description}"' if description else "")
        )

    example_json = (
        '[{"index": 1, "category": "Music / Concerts"}, {"index": 2, "category": null}]'
    )

    prompt = f"""Classify each event into exactly one category. Categories:
{chr(10).join("- " + c for c in CATEGORIES)}
{few_shot}

Events to classify:

{chr(10).join(event_lines)}

Respond with ONLY a JSON array. Each element must have "index" (1-based) and \
"category" (exact category name from the list, or null if none fit). \
Example: {example_json}"""

    raw, headers = anthropic_call(api_key, model, prompt)

    start = raw.find("[")
    end = raw.rfind("]") + 1
    if start < 0 or end <= 0:
        print(f"  WARNING: no JSON array in response: {raw[:200]}", file=sys.stderr)
        return {}, headers

    try:
        items = json.loads(raw[start:end])
    except json.JSONDecodeError as exc:
        print(f"  WARNING: JSON parse error: {exc}", file=sys.stderr)
        return {}, headers

    result_map = {}
    for item in items:
        idx = item.get("index")
        cat = item.get("category")
        if cat and cat in VALID_CATEGORIES:
            result_map[idx] = cat
        elif cat:
            for valid_cat in CATEGORIES:
                if valid_cat.lower() in str(cat).lower():
                    result_map[idx] = valid_cat
                    break

    return result_map, headers


def process_file(  # noqa: PLR0915, PLR0912
    filepath, config, few_shot, dry_run=False, rate_limiter=None
):
    """Classify events in a single events.json file.

    Args:
        filepath: Path to events.json file
        config: Dict with 'api_key' and 'model' keys
        few_shot: Few-shot examples string
        dry_run: If True, don't write changes
        rate_limiter: Optional RateLimitTracker instance
    """
    api_key = config["api_key"]
    model = config["model"]
    path = Path(filepath)
    if not path.exists():
        print(f"  Skipping {filepath}: not found")
        return

    with path.open() as f:
        events = json.load(f)

    # Find events needing classification
    to_classify = [(i, e) for i, e in enumerate(events) if not e.get("category")]
    already = len(events) - len(to_classify)

    city = path.parent.name
    msg = (
        f"{city}: {len(events)} events, {already} already classified, "
        f"{len(to_classify)} to classify"
    )
    print(msg)

    if not to_classify:
        return

    # Initialize rate limiter (shared across files or create new for testing)
    if rate_limiter is None:
        rate_limiter = RateLimitTracker()

    # Group by title to avoid re-classifying recurring event instances
    title_groups = defaultdict(list)
    for idx, event in to_classify:
        title_key = (event.get("title") or "").strip().lower()
        title_groups[title_key].append((idx, event))

    # Pick one representative per title group
    representative_items = [
        (group[0][0], group[0][1]) for group in title_groups.values()
    ]
    if len(representative_items) < len(to_classify):
        msg = (
            f"  {len(representative_items)} unique titles "
            f"(deduplicated from {len(to_classify)} events)"
        )
        print(msg)

    # Classify in batches (using representatives only)
    classified = 0
    cats = Counter()
    rep_results = {}  # maps normalized title_key to category
    total_batches = (len(representative_items) + BATCH_SIZE - 1) // BATCH_SIZE
    batch_start_time = time.time()

    for batch_start in range(0, len(representative_items), BATCH_SIZE):
        batch_items = representative_items[batch_start : batch_start + BATCH_SIZE]
        batch_events = [e for _, e in batch_items]
        batch_num = batch_start // BATCH_SIZE + 1

        # Calculate delay before this batch
        estimated_tokens = len(batch_events) * 50  # Rough estimate
        delay = rate_limiter.calculate_delay(estimated_tokens)

        if delay > 0:
            msg = (
                f"  Rate limit: waiting {delay:.1f}s before batch "
                f"{batch_num}/{total_batches}..."
            )
            print(msg, flush=True)
            time.sleep(delay)

        # Progress with time estimate
        elapsed = time.time() - batch_start_time
        if batch_num > 1:
            avg_batch_time = elapsed / (batch_num - 1)
            remaining_batches = total_batches - batch_num + 1
            eta_seconds = avg_batch_time * remaining_batches
            eta_str = f", ETA {int(eta_seconds)}s"
        else:
            eta_str = ""

        msg = (
            f"  Batch {batch_num}/{total_batches} "
            f"({len(batch_events)} events){eta_str}..."
        )
        print(msg, flush=True)

        try:
            result_map, headers = classify_batch(batch_events, few_shot, api_key, model)

            # Parse and record rate limit info
            rate_info = rate_limiter.parse_headers(headers)
            if rate_info:
                tokens_used = rate_info["tokens_used"]
                rate_limiter.record_request(tokens_used)
                msg = (
                    f"    Tokens: {tokens_used} used, "
                    f"{rate_info['tokens_remaining']} remaining "
                    f"({rate_limiter.get_status()})"
                )
                print(msg, flush=True)
            else:
                # Fallback: estimate tokens and accumulate for current window
                # record_request() treats its argument as cumulative, so add
                # to existing window total rather than passing incremental value
                cumulative_estimated = (
                    rate_limiter.tokens_used_in_window + estimated_tokens
                )
                rate_limiter.record_request(cumulative_estimated)
                msg = (
                    f"    Rate limit headers unavailable, "
                    f"using estimated {estimated_tokens} tokens "
                    f"(cumulative {cumulative_estimated} this window), "
                    f"fixed {FALLBACK_DELAY}s delay"
                )
                print(msg, flush=True)
                # Apply fallback delay to avoid overwhelming API
                time.sleep(FALLBACK_DELAY)

            for j, (_orig_idx, event) in enumerate(batch_items):
                cat = result_map.get(j + 1)
                if cat:
                    title_key = (event.get("title") or "").strip().lower()
                    rep_results[title_key] = cat

        except urllib.error.HTTPError as e:
            print(f"  ERROR in batch {batch_num}: {e}", file=sys.stderr)

            # Parse rate limit headers from failed request if available
            # to update tracker and avoid immediate retry hammering
            try:
                error_headers = e.headers
                rate_info = rate_limiter.parse_headers(error_headers)
                if rate_info:
                    tokens_used = rate_info["tokens_used"]
                    rate_limiter.record_request(tokens_used)
                    msg = (
                        f"    Updated rate limiter from error headers: "
                        f"{tokens_used} tokens used, "
                        f"{rate_info['tokens_remaining']} remaining"
                    )
                    print(msg, file=sys.stderr, flush=True)

                    # Calculate smart delay based on current state
                    cooldown = rate_limiter.calculate_delay(estimated_tokens)
                    if cooldown > 0:
                        msg = f"    Cooling down {cooldown:.1f}s before next batch..."
                        print(msg, file=sys.stderr, flush=True)
                        time.sleep(cooldown)
            except Exception as header_err:
                # If header parsing fails, use conservative fallback
                msg = f"    Could not parse error headers: {header_err}"
                print(msg, file=sys.stderr, flush=True)
                msg = f"    Applying conservative {FALLBACK_DELAY}s cooldown..."
                print(msg, file=sys.stderr, flush=True)
                time.sleep(FALLBACK_DELAY)

            # Continue with remaining batches even if one fails
            continue
        except Exception as e:
            print(f"  ERROR in batch {batch_num}: {e}", file=sys.stderr)
            # Apply conservative cooldown for non-HTTP errors
            msg = f"    Applying conservative {FALLBACK_DELAY}s cooldown..."
            print(msg, file=sys.stderr, flush=True)
            time.sleep(FALLBACK_DELAY)
            # Continue with remaining batches even if one fails
            continue

    # Fan out classifications to all events sharing each title
    for title_key, group in title_groups.items():
        cat = rep_results.get(title_key)
        if cat:
            for orig_idx, event in group:
                events[orig_idx]["category"] = cat
                classified += 1
                cats[cat] += 1
                uid = event.get("source_uid", "")
                title = event.get("title", "")
                print(f'  + {uid} "{title}" → {cat}')

    msg = (
        f"  Classified {classified}/{len(to_classify)} events "
        f"({len(representative_items)} unique titles)"
    )
    print(msg)
    for cat, count in cats.most_common():
        print(f"    {count:4d}  {cat}")

    if not dry_run:
        with path.open("w") as f:
            json.dump(events, f, ensure_ascii=False)
        print(f"  Wrote {filepath}")


def main():
    parser = argparse.ArgumentParser(
        description="Classify events in JSON files via Claude"
    )
    parser.add_argument("files", nargs="+", help="events.json files to classify")
    parser.add_argument(
        "--model", default="claude-haiku-4-5-20251001", help="Anthropic model"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print results without writing"
    )
    parser.add_argument(
        "--no-few-shot",
        action="store_true",
        help="Classify without curator-override examples (for A/B comparison)",
    )
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY env var not set", file=sys.stderr)
        sys.exit(1)

    overrides = [] if args.no_few_shot else fetch_overrides()
    if args.no_few_shot:
        print("Few-shot examples disabled (--no-few-shot)")
    elif overrides:
        print(f"Fetched {len(overrides)} curator overrides for few-shot examples")

    # Create shared rate limiter for all files in this run
    rate_limiter = RateLimitTracker()

    config = {"api_key": api_key, "model": args.model}
    for filepath in args.files:
        # Same-city examples first, so local corrections win the prompt cap
        city = Path(filepath).parent.name
        few_shot = build_few_shot(overrides, city)
        if few_shot:
            print(f"{city}: few-shot examples in prompt:{few_shot}")
        process_file(filepath, config, few_shot, args.dry_run, rate_limiter)


if __name__ == "__main__":
    main()
