#!/usr/bin/env python3
"""Generate a SQL verification query from the DDL files.

Parses supabase/ddl/*.sql to discover tables, columns, functions, indexes,
views, materialized views, and extensions, then emits a single SQL query
that checks whether each object exists in the target database.

How to use:
    1. Generate the SQL:
           python scripts/generate_verify_sql.py > verify.sql
    2. Open your Supabase project's SQL Editor (Dashboard > SQL Editor)
    3. Paste the contents of verify.sql and click Run
    4. Each row shows '✅ OK' or '❌ MISSING' with a pointer to the fix

Other options:
    python scripts/generate_verify_sql.py              # print to stdout
    python scripts/generate_verify_sql.py -o verify.sql  # write to file
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
DDL_DIR = ROOT / "supabase" / "ddl"
MIGRATIONS_DIR = ROOT / "supabase" / "migrations"

# Gist ID for the published verifier
def parse_ddl_files():
    """Extract database objects from DDL files."""
    tables = {}        # name -> ddl_file
    columns = {}       # (table, column) -> ddl_file
    functions = {}     # name -> ddl_file
    indexes = {}       # name -> ddl_file
    views = {}         # name -> ddl_file
    matviews = {}      # name -> ddl_file
    extensions = {}    # name -> ddl_file

    for path in sorted(DDL_DIR.glob("*.sql")):
        ddl_file = f"supabase/ddl/{path.name}"
        text = path.read_text()

        # Tables
        for m in re.finditer(
            r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:public\.)?(\w+)',
            text, re.IGNORECASE
        ):
            tables[m.group(1)] = ddl_file

        # Columns from CREATE TABLE blocks
        for tm in re.finditer(
            r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:public\.)?(\w+)\s*\((.*?)\);',
            text, re.IGNORECASE | re.DOTALL
        ):
            table_name = tm.group(1)
            body = tm.group(2)
            for line in body.split('\n'):
                line = line.strip().rstrip(',')
                if not line or line.startswith('--'):
                    continue
                # Skip constraints
                if re.match(r'(?:PRIMARY|UNIQUE|CHECK|FOREIGN|CONSTRAINT)', line, re.IGNORECASE):
                    continue
                col_match = re.match(r'(\w+)\s+', line)
                if col_match:
                    columns[(table_name, col_match.group(1))] = ddl_file

        # Functions
        for m in re.finditer(
            r'CREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+(?:public\.)?(\w+)',
            text, re.IGNORECASE
        ):
            functions[m.group(1)] = ddl_file

        # Indexes
        for m in re.finditer(
            r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)',
            text, re.IGNORECASE
        ):
            indexes[m.group(1)] = ddl_file

        # Views
        for m in re.finditer(
            r'CREATE\s+(?:OR\s+REPLACE\s+)?VIEW\s+(?:public\.)?(\w+)',
            text, re.IGNORECASE
        ):
            views[m.group(1)] = ddl_file

        # Materialized views
        for m in re.finditer(
            r'CREATE\s+MATERIALIZED\s+VIEW\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:public\.)?(\w+)',
            text, re.IGNORECASE
        ):
            matviews[m.group(1)] = ddl_file

        # Extensions
        for m in re.finditer(
            r'CREATE\s+EXTENSION\s+(?:IF\s+NOT\s+EXISTS\s+)?["\']?(\w+)',
            text, re.IGNORECASE
        ):
            extensions[m.group(1)] = ddl_file

    # Also check migration files for objects not yet in DDL
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        if path.name == "README.md":
            continue
        mig_file = f"supabase/migrations/{path.name}"
        text = path.read_text()
        for m in re.finditer(
            r'CREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+(?:public\.)?(\w+)',
            text, re.IGNORECASE
        ):
            name = m.group(1)
            if name not in functions:
                functions[name] = mig_file
        for m in re.finditer(
            r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)',
            text, re.IGNORECASE
        ):
            name = m.group(1)
            if name not in indexes:
                indexes[name] = mig_file

    return tables, columns, functions, indexes, views, matviews, extensions


def generate_sql(tables, columns, functions, indexes, views, matviews, extensions):
    """Generate the verification SQL."""
    from datetime import date
    lines = [
        f"-- Verify that a fork's Supabase database has all required objects.",
        f"-- Paste this into the Supabase SQL Editor and run it.",
        f"--",
        f"-- Each check returns '✅ OK' or '❌ MISSING' with the fix.",
        f"--",
        f"-- Auto-generated from DDL files on {date.today().isoformat()}.",
        f"-- Regenerate: python scripts/generate_verify_sql.py",
        "",
    ]

    checks = []

    # Tables
    checks.append(("'── TABLES ──'", "''"))
    for name, ddl in sorted(tables.items()):
        checks.append((
            f"'{name}'",
            f"CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables "
            f"WHERE table_schema='public' AND table_name='{name}') "
            f"THEN '✅ OK' ELSE '❌ MISSING — see {ddl}' END"
        ))

    # Key columns (only list columns that were added by migrations or are
    # particularly important for app functionality)
    key_columns = [
        ('events', 'city'), ('events', 'all_day'), ('events', 'source_uid'),
        ('events', 'image_url'), ('events', 'category'), ('events', 'transcript'),
        ('feeds', 'fallback_url'),
    ]
    checks.append(("'── KEY COLUMNS ──'", "''"))
    for table, col in key_columns:
        ddl = columns.get((table, col), 'supabase/ddl/')
        checks.append((
            f"'{table}.{col}'",
            f"CASE WHEN EXISTS (SELECT 1 FROM information_schema.columns "
            f"WHERE table_schema='public' AND table_name='{table}' AND column_name='{col}') "
            f"THEN '✅ OK' ELSE '❌ MISSING — see {ddl}' END"
        ))

    # Functions
    checks.append(("'── FUNCTIONS ──'", "''"))
    for name, ddl in sorted(functions.items()):
        checks.append((
            f"'{name}()'",
            f"CASE WHEN EXISTS (SELECT 1 FROM information_schema.routines "
            f"WHERE routine_schema='public' AND routine_name='{name}') "
            f"THEN '✅ OK' ELSE '❌ MISSING — see {ddl}' END"
        ))

    # Indexes (skip primary keys - those are automatic)
    checks.append(("'── INDEXES ──'", "''"))
    for name, ddl in sorted(indexes.items()):
        checks.append((
            f"'{name}'",
            f"CASE WHEN EXISTS (SELECT 1 FROM pg_indexes "
            f"WHERE schemaname='public' AND indexname='{name}') "
            f"THEN '✅ OK' ELSE '❌ MISSING — see {ddl}' END"
        ))

    # Views
    checks.append(("'── VIEWS ──'", "''"))
    for name, ddl in sorted(views.items()):
        checks.append((
            f"'{name}'",
            f"CASE WHEN EXISTS (SELECT 1 FROM information_schema.views "
            f"WHERE table_schema='public' AND table_name='{name}') "
            f"THEN '✅ OK' ELSE '❌ MISSING — see {ddl}' END"
        ))

    # Materialized views
    for name, ddl in sorted(matviews.items()):
        checks.append((
            f"'{name} (matview)'",
            f"CASE WHEN EXISTS (SELECT 1 FROM pg_matviews "
            f"WHERE schemaname='public' AND matviewname='{name}') "
            f"THEN '✅ OK' ELSE '❌ MISSING — see {ddl}' END"
        ))

    # Extensions
    checks.append(("'── EXTENSIONS ──'", "''"))
    for name, ddl in sorted(extensions.items()):
        checks.append((
            f"'{name}'",
            f"CASE WHEN EXISTS (SELECT 1 FROM pg_extension WHERE extname='{name}') "
            f"THEN '✅ OK' ELSE '❌ MISSING — enable in Supabase Dashboard > Database > Extensions' END"
        ))

    # Build the SQL
    parts = []
    for i, (section, status) in enumerate(checks):
        prefix = "SELECT" if i == 0 else "UNION ALL\nSELECT"
        parts.append(f"{prefix} {section} AS section, {status} AS status")

    lines.append("\n\n".join(parts) + ";")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate DB verification SQL from DDL files")
    parser.add_argument("-o", "--output", help="Write to file instead of stdout")
    args = parser.parse_args()

    tables, columns, functions, indexes, views, matviews, extensions = parse_ddl_files()

    total = (len(tables) + len([c for c in [
        ('events', 'city'), ('events', 'all_day'), ('events', 'source_uid'),
        ('events', 'image_url'), ('events', 'category'), ('events', 'transcript'),
    ]]) + len(functions) + len(indexes) + len(views) + len(matviews) + len(extensions))

    print(f"Found: {len(tables)} tables, {len(functions)} functions, "
          f"{len(indexes)} indexes, {len(views)} views, {len(matviews)} matviews, "
          f"{len(extensions)} extensions", file=sys.stderr)
    print(f"Total checks: {total}", file=sys.stderr)

    sql = generate_sql(tables, columns, functions, indexes, views, matviews, extensions)

    if args.output:
        Path(args.output).write_text(sql)
        print(f"Wrote {args.output}", file=sys.stderr)
    else:
        print(sql)


if __name__ == "__main__":
    main()
