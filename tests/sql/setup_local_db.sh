#!/bin/bash
# Apply all DDL files to local Supabase instance in correct order
# Run this after `supabase start` to initialize the schema

set -e

echo "Applying DDL files to local Supabase instance..."
echo ""

# Check if local Supabase is running
if ! supabase status > /dev/null 2>&1; then
  echo "ERROR: Local Supabase is not running"
  echo "Run: supabase start"
  exit 1
fi

# Get local database URL
DB_URL=$(supabase status --output json | jq -r '.DB_URL')

if [ -z "$DB_URL" ] || [ "$DB_URL" = "null" ]; then
  echo "ERROR: Could not get local database URL"
  exit 1
fi

# Apply DDL files in order (skipping cron jobs for local dev)
DDL_FILES=(
  "01_extensions.sql"
  "01a_admin_users.sql"
  "02_events.sql"
  "03_picks.sql"
  "04_feed_tokens.sql"
  "06_event_enrichments.sql"
  "07_distinct_cities.sql"
  "09_admin_github_users.sql"
  "10_user_settings.sql"
  "11_admin_google_users.sql"
  "12_source_suggestions.sql"
  "13_category_overrides.sql"
  "14_source_names.sql"
  "16_feeds.sql"
  "17_deduplicated_events.sql"
)

for file in "${DDL_FILES[@]}"; do
  filepath="supabase/ddl/$file"
  if [ -f "$filepath" ]; then
    echo "Applying $file..."
    psql "$DB_URL" -f "$filepath" > /dev/null 2>&1 || {
      echo "ERROR applying $file"
      psql "$DB_URL" -f "$filepath"
      exit 1
    }
  else
    echo "WARNING: $filepath not found, skipping"
  fi
done

echo ""
echo "✓ Schema initialized successfully"
echo ""
echo "You can now run tests with: ./tests/sql/run_tests_local.sh"
