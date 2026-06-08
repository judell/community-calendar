# 0001. Use Migrations as Schema Source of Truth

Date: 2026-06-06

## Status

Accepted

## Context

The project has both migrations (`supabase/migrations/`) and DDL files (`supabase/ddl/`). Initially, the schema was created manually in production from DDL files before migrations existed. The first migration (`20260330191500_add_city_column.sql`) added the `city` column via `ALTER TABLE`, not `CREATE TABLE`.

When we added local development support via `supabase start`, we faced an ordering problem:

1. Supabase's `db reset` command runs migrations **before** seed files
2. Our migrations assumed tables already existed (ALTER, not CREATE)
3. Result: `ERROR: relation "events" does not exist`

We initially worked around this by:
- Setting `[db.migrations] enabled = false` in `config.toml`
- Creating a manual setup script (`tests/sql/setup_local_db.sh`) that applied DDL files via `psql`
- Documenting this non-standard approach

This worked but created friction:
- New contributors expected `supabase db reset` to work (it's the standard workflow)
- Custom setup script was one more thing to maintain
- Two paths to schema truth: DDL files for local, migrations for production
- CI couldn't easily test migrations in isolation

## Decision

Use migrations as the single source of truth for schema:

1. Created `20260101000000_initial_schema.sql` containing the complete base schema (all tables, indexes, policies, functions, views) as it existed before migrations were introduced
2. Enabled `[db.migrations] = true` in `supabase/config.toml`
3. Removed `tests/sql/setup_local_db.sh` (no longer needed)
4. Updated `make setup-local` to use standard `supabase db reset`

Existing migrations (March 2026 onward) now work as incremental changes on top of the initial schema.

## Consequences

**Easier:**
- New contributors follow familiar Supabase patterns — `supabase db reset` just works
- No custom setup scripts to learn or maintain
- CI can test migrations in standard ways
- Schema changes have a clear, ordered history in one place
- Local dev matches production's migration path

**Harder:**
- Initial migration is large (427 lines) — but it's write-once, read-rarely
- DDL files in `supabase/ddl/` are now documentation, not executable schema
  - Must keep them in sync with migrations (current practice already)
  - Could generate them from migrations, but that adds build complexity

**Unchanged:**
- Migration workflow for production (SQL Editor or `supabase db push`)
- DDL files still serve as human-readable documentation of current state

## Alternatives Considered

### Keep DDL-first approach

Continue with `migrations = false` and manual `setup_local_db.sh` script.

**Rejected because:**
- Fights against Supabase's tooling expectations
- Every new contributor asks "why doesn't `supabase db reset` work?"
- Custom scripts are maintenance burden
- DDL files would drift from production over time

### Use seed.sql with schema + reorder execution

Put the base schema in `seed.sql` and try to make Supabase run it before migrations.

**Rejected because:**
- Supabase's execution order is: migrations → seed (by design, not configurable)
- Would require forking/patching Supabase CLI or hacking around its workflow
- Seed files are meant for test data, not schema

### Generate DDL from migrations

Automatically generate `supabase/ddl/*.sql` files from the migration history.

**Deferred because:**
- Adds build complexity
- DDL files are currently hand-maintained for clarity/organization
- Migration history doesn't map 1:1 to DDL files (one DDL file = multiple migrations)
- Can revisit if DDL/migration drift becomes a problem

### Start fresh with only migrations

Delete DDL files entirely, treat migrations as the only schema documentation.

**Rejected because:**
- DDL files serve as architecture documentation (one file per table/concept)
- Migration files are change-oriented, not concept-oriented
- DDL files make it easier to understand "what does the schema look like today?"
