#!/bin/bash
# Regression test runner for community-calendar (Santa Rosa)
#
# Test strategy: baselines + one hand-written spec
#
#   pick-roundtrip    — baseline (inspector trace → generated spec)
#   search-roundtrip  — baseline (inspector trace → generated spec)
#   capture-roundtrip — hand-written spec (traces/specs/capture-roundtrip.spec.ts)
#
# capture-roundtrip requires a hand-written spec because:
#   1. File upload uses Playwright's setInputFiles(), which can't be captured
#      by the inspector (it bypasses the native file dialog).
#   2. The audio capture flow makes two POSTs to the same endpoint (extract
#      then commit). The generated spec's waitForResponse catches the wrong
#      one. The hand-written spec handles timing explicitly.
#
# Use `./test.sh test-all` to run everything (specs + baselines).

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
TRACE_TOOLS="$APP_DIR/trace-tools"
REPO_ROOT="$APP_DIR/../.."

# Keep repo copies in sync with trace-tools
cp "$TRACE_TOOLS/xs-trace.js" "$REPO_ROOT/xmlui/xs-trace.js"
cp "$TRACE_TOOLS/xs-diff.html" "$REPO_ROOT/xmlui/xmlui/xs-diff.html"

SUPABASE_URL="https://dzpdualvwspgqghrysyz.supabase.co"
TEST_USER_EMAIL="ci-test@community-calendar.test"

# Clean up test user's picks and event_enrichments before each test run
reset_fixtures() {
  if [ -z "$SUPABASE_KEY" ]; then
    echo "Warning: \$SUPABASE_KEY not set — skipping fixture reset"
    return
  fi

  # Look up the test user's ID
  USER_ID=$(curl -s "${SUPABASE_URL}/auth/v1/admin/users" \
    -H "Authorization: Bearer ${SUPABASE_KEY}" \
    -H "apikey: ${SUPABASE_KEY}" \
    | node -e "
      const data = JSON.parse(require('fs').readFileSync('/dev/stdin','utf8'));
      const user = data.users.find(u => u.email === '${TEST_USER_EMAIL}');
      if (user) process.stdout.write(user.id);
    ")

  if [ -z "$USER_ID" ]; then
    echo "Warning: test user not found — skipping fixture reset"
    return
  fi

  # Delete picks for test user
  curl -s -o /dev/null -w "" \
    "${SUPABASE_URL}/rest/v1/picks?user_id=eq.${USER_ID}" \
    -X DELETE \
    -H "Authorization: Bearer ${SUPABASE_KEY}" \
    -H "apikey: ${SUPABASE_KEY}" \
    -H "Content-Type: application/json"

  # Delete event_enrichments created by test user
  curl -s -o /dev/null -w "" \
    "${SUPABASE_URL}/rest/v1/event_enrichments?user_id=eq.${USER_ID}" \
    -X DELETE \
    -H "Authorization: Bearer ${SUPABASE_KEY}" \
    -H "apikey: ${SUPABASE_KEY}" \
    -H "Content-Type: application/json"

  # Ensure user_settings row exists (upsert with clean defaults)
  curl -s -o /dev/null -w "" \
    "${SUPABASE_URL}/rest/v1/user_settings?on_conflict=user_id,city" \
    -X POST \
    -H "Authorization: Bearer ${SUPABASE_KEY}" \
    -H "apikey: ${SUPABASE_KEY}" \
    -H "Content-Type: application/json" \
    -H "Prefer: resolution=merge-duplicates" \
    -d "{\"user_id\": \"${USER_ID}\", \"city\": \"santarosa\", \"hidden_sources\": [], \"one_click_pick\": false}"

  echo "Fixtures reset for ${TEST_USER_EMAIL}"
}

source "$TRACE_TOOLS/test-base.sh"
