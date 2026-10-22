# Test Suite

This repository uses a Makefile to orchestrate its common test entrypoints.

## Quick Start

```bash
# Show available commands
make help

# Run the default test suite (Python only)
make test

# Run Python tests directly
make test-python

# Run database tests directly
make test-sql
```

## Setup

### Python Tests

Python tests use pytest. Install dependencies with either:

```bash
make setup-python
```

or:

```bash
uv sync
```

### Database Tests

Database tests use Supabase-native pgTAP against the local project database.

```bash
# Start local Supabase and apply migrations
make setup-local

# Run database tests
make test-sql
```

The canonical database test harness is:

```bash
supabase test db supabase/tests/
```

`make test-sql` is a convenience alias for that command.

## Test Files

- `tests/test_timezone_pipeline.py` - Python/pytest tests for ICS timezone handling
- `tests/test_city_filter.py` - shared geo-filter matcher (allowed town names and ZIP codes, out-of-area and venue-only cases)
- `tests/test_visit_bloomington.py` - Visit Bloomington Simpleview REST API scraper (paging, occurrence expansion, geo prefilter, attribution)
- `tests/test_wfiu_community_calendar.py` - WFIU Community Calendar HTML scraper (Horizon date-filtered paging, occurrence cards, detail enrichment and postal geography, detail-failure fallback, relative-href normalization, run-history degradation guard, registration smoke-test page cap, aggregator registration contract, stale-URL guard no-op)
- `tests/test_tribe_fetch.py` - the fetch contract shared by both Tribe REST scrapers, parameterized over `scrapers/lib/tribe_events.py` and `scrapers/tribe_rest.py` (broken first page fails, dormant 200+empty stays quiet, later-page failure keeps fetched pages)
- `tests/test_tribe_events.py` - Tribe Events REST base scraper headers and event parsing
- `tests/test_tribe_rest.py` - parameterized Tribe REST scraper `run()` output (dormant writes a valid empty ICS, first-page failure writes no calendar)
- `tests/test_monroe_county_history_center.py` - SiteGround `sgcaptcha` handling: a blocked first page fails the run and writes no calendar, a later-page non-400 error keeps fetched pages and logs its status, the end-of-list 400 stays quiet
- `tests/test_report.py` - feed-health report keeps a `feeds.txt` source with no `.ics` as a failed build, and drops a source `feeds.txt` no longer lists
- `tests/test_base_scraper.py` - base scraper `X-SOURCE-URL` and `GEO` emission
- `tests/test_validate_pr_feeds.py` - PR feed/scraper registration validation against the DB-first contract
- `tests/test_add_scraper.py` - DB-first registration helper: smoke-test bounds are environment-only (the registered command stays unbounded)
- `supabase/tests/test_refresh_source_names.sql` - pgTAP database tests for `refresh_source_names()`
- `supabase/tests/test_deduplicated_events.sql` - pgTAP tests for route persistence columns and the `deduplicated_events` view (group collapse, NULL isolation, structured source names, representative)
- `supabase/functions/my-picks/dedupe_test.ts` - Deno tests for the saved-picks group collapse (one ICS entry per stored group, NULL isolation, canonical representative). Run with `make test-deno` or the full `make test` command; CI runs these in its dedicated Deno job.
- `supabase/tests/README.md` - database-test-specific setup, workflow, and troubleshooting

## Continuous Integration

The PR workflow runs:
- Feed/scraper validation
- Python tests
- Deno edge-function tests
- Database tests

## Teardown

```bash
# Stop local Supabase
make teardown-local

# Clean Python test artifacts
make clean
```

## Troubleshooting

### Python tests fail with "pytest not found"

```bash
make setup-python
```

### Database tests fail with "Local Supabase is not running"

```bash
make setup-local
```

### Database tests fail with "relation does not exist"

```bash
supabase db reset
```

## Adding New Tests

### Python Tests

1. Add a file under `tests/` with a `test_` prefix
2. `make test-python` will discover it automatically
3. Update this document if the new coverage is worth documenting

### Database Tests

1. Add a `.sql` pgTAP test file under `supabase/tests/`
2. Keep the test focused on observable database behavior
3. Run it with `supabase test db supabase/tests/` or `make test-sql`
4. Update `supabase/tests/README.md` if the workflow or prerequisites change
5. Update this document if the new coverage changes the repo-level testing story
