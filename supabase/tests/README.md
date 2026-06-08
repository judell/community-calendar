# Database Tests

This directory contains Supabase-native pgTAP tests for database behavior.

## Canonical Command

```bash
supabase test db supabase/tests/
```

From the repo root, you can also use:

```bash
make test-sql
```

`make test-sql` is a convenience alias for the canonical Supabase command.

## Local Workflow

Prepare the local project database explicitly:

```bash
make setup-local
```

That starts local Supabase and applies migrations with `supabase db reset`.

Then run the database tests:

```bash
make test-sql
```

The test command does not reset the database automatically. If local schema state has drifted, run:

```bash
supabase db reset
```

## Why Local-Only

Database tests in this repo target a disposable local project database. They are not designed to run against production.

## Writing Tests

- Put new pgTAP files in `supabase/tests/`
- Test observable database behavior through public tables, views, and functions
- Prefer transaction-scoped tests (`BEGIN; ... ROLLBACK;`) when possible
- Keep assertions deterministic and isolated from existing local data

## Current Tests

- `test_refresh_source_names.sql` - verifies `refresh_source_names()` behavior, including comma-split sources, cleanup, idempotency, and malformed input handling

## Troubleshooting

### Local Supabase is not running

```bash
make setup-local
```

### Tests fail because relations or functions are missing

```bash
supabase db reset
```

### Supabase start fails locally

```bash
supabase stop
docker system prune -f
supabase start
```
