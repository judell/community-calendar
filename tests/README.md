# Local Testing Setup

This directory contains local testing infrastructure for the community calendar database functions.

## Quick Start

```bash
# Start local Supabase
supabase start

# Apply base schema (DDL files)
./tests/setup_local_db.sh

# Run tests
./tests/run_tests_local.sh

# Stop when done
supabase stop
```

## Files

- `test_refresh_source_names.sql` - Test suite for `refresh_source_names()` function
- `run_tests_local.sh` - Test runner (supports --local or --linked)
- `setup_local_db.sh` - Applies all DDL files to local instance in correct order

## Why Local Testing?

Running tests against production is risky. Local testing via `supabase start` gives you:
- Isolated database that can be reset anytime
- No risk to production data
- Faster iteration (no network latency)
- Can test destructive operations safely

## Configuration

The `supabase/config.toml` has migrations and seed disabled for local dev because:
- Migrations expect incremental changes from a base state
- The DDL files represent the current complete schema
- `setup_local_db.sh` applies DDL files directly

## Troubleshooting

**If `supabase start` fails:**
```bash
supabase stop
docker system prune -f
supabase start
```

**If tests fail with "relation does not exist":**
```bash
./tests/setup_local_db.sh
```

**To reset local DB completely:**
```bash
supabase db reset --local
./tests/setup_local_db.sh
```
