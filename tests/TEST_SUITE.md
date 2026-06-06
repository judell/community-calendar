# Test Suite

This repository uses a Makefile to orchestrate all tests.

## Quick Start

```bash
# Show all available commands
make help

# Run all tests
make test

# Run only Python tests
make test-python

# Run only SQL tests  
make test-sql
```

## Setup

### Python Tests

Python tests use pytest. Install dependencies:

```bash
# Option 1: Use the Makefile
make setup-python

# Option 2: Manual install
pip install -r requirements-dev.txt

# Option 3: Just pytest
pip install pytest
```

### SQL Tests

SQL tests require a local Supabase instance:

```bash
# One-time setup
make setup-local

# This starts Supabase and applies all DDL files
```

## Test Files

- **`tests/test_timezone_pipeline.py`** - Python/pytest tests for ICS timezone handling
- **`tests/sql/test_refresh_source_names.sql`** - SQL tests for `refresh_source_names()` function
- **`tests/sql/`** - SQL test infrastructure (see `tests/sql/README.md`)

## Continuous Integration

The GitHub Actions workflow runs:
- Python tests on every PR
- SQL tests (when configured)

## Teardown

```bash
# Stop local Supabase
make teardown-local

# Clean test artifacts
make clean
```

## Troubleshooting

### Python tests fail with "pytest not found"

```bash
make setup-python
```

### SQL tests fail with "Supabase not running"

```bash
make setup-local
```

### SQL tests fail with "relation does not exist"

```bash
# Re-apply schema
./tests/sql/setup_local_db.sh
```

## Adding New Tests

### Python Tests

1. Add test file to `tests/` directory with `test_` prefix
2. Update `Makefile` `test-python` target to include new file
3. Update this README

### SQL Tests

1. Add test file to `tests/sql/` directory with `.sql` extension
2. Create a runner script if needed (see `tests/sql/run_tests_local.sh`)
3. Update `Makefile` `test-sql` target
4. Update this README
5. See `tests/sql/README.md` for SQL-specific testing details
