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
pip install -r requirements-dev.txt
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
- `supabase/tests/test_refresh_source_names.sql` - pgTAP database tests for `refresh_source_names()`
- `supabase/tests/README.md` - database-test-specific setup, workflow, and troubleshooting

## Continuous Integration

The PR workflow runs:
- Feed/scraper validation
- Python tests
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
