#!/bin/bash
# Run tests for refresh_source_names() function
# Usage: 
#   ./run_tests_local.sh          # runs against local Supabase
#   ./run_tests_local.sh --linked # runs against production (NOT RECOMMENDED)

MODE="${1:---local}"

if [ "$MODE" = "--local" ]; then
  echo "Running tests against LOCAL Supabase instance..."
  
  # Check if running
  if ! supabase status > /dev/null 2>&1; then
    echo "Starting Supabase..."
    supabase start
  else
    echo "Supabase is already running."
  fi
  echo ""
  
  # Get local database URL
  DB_URL=$(supabase status --output json | jq -r '.DB_URL')
  
  if [ -z "$DB_URL" ] || [ "$DB_URL" = "null" ]; then
    echo "ERROR: Could not get local database URL"
    exit 1
  fi
  
  echo "Running test suite..."
  psql "$DB_URL" -f tests/sql/test_refresh_source_names.sql
  
  echo ""
  echo "Local instance still running. To stop: supabase stop"
else
  echo "⚠️  WARNING: Running tests against PRODUCTION database"
  read -p "Are you sure? (yes/no): " confirm
  if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 1
  fi
  
  echo "Running test suite against production..."
  # For production, we need to use psql with SUPABASE_DB_URL
  if [ -z "$SUPABASE_DB_URL" ]; then
    echo "ERROR: SUPABASE_DB_URL not set"
    echo "Set it to your production database connection string"
    exit 1
  fi
  
  psql "$SUPABASE_DB_URL" -f tests/sql/test_refresh_source_names.sql
fi
